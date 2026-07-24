# -*- coding: utf-8 -*-
"""
科技型小微企业风险定价模型 —— 仿真数据 + 模型拟合 + 回测
题目：《对低息差背景下银行差异化经营路径的研究——科技型小微企业综合经营
"看不清、定不准、绑不牢"的破解之道》

定价逻辑（用户给定）： R = max( FTP, FTP + 风险溢价Π )
八类因子：行业属性 / 显性财务 / 隐性偿债能力 / 经营周期 /
          客户综合贡献 / 区域环境 / 担保方式 / 结算流水
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve

_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
try:
    fm.fontManager.addfont(_CJK)
    plt.rcParams["font.family"] = fm.FontProperties(fname=_CJK).get_name()
except Exception:
    pass
sns.set_style("whitegrid")
plt.rcParams["axes.unicode_minus"] = False
np.random.seed(42)

# ============================================================
# 0. 全局参数（利率水平）
# ============================================================
N = 3000
FTP      = 0.032      # 内部资金转移价格（资金成本）
C_OP     = 0.008      # 单笔运营成本率
RHO0     = 0.005      # 目标基础净息差（无风险基础收益）
R_FLOOR  = FTP + C_OP + RHO0     # 底线执行利率 = 0.045
BASE_LGD = 0.45       # 基准违约损失率
KAPPA    = 0.08       # 资本占用加载系数（非预期损失代理）
LAMBDA   = 0.045      # 信息不确定性溢价系数（看不清）
DELTA    = 0.012      # 客户综合贡献最大折扣（绑不牢）
GAMMA    = 0.006      # 区域竞争最大折扣（区域环境）

# ============================================================
# 1. 合成企业特征（8 类因子）
# ============================================================
# —— 行业属性 ——
ind_track = (np.random.rand(N) < 0.5).astype(int)          # 是否战略性新兴产业赛道
subsidy   = np.clip(np.random.normal(0.05, 0.05, N), 0, 0.3)  # 政策补贴强度
# —— 显性财务 ——
rd        = np.clip(np.random.normal(0.12, 0.07, N), 0.01, 0.45)   # 研发投入强度
rev_growth= np.random.normal(0.15, 0.25, N)                       # 营收同比增长
lev       = np.clip(np.random.normal(0.55, 0.13, N), 0.20, 0.92)  # 资产负债率
cur_ratio = np.clip(np.random.normal(1.35, 0.45, N), 0.4, 3.5)   # 流动比率
net_asset = np.clip(np.random.lognormal(0.8, 0.7, N), 50, 8000)   # 净资产(万元)
# —— 隐性偿债能力（软信息，通常"看不清"）——
ocf_cover = np.random.normal(0.25, 0.22, N)                 # 经营性现金流/总负债
founder_exp = np.clip(np.random.normal(12, 6, N), 1, 35)   # 创始人行业经验(年)
overdue_cnt = np.random.poisson(0.35, N)                   # 历史逾期次数
eq_stable   = np.random.beta(5, 2, N)                      # 股权结构稳定性(0-1)
# —— 经营周期（生命周期阶段）——
lifecycle = np.random.choice([0,1,2,3], N, p=[0.15,0.35,0.35,0.15])  # 0种子 1初创 2成长 3成熟
# —— 担保方式 ——
coll_cover = np.clip(np.random.beta(2,4)*1.3 + np.random.normal(0,0.05,N), 0, 1.3)  # 抵质押覆盖率
patent_cnt = np.random.poisson(4.0, N)                     # 专利数量
patent_qual= np.clip(np.random.beta(2,5,N),0,1)            # 高价值专利占比
patent_pledge = (np.random.rand(N) < 0.30).astype(int)     # 知识产权(专利)质押
gov_backed = (np.random.rand(N) < 0.35).astype(int)        # 政府风险补偿/担保基金背书
# —— 结算流水 ——
settle    = np.clip(np.random.lognormal(0.5, 0.9, N), 5, 5000)     # 月结算流水(万元)
settle_norm = (settle - settle.min()) / (settle.max() - settle.min())
# —— 客户综合贡献（绑不牢）——
deposit_ratio = np.clip(np.random.beta(2,3,N),0,1)         # 存款沉淀/结算归行率
cross_sell    = np.clip(np.random.poisson(1.6,N),0,6)      # 产品交叉销售数
rel_years     = np.clip(np.random.normal(2.5,1.8,N),0,12)  # 合作关系年限
supply_chain  = (np.random.rand(N) < 0.30).astype(int)     # 核心企业上下游
# —— 区域环境 ——
region_comp = np.clip(np.random.beta(2,3,N),0,1)           # 区域竞争强度
# —— 信息透明度（看不清的"解药"：结算流水 + 财务规范化）——
info_quality = np.clip(np.random.normal(0.58, 0.18, N), 0.1, 0.98)  # 财务规范化/数据可得性
q = np.clip(0.20 + 0.50*settle_norm + 0.30*info_quality, 0.05, 0.98)  # 综合信息质量指数

# 透明度低 → 软信息被"看不清"（观测噪声）
obs = 1 - q
founder_exp_o = founder_exp * (1 + np.random.normal(0,0.15,N)*obs)
overdue_cnt_o = np.maximum(0, overdue_cnt + np.random.poisson(0.4*obs, N))
eq_stable_o   = np.clip(eq_stable + np.random.normal(0,0.12,N)*obs, 0, 1)

# ============================================================
# 2. 潜在违约过程（含交互项，体现"定不准"）
# ============================================================
def std(x):
    return (x - x.mean()) / (x.std() + 1e-9)

z = (
    -0.55*std(rd) - 0.45*std(rev_growth) - 0.70*std(ocf_cover)
    + 0.80*std(lev) - 0.40*std(cur_ratio) - 0.35*std(founder_exp_o)
    + 0.90*std(overdue_cnt_o) - 0.30*std(eq_stable_o)
    - 0.25*std(np.log(net_asset)) - 0.20*std(coll_cover)
    - 0.30*std(patent_cnt) - 0.25*std(patent_qual)
    - 0.45*std(gov_backed) - 0.30*std(ind_track)
    - 0.20*std(subsidy) - 0.25*std(lifecycle)
)
inter = (
    + 0.50*std(np.maximum(ocf_cover,0))*std(rd)        # 高研发×正现金流=安全；烧钱风险见下
    + 0.45*std(lev)*std(np.minimum(cur_ratio,1.0))     # 高杠杆×低流动=危险
    + 0.30*std(patent_cnt)*std(ind_track)              # 专利在战略赛道更值钱
)
z_full = z + inter
# 二分搜索平移量，使整体违约率落在约 12%（贴近现实科技小微不良水平）
_target = 0.12
_noise = np.random.normal(0, 0.25, N)
def _md(b):
    return (1.0 / (1.0 + np.exp(-(b + z_full + _noise)))).mean()
_lo, _hi = -8.0, 2.0
for _ in range(50):
    _m = (_lo + _hi) / 2.0
    if _md(_m) > _target:
        _hi = _m
    else:
        _lo = _m
beta0 = (_lo + _hi) / 2.0
p_true = 1.0 / (1.0 + np.exp(-(beta0 + z_full + _noise)))
y = np.random.binomial(1, p_true)
print(f"[数据] 合成样本 N={N}, 实际违约率={y.mean():.3%}")

# ============================================================
# 3. LGD 与真实（fair）定价基准
# ============================================================
LGD = np.clip(BASE_LGD*(1 - 0.5*coll_cover - 0.4*gov_backed - 0.15*patent_pledge), 0.05, 0.6)
EL_true  = p_true * LGD
UL_true  = KAPPA * np.sqrt(p_true*(1-p_true))               # 资本占用（非预期损失代理，凸性）
unc_true = LAMBDA * (1 - q) * (EL_true + UL_true)           # 信息不确定性溢价（看不清）
S = (0.35*deposit_ratio + 0.20*np.clip(cross_sell/6,0,1)
     + 0.20*np.clip(rel_years/12,0,1) + 0.15*supply_chain + 0.10*settle_norm)
strat_true = -DELTA * S                                     # 客户综合贡献折扣（绑不牢）
comp_true  = -GAMMA * region_comp                           # 区域竞争折扣（区域环境）
Pi_true = EL_true + UL_true + unc_true + strat_true + comp_true
R_true = np.maximum(R_FLOOR, R_FLOOR + Pi_true) + np.random.normal(0, 0.0008, N)

# ============================================================
# 4. 子模型：PD 预测（Logistic + 交互，含信息不确定性量化）
# ============================================================
feat = pd.DataFrame({
    "rd": rd, "rev_growth": rev_growth, "ocf_cover": ocf_cover, "lev": lev,
    "cur_ratio": cur_ratio, "founder_exp": founder_exp_o, "overdue_cnt": overdue_cnt_o,
    "eq_stable": eq_stable_o, "ln_net_asset": np.log(net_asset), "coll_cover": coll_cover,
    "patent_cnt": patent_cnt, "patent_qual": patent_qual, "gov_backed": gov_backed,
    "ind_track": ind_track, "subsidy": subsidy, "lifecycle": lifecycle,
    "settle_norm": settle_norm,
})
Xs = (feat - feat.mean()) / (feat.std() + 1e-9)
Xs["ix_burn"]    = std(np.maximum(ocf_cover,0)) * std(rd)
Xs["ix_lev_liq"] = std(lev) * std(np.minimum(cur_ratio,1.0))
Xs["ix_pat_tr"]  = std(patent_cnt) * std(ind_track)
X = Xs.values

idx = np.arange(N)
idx_tr, idx_te = np.split(np.random.permutation(N), [int(N*0.65)])
X_tr, X_te = X[idx_tr], X[idx_te]
y_tr, y_te = y[idx_tr], y[idx_te]
ptrue_te, q_te = p_true[idx_te], q[idx_te]
te_idx = idx_te

lr = LogisticRegression(C=1.0, max_iter=1000)
lr.fit(X_tr, y_tr)
p_hat = lr.predict_proba(X_te)[:, 1]
auc = roc_auc_score(y_te, p_hat)
order = np.argsort(p_hat)
cum_pos = np.cumsum(y_te[order]) / (y_te.sum() + 1e-9)
cum_neg = np.cumsum(1 - y_te[order]) / ((1 - y_te).sum() + 1e-9)
ks = np.max(np.abs(cum_pos - cum_neg))
print(f"[PD子模型] 测试集 AUC={auc:.3f}, KS={ks:.3f}")

# ============================================================
# 5. 主模型：去理想化风险定价 R = max(FTP, FTP + Π)
# ============================================================
LGD_hat = np.clip(BASE_LGD*(1 - 0.5*coll_cover[te_idx] - 0.4*gov_backed[te_idx]
                             - 0.15*patent_pledge[te_idx]), 0.05, 0.6)
EL_hat  = p_hat * LGD_hat
UL_hat  = KAPPA * np.sqrt(p_hat*(1-p_hat))
unc_hat = LAMBDA * (1 - q_te) * (EL_hat + UL_hat)
S_hat = (0.35*deposit_ratio[te_idx] + 0.20*np.clip(cross_sell[te_idx]/6,0,1)
         + 0.20*np.clip(rel_years[te_idx]/12,0,1) + 0.15*supply_chain[te_idx]
         + 0.10*settle_norm[te_idx])
strat_hat = -DELTA * S_hat
comp_hat  = -GAMMA * region_comp[te_idx]
Pi_hat = EL_hat + UL_hat + unc_hat + strat_hat + comp_hat
R_hat = np.maximum(R_FLOOR, R_FLOOR + Pi_hat)
R_true_te = R_true[te_idx]
n_floor = int(np.sum(R_hat <= R_FLOOR + 1e-9))
print(f"[主模型] 触底(按地板价FTP定价)客户数={n_floor} ({n_floor/len(R_hat):.1%})")

# ============================================================
# 6. 对照：理想化朴素模型 R = R0 + Σ α F（老师批评的原型）
# ============================================================
F = (feat.values - feat.values.mean(0)) / (feat.values.std(0) + 1e-9)
# 理想化朴素模型：固定等权（忽略符号差异、交互、风险/粘性/竞争结构）
_alpha_base = np.array([-0.001,-0.001,-0.001,0.0015,-0.0008,-0.001,0.002,-0.001,
                  -0.0008,-0.001,-0.001,-0.001,-0.0015,-0.001,-0.001,
                  -0.0008,-0.001,-0.001,-0.0008])
alpha = np.pad(_alpha_base, (0, max(0, F.shape[1]-len(_alpha_base))), constant_values=-0.001)[:F.shape[1]]
R_naive_all = R_FLOOR + F @ alpha
R_naive = R_naive_all[te_idx]

# 常见对照模型
R_flat   = np.full_like(R_true_te, R_FLOOR + 0.010)        # 基准加点：LPR+固定加点，忽略风险
R_elonly = np.maximum(R_FLOOR, R_FLOOR + EL_hat)           # 仅期望损失（简化 RAROC）

# ============================================================
# 7. 回测
# ============================================================
mse_ideal = np.mean((R_naive - R_true_te)**2)
mse_deid  = np.mean((R_hat - R_true_te)**2)
mse_flat  = np.mean((R_flat - R_true_te)**2)
mse_elonly= np.mean((R_elonly - R_true_te)**2)
print(f"[回测] 理想化模型 MSE={mse_ideal*1e6:.2f}e-6 | 去理想化模型 MSE={mse_deid*1e6:.2f}e-6")

df = pd.DataFrame({
    "p_true": ptrue_te, "p_hat": p_hat, "R_true": R_true_te, "R_hat": R_hat,
    "R_naive": R_naive, "info": q_te, "S": S_hat, "y": y_te,
})
df["tier"] = pd.qcut(df["p_true"], 4, labels=["低","中低","中高","高"])
tier_tbl = df.groupby("tier", observed=True).agg(
    n=("y","size"), default_rate=("y","mean"),
    R_true_mean=("R_true","mean"), R_hat_mean=("R_hat","mean"),
    R_naive_mean=("R_naive","mean")).round(4)
print("\n[风险分层定价]")
print(tier_tbl)

low_info = df[df["info"] < 0.5]; high_info = df[df["info"] >= 0.5]
err_low  = (low_info["R_naive"] - low_info["R_true"]).mean()
err_high = (high_info["R_naive"] - high_info["R_true"]).mean()
print(f"\n[看不清误定价] 低透明度组 朴素模型平均偏差={err_low*1e4:+.1f}bps, 高透明度组={err_high*1e4:+.1f}bps")

# ============================================================
# 8. 绘图
# ============================================================
import os
os.makedirs("/workspace/figs", exist_ok=True)
fpr, tpr, _ = roc_curve(y_te, p_hat)
fig, ax = plt.subplots(figsize=(5,4))
ax.plot(fpr, tpr, color="#c0392b", lw=2, label=f"PD模型 (AUC={auc:.3f})")
ax.plot([0,1],[0,1],"--",color="gray"); ax.set_xlabel("假正率 FPR"); ax.set_ylabel("真正率 TPR")
ax.set_title("PD预测 ROC曲线"); ax.legend(); fig.tight_layout(); fig.savefig("/workspace/figs/fig1_roc.png", dpi=150); plt.close(fig)

bins = np.linspace(0,1,11); df["pbin"] = pd.cut(df["p_hat"], bins, include_lowest=True)
cal = df.groupby("pbin", observed=True).agg(pred=("p_hat","mean"), obs=("y","mean")).reset_index()
fig, ax = plt.subplots(figsize=(5,4))
ax.plot(cal["pred"], cal["obs"], "o-", color="#2980b9", label="模型校准")
ax.plot([0,1],[0,1],"--",color="gray", label="理想校准线")
ax.set_xlabel("预测违约概率 PD"); ax.set_ylabel("实际违约率"); ax.set_title("PD校准曲线（测试集）")
ax.legend(); fig.tight_layout(); fig.savefig("/workspace/figs/fig2_calibration.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(6,4))
xpos = np.arange(len(tier_tbl)); w = 0.25
ax.bar(xpos-w, tier_tbl["R_true_mean"]*100, w, label="真实价格", color="#7f8c8d")
ax.bar(xpos,   tier_tbl["R_hat_mean"]*100,  w, label="去理想化模型", color="#27ae60")
ax.bar(xpos+w, tier_tbl["R_naive_mean"]*100,w, label="理想化朴素模型", color="#e67e22")
ax.axhline(R_FLOOR*100, ls=":", color="black", label=f"FTP底线({R_FLOOR*100:.1f}%)")
ax.set_xticks(xpos); ax.set_xticklabels(tier_tbl.index)
ax.set_ylabel("执行利率 (%)"); ax.set_title("不同风险层定价对比（含FTP底线）")
ax.legend(); fig.tight_layout(); fig.savefig("/workspace/figs/fig3_tier_pricing.png", dpi=150); plt.close(fig)

coef = pd.Series(lr.coef_[0], index=list(feat.columns)+["ix_burn","ix_lev_liq","ix_pat_tr"]).sort_values()
fig, ax = plt.subplots(figsize=(6,5))
ax.barh(coef.index, coef.values, color=["#c0392b" if v>0 else "#2980b9" for v in coef.values])
ax.set_xlabel("Logistic 系数"); ax.set_title("PD子模型因子系数（红=推高违约）")
fig.tight_layout(); fig.savefig("/workspace/figs/fig4_coef.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(5,4))
sc = ax.scatter(df["info"], (df["R_hat"]-df["R_true"]).abs()*1e4, c=df["p_true"], cmap="viridis", s=12, alpha=0.6)
ax.set_xlabel("信息质量指数 q"); ax.set_ylabel("|模型价-真实价| (bps)")
ax.set_title("看不清：信息越不透明，定价偏差越大"); plt.colorbar(sc, label="真实PD")
fig.tight_layout(); fig.savefig("/workspace/figs/fig5_uncertainty.png", dpi=150); plt.close(fig)

# 地板价客户画像（绑不牢）
floor_df = df[df["R_hat"] <= R_FLOOR + 1e-9]
fig, ax = plt.subplots(figsize=(5,4))
ax.scatter(floor_df["S"], floor_df["p_true"]*100, c=floor_df["info"], cmap="plasma", s=20, alpha=0.7)
ax.set_xlabel("客户综合贡献 S（绑不牢）"); ax.set_ylabel("真实违约率 PD(%)")
ax.set_title("触底价客户：高贡献、低风险、透明"); plt.colorbar(ax.collections[0], label="信息质量q")
fig.tight_layout(); fig.savefig("/workspace/figs/fig6_floor.png", dpi=150); plt.close(fig)

# ============================================================
# 9. 汇总
# ============================================================
summary = {
    "N": int(N), "default_rate": float(y.mean()),
    "auc": float(auc), "ks": float(ks),
    "mse_ideal_e6": float(mse_ideal*1e6), "mse_deid_e6": float(mse_deid*1e6),
    "n_floor": n_floor, "floor_share": float(n_floor/len(R_hat)),
    "tier": tier_tbl.reset_index().to_dict("records"),
    "err_low_info_bps": float(err_low*1e4), "err_high_info_bps": float(err_high*1e4),
    "R_FLOOR": R_FLOOR, "coef": {k: float(v) for k,v in coef.items()},
}
import json
with open("/workspace/figs/summary.json","w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# —— 页面对比数据导出（供 model_comparison.html 使用）——
comp = {
    "params": {"FTP": FTP, "C_OP": C_OP, "RHO0": RHO0, "R_FLOOR": R_FLOOR,
               "KAPPA": KAPPA, "LAMBDA": LAMBDA, "DELTA": DELTA, "GAMMA": GAMMA,
               "BASE_LGD": BASE_LGD},
    "metrics": {
        "auc": float(auc), "ks": float(ks), "default_rate": float(y.mean()),
        "floor_share": float(n_floor/len(R_hat)),
        "mse": {"deid": float(mse_deid), "naive": float(mse_ideal),
                "flat": float(mse_flat), "elonly": float(mse_elonly)},
    },
    "firms": {
        "pd_true": [float(x) for x in ptrue_te],
        "pd_hat":  [float(x) for x in p_hat],
        "q":       [float(x) for x in q_te],
        "S":       [float(x) for x in S_hat],
        "R_true":  [float(x) for x in R_true_te],
        "R_deid":  [float(x) for x in R_hat],
        "R_naive": [float(x) for x in R_naive],
        "R_flat":  [float(x) for x in R_flat],
        "R_elonly":[float(x) for x in R_elonly],
    },
}
with open("/workspace/figs/comparison.json", "w") as f:
    json.dump(comp, f, ensure_ascii=False)
print("[完成] 图表、汇总与对比数据已保存至 /workspace/figs")
