import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
exec(open("record_odds.py").read().split("# ---------- 2026 predictions")[0])

def crps_norm(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))

F["year2"] = (F["year"] - 1980).clip(lower=0)  # hinge trend: extra slope after 1980
SPECS2 = {"A trend": ["year"], "B YTD+trend": ["ytd","year"], "C YTD+last1+trend": ["ytd","last1","year"],
          "D YTD+last3+trend": ["ytd","last3","year"], "D2 YTD+last3+hinge": ["ytd","last3","year","year2"],
          "B2 YTD+hinge": ["ytd","year","year2"]}
print("=== CV, test years 2000-2025 ===")
cv=[]
for start in (1895, 1950, 1980):
    for name, cols in SPECS2.items():
        if start==1980 and "year2" in cols: continue
        recs=[]
        for t in range(2000, 2026):
            mu, se, df, _ = ols_pred(F.loc[start:t-1], cols, F.loc[t]); y=F.loc[t,"rest"]
            recs.append((y-mu, crps_norm(y,mu,se), stats.t.cdf((y-mu)/se, df)))
        r=np.array(recs)
        cv.append(dict(window=start, model=name, bias=r[:,0].mean(), rmse=np.sqrt((r[:,0]**2).mean()), crps=r[:,1].mean(),
                       cover90=((r[:,2]>0.05)&(r[:,2]<0.95)).mean(), pit_mean=r[:,2].mean()))
pd.set_option("display.width",200)
print(pd.DataFrame(cv).round(3).to_string(index=False))

print("\n=== 2026 with hinge-trend models ===")
for start in (1895,1950):
    for name in ("B2 YTD+hinge","D2 YTD+last3+hinge"):
        mu,se,df,fit = ols_pred(F.loc[start:2025], SPECS2[name], F.loc[2026])
        print(start, name, f"SOND mu {mu:.2f} se {se:.2f}  P(record) {1-stats.t.cdf((need-mu)/se,df):.3f}  P(top2) {1-stats.t.cdf((need2-mu)/se,df):.3f}")

print("\n=== Hindcasts at the same point (through Aug) for 2012 and 2024, model D, 1950+ window ===")
for t in (2012, 2024, 2016, 2025):
    prior = ann.loc[:t-1]; rec = prior.max()
    ytd_t = F.loc[t,"ytd"]; nd = (12*rec - LAST_MON*ytd_t)/len(rest)
    for start in (1950,1980):
        mu,se,df,_ = ols_pred(F.loc[start:t-1], ["ytd","last3","year"], F.loc[t])
        p = 1-stats.t.cdf((nd-mu)/se, df)
        print(f"{t}: prior record {rec:.2f} ({prior.idxmax()}), YTD rank {int((F.loc[:t-1,'ytd']>ytd_t).sum())+1}, "
              f"window {start}: P(record)={p:.2f}; actual annual {ann.get(t, np.nan):.2f} -> {'RECORD' if ann.get(t,0)>rec else 'no'}")

jja = F["last3"]; print(f"\nJJA 2026 = {jja.loc[2026]:.2f} F, rank {int((jja.loc[:2025]>jja.loc[2026]).sum())+1}; Aug 2026 rank {int((piv.loc[:2025,8]>piv.loc[2026,8]).sum())+1}")
print("2012 SOND:", F.loc[2012,"rest"].round(2), " 2024 SOND:", F.loc[2024,"rest"].round(2), " 2025 SOND:", F.loc[2025,"rest"].round(2))
print("Top SOND years:", F.loc[:2025,"rest"].sort_values(ascending=False).head(8).round(2).to_dict())
