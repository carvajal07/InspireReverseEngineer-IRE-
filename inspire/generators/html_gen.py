"""Generador HTML: portal navegable autocontenido del workflow.

Produce un único archivo `.html` sin dependencias de servidor: embebe el
modelo como JSON y una pequeña aplicación en JavaScript que ofrece búsqueda,
filtros por categoría y navegación entre módulos, variables y reglas.

El diagrama Mermaid se renderiza con la librería desde CDN si hay conexión;
si no, se muestra el código fuente del diagrama (que sigue siendo útil).
"""

from __future__ import annotations

import json
from pathlib import Path

from inspire.analyzers.rules import RuleAnalyzer
from inspire.analyzers.variables import VariableAnalyzer
from inspire.generators.mermaid_gen import MermaidGenerator
from inspire.generators.serialize import workflow_to_dict
from inspire.model.workflow import Workflow


class HtmlGenerator:
    """Genera el portal HTML navegable del workflow."""

    def _payload(self, workflow: Workflow) -> dict[str, object]:
        data = workflow_to_dict(workflow)
        rules = RuleAnalyzer().analyze(workflow).rules
        var_report = VariableAnalyzer().analyze(workflow)
        data["rules"] = [
            {
                "module": r.module,
                "category": r.category,
                "type": r.rule_type,
                "target": r.target,
                "expression": r.expression,
                "detail": r.detail,
            }
            for r in rules
        ]
        data["variable_report"] = var_report.as_dict()
        data["mermaid"] = MermaidGenerator().render(workflow)
        return data

    def render(self, workflow: Workflow) -> str:
        payload = json.dumps(self._payload(workflow), ensure_ascii=False)
        # El JSON se inserta en un <script type="application/json"> para evitar
        # problemas de escape con comillas o llaves.
        title = workflow.name or "Inspire Workflow"
        return _TEMPLATE.replace("__TITLE__", _escape(title)).replace(
            "__DATA__", payload.replace("</", "<\\/")
        )

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(workflow), encoding="utf-8")
        return out


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IRE · __TITLE__</title>
<style>
  :root {
    --bg: #0f172a; --panel: #1e293b; --panel2: #273449; --text: #e2e8f0;
    --muted: #94a3b8; --accent: #38bdf8; --border: #334155;
    --input: #5eead4; --transform: #fbbf24; --control: #f87171;
    --integration: #c084fc; --script: #4ade80; --output: #fb923c; --other: #64748b;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         background: var(--bg); color: var(--text); }
  header { padding: 14px 20px; background: var(--panel); border-bottom: 1px solid var(--border);
           display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  header h1 { font-size: 18px; margin: 0; }
  header .ver { color: var(--muted); font-size: 13px; }
  .stats { display: flex; gap: 8px; flex-wrap: wrap; margin-left: auto; }
  .stat { background: var(--panel2); border: 1px solid var(--border); border-radius: 8px;
          padding: 4px 10px; font-size: 12px; }
  .stat b { color: var(--accent); }
  .tabs { display: flex; gap: 4px; padding: 8px 20px 0; background: var(--panel);
          border-bottom: 1px solid var(--border); }
  .tab { padding: 8px 16px; cursor: pointer; border-radius: 8px 8px 0 0; color: var(--muted);
         font-size: 14px; user-select: none; }
  .tab.active { background: var(--bg); color: var(--text); font-weight: 600; }
  .toolbar { display: flex; gap: 10px; padding: 12px 20px; align-items: center; flex-wrap: wrap; }
  #search { flex: 1; min-width: 240px; padding: 9px 12px; border-radius: 8px;
            border: 1px solid var(--border); background: var(--panel); color: var(--text); font-size: 14px; }
  .chip { padding: 4px 10px; border-radius: 999px; border: 1px solid var(--border);
          background: var(--panel); color: var(--muted); cursor: pointer; font-size: 12px; user-select: none; }
  .chip.active { color: #0f172a; font-weight: 600; }
  .chip.input.active{background:var(--input)} .chip.transform.active{background:var(--transform)}
  .chip.control.active{background:var(--control)} .chip.integration.active{background:var(--integration)}
  .chip.script.active{background:var(--script)} .chip.output.active{background:var(--output)}
  .chip.other.active{background:var(--other)}
  .layout { display: grid; grid-template-columns: 320px 1fr; gap: 0; height: calc(100vh - 190px); }
  .list { overflow-y: auto; border-right: 1px solid var(--border); }
  .item { padding: 10px 14px; border-bottom: 1px solid var(--border); cursor: pointer; }
  .item:hover { background: var(--panel); }
  .item.active { background: var(--panel2); }
  .item .name { font-weight: 600; font-size: 14px; }
  .item .kind { font-size: 11px; color: var(--muted); }
  .badge { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px; }
  .b-input{background:var(--input)} .b-transform{background:var(--transform)} .b-control{background:var(--control)}
  .b-integration{background:var(--integration)} .b-script{background:var(--script)}
  .b-output{background:var(--output)} .b-other{background:var(--other)}
  .detail { padding: 18px 24px; overflow-y: auto; }
  .detail h2 { margin-top: 0; }
  .detail .kindtag { font-size: 12px; color: var(--muted); }
  .section { margin: 18px 0; }
  .section h3 { font-size: 14px; text-transform: uppercase; letter-spacing: .04em;
                color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; }
  code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  pre { background: #0b1220; padding: 10px; border-radius: 8px; overflow-x: auto; font-size: 12px;
        border: 1px solid var(--border); white-space: pre-wrap; }
  .pill { display:inline-block; background: var(--panel2); border:1px solid var(--border);
          border-radius:6px; padding:1px 6px; font-size:11px; margin:1px; }
  .empty { color: var(--muted); padding: 40px; text-align: center; }
  .hidden { display: none; }
  a { color: var(--accent); cursor: pointer; text-decoration: none; }
  .count { color: var(--muted); font-size: 12px; margin-left: 6px; }
  .tag-design { background: var(--integration); color:#0f172a; border-radius:6px;
                padding:1px 8px; font-size:11px; font-weight:600; cursor:pointer; text-decoration:none; }
  .tag-design:hover { filter:brightness(1.1); }
  .tag-nodesign { color: var(--muted); font-size:11px; }
  .pageslist { margin:0; padding-left:18px; }
  .pageslist li { padding:2px 0; font-size:13px; }
  .modal.modal-sm { width: min(560px, 92vw); height:auto; max-height:80vh; }
  /* Modal de linaje de variable */
  .overlay { position: fixed; inset: 0; background: rgba(0,0,0,.6); display:none;
             align-items:center; justify-content:center; z-index:50; }
  .overlay.show { display:flex; }
  .modal { background: var(--bg); border:1px solid var(--border); border-radius:12px;
           width: min(1100px, 94vw); height: min(86vh, 900px); display:flex; flex-direction:column;
           box-shadow: 0 10px 40px rgba(0,0,0,.5); }
  .modal-head { display:flex; align-items:center; gap:12px; padding:12px 18px;
                border-bottom:1px solid var(--border); }
  .modal-head h2 { margin:0; font-size:16px; }
  .modal-close { margin-left:auto; cursor:pointer; font-size:22px; color:var(--muted);
                 background:none; border:none; }
  .modal-body { padding:16px 18px; overflow:auto; }
  .legend span { font-size:11px; margin-right:12px; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:4px; vertical-align:middle; }
  /* Visor de grafos con zoom + paneo */
  .graphview { position: relative; border:1px solid var(--border); border-radius:8px;
               overflow:hidden; background:#0b1220; height: 62vh; touch-action:none; }
  .graphview.lineage { height: 58vh; }
  .graphview svg { transform-origin: 0 0; cursor: grab; max-width:none !important; height:auto; }
  .graphview.grabbing svg { cursor: grabbing; }
  .graphctrl { position:absolute; top:8px; right:8px; display:flex; gap:4px; z-index:5; }
  .graphctrl button { background: var(--panel2); color:var(--text); border:1px solid var(--border);
                      border-radius:6px; width:30px; height:30px; cursor:pointer; font-size:15px;
                      line-height:1; }
  .graphctrl button:hover { background: var(--border); }
  .graphhint { position:absolute; bottom:8px; left:10px; font-size:11px; color:var(--muted);
               z-index:5; background:rgba(15,23,42,.6); padding:2px 6px; border-radius:6px; }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <span class="ver" id="version"></span>
  <div class="stats" id="stats"></div>
</header>
<div class="tabs">
  <div class="tab active" data-tab="modules">Módulos</div>
  <div class="tab" data-tab="variables">Variables</div>
  <div class="tab" data-tab="rules">Reglas</div>
  <div class="tab" data-tab="diagram">Diagrama</div>
</div>

<div id="view-modules">
  <div class="toolbar">
    <input id="search" placeholder="Buscar módulos, variables, expresiones, scripts...">
    <span id="filters"></span>
  </div>
  <div class="layout">
    <div class="list" id="moduleList"></div>
    <div class="detail" id="moduleDetail"><div class="empty">Selecciona un módulo</div></div>
  </div>
</div>

<div id="view-variables" class="hidden">
  <div class="toolbar">
    <input id="searchVar" placeholder="Buscar variables...">
    <label class="chip" style="cursor:pointer"><input type="checkbox" id="filterDesign"> solo usadas en diseño</label>
    <label class="chip" style="cursor:pointer" title="Se declaran pero no se usan ni modifican después"><input type="checkbox" id="filterUnused"> sin uso</label>
    <label class="chip" style="cursor:pointer" title="Se usan/modifican en muchos módulos: cambiarlas es de alto impacto"><input type="checkbox" id="filterCritical"> críticas</label>
    <label class="chip" style="cursor:pointer" title="Se usan pero no se crean en ningún módulo"><input type="checkbox" id="filterOrphan"> huérfanas</label>
  </div>
  <div class="detail" id="variablesView"></div>
</div>

<div id="view-rules" class="hidden">
  <div class="toolbar"><input id="searchRule" placeholder="Buscar reglas / expresiones..."></div>
  <div class="detail" id="rulesView"></div>
</div>

<div id="view-diagram" class="hidden">
  <div class="detail" id="diagramView"></div>
</div>

<div class="overlay" id="lineageOverlay">
  <div class="modal">
    <div class="modal-head">
      <h2 id="lineageTitle">Linaje de variable</h2>
      <span class="legend">
        <span><span class="dot" style="background:#16a34a"></span>Crea</span>
        <span><span class="dot" style="background:#fbbf24"></span>Modifica</span>
        <span><span class="dot" style="background:#38bdf8"></span>Usa</span>
        <span><span class="dot" style="background:#c084fc"></span>Diseño</span>
      </span>
      <button class="modal-close" id="lineageClose">&times;</button>
    </div>
    <div class="modal-body" id="lineageBody"></div>
  </div>
</div>

<div class="overlay" id="pagesOverlay">
  <div class="modal modal-sm">
    <div class="modal-head">
      <h2 id="pagesTitle">Hojas</h2>
      <button class="modal-close" id="pagesClose">&times;</button>
    </div>
    <div class="modal-body" id="pagesBody"></div>
  </div>
</div>

<script type="application/json" id="ire-data">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('ire-data').textContent);
const CATS = ['input','transform','control','integration','script','output','other'];
const esc = s => String(s==null?'':s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
let activeCats = new Set(CATS);
let selectedModule = null;

// ---- Header ----
document.getElementById('version').textContent = 'Inspire ' + (DATA.version||'?');
const S = DATA.statistics || {};
document.getElementById('stats').innerHTML = [
  ['Módulos',S.modules],['Variables',S.variables],['Reglas',S.rules],
  ['Cruces',S.joins],['Filtros',S.filters],['Scripts',S.scripts]
].map(([k,v]) => `<span class="stat">${k} <b>${v||0}</b></span>`).join('');

// ---- Filtros de categoría ----
document.getElementById('filters').innerHTML = CATS.map(c =>
  `<span class="chip ${c} active" data-cat="${c}">${c}</span>`).join('');
document.querySelectorAll('.chip').forEach(ch => ch.onclick = () => {
  const c = ch.dataset.cat;
  if (activeCats.has(c)) { activeCats.delete(c); ch.classList.remove('active'); }
  else { activeCats.add(c); ch.classList.add('active'); }
  renderModuleList();
});

// ---- Tabs ----
document.querySelectorAll('.tab').forEach(t => t.onclick = () => {
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
  ['modules','variables','rules','diagram'].forEach(v =>
    document.getElementById('view-'+v).classList.toggle('hidden', v !== t.dataset.tab));
  if (t.dataset.tab === 'diagram') renderDiagram();
});

// ---- Lista de módulos ----
function moduleMatches(m, q) {
  if (!activeCats.has(m.category)) return false;
  if (!q) return true;
  const hay = (m.name+' '+m.kind+' '+JSON.stringify(m.transformations||[])+' '+
    JSON.stringify(m.filter||'')+' '+JSON.stringify(m.scripts||[])).toLowerCase();
  return hay.includes(q);
}
function renderModuleList() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const list = DATA.modules.filter(m => moduleMatches(m, q));
  const el = document.getElementById('moduleList');
  if (!list.length) { el.innerHTML = '<div class="empty">Sin resultados</div>'; return; }
  el.innerHTML = list.map(m =>
    `<div class="item ${m.id===selectedModule?'active':''}" data-id="${esc(m.id)}">
       <div class="name"><span class="badge b-${m.category}"></span>${esc(m.name)}</div>
       <div class="kind">${esc(m.kind)}</div></div>`).join('');
  el.querySelectorAll('.item').forEach(it => it.onclick = () => selectModule(it.dataset.id));
}
function selectModule(id) {
  selectedModule = id;
  renderModuleList();
  const m = DATA.modules.find(x => x.id === id);
  if (!m) return;
  let h = `<h2><span class="badge b-${m.category}"></span>${esc(m.name)}</h2>
    <div class="kindtag">${esc(m.kind)} · ${esc(m.category)} · id=${esc(m.id)}</div>`;
  if (m.location) h += `<div class="section"><h3>Ubicación</h3><code>${esc(m.location)}</code></div>`;
  if (m.parameters) h += sec('Parámetros', tbl(['Nombre','Tipo','Default','CLI'],
    m.parameters.map(p => [p.name,p.type,p.default,p.command_line])));
  if (m.transformations) h += sec('Transformaciones', m.transformations.map(t =>
    `<div style="margin-bottom:10px"><code>${esc(t.target)}</code>
     <span class="pill">${esc(t.fcv)}</span> <span class="pill">${esc(t.kind)}</span><br>
     <span class="count">${esc(t.expression)}</span>
     ${t.script?`<pre>${esc(t.script)}</pre>`:''}</div>`).join(''));
  if (m.filter) h += sec('Filtro', `<code>${esc(m.filter.expression)}</code>
     ${m.filter.has_else_output?' <span class="pill">else-output</span>':''}`);
  if (m.join) h += sec('Join ('+esc(m.join.type)+')', tbl(['Izquierda','Derecha'],
    m.join.keys.map(k => [k.left, k.right])));
  if (m.scripts) h += sec('Scripts', m.scripts.map(s =>
    `<div><span class="pill">${esc(s.language)}</span> <span class="count">${s.lines} líneas</span>
     <pre>${esc(s.code)}</pre></div>`).join(''));
  if (m.renames) h += sec('Renombrados', tbl(['De','A'], m.renames.map(r => [r.from, r.to])));
  if (m.group_by) h += sec('Group by', m.group_by.map(g=>`<code>${esc(g)}</code>`).join(' '));
  if (m.fields) h += sec('Campos ('+countFields(m.fields)+')', renderFields(m.fields));
  // Conexiones
  const ins = DATA.connections.filter(c => c.to === id).map(c => c.from);
  const outs = DATA.connections.filter(c => c.from === id).map(c => c.to);
  h += sec('Flujo', `<b>Entra desde:</b> ${linkMods(ins)||'—'}<br><b>Sale hacia:</b> ${linkMods(outs)||'—'}`);
  document.getElementById('moduleDetail').innerHTML = h;
  document.querySelectorAll('[data-goto]').forEach(a => a.onclick = () => selectModule(a.dataset.goto));
}
function linkMods(ids) {
  return ids.map(i => { const m = DATA.modules.find(x=>x.id===i);
    return `<a data-goto="${esc(i)}">${esc(m?m.name:i)}</a>`; }).join(', ');
}
function countFields(fs){ return fs.reduce((n,f)=>n+1+countFields(f.children||[]),0); }
function renderFields(fs, d=0) {
  return '<div style="font-size:13px">'+fs.map(f =>
    `<div style="margin-left:${d*16}px"><code>${esc(f.name)}</code>
     <span class="count">${esc(f.type)}${f.optionality==='Array'?' []':''}</span></div>
     ${f.children&&f.children.length?renderFields(f.children,d+1):''}`).join('')+'</div>';
}
function sec(title, body){ return `<div class="section"><h3>${esc(title)}</h3>${body}</div>`; }
function tbl(head, rows){
  return `<table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
document.getElementById('search').oninput = renderModuleList;

// ---- Variables ----
const VAR_BY_NAME = {}; DATA.variables.forEach(v => VAR_BY_NAME[v.name] = v);
const HAS_LAYOUT = !!(DATA.layout && DATA.layout.usages && DATA.layout.usages.length);
function designCell(v) {
  if (v.used_in_layout) {
    const n = (v.layout_pages||[]).length;
    return `<a class="tag-design" data-design="${esc(v.name)}" title="Ver hojas que la usan">Sí · ${n}</a>`;
  }
  return HAS_LAYOUT ? '<span class="tag-nodesign">No</span>' : '<span class="tag-nodesign">—</span>';
}
function renderVariables() {
  const q = document.getElementById('searchVar').value.trim().toLowerCase();
  const rep = DATA.variable_report || {};
  const inArr = (arr, n) => arr && arr.includes(n);
  const flag = n => [
    inArr(rep.unused, n)?'<span class="pill" title="Se declara pero no se usa ni modifica después">sin uso</span>':'',
    inArr(rep.orphan, n)?'<span class="pill" title="Se usa pero no se crea en ningún módulo">huérfana</span>':'',
    inArr(rep.critical, n)?'<span class="pill" title="Se usa/modifica en muchos módulos: cambiarla es de alto impacto">crítica</span>':'',
  ].join('');
  const onlyDesign = document.getElementById('filterDesign').checked;
  const fUnused = document.getElementById('filterUnused').checked;
  const fCritical = document.getElementById('filterCritical').checked;
  const fOrphan = document.getElementById('filterOrphan').checked;
  let vars = DATA.variables.filter(v => !q || v.name.toLowerCase().includes(q));
  if (onlyDesign) vars = vars.filter(v => v.used_in_layout);
  // Filtros de estado: si hay alguno activo, mostrar las que cumplan al menos uno.
  if (fUnused || fCritical || fOrphan) {
    vars = vars.filter(v =>
      (fUnused && inArr(rep.unused, v.name)) ||
      (fCritical && inArr(rep.critical, v.name)) ||
      (fOrphan && inArr(rep.orphan, v.name)));
  }
  const inDesign = DATA.variables.filter(v => v.used_in_layout).length;
  const rows = vars.map(v =>
    `<tr><td><a data-var="${esc(v.name)}">${esc(v.name)}</a></td>`+
    `<td>${esc(v.type)}</td><td>${esc(v.created_in.join(', '))}</td>`+
    `<td>${esc(v.modified_in.join(', '))}</td><td>${esc(v.used_in.join(', '))}</td>`+
    `<td>${designCell(v)}</td><td>${flag(v.name)}</td></tr>`).join('');
  document.getElementById('variablesView').innerHTML =
    `<div class="count">${vars.length} variables · ${(rep.unused||[]).length} sin uso · `+
    `${(rep.critical||[]).length} críticas`+(HAS_LAYOUT?` · ${inDesign} en diseño`:'')+
    ` &nbsp; <em>(clic en una variable para ver su recorrido)</em></div>`+
    `<table><thead><tr>`+
    ['Variable','Tipo','Creada','Modificada','Usada','Diseño','Estado']
      .map(h=>`<th>${h}</th>`).join('')+
    `</tr></thead><tbody>${rows}</tbody></table>`;
  document.querySelectorAll('#variablesView a[data-var]').forEach(a =>
    a.onclick = () => openLineage(a.dataset.var));
  document.querySelectorAll('#variablesView a[data-design]').forEach(a =>
    a.onclick = () => openPages(a.dataset.design));
}
document.getElementById('searchVar').oninput = renderVariables;
['filterDesign','filterUnused','filterCritical','filterOrphan'].forEach(id =>
  document.getElementById(id).onchange = renderVariables);

// ---- Cuadro con las hojas que usan una variable ----
function openPages(name) {
  const v = VAR_BY_NAME[name]; if (!v) return;
  const pages = (v.layout_pages||[]).slice().sort();
  const paths = (v.layout_paths||[]).slice().sort();
  document.getElementById('pagesTitle').textContent = 'Hojas que usan: ' + name;
  document.getElementById('pagesBody').innerHTML =
    `<div class="count" style="margin-bottom:8px">${pages.length} hoja(s) usan esta variable</div>`+
    `<ul class="pageslist">${pages.map(p => `<li>${esc(p)}</li>`).join('')}</ul>`+
    (paths.length ? `<div style="margin-top:10px"><b>Rutas en el diseño:</b><br>`+
      paths.map(r => `<code>${esc(r)}</code>`).join('<br>')+`</div>` : '');
  document.getElementById('pagesOverlay').classList.add('show');
}
document.getElementById('pagesClose').onclick = () =>
  document.getElementById('pagesOverlay').classList.remove('show');
document.getElementById('pagesOverlay').onclick = (e) => {
  if (e.target.id === 'pagesOverlay') e.target.classList.remove('show');
};

// ---- Linaje de variable (grafo de recorrido) ----
function safeId(s){ return 'v_'+String(s).replace(/\W/g,'_'); }
function buildLineageMermaid(v) {
  const nameToIds = {}; DATA.modules.forEach(m => (nameToIds[m.name]=nameToIds[m.name]||[]).push(m.id));
  const idName = {}; DATA.modules.forEach(m => idName[m.id]=m.name);
  const role = {};
  const setRole = (names, r) => (names||[]).forEach(n =>
    (nameToIds[n]||[]).forEach(id => { if (!role[id]) role[id]=r; }));
  setRole(v.created_in, 'crea');
  setRole(v.modified_in, 'modifica');
  setRole(v.used_in, 'usa');
  // Sólo los módulos donde la variable se crea / modifica / usa (sin tránsito).
  const R = Object.keys(role);
  const roleSet = new Set(R);
  const adj = {}; DATA.connections.forEach(c => (adj[c.from]=adj[c.from]||[]).push(c.to));
  // Para cada módulo relevante, qué otros módulos relevantes alcanza por el flujo.
  const reach = {};
  R.forEach(src => {
    const seen = new Set(); const q = [...(adj[src]||[])];
    while (q.length) { const n = q.shift(); if (seen.has(n)) continue; seen.add(n);
      (adj[n]||[]).forEach(x => { if (!seen.has(x)) q.push(x); }); }
    reach[src] = [...seen].filter(id => roleSet.has(id) && id !== src);
  });
  // Reducción transitiva: arista directa r->s sólo si s no se alcanza vía otro relevante.
  const edges = [];
  R.forEach(r => {
    (reach[r] || []).forEach(s => {
      if (!reach[r].some(t => t !== s && (reach[t]||[]).includes(s))) edges.push([r, s]);
    });
  });
  const styleByRole = {crea:'crea', modifica:'modifica', usa:'usa'};
  const lines = ['flowchart LR'];
  lines.push('classDef crea fill:#16a34a,stroke:#14532d,color:#fff;');
  lines.push('classDef modifica fill:#fbbf24,stroke:#92400e,color:#1f2937;');
  lines.push('classDef usa fill:#38bdf8,stroke:#075985,color:#06283d;');
  lines.push('classDef design fill:#c084fc,stroke:#6b21a8,color:#2e1065;');
  R.forEach(id =>
    lines.push(`${safeId(id)}["${esc(idName[id]||id)}<br/>${role[id]}"]:::${styleByRole[role[id]]}`));
  edges.forEach(([a, b]) => lines.push(`${safeId(a)} --> ${safeId(b)}`));
  if (v.used_in_layout) {
    const np = (v.layout_pages||[]).length;
    lines.push(`DESIGN(["Diseño / Layout<br/>${np} página(s)"]):::design`);
    // El diseño consume el dato al final: enlazar desde los nodos sin sucesor relevante.
    const sinks = R.filter(id => !edges.some(e => e[0] === id));
    (sinks.length ? sinks : R).forEach(id => lines.push(`${safeId(id)} -.-> DESIGN`));
  }
  return {src: lines.join('\n'), count: R.length};
}
function openLineage(name) {
  const v = VAR_BY_NAME[name]; if (!v) return;
  document.getElementById('lineageTitle').textContent = 'Linaje: ' + name;
  const created = (v.created_in||[]).join(', ') || '—';
  const modified = (v.modified_in||[]).join(', ') || '—';
  const used = (v.used_in||[]).join(', ') || '—';
  const design = v.used_in_layout
    ? `<b>Diseño:</b> ${esc((v.layout_pages||[]).join('; '))}<br>`+
      `<b>Rutas:</b> <code>${esc((v.layout_paths||[]).join('</code>, <code>'))}</code>`
    : '<b>Diseño:</b> no se usa en el diseño';
  const {src, count} = buildLineageMermaid(v);
  document.getElementById('lineageBody').innerHTML =
    `<div class="count" style="margin-bottom:8px">Tipo: ${esc(v.type||'-')} · `+
    `Crea: ${esc(created)} · Modifica: ${esc(modified)} · Usa: ${esc(used)}</div>`+
    `<div style="margin-bottom:10px">${design}</div>`+
    (count>30?`<div class="count">Grafo grande (${count} módulos): usa el zoom y arrastra para navegar.</div>`:'')+
    `<div id="lineageGraph"><div class="count">Renderizando…</div></div>`+
    `<details style="margin-top:10px"><summary>Ver código Mermaid</summary><pre>${esc(src)}</pre></details>`;
  document.getElementById('lineageOverlay').classList.add('show');
  renderMermaidInto('lineageGraph', src, 'Usa el código de abajo.', {lineage:true});
}
document.getElementById('lineageClose').onclick = () =>
  document.getElementById('lineageOverlay').classList.remove('show');
document.getElementById('lineageOverlay').onclick = (e) => {
  if (e.target.id === 'lineageOverlay') e.target.classList.remove('show');
};

// ---- Reglas ----
function renderRules() {
  const q = document.getElementById('searchRule').value.trim().toLowerCase();
  const rules = (DATA.rules||[]).filter(r => !q ||
    (r.module+' '+r.type+' '+r.target+' '+r.expression+' '+r.detail).toLowerCase().includes(q));
  document.getElementById('rulesView').innerHTML = `<div class="count">${rules.length} reglas</div>` +
    tbl(['Módulo','Categoría','Tipo','Destino','Expresión'],
      rules.map(r => [r.module, r.category, r.type, r.target, r.expression]));
}
document.getElementById('searchRule').oninput = renderRules;

// ---- Carga de Mermaid (compartida por diagrama y linaje) ----
let mermaidPromise = null;
function ensureMermaid() {
  if (mermaidPromise) return mermaidPromise;
  mermaidPromise = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
    s.onload = () => {
      // maxEdges alto: los workflows grandes superan el límite de 500 de Mermaid.
      mermaid.initialize({startOnLoad:false, theme:'dark', maxEdges:100000});
      resolve(mermaid);
    };
    s.onerror = () => reject(new Error('sin conexión'));
    document.body.appendChild(s);
  });
  return mermaidPromise;
}
async function renderMermaidInto(elId, src, fallbackMsg, opts) {
  const host = document.getElementById(elId);
  try {
    const m = await ensureMermaid();
    const {svg} = await m.render(elId+'_svg', src);
    host.innerHTML =
      `<div class="graphview${opts&&opts.lineage?' lineage':''}">`+
        `<div class="graphctrl">`+
          `<button data-zout title="Alejar">&minus;</button>`+
          `<button data-zfit title="Ajustar a la vista">&#9974;</button>`+
          `<button data-zin title="Acercar">+</button>`+
        `</div>`+
        `<div class="graphhint">arrastra para mover · rueda para zoom</div>`+
        svg+
      `</div>`;
    mountPanZoom(host.querySelector('.graphview'));
  } catch(e) {
    host.innerHTML = '<div class="count">No se pudo renderizar ('+e+'). '+(fallbackMsg||'')+'</div>';
  }
}

// Zoom + paneo sobre un SVG ya renderizado (sin dependencias, funciona offline).
function mountPanZoom(view) {
  const svg = view.querySelector('svg');
  if (!svg) return;
  svg.removeAttribute('width'); svg.removeAttribute('height');
  svg.style.maxWidth = 'none';
  let scale = 1, tx = 0, ty = 0, dragging = false, sx = 0, sy = 0;
  const apply = () => { svg.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`; };
  function graphSize() {
    const vb = svg.viewBox && svg.viewBox.baseVal;
    if (vb && vb.width) return [vb.width, vb.height];
    try { const bb = svg.getBBox(); return [bb.width||view.clientWidth, bb.height||view.clientHeight]; }
    catch(e) { return [view.clientWidth, view.clientHeight]; }
  }
  function fit() {
    const [gw, gh] = graphSize();
    const cw = view.clientWidth, ch = view.clientHeight;
    // Escala inicial "decente": no ampliar grafos pequeños (máx 1x) ni encoger
    // los enormes hasta un punto (mín legible y se panea).
    const base = Math.min(cw/gw, ch/gh) * 0.95 || 1;
    scale = Math.min(1, Math.max(0.18, base));
    tx = Math.max(0, (cw - gw*scale)/2); ty = Math.max(0, (ch - gh*scale)/2); apply();
  }
  function zoomAt(mx, my, factor) {
    const ns = Math.min(8, Math.max(0.03, scale*factor));
    tx = mx - (mx-tx)*(ns/scale); ty = my - (my-ty)*(ns/scale); scale = ns; apply();
  }
  view.addEventListener('wheel', e => {
    e.preventDefault();
    const r = view.getBoundingClientRect();
    zoomAt(e.clientX-r.left, e.clientY-r.top, e.deltaY<0 ? 1.15 : 1/1.15);
  }, {passive:false});
  view.addEventListener('mousedown', e => {
    if (e.target.closest('.graphctrl')) return;
    dragging = true; sx = e.clientX-tx; sy = e.clientY-ty; view.classList.add('grabbing');
  });
  view.addEventListener('mousemove', e => { if (dragging) { tx = e.clientX-sx; ty = e.clientY-sy; apply(); } });
  const stop = () => { dragging = false; view.classList.remove('grabbing'); };
  view.addEventListener('mouseup', stop);
  view.addEventListener('mouseleave', stop);
  const c = view.querySelector('.graphctrl');
  c.querySelector('[data-zin]').onclick = () => { const r=view.getBoundingClientRect();
    zoomAt(r.width/2, r.height/2, 1.25); };
  c.querySelector('[data-zout]').onclick = () => { const r=view.getBoundingClientRect();
    zoomAt(r.width/2, r.height/2, 1/1.25); };
  c.querySelector('[data-zfit]').onclick = fit;
  requestAnimationFrame(fit);
}

// ---- Diagrama ----
// Para flujos grandes, el grafo completo es ilegible. Por defecto se enfoca un
// módulo y se muestra su vecindario (aguas arriba/abajo) hasta cierta
// profundidad; "Ver todo" muestra el grafo completo en el visor con zoom.
const CAT_COLORS = {input:'#5eead4',transform:'#fbbf24',control:'#f87171',
  integration:'#c084fc',script:'#4ade80',output:'#fb923c',other:'#64748b'};
const BIG_FLOW = DATA.modules.length > 40;
function buildFlowSubgraph(centerId, depth) {
  const adjOut = {}, adjIn = {};
  DATA.connections.forEach(c => { (adjOut[c.from]=adjOut[c.from]||[]).push(c.to);
    (adjIn[c.to]=adjIn[c.to]||[]).push(c.from); });
  const inc = new Set([centerId]); const q = [[centerId,0]];
  while (q.length) { const [n,d] = q.shift(); if (d>=depth) continue;
    [...(adjOut[n]||[]), ...(adjIn[n]||[])].forEach(nb => {
      if (!inc.has(nb)) { inc.add(nb); q.push([nb,d+1]); } }); }
  const idName = {}, idCat = {};
  DATA.modules.forEach(m => { idName[m.id]=m.name; idCat[m.id]=m.category; });
  const lines = ['flowchart LR'];
  Object.entries(CAT_COLORS).forEach(([c,col]) =>
    lines.push(`classDef ${c} fill:${col},color:#0f172a,stroke:#1e293b;`));
  lines.push('classDef center fill:#38bdf8,color:#06283d,stroke:#0ea5e9,stroke-width:4px;');
  inc.forEach(id => { const cls = id===centerId ? 'center' : (idCat[id]||'other');
    lines.push(`${safeId(id)}["${esc(idName[id]||id)}<br/>${esc(idCat[id]||'')}"]:::${cls}`); });
  DATA.connections.forEach(c => { if (inc.has(c.from) && inc.has(c.to))
    lines.push(`${safeId(c.from)} --> ${safeId(c.to)}`); });
  return {src: lines.join('\n'), count: inc.size};
}
function focusModule() {
  const name = document.getElementById('focusSearch').value.trim();
  const depth = +document.getElementById('focusDepth').value;
  const center = DATA.modules.find(m => m.name === name);
  const mmd = document.getElementById('mmd');
  if (!center) { mmd.innerHTML = '<div class="count">Escribe y elige un módulo de la lista.</div>'; return; }
  const {src, count} = buildFlowSubgraph(center.id, depth);
  mmd.innerHTML = '<div class="count">Renderizando '+count+' módulos…</div>';
  renderMermaidInto('mmd', src, 'Usa el código de abajo.');
}
let diagramRendered = false;
function renderDiagram() {
  if (diagramRendered) return;
  diagramRendered = true;
  const el = document.getElementById('diagramView');
  const names = DATA.modules.map(m => m.name).sort();
  el.innerHTML = `<div class="section"><h3>Diagrama de flujo</h3>
    <div class="toolbar" style="padding:0 0 10px">
      <input id="focusSearch" list="modNames" placeholder="Enfocar un módulo (escribe y elige)…"
             style="flex:1;min-width:220px;padding:9px 12px;border-radius:8px;border:1px solid var(--border);background:var(--panel);color:var(--text)">
      <datalist id="modNames">${names.map(n=>`<option value="${esc(n)}"></option>`).join('')}</datalist>
      <label class="count">Profundidad
        <select id="focusDepth"><option>1</option><option selected>2</option><option>3</option></select></label>
      <button class="chip" id="focusBtn">Enfocar</button>
      <button class="chip" id="fullBtn">Ver todo (${DATA.modules.length})</button>
    </div>
    <div id="mmd"><div class="count">${BIG_FLOW
      ? 'El flujo tiene '+DATA.modules.length+' módulos. Enfoca un módulo para verlo legible, o pulsa “Ver todo”.'
      : 'Renderizando…'}</div></div>
    <details style="margin-top:12px"><summary>Ver código Mermaid (completo)</summary>
    <pre>${esc(DATA.mermaid)}</pre></details></div>`;
  document.getElementById('focusBtn').onclick = focusModule;
  document.getElementById('focusSearch').onkeydown = e => { if (e.key==='Enter') focusModule(); };
  document.getElementById('fullBtn').onclick = () => {
    document.getElementById('mmd').innerHTML = '<div class="count">Renderizando flujo completo…</div>';
    renderMermaidInto('mmd', DATA.mermaid, 'Usa el código de abajo.');
  };
  if (!BIG_FLOW) renderMermaidInto('mmd', DATA.mermaid, 'Usa el código de abajo.');
}

// ---- Init ----
renderModuleList(); renderVariables(); renderRules();
</script>
</body>
</html>
"""
