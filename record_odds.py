"""CONUS warmest-year odds given NOAA CAG monthly data to date.

Annual = unweighted mean of the 12 monthly CAG values (checked, <=0.005 F rounding).
Target: P(annual 2026 > record). Approaches, each giving a predictive distribution of
the Sep-Dec mean (SOND) conditional on what is known:

  A  trend only:      SOND ~ year                      (ignores YTD; baseline)
  B  YTD + trend:     SOND ~ YTD(Jan-Aug) + year
  C  B + last month:  SOND ~ YTD + Aug + year
  D  B + last 3 mo:   SOND ~ YTD + JJA + year
  E  AR(1) on monthly anomalies about a linear trend, simulated forward (Monte Carlo)
  F  empirical: detrended SOND residuals of the last N years added to the trend value

Scored by rolling-origin (expanding window) cross-validation: for year t, fit on years
< t and score the prediction for t (CRPS, PIT coverage). Fit windows: full record and 1950+.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats

m = pd.read_csv("data/cag_all_months.csv", comment="#")
m["year"] = m.Date // 100; m["mon"] = m.Date % 100
piv = m.pivot(index="year", columns="mon", values="Value")
LAST_MON = int(piv.loc[2026].last_valid_index())
rest = list(range(LAST_MON + 1, 13))
full = piv.loc[:2025]
ann = full.mean(axis=1)
record_year = ann.idxmax(); record = ann.max()
runner_up = ann.drop(record_year).max()

def feats(p):
    f = pd.DataFrame(index=p.index)
    f["ytd"] = p.loc[:, :LAST_MON].mean(axis=1)
    f["last1"] = p[LAST_MON]
    f["last3"] = p.loc[:, LAST_MON-2:LAST_MON].mean(axis=1)
    f["year"] = p.index.astype(float)
    return f
F = feats(piv); F["rest"] = piv[rest].mean(axis=1)
ytd26 = F.loc[2026, "ytd"]
need = (12 * record - LAST_MON * ytd26) / len(rest)
need2 = (12 * runner_up - LAST_MON * ytd26) / len(rest)
print(f"Last month available: {LAST_MON}; remaining months: {rest}")
print(f"Record: {record_year} {record:.2f} F; runner-up {runner_up:.2f} F")
print(f"2026 YTD mean {ytd26:.3f} F (rank {int((F.loc[:2025,'ytd']>ytd26).sum())+1})")
print(f"SOND mean needed to beat record: {need:.3f} F; to beat runner-up: {need2:.3f} F")
h = F.loc[:2025, "rest"]
print(f"Historical SOND: mean {h.mean():.2f}, last-10 mean {h.loc[2016:].mean():.2f}, max {h.max():.2f} ({h.idxmax()}), "
      f"n years with SOND>{need:.2f}: {(h>need).sum()} of {len(h)}; since 2000: {(h.loc[2000:]>need).sum()}")

SPECS = {"A trend only": ["year"], "B YTD+trend": ["ytd", "year"],
         "C YTD+last1+trend": ["ytd", "last1", "year"], "D YTD+last3+trend": ["ytd", "last3", "year"],
         "B' YTD only (no trend)": ["ytd"]}

def ols_pred(train, cols, x):
    X = sm.add_constant(train[cols]); fit = sm.OLS(train["rest"], X).fit()
    xr = sm.add_constant(pd.DataFrame([x[cols]]), has_constant="add")
    pr = fit.get_prediction(xr)
    mu = float(pr.predicted_mean[0]); se = float(pr.se_obs[0])  # includes residual + param uncertainty
    return mu, se, fit.df_resid, fit

def ar1_sim(train_piv, start_year, nsim=20000, rng=np.random.default_rng(1)):
    # monthly anomalies about per-month linear trends fitted on training years
    yrs = train_piv.index.values.astype(float)
    A = np.column_stack([np.ones_like(yrs), yrs])
    coefs = np.linalg.lstsq(A, train_piv.values, rcond=None)[0]  # 2 x 12
    resid = train_piv.values - A @ coefs
    sd = resid.std(axis=0, ddof=2)
    z = resid / sd
    # lag-1 month-to-month correlation across the year boundary too
    zf = z.ravel(); rho = np.corrcoef(zf[:-1], zf[1:])[0, 1]
    # climatology for target year
    clim = np.array([1.0, start_year]) @ coefs
    # start from last observed month's standardized anomaly
    cur = piv.loc[start_year]
    z0 = (cur[LAST_MON] - clim[LAST_MON-1]) / sd[LAST_MON-1]
    out = np.zeros(nsim); zprev = np.full(nsim, z0)
    eps_sd = np.sqrt(1 - rho**2)
    vals = np.zeros((nsim, len(rest)))
    for j, mo in enumerate(rest):
        zprev = rho * zprev + eps_sd * rng.standard_normal(nsim)
        vals[:, j] = clim[mo-1] + sd[mo-1] * zprev
    return vals.mean(axis=1), rho

def empirical(train, x, n=30):
    fit = sm.OLS(train["rest"], sm.add_constant(train[["year"]])).fit()
    res = fit.resid.iloc[-n:]
    mu = float(fit.params["const"] + fit.params["year"] * x["year"])
    return mu + res.values

# ---------- 2026 predictions ----------
print("\n=== 2026 predictions of SOND mean and record odds ===")
rows = []
for start in (1895, 1950, 1980):
    tr = F.loc[start:2025]
    for name, cols in SPECS.items():
        mu, se, df, fit = ols_pred(tr, cols, F.loc[2026])
        p = 1 - stats.t.cdf((need - mu) / se, df); p2 = 1 - stats.t.cdf((need2 - mu) / se, df)
        ann_mu = (LAST_MON * ytd26 + len(rest) * mu) / 12
        rows.append(dict(window=start, model=name, sond_mu=mu, sond_se=se, annual_mu=ann_mu,
                         p_record=p, p_top2=p2, r2=fit.rsquared, ytd_coef=fit.params.get("ytd", np.nan),
                         ytd_p=fit.pvalues.get("ytd", np.nan)))
    sims, rho = ar1_sim(piv.loc[start:2025], 2026)
    rows.append(dict(window=start, model=f"E AR1 sim (rho={rho:.2f})", sond_mu=sims.mean(), sond_se=sims.std(),
                     annual_mu=(LAST_MON*ytd26+len(rest)*sims.mean())/12, p_record=(sims>need).mean(), p_top2=(sims>need2).mean()))
    emp = empirical(tr, F.loc[2026], n=30)
    rows.append(dict(window=start, model="F empirical last-30 resid", sond_mu=emp.mean(), sond_se=emp.std(),
                     annual_mu=(LAST_MON*ytd26+len(rest)*emp.mean())/12, p_record=(emp>need).mean(), p_top2=(emp>need2).mean()))
res = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(res.round(3).to_string(index=False))

# ---------- rolling-origin CV ----------
print("\n=== Rolling-origin CV (predict year t from years < t), test years 1980-2025 ===")
def crps_norm(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))
cv = []
for start in (1895, 1950):
    for name, cols in SPECS.items():
        recs = []
        for t in range(1980, 2026):
            tr = F.loc[start:t-1]
            mu, se, df, _ = ols_pred(tr, cols, F.loc[t])
            y = F.loc[t, "rest"]
            recs.append((y - mu, crps_norm(y, mu, se), stats.t.cdf((y - mu) / se, df)))
        r = np.array(recs)
        cv.append(dict(window=start, model=name, rmse=np.sqrt((r[:,0]**2).mean()), crps=r[:,1].mean(),
                       cover90=((r[:,2]>0.05)&(r[:,2]<0.95)).mean(), pit_mean=r[:,2].mean()))
    recs = []
    for t in range(1980, 2026):
        sims, _ = ar1_sim(piv.loc[start:t-1], t, nsim=4000)
        y = F.loc[t, "rest"]
        recs.append((y - sims.mean(), crps_norm(y, sims.mean(), sims.std()), (sims < y).mean()))
    r = np.array(recs)
    cv.append(dict(window=start, model="E AR1 sim", rmse=np.sqrt((r[:,0]**2).mean()), crps=r[:,1].mean(),
                   cover90=((r[:,2]>0.05)&(r[:,2]<0.95)).mean(), pit_mean=r[:,2].mean()))
    recs = []
    for t in range(1980, 2026):
        emp = empirical(F.loc[start:t-1], F.loc[t], n=30); y = F.loc[t, "rest"]
        recs.append((y - emp.mean(), crps_norm(y, emp.mean(), emp.std()), (emp < y).mean()))
    r = np.array(recs)
    cv.append(dict(window=start, model="F empirical last-30", rmse=np.sqrt((r[:,0]**2).mean()), crps=r[:,1].mean(),
                   cover90=((r[:,2]>0.05)&(r[:,2]<0.95)).mean(), pit_mean=r[:,2].mean()))
print(pd.DataFrame(cv).round(3).to_string(index=False))

# correlation diagnostics
print("\nCorrelation of SOND with predictors (1950-2025, detrended):")
d = F.loc[1950:2025].copy()
for c in ["ytd", "last1", "last3", "rest"]:
    d[c] = sm.OLS(d[c], sm.add_constant(d["year"])).fit().resid
print(d[["ytd", "last1", "last3", "rest"]].corr()["rest"].round(3).to_dict())
