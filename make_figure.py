import numpy as np, pandas as pd, statsmodels.api as sm, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
exec(open("record_odds.py").read().split("# ---------- 2026 predictions")[0])
F["year2"] = (F["year"] - 1980).clip(lower=0)

# Calibrated set (CV 2000-2025 bias <0.2 F, 90% coverage 0.81-0.92)
CAL = [("D 1980+", 1980, ["ytd","last3","year"]), ("B 1980+", 1980, ["ytd","year"]),
       ("D2 hinge 1950+", 1950, ["ytd","last3","year","year2"]), ("B2 hinge 1950+", 1950, ["ytd","year","year2"])]
rng = np.random.default_rng(7); draws = []; summary = []
for name, start, cols in CAL:
    mu, se, df, _ = ols_pred(F.loc[start:2025], cols, F.loc[2026])
    d = mu + se * rng.standard_t(df, 50000); draws.append(d)
    summary.append((name, mu, se, (d > need).mean(), (d > need2).mean()))
sims, _ = ar1_sim(piv.loc[1980:2025], 2026, nsim=50000); draws.append(sims); summary.append(("E AR1 1980+", sims.mean(), sims.std(), (sims>need).mean(), (sims>need2).mean()))
emp = empirical(F.loc[1980:2025], F.loc[2026], n=30); bw = 1.06*emp.std()*len(emp)**(-0.2)
emp = rng.choice(emp, 50000) + bw*rng.standard_normal(50000)  # smoothed bootstrap
draws.append(emp); summary.append(("F empirical 1980+", emp.mean(), emp.std(), (emp>need).mean(), (emp>need2).mean()))
pool = np.concatenate(draws); ann_pool = (LAST_MON*ytd26 + len(rest)*pool)/12
p_rec = (pool > need).mean(); p_top2 = (pool > need2).mean()
print(pd.DataFrame(summary, columns=["model","sond_mu","sond_sd","p_record","p_top2"]).round(3).to_string(index=False))
print(f"POOLED: SOND {pool.mean():.2f} sd {pool.std():.2f}; annual median {np.median(ann_pool):.2f} F "
      f"[5-95%: {np.percentile(ann_pool,5):.2f}, {np.percentile(ann_pool,95):.2f}]; P(record)={p_rec:.3f}; P(top2)={p_top2:.3f}")
pd.DataFrame(summary, columns=["model","sond_mu","sond_sd","p_record","p_top2"]).to_csv("results/model_summary.csv", index=False)

# ---- figure ----
plt.rcParams.update({"font.family": ["Avenir", "Avenir Next", "DejaVu Sans"], "font.size": 12})
BG, INK, MUTED, BLUE, RED, GOLD = "#FFFFFF", "#1a1a1a", "#666666", "#2563eb", "#dc2626", "#d97706"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor=BG, gridspec_kw=dict(wspace=0.22))
for ax in (ax1, ax2):
    ax.set_facecolor(BG); ax.tick_params(colors=INK, length=0); ax.grid(True, color="#e5e5e5", lw=0.8)
    for s in ax.spines.values(): s.set_visible(False)

# panel 1: YTD vs annual scatter, colored by year
yrs = F.loc[:2025].index; x = F.loc[:2025, "ytd"]; y = ann.loc[yrs]
sc = ax1.scatter(x, y, c=yrs, cmap="viridis", s=34, edgecolor="white", lw=0.5, zorder=3)
for t in (2012, 2024, 2016, 2025, 1934, 1921):
    ax1.annotate(str(t), (x[t], y[t]), xytext=(6, -3), textcoords="offset points", fontsize=10, color=INK)
ax1.axhline(record, color=RED, lw=1.2, ls="--", zorder=2)
ax1.text(x.min()+0.1, record+0.06, f"2024 record  {record:.2f}°F", color=RED, fontsize=10.5, va="bottom")
ax1.axvline(ytd26, color=GOLD, lw=1.6, zorder=2)
ax1.text(ytd26-0.08, y.min()+0.1, "2026 Jan–Aug\n(warmest to date)", color=GOLD, fontsize=10.5, ha="right", va="bottom", fontweight="bold")
q = np.percentile(ann_pool, [5, 25, 50, 75, 95])
ax1.plot([ytd26, ytd26], [q[0], q[4]], color=GOLD, lw=2, zorder=4)
ax1.plot([ytd26, ytd26], [q[1], q[3]], color=GOLD, lw=6, zorder=4, solid_capstyle="butt")
ax1.scatter([ytd26], [q[2]], color=INK, s=50, zorder=5, edgecolor="white")
ax1.text(ytd26+0.12, q[2], f"2026\nprojected\n{q[2]:.1f}°F", fontsize=10.5, va="center", color=INK)
ax1.set_xlim(x.min()-0.3, ytd26+0.9)
ax1.set_xlabel("January–August mean temperature (°F)", color=INK)
ax1.set_ylabel("Annual mean temperature (°F)", color=INK)
ax1.set_title("Year-to-date vs. annual, 1895–2025", loc="left", fontsize=13, color=INK, pad=10)
cb = fig.colorbar(sc, ax=ax1, fraction=0.04, pad=0.03); cb.outline.set_visible(False); cb.ax.tick_params(length=0, labelsize=9)

# panel 2: predictive distribution of 2026 annual
ax2.hist(ann_pool, bins=70, color=BLUE, alpha=0.85, density=True, zorder=3)
ax2.axvline(record, color=RED, lw=1.6, ls="--", zorder=4)
ax2.text(record-0.04, ax2.get_ylim()[1]*0.97, f"2024 record\n{record:.2f}°F", color=RED, fontsize=10.5, ha="right", va="top")
ax2.axvline(runner_up, color=MUTED, lw=1, ls=":", zorder=4)
ax2.text(runner_up-0.04, ax2.get_ylim()[1]*0.70, f"2012\n{runner_up:.2f}°F", color=MUTED, fontsize=10, ha="right", va="top")
ax2.text(0.98, 0.96, f"P(new record) ≈ {100*p_rec:.0f}%", color=RED, fontsize=15, fontweight="bold", va="top", ha="right", transform=ax2.transAxes)
ax2.text(0.98, 0.87, f"P(top two) ≈ {100*p_top2:.0f}%", color=INK, fontsize=12, va="top", ha="right", transform=ax2.transAxes)
ax2.set_xlabel("2026 annual mean temperature (°F)", color=INK); ax2.set_yticks([])
ax2.set_title("Projected 2026 annual mean (pooled models)", loc="left", fontsize=13, color=INK, pad=10)
ax2.grid(False)

fig.suptitle("Will 2026 be the warmest year on record for the contiguous U.S.?", x=0.045, ha="left", fontsize=19, fontweight="bold", color=INK, y=0.985)
fig.text(0.045, 0.935, f"NOAA nClimDiv monthly data through August 2026. Jan–Aug 2026 averaged {ytd26:.2f}°F, the warmest start to a year on record.\n"
         f"Sep–Dec must average above {need:.1f}°F for a record (reached in 12 of 131 years, 8 since 2000).", fontsize=11, color=MUTED, ha="left", va="top", linespacing=1.5)
fig.text(0.045, 0.02, "Pooled predictive distribution from six models fitted to 1950/1980–2025 (year-to-date, summer, and trend predictors; AR(1) simulation; "
         "empirical residuals), each calibrated by rolling-origin cross-validation. Analysis: Zeke Hausfather.", fontsize=9, color=MUTED, ha="left")
fig.subplots_adjust(top=0.82, bottom=0.12, left=0.06, right=0.98)
fig.savefig("figures/conus_record_odds_2026.png", dpi=180, facecolor=BG)
print("saved")
