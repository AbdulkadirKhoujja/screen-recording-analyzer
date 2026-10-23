"""Conservative lexical review and local evidence pack regressions (network-free)."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest

from screen_analyzer.claim_review import review_claims
from screen_analyzer.models import Analysis
from screen_analyzer.providers import SYSTEM_PROMPT
from review_release import collect_one, markdown


def analysis(**overrides):
    payload={'app_summary':'TipMate shows a calculation screen',
             'workflow_steps':[{'order':1,'action':'Processing remains pending','start_ms':0,'end_ms':1000,'evidence_frames':[0]}],
             'segments':[], 'marketing_moments':[],
             'findings':[{'kind':'uncertain','text':'No completed result visible','evidence_frames':[0]}]}
    payload.update(overrides)
    return Analysis.model_validate(payload)


def test_overclaim_flags_are_review_prompts_not_factual_verdicts():
    a=analysis(app_summary='Split bills and process payments instantly.',
       marketing_moments=[{'hook':'Get a total breakdown with one tap', 'timestamp_ms':0,'evidence_frames':[0]}])
    original=a.model_dump_json()
    result=review_claims(a)
    assert result['status']=='REVIEW_REQUIRED'
    kinds={f['category'] for f in result['flags']}
    assert 'unverified_payment_action' in kinds
    assert 'unverified_multi_payer_feature' in kinds
    assert 'unverified_speed' in kinds
    assert 'unverified_breakdown' in kinds
    assert 'unverified_tap_count' in kinds
    assert a.model_dump_json()==original  # Never silently correct model output.


def test_no_lexical_flags_does_not_mean_verified():
    result=review_claims(analysis())
    assert result['status']=='NO_LEXICAL_FLAGS'
    assert 'does not establish semantic accuracy' in result['limitations'][1]


def test_specific_live_overclaims_from_tip_response_flagged():
    result=review_claims(analysis(app_summary='TipMate is a mobile bill splitting utility that processes payments or calculations',
       marketing_moments=[{'hook':'Clear final total breakdown displayed instantly', 'timestamp_ms':0,'evidence_frames':[0]}]))
    categories={f['category'] for f in result['flags']}
    assert categories=={'unverified_payment_action','unverified_multi_payer_feature','unverified_speed','unverified_breakdown'}


def _files(tmp_path:Path, *, fallback:bool=False, video_hash_correct:bool=True, live:bool=True):
    src=Path(__file__).resolve().parents[1]
    assets=src/'demo'/'assets'
    target=tmp_path/'run';target.mkdir()
    (target/'frames.json').write_text(json.dumps({'frames':[{'id':i,'timestamp_ms':i*2000} for i in range(4)]}))
    (target/'ocr.json').write_text(json.dumps([{'frame_id':i,'timestamp_ms':i*2000,'text':t} for i,t in enumerate(
        ['MOBILE TASKS STAGE 1 / TASK LIST','MOBILE TASKS STAGE 2 / TASK ADDED',
         'MOBILE TASKS STAGE 3 / TASK COMPLETE','MOBILE TASKS STAGE 4 / COMPLETED FILTER'])]))
    (target/'analysis.json').write_text(analysis().model_dump_json())
    import hashlib
    h=hashlib.sha256((assets/'todo_synthetic.mp4').read_bytes()).hexdigest()
    (target/'run.json').write_text(json.dumps({
        'provider':'gemini' if live else 'offline-ocr','requested_provider':'gemini',
        'model':'gemini-3.5-flash-lite','fallback_used':fallback,
        'live_model_executed':live,'model_call_attempted':True,
        'video_filename':'todo_synthetic.mp4',
        'video_sha256':h if video_hash_correct else '0'*64,
        'frames_selected':1,'input_tokens':123,'output_tokens':42,'total_tokens':165,
        'observed_at_utc':'2026-10-23T01:09:15+00:00'}))
    return target


def test_collects_only_actual_model_execution_and_cautious_summary(tmp_path):
    folder=_files(tmp_path)
    r=collect_one('todo',folder)
    assert r['model_call_confirmed'] is True
    assert r['ocr_marker_recall_not_ai_accuracy']==1.0
    assert r['claim_review']['status']=='NO_LEXICAL_FLAGS'
    report={'cases':[r], 'scope':['synthetic video only']}
    md=markdown(report)
    assert 'NOT model accuracy' in md
    assert 'HUMAN_REVIEW_REQUIRED' in md


@pytest.mark.parametrize('options',[
    {'fallback':True},{'video_hash_correct':False},{'live':False}
])
def test_collector_rejects_fallback_or_mismatched_source(tmp_path,options):
    folder=_files(tmp_path,**options)
    with pytest.raises(ValueError):
        collect_one('todo',folder)


def test_prompt_requires_specific_evidence_grounding():
    assert 'promotional copy is not proof' in SYSTEM_PROMPT
    assert 'Marketing hooks are suggestions' in SYSTEM_PROMPT
