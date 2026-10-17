"""A plain PyTorch training loop (no Trainer), used for both stages."""
import json
import math
import os
import random
import time
from dataclasses import asdict, dataclass

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup

from training.data import PairDataset, make_collate
from training.model import init_head_bias, load_model, masked_mse


@dataclass
class TrainConfig:
    model: str                      # HF model id, or a stage-1 checkpoint folder for stage 2
    out_dir: str
    epochs: int = 4
    batch_size: int = 16
    lr: float = 2e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    max_length: int = 256
    grad_accum: int = 1
    patience: int = 2               # early stopping: epochs without validation improvement
    seed: int = 42
    init_bias: bool = True          # False for stage 2 (the stage-1 head is already calibrated)


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _autocast_dtype():
    # bf16 where supported (A100/L4). DeBERTa-v3 is unstable in fp16, so otherwise use fp32.
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return None


def evaluate_loss(model, loader, device):
    """Validation RMSE for valence and arousal (only where labeled)."""
    model.eval()
    se = torch.zeros(2); n = torch.zeros(2)
    with torch.no_grad():
        for batch in loader:
            targets, mask = batch.pop("targets"), batch.pop("mask")
            pred = model(**{k: v.to(device) for k, v in batch.items()}).logits.float().cpu().clamp(1, 9)
            se += ((pred - targets) ** 2 * mask).sum(0); n += mask.sum(0)
    rmse = (se / n.clamp(min=1)).sqrt()
    return {"rmse_v": rmse[0].item(), "rmse_a": rmse[1].item() if n[1] > 0 else float("nan"),
            "score": rmse[0].item() + (rmse[1].item() if n[1] > 0 else 0.0)}


def train(cfg: TrainConfig, train_rows, val_rows):
    set_seed(cfg.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = load_model(cfg.model)
    if cfg.init_bias:
        init_head_bias(model)
    model.to(device)

    collate = make_collate(tokenizer, cfg.max_length)
    train_loader = DataLoader(PairDataset(train_rows), batch_size=cfg.batch_size, shuffle=True, collate_fn=collate)
    val_loader = DataLoader(PairDataset(val_rows), batch_size=cfg.batch_size * 2, collate_fn=collate)

    no_decay = ["bias", "LayerNorm.weight", "layer_norm.weight", "norm.weight"]
    params = [
        {"params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
         "weight_decay": cfg.weight_decay},
        {"params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
         "weight_decay": 0.0},
    ]
    optimizer = torch.optim.AdamW(params, lr=cfg.lr)
    steps = math.ceil(len(train_loader) / cfg.grad_accum) * cfg.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(steps * cfg.warmup_ratio), steps)
    amp_dtype = _autocast_dtype()

    best, bad_epochs, history = float("inf"), 0, []
    os.makedirs(cfg.out_dir, exist_ok=True)
    print(f"Training {cfg.model} on {len(train_rows):,} examples ({device}, "
          f"{'bf16' if amp_dtype else 'fp32'}), validating on {len(val_rows):,}")

    for epoch in range(1, cfg.epochs + 1):
        model.train(); start = time.time(); running = 0.0
        for step, batch in enumerate(train_loader, 1):
            targets, mask = batch.pop("targets").to(device), batch.pop("mask").to(device)
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.autocast(device_type="cuda", dtype=amp_dtype, enabled=amp_dtype is not None):
                pred = model(**batch).logits.float()
            loss = masked_mse(pred, targets, mask) / cfg.grad_accum
            loss.backward()
            running += loss.item() * cfg.grad_accum
            if step % cfg.grad_accum == 0 or step == len(train_loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step(); scheduler.step(); optimizer.zero_grad()

        val = evaluate_loss(model, val_loader, device)
        val.update(epoch=epoch, train_loss=running / len(train_loader), seconds=round(time.time() - start))
        history.append(val)
        print(f"epoch {epoch}: train loss {val['train_loss']:.3f} | val RMSE valence {val['rmse_v']:.3f}"
              f" arousal {val['rmse_a']:.3f} | {val['seconds']}s")

        if val["score"] < best:
            best, bad_epochs = val["score"], 0
            model.save_pretrained(cfg.out_dir); tokenizer.save_pretrained(cfg.out_dir)
            print(f"  saved best checkpoint to {cfg.out_dir}")
        else:
            bad_epochs += 1
            if bad_epochs >= cfg.patience:
                print("  early stopping"); break

    with open(os.path.join(cfg.out_dir, "training_log.json"), "w") as f:
        json.dump({"config": asdict(cfg), "history": history}, f, indent=2)
    return history
