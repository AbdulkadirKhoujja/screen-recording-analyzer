"""Offline, read-only collector of existing *local* live Gemini evidence.

Usage: python review_release.py --todo outputs/todo-vision-flash-lite
         --tip outputs/tip-vision-v022-live --out-dir release-review

No API key, uploads, network, or model invocation. Does not rewrite analyses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evaluate import evaluate
from screen_analyzer.claim_review import review_claims
from screen_analyzer.models import Analysis
from screen_analyzer.providers import validate_frame_evidence

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT/'demo'/'assets'


def sha256(path:Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_one(app:str, folder:Path, *, assets:Path=ASSETS) -> dict:
    names=['run.json','analysis.json','frames.json','ocr.json']
    for name in names:
        if not (folder/name).is_file():
            raise FileNotFoundError(f'{app}: missing {name} in {folder}')
    run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
    frames=json.loads((folder/'frames.json').read_text(encoding='utf-8'))['frames']
    analysis=Analysis.model_validate_json((folder/'analysis.json').read_text(encoding='utf-8'))
    validate_frame_evidence(analysis,frames)
    expected_video=assets/f'{app}_synthetic.mp4'
    if run.get('video_filename')!=expected_video.name or run.get('video_sha256')!=sha256(expected_video):
        raise ValueError(f'{app}: output video hash/name does not match bundled original synthetic recording')
    if not (run.get('provider')=='gemini' and run.get('requested_provider')=='gemini'
            and run.get('live_model_executed') is True and run.get('fallback_used') is False
            and run.get('model_call_attempted') is True):
        raise ValueError(f'{app}: no confirmed live Gemini execution or offline fallback was used')
    if not run.get('model'):
        raise ValueError(f'{app}: missing model identifier')
    scorer=evaluate(folder,assets/f'{app}_ground_truth.json')
    return {
        'app':app,
        'model':run['model'],
        'executed_at_utc':run.get('observed_at_utc'),
        'video_sha256':run['video_sha256'],
        'frames_selected':run.get('frames_selected'),
        'input_tokens':run.get('input_tokens'),
        'output_tokens':run.get('output_tokens'),
        'total_tokens':run.get('total_tokens'),
        'model_call_confirmed':True,
        'fallback_used':False,
        'ocr_marker_recall_not_ai_accuracy':scorer['event_recall'],
        'uncertainty_reporting_gate':scorer['uncertainty_reporting_gate'],
        'model_workflow_steps_for_manual_review':[
            {'action':s.action,'start_ms':s.start_ms,'evidence_frames':s.evidence_frames}
            for s in analysis.workflow_steps],
        'claim_review':review_claims(analysis),
    }


def collect(todo:Path,tip:Path, *, assets:Path=ASSETS) -> dict:
    cases=[collect_one('todo',todo,assets=assets),collect_one('tip',tip,assets=assets)]
    # Always requires human signoff. This is not an independent ML benchmark.
    return {
        'schema':'screen-recording-analyzer.local-live-evidence.v1',
        'publication_gate':'HUMAN_REVIEW_REQUIRED',
        'cases':cases,
        'scope':[
            'Two synthetic videos; repeated exposure to the same scripted stages',
            'OCR marker recall is not model semantic accuracy',
            'Model workflow steps require manual verification against actual frames',
            'Lexical claim review is incomplete by construction',
            'No billing assertions are made from token usage alone',
        ]
    }


def markdown(summary:dict) -> str:
    lines=['# Local live-model evidence (synthetic only)','',
           '**Publication gate: HUMAN_REVIEW_REQUIRED.** This is a diagnostic, not a certification.','']
    for case in summary['cases']:
        lines += [f"## {case['app']}", '',
                  f"- Model: `{case['model']}`; recorded at {case['executed_at_utc'] or 'not recorded'}",
                  f"- Actual Gemini execution: yes; fallback: no; frames: {case['frames_selected']}",
                  f"- Token usage (input/output/total): {case['input_tokens']}/{case['output_tokens']}/{case['total_tokens']}",
                  f"- OCR stage-marker recall: {case['ocr_marker_recall_not_ai_accuracy']} (NOT model accuracy)",
                  f"- Explicit uncertainty reporting: {case['uncertainty_reporting_gate']}",
                  f"- Claim-review status: {case['claim_review']['status']}", '',
                  '**Model-reported workflow (review against the actual frames):**', '']
        lines.extend(f"- {step['start_ms']/1000:g}s (frames {step['evidence_frames']}): {step['action']}"
                     for step in case['model_workflow_steps_for_manual_review'])
        lines+=['','**Potential overclaims (not automatic factual judgments):**','']
        if case['claim_review']['flags']:
            for flag in case['claim_review']['flags']:
                lines.append(f"- `{flag['field']}`: `{flag['excerpt']}` — {flag['category']}")
        else:
            lines.append('- No phrases from the small configured review list were found; semantic verification is still required.')
        lines.append('')
    lines += ['## Limits','',*(f'- {note}' for note in summary['scope']),'',
              'Never describe these controlled synthetic runs as independent real-client accuracy results.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description='Create an offline synthetic live-run evidence review; no API calls')
    p.add_argument('--todo',type=Path,required=True)
    p.add_argument('--tip',type=Path,required=True)
    p.add_argument('--out-dir',type=Path,required=True)
    opts=p.parse_args()
    report=collect(opts.todo,opts.tip)
    opts.out_dir.mkdir(parents=True,exist_ok=True)
    (opts.out_dir/'live_evidence_summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    (opts.out_dir/'live_evidence_review.md').write_text(markdown(report),encoding='utf8')
    print(f"LOCAL_EVIDENCE_REVIEW_WRITTEN={opts.out_dir}")
    for item in report['cases']:
        print(f"{item['app'].upper()}_MODEL={item['model']}; UNCERTAINTY={item['uncertainty_reporting_gate']}; CLAIMS={item['claim_review']['status']}")
    print(f"PUBLICATION_GATE={report['publication_gate']}")


if __name__=='__main__':
    main()
