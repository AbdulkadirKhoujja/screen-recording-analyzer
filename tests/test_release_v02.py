"""Release v0.2 route, no-upload preflight, pricing and fallback regression checks."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from screen_analyzer.cli import run
from screen_analyzer.routing import preflight, price_estimate, validate_rate_options
from screen_analyzer.models import Analysis

ROOT=Path(__file__).resolve().parents[1]
VIDEO=ROOT/'demo/assets/todo_synthetic.mp4'


def test_preflight_default_offline_requires_no_secret(monkeypatch):
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    p=preflight(provider='offline-ocr')
    assert p['ready'] and not p['uploads_permitted'] and not p['api_call_made']


@pytest.mark.parametrize('allow,confirm',[(False,False),(True,False),(False,True)])
def test_gemini_preflight_requires_both_consent_flags(monkeypatch,allow,confirm):
    monkeypatch.setenv('GOOGLE_API_KEY','fake-key')
    with pytest.raises(ValueError, match='--allow-network AND --confirm-upload'):
        preflight(provider='gemini',allow_network=allow,confirm_upload=confirm)


def test_gemini_preflight_missing_key(monkeypatch):
    monkeypatch.delenv('GOOGLE_API_KEY',raising=False)
    with pytest.raises(ValueError, match='GOOGLE_API_KEY not set'):
        preflight(provider='gemini',allow_network=True,confirm_upload=True)


def test_preflight_validates_sdk(monkeypatch):
    import screen_analyzer.routing as rt
    monkeypatch.setenv('GOOGLE_API_KEY','dummy')
    monkeypatch.setattr(rt.importlib,'import_module',lambda name: SimpleNamespace(Client=object))
    assert preflight(provider='gemini',allow_network=True,confirm_upload=True)['ready']
    assert not preflight(provider='gemini',allow_network=True,confirm_upload=True)['api_call_made']


def test_route_no_consent_fails_before_writing_files(tmp_path):
    out=tmp_path/'out'
    with pytest.raises(ValueError, match='--allow-network AND --confirm-upload'):
        run(VIDEO,out,provider='gemini')
    assert not out.exists()


def test_gemini_missing_key_rejected_before_creating_output(monkeypatch,tmp_path):
    monkeypatch.delenv('GOOGLE_API_KEY',raising=False)
    out=tmp_path/'out'
    with pytest.raises(ValueError,match='GOOGLE_API_KEY not set'):
        run(VIDEO,out,provider='gemini',allow_network=True,confirm_upload=True)
    assert not out.exists()


def test_explicit_fallback_on_preflight_failure(monkeypatch,tmp_path):
    monkeypatch.delenv('GOOGLE_API_KEY',raising=False)
    r=run(VIDEO,tmp_path/'output',provider='gemini',fps=2,
          allow_network=True,confirm_upload=True,fallback_offline=True)
    assert r['requested_provider']=='gemini'
    assert r['provider']=='offline-ocr' and r['fallback_used']
    assert not r['live_model_executed'] and not r['model_call_attempted']
    assert r['estimated_api_cost_usd'] is None
    assert 'GOOGLE_API_KEY' in r['fallback_reason']


def test_explicit_fallback_never_bypasses_consent(tmp_path):
    out=tmp_path/'output'
    with pytest.raises(ValueError,match='--allow-network AND --confirm-upload'):
        run(VIDEO,out,provider='gemini',fallback_offline=True)
    assert not out.exists()


def test_failed_live_route_fallback_discloses_attempt(monkeypatch,tmp_path):
    import screen_analyzer.cli as cli
    monkeypatch.setenv('GOOGLE_API_KEY','fake')
    monkeypatch.setattr(cli,'preflight',lambda **kwargs: {'ready':True})
    def failure(*args,**kwargs):
        raise TimeoutError('synthetic network timeout')
    monkeypatch.setattr(cli,'gemini_vision',failure)
    r=run(VIDEO,tmp_path/'output',provider='gemini',fps=2,
          allow_network=True,confirm_upload=True,fallback_offline=True)
    assert r['model_call_attempted'] is True
    assert r['live_model_executed'] is False
    assert r['provider']=='offline-ocr'
    assert 'TimeoutError' in r['fallback_reason']
    assert 'might still incur charges' in r['cost_note']


def test_no_silent_fallback_when_remote_call_fails(monkeypatch,tmp_path):
    import screen_analyzer.cli as cli
    monkeypatch.setenv('GOOGLE_API_KEY','fake')
    monkeypatch.setattr(cli,'preflight',lambda **kwargs: {'ready':True})
    monkeypatch.setattr(cli,'gemini_vision',lambda *args,**kwargs: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        run(VIDEO,tmp_path/'output',provider='gemini',fps=2,
            allow_network=True,confirm_upload=True)
    assert not (tmp_path/'output/run.json').exists()


def test_usage_based_cost_estimate_without_spurious_claims():
    u={'input_tokens':100000,'output_tokens':20000}
    assert price_estimate(u,input_rate=0.30,output_rate=2.5)==0.08
    assert price_estimate(u,input_rate=None,output_rate=None) is None
    assert price_estimate({'input_tokens':None,'output_tokens':None},
                          input_rate=0.3,output_rate=2.5) is None
    with pytest.raises(ValueError,match='BOTH'):
        validate_rate_options(0.3,None)
    with pytest.raises(ValueError,match='finite'):
        validate_rate_options(float('inf'),2.5)
    with pytest.raises(ValueError,match='finite'):
        validate_rate_options(-1,2.5)


def test_mocked_successful_gemini_route_and_estimation(monkeypatch,tmp_path):
    import screen_analyzer.cli as cli
    monkeypatch.setenv('GOOGLE_API_KEY','fake')
    monkeypatch.setattr(cli,'preflight',lambda **kwargs: {'ready':True})
    # This is a mocked contract test, not an actual remote multimodal run.
    def fake_live(frames,out,**kwargs):
        a=Analysis.model_validate({'app_summary':'mocked test only','workflow_steps':[],
           'segments':[],'marketing_moments':[],
           'findings':[{'kind':'observed','text':'synthetic local test','evidence_frames':[0]}]})
        return a,{'input_tokens':100000,'output_tokens':20000,'total_tokens':120000}
    monkeypatch.setattr(cli,'gemini_vision',fake_live)
    result=run(VIDEO,tmp_path/'output',provider='gemini',fps=2,
               allow_network=True,confirm_upload=True,
               input_usd_per_million=0.3,output_usd_per_million=2.5)
    assert result['provider']=='gemini'
    assert result['live_model_executed'] is True  # tested with a mock only
    assert result['estimated_api_cost_usd']==0.08
    assert result['fallback_used'] is False
    assert result['model_call_attempted'] is True
    assert json.loads((tmp_path/'output/analysis.json').read_text())['app_summary']=='mocked test only'
