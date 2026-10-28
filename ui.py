"""Presentation helpers and design system for IntentLedger."""

from __future__ import annotations

import html
import json
from typing import Any

import streamlit as st

from engine.extractor import OFFLINE_MODE_NOTE
from engine.scorer import ScoreResult


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def display_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).lower() if isinstance(value, bool) else str(value)


def inject_design_system() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{--ink:#f4f5fb;--muted:#929ab0;--dim:#626b82;--line:#252b43;--panel:#11162a;--navy:#080b18;--violet:#8b7cff;--blue:#55a7ff;--green:#46d9a3;--red:#ff647c;--amber:#ffbd66}
html,body,[data-testid="stAppViewContainer"]{background:var(--navy);color:var(--ink);font-family:'DM Sans',sans-serif}
[data-testid="stAppViewContainer"]{background-image:radial-gradient(circle at 78% -10%,rgba(88,75,190,.16),transparent 30%)}
[data-testid="stMainBlockContainer"]{max-width:1280px;padding:2rem 2.6rem 4rem}
[data-testid="stSidebar"]{background:#0c1021;border-right:1px solid var(--line)}[data-testid="stSidebarUserContent"]{padding:1.4rem 1.15rem}
#MainMenu,footer,[data-testid="stHeader"]{visibility:hidden}h1,h2,h3{color:var(--ink);letter-spacing:-.035em}p{color:#c2c7d6}
.brand{display:flex;gap:.75rem;align-items:center;margin:.2rem 0 .35rem}.brand-mark{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:linear-gradient(145deg,#9283ff,#4e87ff);box-shadow:0 8px 24px rgba(112,101,255,.25);font-weight:700}.brand-name{font-weight:700;font-size:1.05rem}.brand-copy{color:var(--muted);font-size:.78rem;line-height:1.45;margin:0 0 1.4rem}
.side-label,.section-kicker{color:#858da5;font-size:.67rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin:.9rem 0 .55rem}.side-rule,.workspace-rule{height:1px;background:var(--line);margin:1.2rem 0}
.scope-card{margin-top:1rem;padding:.85rem;border:1px solid var(--line);border-radius:12px;background:#10152a}.scope-card span{color:var(--amber);font:600 .62rem 'JetBrains Mono';letter-spacing:.12em}.scope-card strong{display:block;margin:.35rem 0;font-size:.83rem}.scope-card p{color:var(--muted);margin:0;font-size:.7rem;line-height:1.45}
.status-box{border:1px solid var(--line);border-radius:12px;padding:.8rem;background:#10152a;margin-bottom:.65rem}.status-row{display:flex;align-items:center;gap:.5rem;margin:.32rem 0;font-size:.74rem;color:#c2c7d6}.dot{width:7px;height:7px;border-radius:50%;background:var(--dim);box-shadow:0 0 0 3px rgba(98,107,130,.12)}.dot.good{background:var(--green)}.dot.warn{background:var(--amber)}.dot.bad{background:var(--red)}.model-name{font:500 .7rem 'JetBrains Mono';color:#d7dafa;overflow-wrap:anywhere}
.hero{display:flex;justify-content:space-between;gap:2rem;align-items:flex-start;margin:.15rem 0 1.15rem}.eyebrow{display:inline-flex;color:#b9b2ff;border:1px solid rgba(139,124,255,.3);background:rgba(139,124,255,.08);padding:.34rem .58rem;border-radius:999px;font:600 .65rem 'JetBrains Mono';letter-spacing:.1em;text-transform:uppercase}.hero h1{margin:.75rem 0 .3rem;font-size:2.15rem}.hero p{margin:0;max-width:710px;color:var(--muted);font-size:.95rem}.hero-model{min-width:210px;border-left:1px solid var(--line);padding-left:1rem;margin-top:.45rem}.hero-model span{display:block;color:var(--dim);font-size:.66rem;text-transform:uppercase;letter-spacing:.12em}.hero-model code{display:block;color:#c7c2ff;margin-top:.35rem;font-size:.72rem;overflow-wrap:anywhere}
.metric{min-height:118px;padding:1rem 1.1rem;border:1px solid var(--line);border-radius:14px;background:linear-gradient(145deg,rgba(21,27,49,.98),rgba(14,19,37,.98));box-shadow:0 12px 35px rgba(0,0,0,.14)}.metric:before{content:'';display:block;width:24px;height:2px;background:var(--metric-accent,var(--violet));margin-bottom:.75rem}.metric-label{color:var(--muted);font-size:.72rem}.metric-value{font-size:1.65rem;font-weight:700;margin:.12rem 0;letter-spacing:-.04em}.metric-note{color:var(--dim);font-size:.66rem}
.scenario-head{margin-bottom:.7rem}.scenario-head h2{font-size:1.55rem;margin:.3rem 0}.scenario-head p{color:var(--muted);max-width:850px;margin:.2rem 0;font-size:.88rem}.pill{display:inline-block;border:1px solid #30385a;color:#a9b1c8;border-radius:999px;padding:.25rem .55rem;font:500 .65rem 'JetBrains Mono';text-transform:uppercase;letter-spacing:.06em}
.turn{position:relative;margin:.6rem 0;padding:.9rem 1rem .95rem 3rem;border:1px solid var(--line);border-radius:13px;background:var(--panel)}.turn.user{border-left:2px solid var(--blue)}.turn.assistant{border-left:2px solid var(--violet);background:#10152a}.turn-index{position:absolute;left:1rem;top:.9rem;font:600 .66rem 'JetBrains Mono';color:var(--dim)}.turn-role{color:#8e96ad;font:600 .64rem 'JetBrains Mono';letter-spacing:.12em;text-transform:uppercase;margin-bottom:.35rem}.turn-body{color:#e1e4ef;font-size:.86rem;line-height:1.55}
.state-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.55rem}.state-row{padding:.75rem .85rem;border:1px solid var(--line);background:var(--panel);border-radius:10px}.state-key{color:#8992aa;font:500 .68rem 'JetBrains Mono';margin-bottom:.3rem}.state-value{color:#eceefa;font:500 .78rem 'JetBrains Mono';overflow-wrap:anywhere}.callout{border:1px solid #2f3655;background:#10162b;border-radius:11px;padding:.8rem 1rem;color:#aeb6cb;font-size:.78rem;margin:.9rem 0}
.result-head{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.85rem 1rem;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin-bottom:.7rem}.result-title{font-weight:700}.result-sub{color:var(--muted);font-size:.72rem;margin-top:.15rem}.badge{display:inline-flex;align-items:center;gap:.35rem;padding:.28rem .55rem;border:1px solid;border-radius:999px;font:600 .65rem 'JetBrains Mono';letter-spacing:.08em}.badge-pass{color:var(--green);background:rgba(70,217,163,.08);border-color:rgba(70,217,163,.35)}.badge-fail{color:var(--red);background:rgba(255,100,124,.08);border-color:rgba(255,100,124,.35)}.badge-error{color:var(--amber);background:rgba(255,189,102,.08);border-color:rgba(255,189,102,.35)}
.score-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin:.7rem 0 1rem}.score-stat{border:1px solid var(--line);border-radius:10px;padding:.7rem .8rem;background:#0f1427}.score-stat strong{display:block;font-size:1.05rem}.score-stat span{color:var(--muted);font-size:.65rem}
.field-table,.case-table{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:.76rem}.field-table th,.case-table th{padding:.65rem .75rem;background:#151b31;color:#8992aa;text-align:left;font:600 .62rem 'JetBrains Mono';text-transform:uppercase;letter-spacing:.08em}.field-table td,.case-table td{padding:.7rem .75rem;border-top:1px solid var(--line);color:#d8dce9;background:#0f1426;vertical-align:middle}.field-table code,.case-table code{color:#c9c5ff;font-size:.68rem;white-space:normal;overflow-wrap:anywhere}.s-match{color:var(--green)}.s-mismatch{color:var(--red)}.s-missing{color:var(--amber)}.s-unexpected{color:#b69cff}
.error-panel{border:1px solid rgba(255,189,102,.32);border-radius:12px;background:rgba(255,189,102,.05);padding:1rem}.error-panel strong{color:var(--amber)}.error-panel p{margin:.4rem 0;font-size:.78rem;color:#c6c0b4}.empty{text-align:center;border:1px dashed #303751;border-radius:12px;padding:2.2rem 1rem;color:var(--muted);background:rgba(17,22,42,.55)}
.compare-card{border:1px solid var(--line);border-radius:13px;padding:1rem;background:var(--panel)}.compare-rate{font-size:1.8rem;font-weight:700;margin:.5rem 0}.compare-bar{height:6px;background:#242a41;border-radius:99px;overflow:hidden}.compare-bar span{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--violet),var(--blue))}.changed{color:var(--green);font-weight:600}.unchanged{color:var(--dim)}.footer-note{color:var(--dim);text-align:center;font-size:.68rem;margin-top:2.5rem}
[data-testid="stRadio"] label{border-radius:9px;padding:.3rem .45rem}[data-testid="stRadio"] label:hover{background:#151a30}[data-baseweb="tab-list"]{gap:.25rem;border-bottom:1px solid var(--line)}[data-baseweb="tab"]{padding:.7rem .9rem;color:#8f97ae}[aria-selected="true"][data-baseweb="tab"]{color:#f0f1f8;background:#151a30;border-radius:8px 8px 0 0}.stButton>button{border-radius:9px;min-height:2.55rem;font-weight:600;transition:transform .15s ease,border-color .15s ease}.stButton>button:hover{transform:translateY(-1px);border-color:#776aea}.stButton>button:focus-visible{outline:2px solid var(--blue);outline-offset:2px}.stButton>button[kind="primary"]{background:linear-gradient(135deg,#7567ea,#536fe7);border:1px solid #8c82f1}[data-testid="stProgress"]>div>div{background:linear-gradient(90deg,var(--violet),var(--blue))}

/* Richer indigo surface hierarchy */
:root{--ink:#f7f8ff;--muted:#a4acc2;--dim:#717b95;--line:#303958;--panel:#151c36;--navy:#0b1025;--violet:#9b8cff;--blue:#62b5ff;--green:#4de1ac;--red:#ff7088;--amber:#ffc36b}
html,body,[data-testid="stAppViewContainer"]{background:#0b1025}
[data-testid="stAppViewContainer"],.stApp,[data-testid="stMain"]{background-color:#141a38!important;background-image:radial-gradient(circle at 82% 4%,rgba(121,91,255,.34),transparent 30%),radial-gradient(circle at 12% 34%,rgba(40,143,219,.22),transparent 28%),linear-gradient(145deg,#151b3a 0%,#111733 52%,#0d1430 100%)!important;background-attachment:fixed!important}
[data-testid="stAppViewContainer"]:before{content:'';position:fixed;inset:0;pointer-events:none;opacity:.24;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,black,transparent 72%)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#121936 0%,#0e142d 100%);border-right:1px solid #354064;box-shadow:18px 0 55px rgba(2,5,18,.28)}
.status-box,.scope-card{border-color:#394568;background:linear-gradient(145deg,rgba(28,37,72,.92),rgba(18,25,52,.94));box-shadow:0 12px 30px rgba(2,6,20,.18)}
.hero{position:relative;overflow:hidden;padding:1.45rem 1.55rem;border:1px solid #3a456b;border-radius:18px;background:linear-gradient(135deg,rgba(28,38,78,.94),rgba(19,27,58,.9));box-shadow:0 22px 60px rgba(1,4,18,.26)}
.hero:after{content:'';position:absolute;width:240px;height:240px;border-radius:50%;right:-90px;top:-135px;background:rgba(111,91,255,.24)}.hero>div{position:relative;z-index:1}.hero p{color:#b3bbd2}.hero-model{border-color:#465178}.hero-model code{color:#d4d0ff}
.metric{border-color:#364164;background:linear-gradient(145deg,rgba(28,37,72,.96),rgba(18,25,53,.96));box-shadow:0 16px 38px rgba(1,4,18,.2)}
.turn{border-color:#354061;box-shadow:0 8px 24px rgba(2,5,18,.12)}.turn.user{border-left-width:3px;background:linear-gradient(100deg,rgba(26,48,86,.95),rgba(23,31,62,.92))}.turn.assistant{border-left-width:3px;background:linear-gradient(100deg,rgba(44,35,82,.9),rgba(23,31,62,.92))}
.field-table td,.case-table td{border-top-color:#303a5b;color:#e2e5f0;background:rgba(20,28,57,.94)}.field-table tr:nth-child(even) td,.case-table tr:nth-child(even) td{background:rgba(24,33,65,.96)}.case-table tr:hover td{background:#202b52}
[data-testid="stRadio"] label{padding:.38rem .5rem;border:1px solid transparent}[data-testid="stRadio"] label:hover{background:#1b2448;border-color:#384569}[data-testid="stRadio"] label:has(input:checked){background:linear-gradient(90deg,rgba(111,92,255,.22),rgba(70,133,220,.12));border-color:#495582}
[data-baseweb="tab-list"]{padding:.25rem;border:1px solid #303a5b;border-radius:11px;background:rgba(17,24,51,.72)}[aria-selected="true"][data-baseweb="tab"]{background:linear-gradient(135deg,#6256c9,#435fbf);box-shadow:0 6px 18px rgba(52,47,135,.25)}

/* Prevent Streamlit's light theme from leaking into the dark product UI. */
.brand-name,.scope-card strong{color:#f4f6ff!important}
code,[data-testid="stCode"] code,.hero-model code,.field-table code,.case-table code{
  color:#c8c4ff!important;background:#11172d!important;border:1px solid #313b5d!important;
  border-radius:5px!important;padding:.12rem .28rem!important;box-shadow:none!important
}
.hero-model code{display:block!important;padding:.32rem .45rem!important}
.field-table code,.case-table code{display:inline-block!important;background:#171e3a!important;border-color:#2b3557!important}
.stButton>button[kind="secondary"],button[kind="secondary"]{
  color:#e6e9f5!important;background:linear-gradient(145deg,#171e38,#11172d)!important;
  border:1px solid #3a4568!important;box-shadow:0 8px 20px rgba(2,5,18,.18)!important
}
.stButton>button[kind="secondary"] p,button[kind="secondary"] p{color:#e6e9f5!important}
.stButton>button:disabled,.stButton>button[disabled]{
  color:#707990!important;background:#11172b!important;border-color:#28314d!important;
  opacity:.72!important;box-shadow:none!important
}
.stButton>button:disabled p,.stButton>button[disabled] p{color:#707990!important}
[data-testid="stSidebar"] .stButton>button{background:#11172b!important;color:#cbd1e3!important;border-color:#34405f!important}
[data-testid="stSidebar"] .stButton>button p{color:#cbd1e3!important}
.stDownloadButton>button{
  width:100%;min-height:2.55rem;color:#eef0ff!important;
  background:linear-gradient(135deg,#6256cf,#4967d2)!important;
  border:1px solid #887df1!important;border-radius:9px!important;
  font-weight:600!important;box-shadow:0 9px 24px rgba(42,38,128,.24)!important
}
.stDownloadButton>button:hover{transform:translateY(-1px);border-color:#aaa2ff!important}
.stDownloadButton>button:focus-visible{outline:2px solid var(--blue)!important;outline-offset:2px!important}
.stDownloadButton>button p{color:#eef0ff!important}
@media(max-width:800px){[data-testid="stMainBlockContainer"]{padding:1.1rem 1rem 3rem}.hero{display:block}.hero-model{border-left:0;padding-left:0;margin-top:1rem}.score-strip{grid-template-columns:repeat(2,1fr)}.field-table,.case-table{display:block;overflow-x:auto}.metric{min-height:104px}}
</style>""", unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    st.markdown('<div class="brand"><div class="brand-mark">IL</div><div class="brand-name">IntentLedger</div></div><p class="brand-copy">A compact lab for testing whether models preserve final user intent across changing instructions.</p>', unsafe_allow_html=True)


def render_api_status(model: str, key_present: bool, verified: bool | None, message: str) -> None:
    key_text, key_class = ("API key configured", "good") if key_present else ("API key not configured", "warn")
    live_text, live_class = (("Live request verified", "good") if verified is True else
                             ("Live verification failed", "bad") if verified is False else
                             ("Live access not verified", "warn"))
    detail = f'<div class="result-sub">{esc(message)}</div>' if message else ""
    st.markdown(f'<div class="side-label">Runtime</div><div class="status-box"><div class="model-name">{esc(model)}</div><div class="status-row"><i class="dot {key_class}"></i>{key_text}</div><div class="status-row"><i class="dot {live_class}"></i>{live_text}</div>{detail}</div>', unsafe_allow_html=True)


def render_header(model: str) -> None:
    st.markdown(f'<div class="hero"><div><span class="eyebrow">◈ Evaluation lab</span><h1>Track the intent. Measure the drift.</h1><p>Compare a naive extraction prompt with an instruction-aware prompt across corrections, rejections, partial updates, cancellations, and ambiguity.</p></div><div class="hero-model"><span>Configured model</span><code>{esc(model)}</code></div></div>', unsafe_allow_html=True)


def render_metric(label: str, value: str | None, note: str, accent: str) -> None:
    colors = {"violet":"#8b7cff","blue":"#55a7ff","green":"#46d9a3","neutral":"#929ab0"}
    st.markdown(f'<div class="metric" style="--metric-accent:{colors[accent]}"><div class="metric-label">{esc(label)}</div><div class="metric-value">{esc(value or "Not run")}</div><div class="metric-note">{esc(note)}</div></div>', unsafe_allow_html=True)


def render_scenario_intro(case: dict) -> None:
    kind = case.get("scenario_type", "scenario").replace("_", " ")
    st.markdown(f'<div class="scenario-head"><span class="pill">{esc(kind)}</span><h2>{esc(case["name"])}</h2><p>{esc(case.get("description", ""))}</p></div>', unsafe_allow_html=True)


def render_transcript(conversation: list[dict]) -> None:
    for index, turn in enumerate(conversation, 1):
        role = turn.get("role", "unknown")
        st.markdown(f'<div class="turn {esc(role)}"><span class="turn-index">{index:02d}</span><div class="turn-role">{esc(role)}</div><div class="turn-body">{esc(turn.get("content", ""))}</div></div>', unsafe_allow_html=True)


def render_expected_state(expected: dict, notes: str = "") -> None:
    rows = "".join(f'<div class="state-row"><div class="state-key">{esc(key)}</div><div class="state-value">{esc(display_value(value))}</div></div>' for key, value in expected.items())
    st.markdown(f'<div class="state-grid">{rows}</div>', unsafe_allow_html=True)
    if notes: st.markdown(f'<div class="callout"><strong>Evaluation intent</strong><br>{esc(notes)}</div>', unsafe_allow_html=True)


def badge(verdict: str) -> str:
    icon = {"PASS":"●","FAIL":"×","ERROR":"!"}.get(verdict, "?")
    return f'<span class="badge badge-{verdict.lower()}">{icon} {esc(verdict)}</span>'


def troubleshooting(error: str) -> str:
    lowered = error.lower()
    if OFFLINE_MODE_NOTE.lower() in lowered or "offline mode" in lowered: return "Set GEMINI_API_KEY, then use Verify live access before running the case again."
    if "quota" in lowered or "429" in lowered: return "Review the API project's quota and billing limits, then retry after the quota window resets."
    if "invalid api key" in lowered: return "Replace GEMINI_API_KEY with a valid key. The key is never displayed by IntentLedger."
    if "model not found" in lowered or "404" in lowered: return "Check INTENTLEDGER_MODEL and verify that this key can access the configured model."
    if "non-json" in lowered: return "Inspect the raw model output below; the response must contain a valid JSON object."
    return "Verify network and model access in the sidebar, then retry this evaluation."


def render_field_table(result: ScoreResult) -> None:
    rows = "".join(f'<tr><td><span class="s-{esc(field.status)}">{esc(field.status.upper())}</span></td><td><code>{esc(field.key)}</code></td><td><code>{esc(display_value(field.expected))}</code></td><td><code>{esc(display_value(field.predicted))}</code></td></tr>' for field in result.field_results)
    st.markdown(f'<table class="field-table"><thead><tr><th>Result</th><th>Field</th><th>Expected</th><th>Predicted</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)


def render_result(result: ScoreResult, label: str) -> None:
    st.markdown(f'<div class="result-head"><div><div class="result-title">{esc(label)} evaluation</div><div class="result-sub">Measured against the human-authored expected state</div></div>{badge(result.verdict)}</div>', unsafe_allow_html=True)
    if result.verdict == "ERROR":
        st.markdown(f'<div class="error-panel"><strong>Evaluation could not be scored</strong><p>{esc(result.error_message)}</p><p><b>Next step:</b> {esc(troubleshooting(result.error_message))}</p></div>', unsafe_allow_html=True)
        if result.raw_prediction:
            with st.expander("Inspect raw model output"): st.code(result.raw_prediction, language="text")
        return
    st.markdown(f'<div class="score-strip"><div class="score-stat"><strong>{result.field_match_rate * 100:.0f}%</strong><span>Field match</span></div><div class="score-stat"><strong>{result.matched}</strong><span>Matched</span></div><div class="score-stat"><strong>{result.mismatched + result.missing}</strong><span>Mismatch / missing</span></div><div class="score-stat"><strong>{result.unexpected}</strong><span>Unexpected</span></div></div>', unsafe_allow_html=True)
    render_field_table(result)
    if result.clarification_expected:
        message = "Clarification behavior detected" if result.clarification_ok else "Required clarification was not detected"
        st.markdown(f'<div class="callout">{esc(message)}</div>', unsafe_allow_html=True)
    if result.raw_prediction:
        with st.expander("Inspect raw model output"): st.code(result.raw_prediction, language="json")


def render_empty_result(label: str) -> None:
    st.markdown(f'<div class="empty"><strong>{esc(label)} has not been run</strong><br><span>Run this case to generate a measured prediction and field-level comparison.</span></div>', unsafe_allow_html=True)


def render_compare(baseline: ScoreResult | None, improved: ScoreResult | None) -> None:
    cols = st.columns(2, gap="medium")
    for column, result, label in ((cols[0], baseline, "Baseline"), (cols[1], improved, "Improved")):
        with column:
            if result is None:
                render_empty_result(label); continue
            rate = result.field_match_rate * 100 if result.verdict != "ERROR" else 0
            score_text = f"{rate:.0f}%" if result.verdict != "ERROR" else "Not scored"
            st.markdown(f'<div class="compare-card"><div class="result-head"><strong>{label}</strong>{badge(result.verdict)}</div><div class="compare-rate">{score_text}</div><div class="result-sub">Field match rate</div><div class="compare-bar"><span style="width:{rate:.0f}%"></span></div></div>', unsafe_allow_html=True)
            if result.verdict == "ERROR":
                st.caption(result.error_message)
            else:
                render_field_table(result)
    if baseline and improved and baseline.verdict != "ERROR" and improved.verdict != "ERROR":
        delta = (improved.field_match_rate - baseline.field_match_rate) * 100
        word = "higher" if delta > 0 else "lower" if delta < 0 else "unchanged"
        st.markdown(f'<div class="callout">Measured difference: <span class="{"changed" if delta > 0 else "unchanged"}">{abs(delta):.0f} percentage points {word}</span> for the improved prompt.</div>', unsafe_allow_html=True)


def result_cell(result: ScoreResult | None) -> str:
    if result is None: return '<span class="unchanged">Not run</span>'
    rate = f" · {result.field_match_rate * 100:.0f}%" if result.verdict != "ERROR" else ""
    return f'{badge(result.verdict)} <span>{rate}</span>'


def render_all_cases(cases: list[dict], baseline: dict[str, ScoreResult], improved: dict[str, ScoreResult]) -> None:
    rows = []
    for case in cases:
        b_result, i_result = baseline.get(case["id"]), improved.get(case["id"])
        if b_result and i_result and b_result.verdict != "ERROR" and i_result.verdict != "ERROR":
            delta = (i_result.field_match_rate - b_result.field_match_rate) * 100
            change = f'<span class="changed">+{delta:.0f} pp</span>' if delta > 0 else (f'<span class="s-mismatch">{delta:.0f} pp</span>' if delta < 0 else '<span class="unchanged">No change</span>')
        else: change = '<span class="unchanged">—</span>'
        rows.append(f'<tr><td><strong>{esc(case["name"])}</strong><br><code>{esc(case["scenario_type"])}</code></td><td>{result_cell(b_result)}</td><td>{result_cell(i_result)}</td><td>{change}</td></tr>')
    st.markdown(f'<table class="case-table"><thead><tr><th>Scenario</th><th>Baseline</th><th>Improved</th><th>Measured change</th></tr></thead><tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)
