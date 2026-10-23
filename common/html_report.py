"""
html_report.py - turns a recorded trace (list of state snapshots) into one
standalone HTML page. The trace data is embedded as JSON; the page only
replays it, it never invents events.
"""
import json

PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2733;--mute:#667085;--line:#d8dde5}
@media (prefers-color-scheme:dark){:root{--bg:#14181d;--card:#1e242c;--ink:#e8ecf1;--mute:#9aa5b3;--line:#333c48}}
body{margin:0;font:15px/1.4 system-ui,sans-serif;background:var(--bg);color:var(--ink)}
main{max-width:1000px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:0 0 4px} h3{margin:10px 0 2px;font-size:14px;color:var(--mute)}
.sub{color:var(--mute);margin-bottom:8px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
button,select{padding:6px 12px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;cursor:pointer}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.chip{display:inline-block;min-width:110px;margin:4px;padding:8px 10px;border-radius:6px;color:#111;text-align:center}
#now{font-weight:600;margin:6px 0 10px;min-height:1.4em}
#log{max-height:320px;overflow:auto;font:13px ui-monospace,monospace}
#log div{padding:2px 6px;cursor:pointer;border-radius:4px}
#log .now{background:#ffe08a;color:#111}
svg text{fill:var(--ink)} .bad{color:#c0392b;font-weight:700}
.legend span{display:inline-block;padding:1px 8px;margin:2px;border-radius:4px;color:#111;font-size:12px}
</style></head><body><main>
<h1>__TITLE__</h1>
<div class="sub" id="sub"></div>
<div class="bar">
 <button id="play">Play</button><button id="step">Step</button><button id="reset">Reset</button>
 <label>Speed <select id="speed"><option value="1000">slow</option><option value="500" selected>normal</option>
 <option value="200">fast</option><option value="60">very fast</option></select></label>
 <input type="range" id="slider" min="0" value="0" style="flex:1;min-width:160px">
 <span id="count"></span>
</div>
<div id="now"></div>
<div class="grid">
 <div class="card"><div id="vis"></div><div class="legend" id="legend"></div></div>
 <div class="card"><h3 style="margin-top:0">Event log (click to jump)</h3><div id="log"></div></div>
</div>
</main>
<script>
const T = __DATA__;
const ev = T.events;
const COL = {"Thinking":"#cfd8e3","Waiting":"#ffd166","Hungry":"#ffd166","Acquiring Forks":"#f4a261",
  "Reading":"#52b788","Writing":"#e76f51","Eating":"#52b788","Releasing Forks":"#8ecae6"};
const $ = id => document.getElementById(id);
let i = 0, timer = null;

const chip = (n, s) => `<span class="chip" style="background:${COL[s]||'#ddd'}"><b>${n}</b><br>${s}</span>`;

function drawRW(s) {
  const r = s.resource;
  const col = r.status === "Idle" ? "#cfd8e3" : r.status === "Being read" ? "#52b788" : "#e76f51";
  return `<h3>Readers</h3>${Object.entries(s.readers).map(([k,v])=>chip(k,v)).join("")}
   <h3>Writers</h3>${Object.entries(s.writers).map(([k,v])=>chip(k,v)).join("")}
   <h3>Shared resource (critical section)</h3>
   <div class="chip" style="background:${col};min-width:240px"><b>${r.status}</b><br>
   readers inside: ${r.readers} | writer inside: ${r.writer}<br>stored value: ${r.value}</div>`;
}

function drawDP(s) {
  const names = Object.keys(s.philosophers), n = names.length, cx = 200, cy = 200;
  const ang = (k, off) => (-90 + (k + off) * 360 / n) * Math.PI / 180;
  const at = (k, off, rad) => [cx + rad * Math.cos(ang(k, off)), cy + rad * Math.sin(ang(k, off))];
  let o = `<svg viewBox="0 0 400 400" style="width:100%;max-width:440px">
    <circle cx="200" cy="200" r="68" fill="none" stroke="#999" stroke-dasharray="4"/>`;
  Object.entries(s.forks).forEach(([f, owner], k) => {
    const [x, y] = at(k, 0.5, 92);
    if (owner !== "free") {
      const [px, py] = at(names.indexOf(owner), 0, 140);
      o += `<line x1="${x}" y1="${y}" x2="${px}" y2="${py}" stroke="#e76f51" stroke-width="4"/>`;
    }
    o += `<circle cx="${x}" cy="${y}" r="15" fill="${owner==='free'?'#fff':'#e76f51'}" stroke="#555"/>
          <text x="${x}" y="${y+4}" text-anchor="middle" font-size="11" style="fill:#111">${f}</text>`;
  });
  names.forEach((p, k) => {
    const [x, y] = at(k, 0, 160), st = s.philosophers[p];
    o += `<circle cx="${x}" cy="${y}" r="38" fill="${COL[st]||'#ddd'}" stroke="#555"/>
          <text x="${x}" y="${y-2}" text-anchor="middle" font-size="14" font-weight="700" style="fill:#111">${p}</text>
          <text x="${x}" y="${y+13}" text-anchor="middle" font-size="9.5" style="fill:#111">${st}</text>`;
  });
  return o + "</svg><div style='color:var(--mute);font-size:13px'>Filled fork = held (line shows owner). White fork = free.</div>";
}

function show(k) {
  i = Math.max(0, Math.min(ev.length - 1, k));
  const e = ev[i];
  $("vis").innerHTML = T.kind === "rw" ? drawRW(e.state) : drawDP(e.state);
  $("now").innerHTML = `[${e.t_ms} ms] ` + (e.msg.startsWith("!!") ? `<span class="bad">${e.msg}</span>` : e.msg);
  $("count").textContent = `event ${i + 1} / ${ev.length}`;
  $("slider").value = i;
  [...$("log").children].forEach((d, j) => d.className = j === i ? "now" : "");
  const cur = $("log").children[i]; if (cur) cur.scrollIntoView({block: "nearest"});
}
function stop() { clearInterval(timer); timer = null; $("play").textContent = "Play"; }
function play() {
  if (timer) return stop();
  if (i >= ev.length - 1) show(0);
  $("play").textContent = "Pause";
  timer = setInterval(() => { if (i >= ev.length - 1) stop(); else show(i + 1); }, +$("speed").value);
}
$("log").innerHTML = ev.map((e, k) => `<div onclick="show(${k})">${String(e.t_ms).padStart(5)} ms &nbsp;${e.msg}</div>`).join("");
$("slider").max = ev.length - 1;
$("legend").innerHTML = Object.entries(COL).filter(([k]) => T.kind==="rw" ? ["Thinking","Waiting","Reading","Writing"].includes(k) : !["Reading","Writing"].includes(k))
  .map(([k, v]) => `<span style="background:${v}">${k}</span>`).join("");
$("sub").textContent = Object.entries(T.params).map(([k, v]) => k + "=" + v).join("  |  ") + "  |  violations: " + T.violations;
$("play").onclick = play; $("step").onclick = () => { stop(); show(i + 1); };
$("reset").onclick = () => { stop(); show(0); };
$("slider").oninput = e => { stop(); show(+e.target.value); };
$("speed").onchange = () => { if (timer) { stop(); play(); } };
show(0);
</script></body></html>
"""


def write_html(path, data):
    payload = json.dumps(data).replace("</", "<\\/")
    html = PAGE.replace("__TITLE__", data["title"]).replace("__DATA__", payload)
    path.write_text(html, encoding="utf-8")
