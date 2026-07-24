# -*- coding: utf-8 -*-
"""生成单文件、零依赖的模型对比交互页面（Chart.js 内嵌）。"""
import json

with open("/workspace/figs/comparison.json", encoding="utf-8") as f:
    DATA = json.load(f)
DATA_JS = json.dumps(DATA, ensure_ascii=False)

with open("/workspace/vendor/chart.umd.min.js", encoding="utf-8") as f:
    CHART_JS = f.read().replace("</script>", "<\\/script>")

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>科技型小微企业风险定价模型 · 对比演示</title>
<style>
  :root{--green:#27ae60;--orange:#e67e22;--red:#c0392b;--blue:#2980b9;
        --gray:#7f8c8d;--bg:#f5f7fa;--card:#fff;--ink:#2c3e50;--line:#e1e8ed;}
  *{box-sizing:border-box;}
  body{margin:0;font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
       background:var(--bg);color:var(--ink);line-height:1.6;}
  header{background:linear-gradient(135deg,#1f3a5f,#2c3e50);color:#fff;padding:26px 34px;}
  header h1{margin:0;font-size:21px;}
  header p{margin:6px 0 0;opacity:.85;font-size:12.5px;}
  .wrap{max-width:1160px;margin:0 auto;padding:22px 16px 56px;}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:13px;margin:16px 0 6px;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 15px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
  .card .k{font-size:12px;color:#8a97a3;}
  .card .v{font-size:21px;font-weight:700;margin-top:3px;}
  .card .sub{font-size:11px;color:#aab4bd;margin-top:2px;}
  section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,.04);}
  h2{font-size:16px;margin:0 0 3px;border-left:4px solid var(--blue);padding-left:10px;}
  .note{font-size:12px;color:#8a97a3;margin:2px 0 12px;}
  .plot{width:100%;height:400px;}
  .legend{display:flex;flex-wrap:wrap;gap:13px;font-size:12px;margin:8px 0 0;}
  .legend span{display:inline-flex;align-items:center;gap:6px;}
  .dot{width:11px;height:11px;border-radius:50%;display:inline-block;}
  .calc{display:grid;grid-template-columns:310px 1fr;gap:20px;}
  .ctrl{margin:11px 0;}
  .ctrl label{font-size:13px;display:flex;justify-content:space-between;}
  .ctrl input[type=range]{width:100%;}
  .verdict{font-size:13px;background:#fbfcfd;border:1px dashed var(--line);border-radius:8px;padding:10px 12px;margin-top:10px;min-height:56px;}
  table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px;}
  th,td{border:1px solid var(--line);padding:7px 9px;text-align:right;}
  th{background:#f0f4f8;text-align:center;}
  td.name,th.name{text-align:left;}
  .footer{font-size:11px;color:#aab4bd;text-align:center;margin-top:24px;}
</style>
</head>
<body>
<header>
  <h1>科技型小微企业风险定价模型 · 对比演示</h1>
  <p>你的去理想化模型 <b>R = max(FTP, FTP + 风险溢价Π)</b> 对比三种常见定价模型 · 数据为仿真样本（N=3000，违约率约12.3%）</p>
</header>
<div class="wrap">

  <div class="cards" id="cards"></div>

  <section>
    <h2>① 组合视角：风险（PD）vs 执行利率</h2>
    <div class="note">每个点为一家企业。横轴=真实违约概率，纵轴=执行利率。理想模型应随风险右上倾斜；常见模型近乎水平，对高风险客户严重低估。</div>
    <canvas id="scatter" class="plot"></canvas>
    <div class="legend">
      <span><i class="dot" style="background:var(--gray)"></i>真实价格（基准）</span>
      <span><i class="dot" style="background:var(--green)"></i>去理想化模型（本模型）</span>
      <span><i class="dot" style="background:var(--orange)"></i>朴素加性 R=R₀+ΣαF</span>
      <span><i class="dot" style="background:var(--red)"></i>LPR固定加点（忽略风险）</span>
      <span><i class="dot" style="background:var(--blue)"></i>仅期望损失（简化RAROC）</span>
    </div>
  </section>

  <section>
    <h2>② 风险分层定价对比</h2>
    <div class="note">按真实违约概率分四层，比较各模型层均利率。仅你的模型随风险显著抬升；其余三者对高风险层定价不足。</div>
    <canvas id="tier" class="plot"></canvas>
  </section>

  <section>
    <h2>③ 误定价程度（均方误差 MSE，×10⁻⁶）</h2>
    <div class="note">MSE 越小越好。你的模型误差最低；朴素与固定加点模型对高风险客户大幅低估。</div>
    <canvas id="mse" class="plot" style="height:300px;"></canvas>
  </section>

  <section>
    <h2>④ 单户试算器：拖动滑块，实时看四类模型如何定价</h2>
    <div class="note">调节一家企业的违约概率、损失率、信息质量、综合贡献、区域竞争，观察四个模型的定价差异与"是否覆盖风险"。</div>
    <div class="calc">
      <div>
        <div class="ctrl"><label>违约概率 PD <span id="v_pd">12%</span></label>
          <input id="pd" type="range" min="0.5" max="60" step="0.5" value="12"></div>
        <div class="ctrl"><label>违约损失率 LGD <span id="v_lgd">35%</span></label>
          <input id="lgd" type="range" min="5" max="60" step="1" value="35"></div>
        <div class="ctrl"><label>信息质量 q（越高越透明）<span id="v_q">0.60</span></label>
          <input id="q" type="range" min="0.05" max="0.98" step="0.01" value="0.60"></div>
        <div class="ctrl"><label>客户综合贡献 S <span id="v_s">0.40</span></label>
          <input id="s" type="range" min="0" max="1" step="0.01" value="0.40"></div>
        <div class="ctrl"><label>区域竞争强度 C <span id="v_c">0.50</span></label>
          <input id="c" type="range" min="0" max="1" step="0.01" value="0.50"></div>
        <div class="verdict" id="verdict"></div>
      </div>
      <div>
        <canvas id="calcBar" class="plot" style="height:280px;"></canvas>
        <table id="calcTable"></table>
      </div>
    </div>
  </section>

  <div class="footer">
    模型参数（FTP / 运营成本 / 基础净息差 / κ / λ / δ / γ）为示意值，落地时应替换为行内实际 FTP 曲线与风险偏好。数据由仿真生成，仅用于方法论证与演示。
  </div>
</div>

<script>/*CHARTJS*/</script>
<script>
const DATA = /*DATA*/;
const P = DATA.params, M = DATA.metrics, RFL = P.R_FLOOR;
const F = DATA.firms;
const fmtPct = x => (x*100).toFixed(2) + "%";
const pct = v => (v*100).toFixed(0) + "%";

// KPI
const cards = [
  {k:"PD 判别力 AUC", v:M.auc.toFixed(3), sub:"测试集（越强越好）"},
  {k:"PD 区分度 KS", v:M.ks.toFixed(3), sub:">0.6 为强区分"},
  {k:"去理想化模型 MSE", v:(M.mse.deid*1e6).toFixed(1), sub:"×10⁻⁶（最小）"},
  {k:"朴素模型 MSE", v:(M.mse.naive*1e6).toFixed(1), sub:"×10⁻⁶（约本模型 "+(M.mse.naive/M.mse.deid).toFixed(0)+" 倍）"},
  {k:"FTP 地板价客户占比", v:(M.floor_share*100).toFixed(1)+"%", sub:"高贡献客户让利到底价"},
];
document.getElementById("cards").innerHTML = cards.map(c=>
  `<div class="card"><div class="k">${c.k}</div><div class="v">${c.v}</div><div class="sub">${c.sub}</div></div>`).join("");

const COL = {gray:"#7f8c8d",green:"#27ae60",orange:"#e67e22",red:"#c0392b",blue:"#2980b9"};
const mk = (c,o)=>({x:o.x,y:o.y,mode:"markers",type:"scatter",
  name:c, marker:{color:o.color,size:4,opacity:0.4}});

// ① 散点
const toXY = a => F.pd_true.map((x,i)=>({x:x, y:a[i]}));
new Chart(document.getElementById("scatter"), {
  type:"scatter",
  data:{datasets:[
    mk("真实价格",{x:F.pd_true,y:F.R_true,color:COL.gray}),
    mk("去理想化模型",{x:F.pd_true,y:F.R_deid,color:COL.green}),
    mk("朴素加性",{x:F.pd_true,y:F.R_naive,color:COL.orange}),
    mk("LPR固定加点",{x:F.pd_true,y:F.R_flat,color:COL.red}),
    mk("仅期望损失",{x:F.pd_true,y:F.R_elonly,color:COL.blue}),
  ]},
  options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:"bottom"},tooltip:{enabled:false}},
    scales:{
      x:{title:{display:true,text:"真实违约概率 PD"},ticks:{callback:v=>pct(v)}},
      y:{title:{display:true,text:"执行利率"},ticks:{callback:v=>pct(v)}}}}
});

// ② 分层（按 pd_true 四分位）
function tierMeans(arr){
  const idx=[...F.pd_true.keys()].sort((a,b)=>F.pd_true[a]-F.pd_true[b]);
  const out=[[],[],[],[]];
  idx.forEach((i,k)=>out[Math.min(3,Math.floor(k/idx.length*4))].push(arr[i]));
  return out.map(a=>a.reduce((s,x)=>s+x,0)/a.length*100);
}
const tNames=["低","中低","中高","高"];
const tData=[
  {label:"真实价格",data:tierMeans(F.R_true),backgroundColor:COL.gray},
  {label:"去理想化模型",data:tierMeans(F.R_deid),backgroundColor:COL.green},
  {label:"仅期望损失",data:tierMeans(F.R_elonly),backgroundColor:COL.blue},
  {label:"朴素加性",data:tierMeans(F.R_naive),backgroundColor:COL.orange},
  {label:"LPR固定加点",data:tierMeans(F.R_flat),backgroundColor:COL.red},
];
new Chart(document.getElementById("tier"), {
  type:"bar", data:{labels:tNames,datasets:tData},
  options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:"bottom"}},
    scales:{y:{title:{display:true,text:"层均执行利率 (%)"}}}}
});

// ③ MSE
new Chart(document.getElementById("mse"), {
  type:"bar",
  data:{labels:["去理想化模型","仅期望损失","LPR固定加点","朴素加性"],
    datasets:[{data:[(M.mse.deid*1e6).toFixed(2),(M.mse.elonly*1e6).toFixed(2),
                    (M.mse.flat*1e6).toFixed(2),(M.mse.naive*1e6).toFixed(2)],
      backgroundColor:[COL.green,COL.blue,COL.red,COL.orange]}]},
  options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:false}},
    scales:{y:{title:{display:true,text:"MSE (×10⁻⁶)"}}}}
});

// ④ 单户试算器
const el = id=>document.getElementById(id);
function calcOne(pd,lgd,q,S,C){
  const EL=pd*lgd, UL=P.KAPPA*Math.sqrt(pd*(1-pd)),
        UNC=P.LAMBDA*(1-q)*(EL+UL),
        pi=EL+UL+UNC-P.DELTA*S-P.GAMMA*C;
  return {
    deid:Math.max(RFL,RFL+pi), naive:RFL+0.004, flat:RFL+0.010,
    elonly:Math.max(RFL,RFL+EL), fair:Math.max(RFL,RFL+pi), pi
  };
}
let calcChart=null;
function refresh(){
  const pd=+el("pd").value/100, lgd=+el("lgd").value/100,
        q=+el("q").value, S=+el("s").value, C=+el("c").value;
  el("v_pd").textContent=(pd*100).toFixed(1)+"%";
  el("v_lgd").textContent=(lgd*100).toFixed(0)+"%";
  el("v_q").textContent=q.toFixed(2);
  el("v_s").textContent=S.toFixed(2);
  el("v_c").textContent=C.toFixed(2);
  const r=calcOne(pd,lgd,q,S,C);
  const labels=["去理想化模型","仅期望损失","LPR固定加点","朴素加性"];
  const vals=[r.deid,r.elonly,r.flat,r.naive].map(v=>v*100);
  const colors=[COL.green,COL.blue,COL.red,COL.orange];
  if(calcChart) calcChart.destroy();
  calcChart=new Chart(el("calcBar"),{type:"bar",
    data:{labels,datasets:[{data:vals,backgroundColor:colors,
      datalabels:false}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:c=>c.parsed.y.toFixed(2)+"%"}}},
      scales:{y:{title:{display:true,text:"执行利率 (%)"},
        min:RFL*100-0.5, max:Math.max(...vals)+1}}}});
  const naiveGap=(r.naive-r.fair)*1e4, deidGap=(r.deid-r.fair)*1e4;
  let html=`公允价约 <b>${fmtPct(r.fair)}</b>（FTP底线 ${fmtPct(RFL)}）。<br>`;
  if(Math.abs(naiveGap)>3)
    html+=`<span style="color:${COL.orange}">朴素加性</span> 定价 ${fmtPct(r.naive)}，相对公允价 ${naiveGap>0?"高":""}${naiveGap.toFixed(0)} bps（${naiveGap<0?"低估、少收利息":""}）。<br>`;
  else html+=`<span style="color:${COL.orange}">朴素加性</span> 与公允价接近。<br>`;
  if(r.deid<=RFL+1e-9)
    html+=`<span style="color:${COL.green}">本模型触达 FTP 地板价</span>：高综合贡献客户主动让利以"绑牢"。`;
  else
    html+=`<span style="color:${COL.green}">本模型</span> 定价 ${fmtPct(r.deid)}，贴合公允价（偏差 ${deidGap.toFixed(0)} bps）。`;
  el("verdict").innerHTML=html;
  const rows=[["去理想化模型(本)",r.deid],["仅期望损失",r.elonly],
              ["LPR固定加点",r.flat],["朴素加性",r.naive],["公允价(基准)",r.fair]];
  el("calcTable").innerHTML="<tr><th class='name'>模型</th><th>执行利率</th><th>vs 公允价</th></tr>"+
    rows.map(([n,v])=>`<tr><td class='name'>${n}</td><td>${fmtPct(v)}</td><td>${((v-r.fair)*1e4).toFixed(0)} bps</td></tr>`).join("");
}
["pd","lgd","q","s","c"].forEach(id=>el(id).addEventListener("input",refresh));
refresh();
</script>
</body>
</html>
"""

HTML = HTML.replace("/*CHARTJS*/", CHART_JS).replace("/*DATA*/", DATA_JS)
with open("/workspace/model_comparison.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("已生成 /workspace/model_comparison.html (", len(HTML)//1024, "KB )")
