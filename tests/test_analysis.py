"""Real executable evidence checks for synthetic footage and fail-closed output schema."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from screen_analyzer.cli import run
from screen_analyzer.frames import decode, probe_video
from screen_analyzer.models import Analysis, Finding, MarketingMoment, Segment, WorkflowStep
from screen_analyzer.providers import offline_ocr, gemini_vision, validate_frame_evidence

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'demo'/'assets'


def example_analysis(**changes):
    data={'app_summary':'Shows a task list',
          'workflow_steps':[{'order':1,'action':'List visible','start_ms':0,'end_ms':1000,'evidence_frames':[0]}],
          'segments':[{'title':'List','start_ms':0,'end_ms':1000,'evidence_frames':[0]}],
          'marketing_moments':[{'hook':'List visible','timestamp_ms':0,'evidence_frames':[0]}],
          'findings':[{'kind':'observed','text':'Text visible','evidence_frames':[0]}]}
    data.update(changes)
    return Analysis.model_validate(data)


def test_required_outputs_and_strict_schema():
    parsed=example_analysis()
    assert parsed.findings[0].kind=='observed'
    with pytest.raises(ValidationError):
        example_analysis(unexpected='x')


def test_observation_requires_real_evidence():
    analysis=example_analysis(findings=[{'kind':'observed','text':'No citation','evidence_frames':[]}])
    with pytest.raises(ValueError,match='Observed finding'):
        validate_frame_evidence(analysis,[{'id':0,'timestamp_ms':1000}])


def test_nonexistent_frame_reference_rejected():
    analysis=example_analysis(findings=[{'kind':'observed','text':'Unknown frame','evidence_frames':[999]}])
    with pytest.raises(ValueError,match='Invalid evidence'):
        validate_frame_evidence(analysis,[{'id':0,'timestamp_ms':1000}])


def test_end_before_start_rejected():
    with pytest.raises(ValidationError):
        example_analysis(segments=[{'title':'time reversed','start_ms':1000,'end_ms':0,'evidence_frames':[0]}])


def test_out_of_range_time_rejected():
    a=example_analysis(marketing_moments=[{'hook':'some claim','timestamp_ms':100_000,'evidence_frames':[0]}])
    with pytest.raises(ValueError,match='outside sampled'):
        validate_frame_evidence(a,[{'id':0,'timestamp_ms':1000}])


def test_offline_mode_does_not_conjure_undetected_results():
    frames=[{'id':0,'timestamp_ms':0}, {'id':1,'timestamp_ms':1000}]
    ocr=[{'frame_id':0,'timestamp_ms':0,'text':'Please wait processing pending'},
         {'frame_id':1,'timestamp_ms':1000,'text':'Processing still pending'}]
    a=offline_ocr(frames,ocr)
    assert any(f.kind=='uncertain' for f in a.findings)
    assert not a.marketing_moments
    assert all('success' not in f.text.lower() for f in a.findings)


def test_model_api_requires_explicit_two_flags(tmp_path):
    with pytest.raises(ValueError,match='--allow-network AND --confirm-upload'):
        gemini_vision([],tmp_path,model='gemini-2.5-flash',allow_network=False,confirm_upload=False)
    with pytest.raises(ValueError,match='--allow-network AND --confirm-upload'):
        gemini_vision([],tmp_path,model='gemini-2.5-flash',allow_network=True,confirm_upload=False)


def test_provider_rejects_missing_key_before_network(monkeypatch,tmp_path):
    monkeypatch.delenv('GOOGLE_API_KEY',raising=False)
    with pytest.raises(ValueError,match='GOOGLE_API_KEY not set'):
        gemini_vision([],tmp_path,model='gemini-2.5-flash',allow_network=True,confirm_upload=True)


def test_probe_source_is_actual_video_metadata():
    details=probe_video(ASSETS/'todo_synthetic.mp4')
    assert details['duration_ms']==8000
    assert (details['width'],details['height'])==(390,844)


def test_timestamps_stable_and_video_content_hashed(tmp_path):
    frames,meta=decode(ASSETS/'todo_synthetic.mp4',2,0.3,tmp_path)
    assert len(frames)==16
    assert frames[0]['timestamp_ms']==0
    assert frames[-1]['timestamp_ms']==7500
    assert frames[4]['timestamp_ms']==2000
    assert frames[8]['timestamp_ms']==4000
    assert len({f['sha256'] for f in frames})>=4
    assert (tmp_path/'frames.json').is_file()


def test_out_of_range_fps_and_threshold_rejected(tmp_path):
    with pytest.raises(ValueError):
        decode(ASSETS/'todo_synthetic.mp4',0,0.3,tmp_path)
    with pytest.raises(ValueError):
        decode(ASSETS/'todo_synthetic.mp4',2,1.1,tmp_path)


@pytest.mark.parametrize('app',["todo","tip"])
def test_full_offline_run_real_video_and_ground_truth(app,tmp_path):
    from evaluate import evaluate
    result=run(ASSETS/f'{app}_synthetic.mp4',tmp_path,fps=2,provider='offline-ocr')
    assert result['live_model_executed'] is False
    assert result['input_tokens'] is None
    assert result['estimated_api_cost_usd'] is None
    assert result['frames_selected']==16
    assert all((tmp_path/fn).exists() for fn in
               ('analysis.json','summary.md','frames.json','ocr.json','run.json'))
    evaluation=evaluate(tmp_path,ASSETS/f'{app}_ground_truth.json')
    assert evaluation['event_recall']==1.0
    assert evaluation['observed_findings_with_frame_citation']
    a=json.loads((tmp_path/'analysis.json').read_text())
    assert len(a['workflow_steps'])==4
    assert 2<=len(a['marketing_moments'])<=3
    if app=='tip':
        assert evaluation['uncertainty_flag_correct']
        assert any(f['kind']=='uncertain' for f in a['findings'])


def test_invalid_path_no_output_or_network(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path/'missing.mp4',tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_invalid_file_rejected_without_model_calls(tmp_path):
    bad=tmp_path/'bad.mp4'
    bad.write_text('not a video')
    with pytest.raises(Exception):
        run(bad,tmp_path/'out')


def test_frames_cannot_satisfy_fabricated_extra_claims():
    with pytest.raises(ValidationError):
        example_analysis(findings=[{'kind':'certain','text':'This video guarantees success','evidence_frames':[0]}])


def test_gemini_adapter_has_mocked_schema_and_usage_contract(monkeypatch,tmp_path):
    """Contract test only. Absolutely no real model calls or billing."""
    import os
    import sys
    from types import SimpleNamespace
    monkeypatch.setenv('GOOGLE_API_KEY','synthetic-test-key-only')
    captured=[]

    class Part:
        @staticmethod
        def from_text(text):return ('text',text)
        @staticmethod
        def from_bytes(data,mime_type):return ('image',data,mime_type)

    class GenerateContentConfig:
        def __init__(self,**kwargs):self.args=kwargs

    class Model:
        def generate_content(self,**kwargs):
            captured.append(kwargs)
            return SimpleNamespace(text=example_analysis().model_dump_json(),
                usage_metadata=SimpleNamespace(prompt_token_count=750,
                    candidates_token_count=120,total_token_count=870))

    class Client:
        def __init__(self,api_key): assert api_key=='synthetic-test-key-only';self.models=Model()

    fake=SimpleNamespace(Client=Client,types=SimpleNamespace(Part=Part,GenerateContentConfig=GenerateContentConfig))
    monkeypatch.setitem(sys.modules,'google.genai',fake)
    from google import genai as cached_genai
    # Part metadata is only consumed after explicit consent.
    image_file=tmp_path/'f0.jpg'
    image_file.write_bytes(b'fake-synthetic-frame')
    a,usage=gemini_vision([{'id':0,'timestamp_ms':0,'path':'f0.jpg'}],tmp_path,
      model='gemini-2.5-flash',allow_network=True,confirm_upload=True)
    assert a.app_summary=='Shows a task list'
    assert usage=={'input_tokens':750,'output_tokens':120,'total_tokens':870}
    assert len(captured)==1
    assert captured[0]['model']=='gemini-2.5-flash'
    assert captured[0]['config'].args['response_mime_type']=='application/json'
    # Regression for live API HTTP 400: legacy response_schema converts
    # Pydantic extra="forbid" into unsupported `additional_properties` proto
    # fields. Use raw JSON Schema routing; Gemini's modern endpoint supports it.
    from screen_analyzer.models import Analysis
    config=captured[0]['config'].args
    assert 'response_schema' not in config
    assert config['response_json_schema']==Analysis.model_json_schema()
    assert config['response_json_schema']['additionalProperties'] is False
    assert len(captured[0]['contents'])==3
    assert captured[0]['contents'][2]==('image',b'fake-synthetic-frame','image/jpeg')
