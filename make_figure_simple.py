import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
src = open("make_figure.py").read()
exec(src.split("# ---- figure ----")[0])   # reuse data + pooled draws (ann_pool, p_rec, p_top2)

plt.rcParams.update({"font.family": ["Avenir", "Avenir Next", "DejaVu Sans"], "font.size": 12})
BG, INK, MUTED, RED, GOLD = "#FFFFFF", "#1a1a1a", "#666666", "#dc2626", "#d97706"
fig, ax = plt.subplots(figsize=(10, 8.2), facecolor=BG)
ax.set_facecolor(BG); ax.tick_params(colors=INK, length=0); ax.grid(True, color="#e5e5e5", lw=0.8)
for s in ax.spines.values(): s.set_visible(False)

yrs = F.loc[:2025].index; x = F.loc[:2025, "ytd"]; y = ann.loc[yrs]
sc = ax.scatter(x, y, c=yrs, cmap="viridis", s=42, edgecolor="white", lw=0.5, zorder=3)
for t, dx, dy in ((2012, -8, -4), (2024, 7, 2), (2016, 7, -3), (2025, 7, -3), (1934, 7, -3), (1921, 7, -3)):
    ax.annotate(str(t), (x[t], y[t]), xytext=(dx, dy), textcoords="offset points", fontsize=10.5, color=INK, ha="right" if dx < 0 else "left")
ax.axhline(record, color=RED, lw=1.3, ls="--", zorder=2)
ax.text(x.min() - 0.2, record + 0.06, f"2024 record: {record:.2f}°F", color=RED, fontsize=11, va="bottom")
ax.axvline(ytd26, color=GOLD, lw=1.8, zorder=2)
ax.text(ytd26 - 0.1, y.min() + 0.05, "2026 Jan–Aug:\nwarmest on record", color=GOLD, fontsize=11, ha="right", va="bottom", fontweight="bold")
q = np.percentile(ann_pool, [5, 25, 50, 75, 95])
ax.plot([ytd26, ytd26], [q[0], q[4]], color=GOLD, lw=2.5, zorder=4)
ax.plot([ytd26, ytd26], [q[1], q[3]], color=GOLD, lw=8, zorder=4, solid_capstyle="butt")
ax.scatter([ytd26], [q[2]], color=INK, s=60, zorder=5, edgecolor="white")
ax.text(ytd26 + 0.13, q[2], f"2026 projected\n{q[2]:.1f}°F\n(5–95%: {q[0]:.1f}–{q[4]:.1f})", fontsize=10.5, va="center", color=INK, linespacing=1.4)
ax.text(ytd26 + 0.13, record - 0.55, f"≈{100*p_rec:.0f}% chance\nof a new record", fontsize=11.5, va="top", color=RED, fontweight="bold", linespacing=1.3)
ax.set_xlim(x.min() - 0.3, ytd26 + 1.25)
ax.set_xlabel("January–August mean temperature (°F)", color=INK, fontsize=12.5)
ax.set_ylabel("Annual mean temperature (°F)", color=INK, fontsize=12.5)
cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02); cb.outline.set_visible(False); cb.ax.tick_params(length=0, labelsize=9.5)

fig.suptitle("Is 2026 on track to be the warmest U.S. year on record?", x=0.06, ha="left", fontsize=18.5, fontweight="bold", color=INK, y=0.975)
fig.text(0.06, 0.915, f"Contiguous U.S., NOAA nClimDiv, 1895–2025 by year. Jan–Aug 2026 averaged {ytd26:.2f}°F, the warmest start to a year on record.\n"
         f"Beating 2024 requires Sep–Dec to average above {need:.1f}°F, reached in 12 of 131 years and 8 times since 2000.",
         fontsize=10.5, color=MUTED, ha="left", va="top", linespacing=1.5)
fig.text(0.06, 0.02, "Projection pools six statistical models of the Sep–Dec mean (year-to-date, summer and trend predictors; AR(1) simulation; empirical\n"
         "residuals) fitted to 1950/1980–2025 and checked by rolling-origin cross-validation. Analysis: Zeke Hausfather.",
         fontsize=9, color=MUTED, ha="left", va="bottom", linespacing=1.4)
fig.subplots_adjust(top=0.84, bottom=0.14, left=0.09, right=0.93)
fig.savefig("figures/conus_record_odds_2026_simple.png", dpi=180, facecolor=BG)
print("saved", round(p_rec, 3), q.round(2))
