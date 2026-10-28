"""IntentLedger — Streamlit evaluation laboratory with a refined indigo UI."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from engine.extractor import _get_api_key, _get_model_name, check_model_supported, extract_state
from engine.loader import load_all_cases
from engine.prompts import build_extraction_prompt
from engine.scorer import ScoreResult, score, summarise
from engine.exporter import build_export_bundle, export_csv, export_json
from ui import (
    inject_design_system, render_all_cases, render_api_status, render_compare,
    render_empty_result, render_expected_state, render_header, render_metric,
    render_result, render_scenario_intro, render_sidebar_brand, render_transcript,
)

st.set_page_config(page_title="IntentLedger · Evaluation Lab", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
inject_design_system()


@st.cache_data
def get_cases() -> list[dict]:
    return load_all_cases()


def run_case(case: dict, mode: str) -> ScoreResult:
    system_prompt, user_prompt = build_extraction_prompt(case["conversation"], mode)
    predicted, raw_text, error_message = extract_state(
        conversation=case["conversation"], mode=mode,
        system_prompt=system_prompt, user_prompt=user_prompt,
    )
    return score(
        case_id=case["id"], mode=mode, expected=case["expected_state"], predicted=predicted,
        clarification_expected=case.get("clarification_expected", False),
        error_message=error_message, raw_prediction=raw_text,
    )


def run_all(cases: list[dict], mode: str) -> dict[str, ScoreResult]:
    results: dict[str, ScoreResult] = {}
    progress = st.progress(0, text=f"Preparing {mode} evaluation…")
    for index, case in enumerate(cases):
        progress.progress(index / len(cases), text=f"{mode.title()} · {index + 1}/{len(cases)} · {case['name']}")
        results[case["id"]] = run_case(case, mode)
    progress.progress(1.0, text=f"{mode.title()} evaluation complete")
    progress.empty()
    return results


def average_rate(results: dict[str, ScoreResult]) -> str | None:
    if not results:
        return None
    summary = summarise(list(results.values()))
    return f"{summary['avg_field_match_rate'] * 100:.0f}%" if summary["total"] > summary["errors"] else "No score"


for key, default in {
    "results_baseline": {}, "results_improved": {},
    "api_verification": None, "api_verification_message": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

cases = get_cases()
case_map = {case["id"]: case for case in cases}
api_key_present = bool(_get_api_key())
model_name = _get_model_name()

with st.sidebar:
    render_sidebar_brand()
    st.markdown('<div class="side-label">Scenarios</div>', unsafe_allow_html=True)
    scenario_options = {case["id"]: f"{index + 1:02d}  ·  {case['name']}" for index, case in enumerate(cases)}
    selected_id = st.radio("Benchmark scenarios", options=list(scenario_options), format_func=scenario_options.get,
                           label_visibility="collapsed", key="selected_case_id")
    st.markdown('<div class="side-rule"></div>', unsafe_allow_html=True)
    render_api_status(model_name, api_key_present, st.session_state.api_verification,
                      st.session_state.api_verification_message)
    verify = st.button("Verify live access", disabled=not api_key_present, use_container_width=True,
                       help="Makes a model-list request; it does not run a benchmark case.")
    if verify:
        with st.spinner("Checking model access…"):
            ok, message = check_model_supported(model_name)
        st.session_state.api_verification = ok
        st.session_state.api_verification_message = message
        st.rerun()
    st.markdown(
        f'<div class="scope-card"><span>DEMO SCOPE</span><strong>{len(cases)} hand-crafted cases</strong>'
        '<p>Directional prompt comparison only. Results do not establish general AI reliability.</p></div>',
        unsafe_allow_html=True,
    )

render_header(model_name)
action_left, action_mid, action_right = st.columns([1.2, 1.2, 2.6], gap="small")
with action_left:
    run_baseline_all = st.button("Run all · Baseline", use_container_width=True)
with action_mid:
    run_improved_all = st.button("Run all · Improved", type="primary", use_container_width=True)
with action_right:
    st.caption("Each run calls the configured model once per scenario and keeps results in this session.")

if run_baseline_all:
    st.session_state.results_baseline = run_all(cases, "baseline")
if run_improved_all:
    st.session_state.results_improved = run_all(cases, "improved")

baseline_results: dict[str, ScoreResult] = st.session_state.results_baseline
improved_results: dict[str, ScoreResult] = st.session_state.results_improved
completed = len(set(baseline_results) | set(improved_results))

st.markdown('<div class="section-kicker">Benchmark overview</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4, gap="small")
with m1: render_metric("Scenario set", str(len(cases)), "Fixed benchmark scope", "violet")
with m2: render_metric("Completed", f"{completed}/{len(cases)}", "Unique scenarios evaluated", "blue")
with m3: render_metric("Baseline match", average_rate(baseline_results), "Average scored fields", "neutral")
with m4: render_metric("Improved match", average_rate(improved_results), "Average scored fields", "green")

selected_case = case_map[selected_id]
st.markdown('<div class="workspace-rule"></div>', unsafe_allow_html=True)
render_scenario_intro(selected_case)
info, run_b_col, run_i_col = st.columns([3.4, 1, 1], gap="small")
with info: st.caption("Run this case independently or inspect any result already held in session.")
with run_b_col: run_case_baseline = st.button("Run case · Baseline", use_container_width=True)
with run_i_col: run_case_improved = st.button("Run case · Improved", type="primary", use_container_width=True)

if run_case_baseline:
    with st.spinner(f"Evaluating {selected_case['name']} with the baseline prompt…"):
        baseline_results[selected_id] = run_case(selected_case, "baseline")
if run_case_improved:
    with st.spinner(f"Evaluating {selected_case['name']} with the improved prompt…"):
        improved_results[selected_id] = run_case(selected_case, "improved")

baseline = baseline_results.get(selected_id)
improved = improved_results.get(selected_id)
tabs = st.tabs(["Transcript", "Expected state", "Baseline", "Improved", "Compare"])
with tabs[0]: render_transcript(selected_case["conversation"])
with tabs[1]: render_expected_state(selected_case["expected_state"], selected_case.get("notes", ""))
with tabs[2]:
    if baseline:
        render_result(baseline, "Baseline")
    else:
        render_empty_result("Baseline")
with tabs[3]:
    if improved:
        render_result(improved, "Improved")
    else:
        render_empty_result("Improved")
with tabs[4]: render_compare(baseline, improved)

st.markdown('<div class="workspace-rule"></div><div class="section-kicker">All-case matrix</div>', unsafe_allow_html=True)
st.markdown("## Benchmark results")
st.caption("Every measured result at a glance. Select a scenario in the sidebar for field-level detail.")
render_all_cases(cases, baseline_results, improved_results)

st.markdown('<div class="workspace-rule"></div><div class="section-kicker">Export results</div>', unsafe_allow_html=True)
st.markdown("## Download evaluation report")
export_count = len(baseline_results) + len(improved_results)
if export_count:
    st.caption(
        f"{export_count} evaluated scenario-mode record{'s' if export_count != 1 else ''} available. "
        "Downloads use existing session results and do not call the model."
    )
    export_bundle = build_export_bundle(
        cases,
        baseline_results,
        improved_results,
        model_name,
    )
    json_data = export_json(export_bundle)
    csv_data = export_csv(export_bundle)
    export_json_col, export_csv_col, export_note_col = st.columns([1, 1, 2.2], gap="small")
    with export_json_col:
        st.download_button(
            "Download JSON",
            data=json_data,
            file_name="intentledger_evaluation_results.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_csv_col:
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name="intentledger_evaluation_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with export_note_col:
        st.caption("JSON preserves nested values. CSV stores expected and predicted states as valid JSON strings.")
else:
    st.markdown(
        '<div class="empty"><strong>No results available to export</strong><br>'
        '<span>Run a baseline or improved evaluation to enable JSON and CSV downloads.</span></div>',
        unsafe_allow_html=True,
    )
st.markdown('<div class="footer-note">IntentLedger · Prompt evaluation workspace · Results persist for this browser session</div>', unsafe_allow_html=True)
