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
  <div class="toolbar"><input id="searchVar" placeholder="Buscar variables..."></div>
  <div class="detail" id="variablesView"></div>
</div>

<div id="view-rules" class="hidden">
  <div class="toolbar"><input id="searchRule" placeholder="Buscar reglas / expresiones..."></div>
  <div class="detail" id="rulesView"></div>
</div>

<div id="view-diagram" class="hidden">
  <div class="detail" id="diagramView"></div>
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
  ['Joins',S.joins],['Filtros',S.filters],['Scripts',S.scripts]
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
function renderVariables() {
  const q = document.getElementById('searchVar').value.trim().toLowerCase();
  const rep = DATA.variable_report || {};
  const flag = n => [
    rep.unused&&rep.unused.includes(n)?'<span class="pill">sin uso</span>':'',
    rep.orphan&&rep.orphan.includes(n)?'<span class="pill">huérfana</span>':'',
    rep.critical&&rep.critical.includes(n)?'<span class="pill">crítica</span>':'',
  ].join('');
  const vars = DATA.variables.filter(v => !q || v.name.toLowerCase().includes(q));
  document.getElementById('variablesView').innerHTML =
    `<div class="count">${vars.length} variables · ${(rep.unused||[]).length} sin uso · `+
    `${(rep.critical||[]).length} críticas</div>` +
    tbl(['Variable','Tipo','Creada','Modificada','Usada','Estado'],
      vars.map(v => [v.name, v.type, v.created_in.join(', '), v.modified_in.join(', '),
        v.used_in.join(', '), flag(v.name)])).replace(/&lt;span/g,'<span').replace(/span&gt;/g,'span>');
}
document.getElementById('searchVar').oninput = renderVariables;

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

// ---- Diagrama ----
let diagramRendered = false;
function renderDiagram() {
  if (diagramRendered) return;
  diagramRendered = true;
  const el = document.getElementById('diagramView');
  el.innerHTML = `<div class="section"><h3>Diagrama de flujo</h3>
    <div class="mermaid" id="mmd">${esc(DATA.mermaid)}</div>
    <details style="margin-top:12px"><summary>Ver código Mermaid</summary>
    <pre>${esc(DATA.mermaid)}</pre></details></div>`;
  const s = document.createElement('script');
  s.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
  s.onload = () => { try {
    // maxEdges alto: los workflows grandes superan el límite de 500 de Mermaid.
    mermaid.initialize({startOnLoad:false, theme:'dark', maxEdges:100000});
    mermaid.run({nodes:[document.getElementById('mmd')]}).catch(err => {
      document.getElementById('mmd').innerHTML =
        '<div class="count">No se pudo renderizar: '+err+'. Usa el código de abajo.</div>';
    });
  } catch(e){
    document.getElementById('mmd').innerHTML =
      '<div class="count">No se pudo renderizar: '+e+'. Usa el código de abajo.</div>';
  } };
  s.onerror = () => { document.getElementById('mmd').innerHTML =
    '<div class="count">Sin conexión para renderizar; usa el código de abajo.</div>'; };
  document.body.appendChild(s);
}

// ---- Init ----
renderModuleList(); renderVariables(); renderRules();
</script>
</body>
</html>
"""
