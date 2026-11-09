"""Display pieces for the v2 pages: score bars, intensity meters, stacked intensity bars
(small HTML snippets) and the valence-arousal map (Altair)."""
import altair as alt
import pandas as pd

# Whites, cool greys and blues. Intensity and severity read as light -> dark blue.
INK, MUTED, SOFT, LINE = "#1B2430", "#5B6472", "#E8ECF2", "#D9DEE6"
POS, NEG, NEU = "#2F6FD0", "#0B2E59", "#8A94A3"      # effectiveness, side effects, satisfaction
MILD, MOD, DIST = "#BCD2F3", "#5C8FD6", "#0B2E59"     # mild, moderate, distressing
BAND_COLORS = {"Mild": MILD, "Calm": MILD, "Moderate": MOD, "Distressing": DIST, "Strong": DIST}
ASPECT_COLORS = {"effectiveness": POS, "side_effect": NEG, "satisfaction": NEU}


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
STAR_NOTE = {"side_effect": "More stars = milder side effects"}


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


def intensity_meter(arousal):
    """Nine segments, filled up to the arousal score; light to dark as intensity rises."""
    segs = []
    for i in range(1, 10):
        color = MILD if i <= 3 else MOD if i <= 6 else DIST
        segs.append(f'<span style="flex:1;height:10px;border-radius:2px;'
                    f'background:{color if i <= round(arousal) else SOFT}"></span>')
    return f"""
<div role="img" aria-label="Intensity {arousal:.1f} out of 9" style="margin:4px 0 2px">
  <div style="display:flex;gap:3px">{''.join(segs)}</div>
  <div style="display:flex;justify-content:space-between;font-size:11px;color:{MUTED};margin-top:4px">
    <span>Calm</span><span>Intense</span></div>
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
    return f'<div style="font-size:13px;color:{MUTED}">{items}</div>'


_CORNERS = pd.DataFrame([
    {"v": 1.2, "a": 8.75, "t": "Distressing", "align": "left"},
    {"v": 8.8, "a": 8.75, "t": "Strong relief", "align": "right"},
    {"v": 1.2, "a": 1.25, "t": "Mildly unpleasant", "align": "left"},
    {"v": 8.8, "a": 1.25, "t": "Calm, content", "align": "right"},
])


def va_map(points=None, dots=None, height=330):
    """Valence (x) by arousal (y), 1-9, with plain-language corners.
    points: DataFrame v, a, label, color (labeled markers). dots: DataFrame v, a, band (scatter)."""
    x = alt.X("v:Q", scale=alt.Scale(domain=[1, 9]), title="Valence: negative → positive",
              axis=alt.Axis(values=[1, 3, 5, 7, 9], grid=False))
    y = alt.Y("a:Q", scale=alt.Scale(domain=[1, 9]), title="Arousal: calm → intense",
              axis=alt.Axis(values=[1, 3, 5, 7, 9], grid=False))
    mid = pd.DataFrame({"v": [5], "a": [5]})
    layers = [
        alt.Chart(mid).mark_rule(strokeDash=[4, 4], color=LINE).encode(x="v:Q"),
        alt.Chart(mid).mark_rule(strokeDash=[4, 4], color=LINE).encode(y="a:Q"),
    ]
    for align in ("left", "right"):
        layers.append(alt.Chart(_CORNERS[_CORNERS["align"] == align])
                      .mark_text(align=align, fontSize=11, color=MUTED).encode(x=x, y=y, text="t:N"))
    if dots is not None and len(dots):
        layers.append(alt.Chart(dots).mark_circle(size=34, opacity=0.75).encode(
            x=x, y=y,
            color=alt.Color("band:N", scale=alt.Scale(domain=["Mild", "Moderate", "Distressing"],
                                                       range=[MILD, MOD, DIST]), legend=None),
            tooltip=[alt.Tooltip("band:N", title="Intensity"), alt.Tooltip("v:Q", title="Valence", format=".1f"),
                     alt.Tooltip("a:Q", title="Arousal", format=".1f")]))
    if points is not None and len(points):
        layers.append(alt.Chart(points).mark_point(size=220, filled=True, opacity=1, stroke="white",
                                                   strokeWidth=2).encode(
            x=x, y=y, color=alt.Color("color:N", scale=None),
            tooltip=[alt.Tooltip("label:N", title="Aspect"), alt.Tooltip("v:Q", title="Valence", format=".1f"),
                     alt.Tooltip("a:Q", title="Arousal", format=".1f")]))
        layers.append(alt.Chart(points).mark_text(align="left", dx=12, fontSize=12, fontWeight=600,
                                                  color=INK).encode(x=x, y=y, text="label:N"))
    return (alt.layer(*layers).properties(height=height)
            .configure_view(stroke=LINE, fill="#F7F9FC")
            .configure_axis(labelColor=MUTED, titleColor=MUTED, domain=False, ticks=False, titleFontWeight=400))
