# -*- coding: utf-8 -*-
"""Génère la page visuelle (docs/index.html) à partir du sweep."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
builds = json.load(open(ROOT / 'data' / 'pareto.json', encoding='utf-8'))
icons = json.load(open(ROOT / 'data' / 'icons_b64.json', encoding='utf-8'))

HTML = """<!doctype html>
<html lang="fr">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forge du Sacrieur — Optimiseur de stuff</title>
<style>
:root{
  --bg:#eef0f2; --panel:#ffffff; --ink:#241b1d; --ink2:#6b5f62; --mut:#9a8f92;
  --accent:#c22b33; --accent-ink:#ffffff; --line:#ddd6d8; --gold:#a07d2a;
  --neutre:#8a8a92; --terre:#8a6d3b; --feu:#d0652a; --eau:#3a7fc1; --air:#4f9e6b;
  --ok:#3d7a4f; --shadow:0 1px 4px rgba(36,27,29,.08);
}
@media (prefers-color-scheme: dark){:root{
  --bg:#171215; --panel:#211a1d; --ink:#f2e9e9; --ink2:#b3a5a8; --mut:#7d7074;
  --accent:#e4525a; --accent-ink:#1c1214; --line:#382e31; --gold:#d3a94c;
  --neutre:#9c9ca6; --terre:#b08c50; --feu:#e58045; --eau:#5f9fd8; --air:#66b585;
  --ok:#5da874; --shadow:0 1px 4px rgba(0,0,0,.4);
}}
:root[data-theme="dark"]{
  --bg:#171215; --panel:#211a1d; --ink:#f2e9e9; --ink2:#b3a5a8; --mut:#7d7074;
  --accent:#e4525a; --accent-ink:#1c1214; --line:#382e31; --gold:#d3a94c;
  --neutre:#9c9ca6; --terre:#b08c50; --feu:#e58045; --eau:#5f9fd8; --air:#66b585;
  --ok:#5da874; --shadow:0 1px 4px rgba(0,0,0,.4);
}
:root[data-theme="light"]{
  --bg:#eef0f2; --panel:#ffffff; --ink:#241b1d; --ink2:#6b5f62; --mut:#9a8f92;
  --accent:#c22b33; --accent-ink:#ffffff; --line:#ddd6d8; --gold:#a07d2a;
  --neutre:#8a8a92; --terre:#8a6d3b; --feu:#d0652a; --eau:#3a7fc1; --air:#4f9e6b;
  --ok:#3d7a4f; --shadow:0 1px 4px rgba(36,27,29,.08);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:28px 20px 60px}
header h1{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-size:clamp(26px,4vw,38px);margin:0;text-wrap:balance}
header h1 em{color:var(--accent);font-style:normal}
.sub{color:var(--ink2);margin:6px 0 0;max-width:68ch}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:11px;color:var(--accent);
  font-weight:700;margin:0 0 4px}
.picker{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0 8px}
.picker button{border:1px solid var(--line);background:var(--panel);color:var(--ink);
  padding:8px 14px;border-radius:6px;cursor:pointer;font:600 13px system-ui;
  transition:border-color .15s}
.picker button:hover{border-color:var(--accent)}
.picker button.on{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.picker button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.cols{display:grid;grid-template-columns:1fr 340px;gap:20px;margin-top:16px}
@media(max-width:860px){.cols{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:16px;box-shadow:var(--shadow)}
h2{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-size:17px;margin:0 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.item{display:flex;gap:10px;align-items:center;border:1px solid var(--line);
  border-radius:8px;padding:8px;position:relative;cursor:default}
.item:hover{border-color:var(--accent)}
.item img{width:40px;height:40px;image-rendering:auto;flex:none}
.item .n{font-size:12.5px;font-weight:600;line-height:1.25}
.item .s{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
.item .cond{position:absolute;top:5px;right:6px;width:8px;height:8px;border-radius:50%;
  background:var(--gold)}
.tip{position:absolute;z-index:30;left:50%;top:100%;transform:translateX(-50%);
  background:var(--panel);border:1px solid var(--line);border-radius:8px;
  box-shadow:0 6px 24px rgba(0,0,0,.25);padding:10px 12px;width:230px;display:none;
  font-size:12px}
.item:hover .tip,.item:focus-within .tip{display:block}
.tip b{display:block;margin-bottom:4px}
.tip .c{color:var(--gold);font-weight:600;margin-top:6px}
.tip table{width:100%;border-collapse:collapse}
.tip td{padding:1px 0;color:var(--ink2)}
.tip td:last-child{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}
.hero{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat{border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.stat .v{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.1}
.stat .l{font-size:11px;color:var(--ink2);text-transform:uppercase;letter-spacing:.08em}
.kv{display:grid;grid-template-columns:1fr auto;row-gap:4px;font-size:13.5px;margin-bottom:14px}
.kv span:nth-child(even){font-variant-numeric:tabular-nums;font-weight:600}
.kv span:nth-child(odd){color:var(--ink2)}
.res .row{display:grid;grid-template-columns:52px 1fr 74px;gap:8px;align-items:center;
  margin-bottom:6px;font-size:12.5px}
.res .lab{color:var(--ink2)}
.res .bar{height:10px;background:var(--line);border-radius:4px;position:relative;overflow:visible}
.res .fill{height:100%;border-radius:4px;position:relative}
.res .pre{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--ink);opacity:.55}
.res .cap{position:absolute;top:-3px;bottom:-3px;width:1px;background:var(--mut);left:calc(100%*50/60)}
.res .val{text-align:right;font-variant-numeric:tabular-nums}
.res .val b{color:var(--ok)}
.rot table{width:100%;border-collapse:collapse;font-size:13px}
.rot th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--ink2);font-weight:600;padding:4px 6px;border-bottom:1px solid var(--line)}
.rot td{padding:5px 6px;border-bottom:1px solid var(--line);
  font-variant-numeric:tabular-nums}
.rot td:nth-child(n+2),.rot th:nth-child(n+2){text-align:right}
.rot tr:last-child td{border-bottom:none;font-weight:700}
.front{margin:10px 0 4px}
.front svg{width:100%;height:150px;display:block}
.front text{fill:var(--ink2);font:10.5px system-ui}
.front .pt{fill:var(--panel);stroke:var(--mut);stroke-width:1.5;cursor:pointer}
.front .pt.on{fill:var(--accent);stroke:var(--accent)}
.front .axis{stroke:var(--line)}
.notes{color:var(--ink2);font-size:12.5px;margin-top:18px;max-width:75ch}
.notes b{color:var(--ink)}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style>
<div class="wrap">
<header>
  <p class="eyebrow">Sacrieur Terre · niv 200 · PvP 2v2 · 12/6 naturel · conditions vérifiées</p>
  <h1>Forge du <em>Sacrieur</em></h1>
  <p class="sub">Cinq stuffs optimisés le long du front dégâts / survie (rotation optimale par sort,
  runes de résistance allouées automatiquement, conditions d'équipement respectées).
  Choisis ton point d'équilibre — ou <a href="opti.html" style="color:var(--accent)">forge le tien en direct</a>.</p>
</header>
<nav class="picker" id="picker"></nav>
<div class="front panel" id="front"></div>
<div class="cols">
  <section class="panel">
    <h2 id="btitle">Équipement</h2>
    <div class="grid" id="items"></div>
  </section>
  <aside>
    <section class="panel" style="margin-bottom:16px">
      <h2>Bilan</h2>
      <div class="hero">
        <div class="stat"><div class="v" id="vdpt"></div><div class="l">Dégâts / tour</div></div>
        <div class="stat"><div class="v" id="vehp"></div><div class="l">PV effectifs</div></div>
      </div>
      <div class="kv" id="kv"></div>
      <div class="res" id="res"></div>
    </section>
    <section class="panel rot">
      <h2>Rotation (12 PA)</h2>
      <table id="rot"></table>
    </section>
  </aside>
</div>
<p class="notes"><b>Hypothèses :</b> rolls parfaits · ~28 % de runes res réparties sur les pièces
magables (les trophées ne se magent pas) · caractéristiques +550 (points + parchemins) ·
vita de base 1200. Le point doré ● sur un item signale une condition d'équipement — toutes
sont satisfaites par ces builds. Données items : DofusDude (Dofus 3 / Unity).</p>
</div>
<script>
const BUILDS=__BUILDS__;
const ICONS=__ICONS__;
const SLOTS={coiffe:"Coiffe",cape:"Cape",amulette:"Amulette",ceinture:"Ceinture",bottes:"Bottes",
anneau1:"Anneau",anneau2:"Anneau",arme:"Arme",bouclier:"Bouclier",d1:"Trophée",d2:"Trophée",
d3:"Trophée",d4:"Trophée",d5:"Trophée",d6:"Trophée",familier:"Familier"};
const RES=[["Neutre","--neutre"],["Terre","--terre"],["Feu","--feu"],["Eau","--eau"],["Air","--air"]];
let cur=2;
const $=id=>document.getElementById(id);
const fmt=n=>n.toLocaleString("fr-FR");

function condTxt(c){
  const m={"Bonus de panoplies":"Bonus de panoplies","PA":"PA totaux","PM":"PM totaux"};
  return c.map(x=>`${m[x[0]]||x[0]} ${x[1]} ${x[2]}`).join(" · ");
}
function render(){
  const b=BUILDS[cur], st=b.stats;
  document.querySelectorAll("#picker button").forEach((el,i)=>el.classList.toggle("on",i===cur));
  document.querySelectorAll("#front .pt").forEach((el,i)=>el.classList.toggle("on",i===cur));
  $("btitle").textContent=`Équipement — profil ${b.profil}`;
  $("items").innerHTML=b.items.map(it=>{
    const rows=Object.entries(it.stats).map(([k,v])=>`<tr><td>${k}</td><td>${v>0?"+":""}${v}</td></tr>`).join("");
    const cond=it.conds.length?`<div class="c">Condition : ${condTxt(it.conds)}</div>`:"";
    return `<div class="item" tabindex="0">${it.conds.length?'<span class="cond"></span>':""}
      <img src="${ICONS[it.icon]}" alt="">
      <div><div class="n">${it.name}</div><div class="s">${SLOTS[it.slot]} · ${it.level}</div></div>
      <div class="tip"><b>${it.name}</b><table>${rows}</table>${cond}</div></div>`;
  }).join("");
  $("vdpt").textContent=fmt(b.dpt); $("vehp").textContent=fmt(b.ehp);
  const kv=[["PA / PM",(st.PA||0)+7+" / "+((st.PM||0)+3)],["Vitalité stuff",fmt(st["Vitalité"]||0)],
    ["Force stuff",st["Force"]||0],["Puissance",st["Puissance"]||0],
    ["% Critique",(st["% Critique"]||0)+" %"],["Do terre + do",(st["Dommage Terre"]||0)+(st["Dommage"]||0)],
    ["Do critiques",st["Dommage Critiques"]||0],["Tacle",st["Tacle"]||0],["Soin",st["Soin"]||0]];
  $("kv").innerHTML=kv.map(([k,v])=>`<span>${k}</span><span>${v}</span>`).join("");
  $("res").innerHTML=RES.map(([n,cv],i)=>{
    const before=st["% Résistance "+n]||0, after=b.res_apres[i];
    return `<div class="row"><span class="lab">${n}</span>
      <span class="bar"><span class="fill" style="width:${Math.min(after,60)/60*100}%;background:var(${cv})">
      <span class="pre" style="left:${Math.min(before,60)/Math.max(after,1)*100}%"></span></span>
      <span class="cap"></span></span>
      <span class="val">${before} → <b>${after} %</b></span></div>`;
  }).join("");
  const rows=b.rotation.map(r=>
    `<tr><td>${r.name}${r.casts>1?" ×"+r.casts:""}</td><td>${r.pa} PA</td><td>${r.crit} %</td><td>${fmt(r.avg*r.casts)}</td></tr>`
  ).join("");
  $("rot").innerHTML=`<tr><th>Sort</th><th>Coût</th><th>Crit</th><th>Moy.</th></tr>${rows}
    <tr><td>Total par tour</td><td></td><td></td><td>${fmt(b.dpt)}</td></tr>`;
}
$("picker").innerHTML=BUILDS.map((b,i)=>`<button type="button" data-i="${i}">${b.profil}</button>`).join("");
$("picker").addEventListener("click",e=>{const b=e.target.closest("button");if(b){cur=+b.dataset.i;render();}});
(function front(){
  const W=720,H=150,P=34;
  const xs=BUILDS.map(b=>b.dpt), ys=BUILDS.map(b=>b.ehp);
  const x0=Math.min(...xs)-80,x1=Math.max(...xs)+80,y0=Math.min(...ys)-400,y1=Math.max(...ys)+400;
  const X=v=>P+(v-x0)/(x1-x0)*(W-2*P), Y=v=>H-22-(v-y0)/(y1-y0)*(H-40);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Front dégâts / survie">`;
  s+=`<line class="axis" x1="${P}" y1="${H-22}" x2="${W-P}" y2="${H-22}"/>`;
  s+=`<line class="axis" x1="${P}" y1="12" x2="${P}" y2="${H-22}"/>`;
  s+=`<text x="${W-P}" y="${H-8}" text-anchor="end">Dégâts / tour →</text>`;
  s+=`<text x="${P+4}" y="14">PV effectifs ↑</text>`;
  BUILDS.forEach((b,i)=>{
    s+=`<circle class="pt" data-i="${i}" cx="${X(b.dpt)}" cy="${Y(b.ehp)}" r="7"><title>${b.profil} — ${b.dpt} DPT · ${b.ehp} EHP</title></circle>`;
    s+=`<text x="${X(b.dpt)}" y="${Y(b.ehp)-11}" text-anchor="middle">${b.profil}</text>`;
  });
  $("front").innerHTML=s+"</svg>";
  $("front").addEventListener("click",e=>{const c=e.target.closest(".pt");if(c){cur=+c.dataset.i;render();}});
})();
render();
</script>
"""

html = HTML.replace('__BUILDS__', json.dumps(builds, ensure_ascii=False)) \
           .replace('__ICONS__', json.dumps(icons))
out = ROOT / 'docs' / 'index.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding='utf-8')
print('OK ->', out, len(html) // 1024, 'Ko')
