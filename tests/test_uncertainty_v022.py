"""Regression checks for explicit pending-state reporting (no network calls)."""
from __future__ import annotations
import json
from pathlib import Path
from evaluate import evaluate
from screen_analyzer.providers import SYSTEM_PROMPT


def _fixture(tmp_path: Path, explicit_uncertainty: bool, pending_step: bool=True) -> tuple[Path,Path]:
    output=tmp_path/'output'
    output.mkdir()
    # Deliberately nonsequential frame IDs: report checker must use IDs, not offsets.
    frames=[{'id':10,'timestamp_ms':0},{'id':20,'timestamp_ms':2000},
            {'id':30,'timestamp_ms':4000},{'id':40,'timestamp_ms':6000}]
    ocr=[{'frame_id':f['id'],'timestamp_ms':f['timestamp_ms'],
          'text':f'STAGE {i+1}'} for i,f in enumerate(frames)]
    findings=[{'kind':'observed','text':'Result visible','evidence_frames':[40]}]
    if explicit_uncertainty:
        findings.append({'kind':'uncertain','text':'Result pending at 4 seconds','evidence_frames':[30]})
    steps=[{'order':1,'action':'Processing: result pending' if pending_step else 'A screen is visible',
            'start_ms':4000,'end_ms':6000,'evidence_frames':[30]}]
    for name, data in {'frames.json':{'frames':frames},'ocr.json':ocr,
                       'analysis.json':{'app_summary':'test','workflow_steps':steps,'segments':[],
                                        'marketing_moments':[],'findings':findings}}.items():
        (output/name).write_text(json.dumps(data),encoding='utf8')
    truth=tmp_path/'truth.json'
    truth.write_text(json.dumps({'app':'tip','uncertainty_expected_at_ms':4000,
                                 'events':[{'at_ms':4000,'label':'loading','visible_marker':'STAGE 3'}]}),encoding='utf8')
    return output,truth


def test_missing_uncertain_finding_is_review_required_even_when_step_is_right(tmp_path):
    output,truth=_fixture(tmp_path,False)
    result=evaluate(output,truth)
    assert result['event_recall']==1.0
    assert result['pending_state_mentioned_in_workflow'] is True
    assert result['uncertainty_flag_correct'] is False
    assert result['uncertainty_reporting_gate']=='REVIEW_REQUIRED'


def test_uncertain_finding_and_step_both_cited_pass(tmp_path):
    output,truth=_fixture(tmp_path,True)
    result=evaluate(output,truth)
    assert result['uncertainty_flag_correct'] is True
    assert result['pending_state_mentioned_in_workflow'] is True
    assert result['uncertainty_reporting_gate']=='PASS'


def test_uncertain_finding_alone_not_accepted_as_complete_workflow_report(tmp_path):
    output,truth=_fixture(tmp_path,True,False)
    assert evaluate(output,truth)['uncertainty_reporting_gate']=='REVIEW_REQUIRED'


def test_prompt_requires_explicit_uncertain_finding_and_preserves_later_result():
    assert 'kind="uncertain"' in SYSTEM_PROMPT
    assert 'keep the earlier uncertain finding' in SYSTEM_PROMPT
    assert 'unconfirmed state' in SYSTEM_PROMPT


def test_cli_defaults_to_model_used_successfully_in_live_synthetic_run():
    from inspect import signature
    from screen_analyzer.cli import run
    from screen_analyzer.routing import preflight
    assert signature(run).parameters['model'].default == 'gemini-3.5-flash-lite'
    assert signature(preflight).parameters['model'].default == 'gemini-3.5-flash-lite'
