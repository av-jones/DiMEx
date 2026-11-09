"""Display pieces for the v2 pages: score bars, intensity meters, stacked intensity bars
(small HTML snippets) and the valence-arousal map (Altair)."""
import altair as alt
import pandas as pd

# Whites, cool greys and blues. Intensity and severity read as light -> dark blue.
INK, MUTED, SOFT, LINE = "#1B2430", "#5B6472", "#E8ECF2", "#D9DEE6"
POS, NEG, NEU = "#2F6FD0", "#0B2E59", "#8A94A3"      # effectiveness, side effects, satisfaction
MILD, MOD, DIST = "#5BBF85", "#F2C14E", "#C83E3E"     # mild (green), moderate (yellow), distressing (red)
# Intensity of effectiveness and satisfaction isn't good or bad (strong relief is intense), so their
# gauges use a neutral light-to-dark blue instead of green/yellow/red.
CALM_B, MOD_B, STRONG_B = "#BCD2F3", "#5C8FD6", "#0B2E59"
BAND_COLORS = {"Mild": MILD, "Calm": MILD, "Moderate": MOD, "Distressing": DIST, "Strong": DIST}
ASPECT_COLORS = {"effectiveness": POS, "side_effect": NEG, "satisfaction": NEU}


def person_icon(size=18, color=NEG):
    """A small person glyph (head and shoulders), white on a navy circle: marks the patient's own rating."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" style="display:block">'
            f'<circle cx="12" cy="12" r="11.5" fill="{color}" stroke="#fff" stroke-width="1"/>'
            f'<circle cx="12" cy="9" r="3.6" fill="#fff"/>'
            f'<path d="M5.2 19.2c1.2-3.3 3.8-5 6.8-5s5.6 1.7 6.8 5" fill="#fff"/></svg>')


def dimex_icon(size=18):
    """The DiMEx logo mark (crossing axes, a large blue dot top right, a small navy dot bottom left) in a white
    circle with a blue ring: marks DiMEx's prediction, next to the patient's person icon."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" style="display:block">'
            f'<circle cx="12" cy="12" r="11.2" fill="#fff" stroke="{POS}" stroke-width="1.6"/>'
            f'<path d="M12 4v16M4 12h16" stroke="#8A97AB" stroke-width="1.4" stroke-linecap="round"/>'
            f'<circle cx="16.4" cy="7.6" r="3.7" fill="{POS}"/>'
            f'<circle cx="7.9" cy="16.1" r="2.3" fill="{NEG}"/></svg>')


def accuracy_grid(rows):
    """'How close' table for a navy panel: one row per aspect, three metrics as plain numbers.
    rows: dicts with Aspect, Scale ("1–5"), MAE, within1 (0-1), Kappa. Hover a number for what it means."""
    head = ('<div class="acc-grid"><div class="acc-h"></div>'
            '<div class="acc-h">Average gap (MAE)</div><div class="acc-h">Within ±1 point</div>'
            '<div class="acc-h">Agreement (κ)</div>')
    body = ""
    for r in rows:
        span = int(r["Scale"].split("–")[1]) - 1
        body += (f'<div class="acc-name">{r["Aspect"]}<span>scale {r["Scale"]}</span></div>'
                 f'<div class="acc-val" title="Off by {r["MAE"]:.2f} rating points on average, out of a possible {span}">'
                 f'{r["MAE"]:.2f}</div>'
                 f'<div class="acc-val" title="Share of predictions within 1 point of the patient">'
                 f'{r["within1"]:.0%}</div>'
                 f'<div class="acc-val" title="Cohen\'s kappa on low/mid/high classes: 0 = chance, 1 = perfect">'
                 f'{r["Kappa"]:.2f}</div>')
    return head + body + "</div>"


def compare_bar(patient, model, scale):
    """The patient's rating and the model's prediction as two markers on one 1..scale track,
    joined by a line whose length is the disagreement. Patient = person icon, model = the DiMEx mark."""
    def pct(x):
        return (x - 1) / (scale - 1) * 100
    lo, hi = sorted([pct(patient), pct(model)])
    ticks = range(1, scale + 1) if scale == 5 else range(1, 11)
    tick_html = "".join(f"<span>{t}</span>" for t in ticks)
    return f"""
<div role="img" aria-label="Patient {patient:g}, model {model:.1f}, out of {scale}" style="margin:16px 10px 2px">
  <div style="position:relative;height:6px;background:{SOFT};border-radius:3px">
    <div style="position:absolute;left:{lo:.1f}%;width:{hi - lo:.1f}%;top:0;bottom:0;background:#9DB7E0;
                border-radius:3px"></div>
    <div title="DiMEx" style="position:absolute;left:calc({pct(model):.1f}% - 12px);top:-9px">{dimex_icon(24)}</div>
    <div title="Patient" style="position:absolute;left:calc({pct(patient):.1f}% - 12px);top:-9px;z-index:1">
      {person_icon(24)}</div>
  </div>
  <div style="display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:12px;
              color:{MUTED};margin:10px -4px 0">{tick_html}</div>
</div>"""


COMPARE_KEY = (f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px;vertical-align:middle">'
               f'{person_icon(18)}Patient\'s rating</span>'
               f'<span style="display:inline-flex;align-items:center;gap:6px;vertical-align:middle">'
               f'{dimex_icon(18)}DiMEx prediction</span>')


def score_bar(value, scale, color):
    """A filled bar with a marker, on a 1..scale axis."""
    pct = (value - 1) / (scale - 1) * 100
    ticks = [1, 2, 3, 4, 5] if scale == 5 else [1, 4, 7, 10]
    tick_html = "".join(f"<span>{t}</span>" for t in ticks)
    return f"""
<div role="img" aria-label="{value:.1f} out of {scale}" style="margin:4px 0 2px">
  <div style="position:relative;height:10px;background:{SOFT};border-radius:5px">
    <div style="position:absolute;left:0;top:0;bottom:0;width:{pct:.0f}%;background:{color};border-radius:5px"></div>
    <div style="position:absolute;left:calc({pct:.0f}% - 7px);top:-4px;width:14px;height:14px;border-radius:50%;
                background:#fff;border:3px solid {color};box-sizing:border-box"></div>
  </div>
  <div style="display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:11px;
              color:{MUTED};margin-top:4px">{tick_html}</div>
</div>"""


STAR_ON, STAR_OFF = "#2F6FD0", "#D3DAE4"
STAR_NOTE = {}


def to_stars(value, scale, kind):
    """A score as 0-5 stars, where more stars is always better. Side-effect severity (higher is
    worse) is flipped; satisfaction (1-10) is halved."""
    if kind == "side_effect":
        value = scale + 1 - value
    return max(0.0, min(5.0, value * 5 / scale))


def star_rating(value, scale, kind, size=22):
    """Five stars filled to the score, with fractional fill (e.g. 3.6 stars)."""
    stars = to_stars(value, scale, kind)
    row = "★★★★★"
    note = STAR_NOTE.get(kind, "")
    note_html = f'<span style="font-size:12px;color:{MUTED};margin-left:8px">{note}</span>' if note else ""
    return f"""
<div role="img" aria-label="{stars:.1f} out of 5 stars" style="display:flex;align-items:center;margin:2px 0 4px">
  <span style="position:relative;display:inline-block;font-size:{size}px;line-height:1;letter-spacing:2px">
    <span style="color:{STAR_OFF}">{row}</span>
    <span style="position:absolute;left:0;top:0;width:{stars / 5 * 100:.0f}%;overflow:hidden;white-space:nowrap;color:{STAR_ON}">{row}</span>
  </span>
  <span style="font-size:13px;color:{MUTED};margin-left:8px">{stars:.1f} / 5</span>{note_html}
</div>"""


BREAKDOWN_SHORT = {
    "Highly effective": "Highly effective", "Considerably effective": "Considerably",
    "Moderately effective": "Moderately", "Marginally effective": "Marginally", "Ineffective": "Ineffective",
    "No side effects": "None", "Mild side effects": "Mild", "Moderate side effects": "Moderate",
    "Severe side effects": "Severe", "Extremely severe side effects": "Extremely severe",
    "Satisfied": "Satisfied (7–10)", "Mixed": "Mixed (5–6)", "Dissatisfied": "Dissatisfied (1–4)",
}
BREAKDOWN_COLORS = {
    "No side effects": MILD, "Mild side effects": MILD, "Moderate side effects": MOD,
    "Severe side effects": DIST, "Extremely severe side effects": DIST,
    "Satisfied": POS, "Mixed": NEU, "Dissatisfied": NEG,
}


def breakdown(rows):
    """Bars for the share of reviews at each level: rows = [(level name, share 0-1), ...]."""
    out = []
    for name, share in rows:
        color = BREAKDOWN_COLORS.get(name, POS)
        out.append(
            f'<div style="display:grid;grid-template-columns:118px 1fr 38px;align-items:center;gap:8px;margin:5px 0">'
            f'<span style="font-size:12px;color:#3E4652;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
            f'{BREAKDOWN_SHORT.get(name, name)}</span>'
            f'<div role="img" aria-label="{share:.0%} of reviews" style="height:9px;background:{SOFT};'
            f'border-radius:5px;overflow:hidden"><div style="height:100%;width:{share * 100:.0f}%;'
            f'background:{color};border-radius:5px"></div></div>'
            f'<span style="font-size:12px;color:{MUTED};text-align:right">{share:.0%}</span></div>')
    return '<div style="margin-top:6px">' + "".join(out) + "</div>"


def split_tag(kind):
    word = "Split experiences" if kind == "side_effect" else "Split opinions"
    return (f'<span title="Many reviews at both ends: the average hides a disagreement" '
            f'style="font-size:11px;font-weight:600;color:#6B4A00;background:#FCEFC7;border-radius:999px;'
            f'padding:2px 8px;margin-left:8px;white-space:nowrap">{word}</span>')


def intensity_gauge(arousal, kind="side_effect", size=200, caption=None):
    """A half-circle gauge for intensity (arousal, 1-9): a needle over three bands, calm to intense.
    Band edges match the intensity words (core.explain.INTENSITY_CUTS)."""
    import math
    from core.explain import INTENSITY_CUTS, intensity_band
    cx, cy, r, w = 100, 100, 78, 16

    def pt(value, radius):                    # 1 -> far left, 9 -> far right, over the top
        ang = math.pi * (1 - (value - 1) / 8)
        return cx + radius * math.cos(ang), cy - radius * math.sin(ang)

    def arc(v0, v1, color):
        (x0, y0), (x1, y1) = pt(v0, r), pt(v1, r)
        return (f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 0 1 {x1:.1f} {y1:.1f}" fill="none" '
                f'stroke="{color}" stroke-width="{w}"/>')

    a = max(1.0, min(9.0, float(arousal)))
    (nx, ny) = pt(a, r - 22)
    edges = [1, *INTENSITY_CUTS, 9]
    bands = "".join(arc(edges[i] + (0.04 if i else 0), edges[i + 1] - (0.04 if i < 2 else 0), c)
                    for i, c in enumerate((MILD, MOD, DIST) if kind == "side_effect"
                                          else (CALM_B, MOD_B, STRONG_B)))
    word = intensity_band(a, kind)
    low = "Mild" if kind == "side_effect" else "Calm"
    caption_html = (f'<div style="font-size:12px;color:{MUTED};text-align:center;margin-top:2px">{caption}</div>'
                    if caption else "")
    return f"""
<div style="display:flex;flex-direction:column;align-items:center">
<svg viewBox="0 0 200 128" width="{size}" role="img" aria-label="Intensity {a:.1f} out of 9: {word}">
  {bands}
  <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="7" fill="{INK}"/>
  <text x="14" y="122" font-size="11" fill="{MUTED}" font-family="sans-serif">{low}</text>
  <text x="186" y="122" font-size="11" fill="{MUTED}" text-anchor="end" font-family="sans-serif">Intense</text>
</svg>
<div style="font-size:17px;font-weight:600;color:{INK};margin-top:-4px">{word}
  <span style="font-size:12px;font-weight:400;color:{MUTED};font-family:'IBM Plex Mono',monospace">{a:.1f}/9</span></div>
{caption_html}
</div>"""

def stacked(shares, height=14):
    """shares: dict band -> fraction, in the order Mild, Moderate, Distressing."""
    parts = [f'<div style="width:{shares.get(b, 0) * 100:.1f}%;background:{BAND_COLORS[b]}"></div>'
             for b in ("Mild", "Moderate", "Distressing") if shares.get(b, 0) > 0]
    aria = ", ".join(f"{shares.get(b, 0):.0%} {b.lower()}" for b in ("Mild", "Moderate", "Distressing"))
    return (f'<div role="img" aria-label="{aria}" style="display:flex;height:{height}px;'
            f'border-radius:{height // 2}px;overflow:hidden;gap:2px;background:{SOFT}">{"".join(parts)}</div>')


def legend():
    items = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
                    f'<span style="width:10px;height:10px;border-radius:3px;background:{BAND_COLORS[b]}"></span>{b}</span>'
                    for b in ("Mild", "Moderate", "Distressing"))
    return f'<div style="font-size:{size}px;color:{MUTED}">{items}</div>'


_CORNERS = pd.DataFrame([
    {"v": 1.2, "a": 8.75, "t": "Distressing", "align": "left"},
    {"v": 8.8, "a": 8.75, "t": "Strong relief", "align": "right"},
    {"v": 1.2, "a": 1.25, "t": "Mildly unpleasant", "align": "left"},
    {"v": 8.8, "a": 1.25, "t": "Calm, content", "align": "right"},
])


# Quadrant tints: positive side light blue, negative side blue-grey, the intense (top) half a shade deeper,
# so the four regions read clearly against a white plot
_QUADS = pd.DataFrame([
    {"v": 1, "v2": 5, "a": 5, "a2": 9, "fill": "#E6EAF2"},   # negative, intense
    {"v": 1, "v2": 5, "a": 1, "a2": 5, "fill": "#F1F3F8"},   # negative, calm
    {"v": 5, "v2": 9, "a": 5, "a2": 9, "fill": "#DFEBFB"},   # positive, intense
    {"v": 5, "v2": 9, "a": 1, "a2": 5, "fill": "#EEF4FD"},   # positive, calm
])
AXIS_INK = "#3A4352"


SIDE_GROUPS = (["Mild", "Moderate", "Distressing"], [MILD, MOD, DIST], "Intensity")
EFFECT_GROUPS = (["Effective", "Moderate", "Not effective"], [POS, NEU, NEG], "Effectiveness")


def va_map(points=None, dots=None, height=330, groups=SIDE_GROUPS, big=False):
    """Valence (x) by arousal (y), 1-9, with plain-language corners.
    points: DataFrame v, a, label, color (labeled markers).
    dots: DataFrame v, a and a "band" or "group" column, colored by groups = (names, colors, title).
    big=True: larger text and dots, for a full-width chart."""
    corner_px, dot_size = (14, 170) if big else (11, 120)
    x = alt.X("v:Q", scale=alt.Scale(domain=[1, 9]), title="Valence: negative → positive",
              axis=alt.Axis(values=[1, 3, 5, 7, 9], format="d", grid=False))
    y = alt.Y("a:Q", scale=alt.Scale(domain=[1, 9]), title="Arousal: calm → intense",
              axis=alt.Axis(values=[1, 3, 5, 7, 9], format="d", grid=False))
    mid = pd.DataFrame({"v": [5], "a": [5]})
    layers = [
        alt.Chart(_QUADS).mark_rect().encode(x=x, x2="v2:Q", y=y, y2="a2:Q", color=alt.Color("fill:N", scale=None)),
        alt.Chart(mid).mark_rule(strokeDash=[4, 4], color="#A3AEBE").encode(x="v:Q"),
        alt.Chart(mid).mark_rule(strokeDash=[4, 4], color="#A3AEBE").encode(y="a:Q"),
    ]
    for align in ("left", "right"):
        layers.append(alt.Chart(_CORNERS[_CORNERS["align"] == align])
                      .mark_text(align=align, fontSize=corner_px, fontWeight=600, color=INK).encode(x=x, y=y, text="t:N"))
    if dots is not None and len(dots):
        col = "band" if "band" in dots else "group"
        layers.append(alt.Chart(dots).mark_circle(size=dot_size, opacity=0.55, stroke="white", strokeWidth=0.6).encode(
            x=x, y=y,
            color=alt.Color(f"{col}:N", scale=alt.Scale(domain=groups[0], range=groups[1]), legend=None),
            tooltip=[alt.Tooltip(f"{col}:N", title=groups[2]), alt.Tooltip("v:Q", title="Valence", format=".1f"),
                     alt.Tooltip("a:Q", title="Arousal", format=".1f")]))
    if points is not None and len(points):
        layers.append(alt.Chart(points).mark_point(size=220, filled=True, opacity=1, stroke="white",
                                                   strokeWidth=2).encode(
            x=x, y=y, color=alt.Color("color:N", scale=None),
            tooltip=[alt.Tooltip("label:N", title="Aspect"), alt.Tooltip("v:Q", title="Valence", format=".1f"),
                     alt.Tooltip("a:Q", title="Arousal", format=".1f")]))
        layers.append(alt.Chart(points).mark_text(align="left", dx=12, fontSize=12, fontWeight=600,
                                                  color=INK).encode(x=x, y=y, text="label:N"))
    return (alt.layer(*layers).properties(height=height).configure(background="#FFFFFF")
            .configure_view(stroke=LINE, fill="#FFFFFF")
            .configure_axis(labelColor=AXIS_INK, titleColor=AXIS_INK, domain=False, ticks=False, titleFontWeight=400,
                            labelFontSize=14 if big else 11, titleFontSize=15 if big else 11))


def group_legend(groups, size=13):
    names, colors, _ = groups
    items = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
                    f'<span style="width:10px;height:10px;border-radius:3px;background:{c}"></span>{n}</span>'
                    for n, c in zip(names, colors))
    return f'<div style="font-size:{size}px;color:{MUTED}">{items}</div>'


def share_bars(rows, color=POS):
    """Labeled bars: rows = [(label, share 0-1, n reviews)]."""
    out = []
    for label, share, n in rows:
        out.append(
            f'<div style="display:grid;grid-template-columns:150px 1fr 92px;align-items:center;gap:10px;margin:7px 0">'
            f'<span style="font-size:13px;color:{INK}">{label}</span>'
            f'<div role="img" aria-label="{share:.0%}" style="height:12px;background:{SOFT};border-radius:6px;overflow:hidden">'
            f'<div style="height:100%;width:{share * 100:.0f}%;background:{color};border-radius:6px"></div></div>'
            f'<span style="font-size:13px;color:{MUTED};text-align:right">{share:.0%} '
            f'<span style="font-size:11px">({n} reviews)</span></span></div>')
    return "".join(out)


def stars_vs_model(points, height=280):
    """Patients' star ratings (x) against the model's satisfaction estimate (y), with a 'perfect
    agreement' diagonal. points: DataFrame stars, satisfaction."""
    line = pd.DataFrame({"x": [1, 10], "y": [1, 10]})
    base_x = alt.X("stars:Q", scale=alt.Scale(domain=[0.5, 10.5]), title="Patient's stars",
                   axis=alt.Axis(values=list(range(1, 11)), grid=False))
    base_y = alt.Y("satisfaction:Q", scale=alt.Scale(domain=[0.5, 10.5]), title="Model's satisfaction estimate",
                   axis=alt.Axis(values=[1, 4, 7, 10], grid=False))
    diag = alt.Chart(line).mark_line(strokeDash=[4, 4], color=LINE).encode(x="x:Q", y="y:Q")
    dots = alt.Chart(points).mark_circle(size=120, opacity=0.4, color=POS).encode(
        x=base_x, y=base_y,
        tooltip=[alt.Tooltip("stars:Q", title="Stars"),
                 alt.Tooltip("satisfaction:Q", title="Model estimate", format=".1f")])
    return (alt.layer(diag, dots).properties(height=height)
            .configure_view(stroke=LINE, fill="#F7F9FC")
            .configure_axis(labelColor=MUTED, titleColor=MUTED, domain=False, ticks=False, titleFontWeight=400,
                            labelFontSize=11, titleFontSize=11))


def calibration_chart(by_level, scale, height=300):
    """For each rating the patient gave (x): DiMEx's average prediction (dot) and its middle half (bar),
    against a dashed 'perfect agreement' line. Dots on the line = right on average."""
    x = alt.X("level:Q", title="Patient's rating", scale=alt.Scale(domain=[0.5, scale + 0.5]),
              axis=alt.Axis(values=list(range(1, scale + 1)), format="d", grid=False))
    y_scale = alt.Scale(domain=[1, scale])
    diag = alt.Chart(pd.DataFrame({"level": [1, scale], "mean_pred": [1, scale]})).mark_line(
        strokeDash=[5, 4], color="#A3AEBE").encode(x="level:Q", y=alt.Y("mean_pred:Q", scale=y_scale))
    spread = alt.Chart(by_level).mark_rule(strokeWidth=6, color="#BFD3F2", strokeCap="round").encode(
        x=x, y=alt.Y("q25:Q", scale=y_scale), y2="q75:Q")
    tip = [alt.Tooltip("label:N", title="Patient said"), alt.Tooltip("n:Q", title="Reviews"),
           alt.Tooltip("mean_pred:Q", title="DiMEx average", format=".1f"),
           alt.Tooltip("mae:Q", title="Average gap", format=".2f")]
    dots = alt.Chart(by_level).mark_circle(size=140, color=POS, opacity=1, stroke="white", strokeWidth=1.5).encode(
        x=x, y=alt.Y("mean_pred:Q", scale=y_scale, title="DiMEx's prediction",
                     axis=alt.Axis(values=list(range(1, scale + 1)), format="d", grid=True, gridColor="#EEF1F5")),
        tooltip=tip)
    return (alt.layer(diag, spread, dots).properties(height=height)
            .configure_view(stroke=None).configure(background="#FFFFFF")
            .configure_axis(labelColor=AXIS_INK, titleColor=AXIS_INK, domain=False, ticks=False,
                            titleFontWeight=400, labelFontSize=12, titleFontSize=13))
