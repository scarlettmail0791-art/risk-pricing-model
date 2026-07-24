# -*- coding: utf-8 -*-
"""纯图片静态对比页（无 JS，兜底预览）。"""
import json, base64
d = json.load(open("/workspace/figs/comparison.json", encoding="utf-8"))
M = d["metrics"]

def b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

def row(name, val, sub=""):
    return f"<tr><td class='name'>{name}</td><td>{val}</td><td>{sub}</td></tr>"

roi = b64("/workspace/figs/fig1_roc.png")
tier = b64("/workspace/figs/fig3_tier_pricing.png")
unc = b64("/workspace/figs/fig5_uncertainty.png")
floor = b64("/workspace/figs/fig6_floor.png")

HTML = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>科技型小微企业风险定价模型 · 对比演示（静态版）</title>
<style>
:root{{--green:#27ae60;--orange:#e67e22;--red:#c0392b;--blue:#2980b9;--gray:#7f8c8d;--bg:#f5f7fa;--card:#fff;--ink:#2c3e50;--line:#e1e8ed;}}
body{{margin:0;font-family:"Microsoft YaHei",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6;}}
header{{background:linear-gradient(135deg,#1f3a5f,#2c3e50);color:#fff;padding:22px 30px;}}
header h1{{margin:0;font-size:20px;}} header p{{margin:6px 0 0;opacity:.85;font-size:12.5px;}}
.wrap{{max-width:1000px;margin:0 auto;padding:20px 16px 50px;}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:16px 0;}}
h2{{font-size:16px;margin:0 0 8px;border-left:4px solid var(--blue);padding-left:10px;}}
.note{{font-size:12px;color:#8a97a3;margin:0 0 12px;}}
img{{width:100%;border:1px solid var(--line);border-radius:8px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px;}}
th,td{{border:1px solid var(--line);padding:7px 9px;text-align:right;}} th{{background:#f0f4f8;}}
td.name,th.name{{text-align:left;}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
.kpi .v{{font-size:20px;font-weight:700;}} .kpi .k{{font-size:12px;color:#8a97a3;}}
.footer{{font-size:11px;color:#aab4bd;text-align:center;margin-top:20px;}}
</style></head><body>
<header><h1>科技型小微企业风险定价模型 · 对比演示（静态版）</h1>
<p>你的去理想化模型 R=max(FTP,FTP+风险溢价Π) 对比三种常见定价模型 · 仿真样本 N=3000，违约率约12.3%</p></header>
<div class="wrap">

<div class="kpis">
  <div class="kpi"><div class="v">{M['auc']:.3f}</div><div class="k">PD 判别力 AUC</div></div>
  <div class="kpi"><div class="v">{M['ks']:.3f}</div><div class="k">PD 区分度 KS</div></div>
  <div class="kpi"><div class="v">{M['mse']['deid']*1e6:.1f}</div><div class="k">去理想化 MSE (×10⁻⁶)</div></div>
  <div class="kpi"><div class="v">{M['mse']['naive']*1e6:.1f}</div><div class="k">朴素模型 MSE (×10⁻⁶)</div></div>
  <div class="kpi"><div class="v">{M['floor_share']*100:.1f}%</div><div class="k">FTP 地板价客户占比</div></div>
</div>

<section><h2>① 组合视角：风险（PD）vs 执行利率</h2>
<div class="note">理想模型随风险右上倾斜；常见模型近乎水平，对高风险客户严重低估。</div>
<img src="{roi}" alt="ROC"><img src="{tier}" alt="分层定价"></section>

<section><h2>② 风险分层定价对比</h2>
<div class="note">四层利率：仅你的模型随风险显著抬升。</div>
<img src="{tier}" alt="分层"></section>

<section><h2>③ 误定价与不确定性</h2>
<div class="note">左：信息越不透明定价偏差越大；右：触底价客户（高贡献、低风险、透明）。</div>
<img src="{unc}" alt="不确定性"><img src="{floor}" alt="地板价"></section>

<section><h2>④ 各模型均方误差（MSE，×10⁻⁶，越小越好）</h2>
<table>
{row("去理想化模型（本）", f"{{M['mse']['deid']*1e6:.2f}}", "最小")}
{row("仅期望损失（简化RAROC）", f"{{M['mse']['elonly']*1e6:.2f}}", "约本模型 2 倍")}
{row("LPR固定加点", f"{{M['mse']['flat']*1e6:.2f}}", "忽略风险")}
{row("朴素加性 R=R₀+ΣαF", f"{{M['mse']['naive']*1e6:.2f}}", f"约本模型 {{M['mse']['naive']/M['mse']['deid']:.0f}} 倍")}
</table></section>

<div class="footer">参数与数据均为仿真示意值，落地时替换为行内实际 FTP 曲线与历史样本。</div>
</div></body></html>"""

with open("/workspace/model_comparison_static.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("已生成 /workspace/model_comparison_static.html (", len(HTML)//1024, "KB )")
