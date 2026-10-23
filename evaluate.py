"""Evaluate evidence against known synthetic event timestamps, not guess accuracy."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def evaluate(folder:Path, truth:Path) -> dict:
    frames=json.loads((folder/'frames.json').read_text())['frames']
    ocr=json.loads((folder/'ocr.json').read_text())
    analysis=json.loads((folder/'analysis.json').read_text())
    gt=json.loads(truth.read_text())
    assert len(frames)==len(ocr)
    checks=[]
    for event in gt['events']:
        target=event['at_ms']
        hit=[r for r in ocr if event['visible_marker'].lower() in r['text'].lower()
             and abs(r['timestamp_ms']-target)<=1000]
        checks.append({'event':event['label'],'expected_ms':target,'found':bool(hit),
                       'detected_ms':hit[0]['timestamp_ms'] if hit else None})
    uncertain=gt.get('uncertainty_expected_at_ms')
    uncertain_ok=None
    pending_step_mentioned=None
    reporting_gate='NOT_APPLICABLE'
    if uncertain is not None:
        # Evidence IDs are identifiers, not guaranteed array offsets.
        sampled_ms={frame['id']:frame['timestamp_ms'] for frame in frames}
        def near_pending(cited):
            return any(abs(sampled_ms[fid]-uncertain)<=1000 for fid in cited
                       if fid in sampled_ms)
        uncertain_ok=any(f['kind']=='uncertain' and near_pending(f['evidence_frames'])
                         for f in analysis['findings'])
        pending_terms=('pending','loading','processing','please wait','waiting','in progress')
        pending_step_mentioned=any(
            near_pending(step['evidence_frames']) and
            any(word in step['action'].lower() for word in pending_terms)
            for step in analysis['workflow_steps'])
        reporting_gate=('PASS' if uncertain_ok and pending_step_mentioned
                        else 'REVIEW_REQUIRED')
    n=sum(x['found'] for x in checks)
    return {'schema':'synthetic-evaluation.v1','app':gt['app'],'n_events':len(checks),
      'timestamp_tolerance_ms':1000,'event_recall':round(n/len(checks),3),
      'timestamp_detection_checks':checks,'uncertainty_flag_correct':uncertain_ok,
      'pending_state_mentioned_in_workflow':pending_step_mentioned,
      'uncertainty_reporting_gate':reporting_gate,
      'observed_findings_with_frame_citation':all(f['evidence_frames'] for f in analysis['findings'] if f['kind']=='observed'),
      'caveats':['Synthetic controlled recording only','Metric is OCR-stage marker detection, NOT semantic workflow precision or multimodal video understanding accuracy','Screen transitions are not equivalent to action detection','Uncertainty reporting gate checks structure and references, not the full visual truth of any model claim']}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('folder',type=Path)
    p.add_argument('ground_truth',type=Path)
    p.add_argument('--save',type=Path)
    a=p.parse_args()
    result=evaluate(a.folder,a.ground_truth)
    if a.save: a.save.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
