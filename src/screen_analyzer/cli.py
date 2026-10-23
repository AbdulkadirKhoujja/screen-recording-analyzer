"""CLI entry point: offline by default, remote calls explicitly opt-in."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from .frames import decode, extract_ocr
from .providers import gemini_vision, offline_ocr, validate_frame_evidence
from .routing import preflight, price_estimate, validate_rate_options


def run(video: Path, out: Path, *, provider: str='offline-ocr', model: str='gemini-3.5-flash-lite',
        fps: float=1.0, scene_threshold: float=0.3, max_frames: int=120,
        allow_network: bool=False, confirm_upload: bool=False,
        fallback_offline: bool=False, input_usd_per_million: float | None=None,
        output_usd_per_million: float | None=None) -> dict:
    """Analyze a video, never silently falling back from requested remote inference."""
    if not video.is_file():
        raise FileNotFoundError(video)
    if out.resolve() == video.resolve():
        raise ValueError('Output path cannot be the video')
    validate_rate_options(input_usd_per_million, output_usd_per_million)
    if provider not in ('offline-ocr', 'gemini'):
        raise ValueError('Unsupported provider')
    if fallback_offline and provider != 'gemini':
        raise ValueError('Offline fallback only applies to Gemini route')
    requested_provider = provider
    preflight_error = None
    try:
        preflight(provider=provider, model=model, allow_network=allow_network,
                  confirm_upload=confirm_upload)
    except (ValueError, RuntimeError) as exc:
        # Explicit fallback never bypasses the dual-consent flags, and never
        # suggests a missing key or SDK is a successful remote model test.
        if not fallback_offline or not (allow_network and confirm_upload):
            raise
        preflight_error = f'{type(exc).__name__}: {exc}'
        provider = 'offline-ocr'

    start = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    frames, meta = decode(video, fps, scene_threshold, out, max_frames=max_frames)
    ocr = extract_ocr(frames, out)
    fallback_reason = preflight_error
    model_call_attempted = False
    if provider == 'gemini':
        try:
            # An exception after this point can indicate uncertain remote
            # usage/billing. Record an attempt, never "cost = 0".
            model_call_attempted = True
            analysis, usage = gemini_vision(frames, out, model=model,
               allow_network=allow_network, confirm_upload=confirm_upload)
        except Exception as exc:
            if not fallback_offline:
                raise
            fallback_reason = f'{type(exc).__name__}: {exc}'
            provider = 'offline-ocr'
            analysis = offline_ocr(frames, ocr)
            usage = {'input_tokens': None, 'output_tokens': None, 'total_tokens': None}
    else:
        analysis = offline_ocr(frames, ocr)
        usage = {'input_tokens': None, 'output_tokens': None, 'total_tokens': None}

    validate_frame_evidence(analysis, frames)
    (out/'analysis.json').write_text(analysis.model_dump_json(indent=2)+'\n', encoding='utf-8')
    lines = ['# Screen recording review', '',
             f'**Executed mode:** {provider}',
             f'**Requested mode:** {requested_provider}',
             '**Offline OCR is NOT multimodal vision analysis.**',
             *( [f'**Gemini fallback:** {fallback_reason}'] if fallback_reason else [] ),
             '', analysis.app_summary, '', '## Timeline evidence']
    for step in analysis.workflow_steps:
        lines.append(f'- {step.start_ms/1000:.2f}–{step.end_ms/1000:.2f}s: {step.action} (frames {step.evidence_frames})')
    lines.extend(['', '## Marketing moments (suggestions, not validated marketing claims)'])
    lines.extend(f'- {m.timestamp_ms/1000:.2f}s: {m.hook} (frames {m.evidence_frames})' for m in analysis.marketing_moments)
    lines.extend(['', '## Findings'])
    lines.extend(f'- **{f.kind}:** {f.text} (frames {f.evidence_frames})' for f in analysis.findings)
    lines.extend(['', '## Limitations',
       'Frame citations show which images were sampled, not semantic accuracy. '
       'A human must review inferences against video and ground truth. No audio transcription.'])
    (out/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

    estimated_cost = price_estimate(usage, input_rate=input_usd_per_million,
                                    output_rate=output_usd_per_million) if provider == 'gemini' else None
    record = {
        'schema':'screen-recording-analyzer.run.v2',
        'provider':provider, 'requested_provider':requested_provider,
        'fallback_used':fallback_reason is not None, 'fallback_reason':fallback_reason,
        'model':model if provider == 'gemini' else None,
        'video_filename':video.name,
        'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'video_metadata':meta, 'frames_selected':len(frames), 'ocr_executed':True,
        'live_model_executed':provider == 'gemini',
        'model_call_attempted':model_call_attempted,
        'input_tokens':usage['input_tokens'], 'output_tokens':usage['output_tokens'],
        'total_tokens':usage['total_tokens'],
        'estimated_api_cost_usd':estimated_cost,
        'rate_assumptions_per_million_tokens': {'input_usd':input_usd_per_million,
                                                 'output_usd':output_usd_per_million}
          if input_usd_per_million is not None else None,
        'cost_note':('Estimate based only on operator-supplied rates and returned usage, not actual billing.'
          if estimated_cost is not None else
          'No billing estimate: no actual model usage and/or no verified caller-supplied rates. '
          'A failed network attempt might still incur charges.'),
        'elapsed_seconds':round(time.perf_counter()-start,3),
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'privacy_note':'Offline OCR processes local files. Gemini uploads selected frames only with explicit opt-in.'}
    (out/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return record


def main():
    parser=argparse.ArgumentParser(description='Evidence-grounded mobile app video analysis')
    parser.add_argument('video',type=Path,nargs='?',help='Video file under 3 minutes')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--provider',choices=['offline-ocr','gemini'],default='offline-ocr')
    parser.add_argument('--model',default='gemini-3.5-flash-lite')
    parser.add_argument('--fps',type=float,default=1.0)
    parser.add_argument('--scene-threshold',type=float,default=0.3)
    parser.add_argument('--max-frames',type=int,default=120)
    parser.add_argument('--allow-network',action='store_true')
    parser.add_argument('--confirm-upload',action='store_true')
    parser.add_argument('--fallback-offline',action='store_true',help='On Gemini error, run local OCR; reports fallback explicitly')
    parser.add_argument('--preflight-only',action='store_true',help='Validate provider configuration without processing or uploading video')
    parser.add_argument('--input-usd-per-million',type=float,help='Operator-verified model input USD rate per 1M tokens')
    parser.add_argument('--output-usd-per-million',type=float,help='Operator-verified model output USD rate per 1M tokens')
    opts=parser.parse_args()
    if opts.preflight_only:
        validate_rate_options(opts.input_usd_per_million,opts.output_usd_per_million)
        print(json.dumps(preflight(provider=opts.provider,model=opts.model,
                                  allow_network=opts.allow_network,confirm_upload=opts.confirm_upload),indent=2))
        return
    if opts.video is None or opts.out is None:
        parser.error('video and --out are required unless --preflight-only')
    print(json.dumps(run(opts.video,opts.out,provider=opts.provider,model=opts.model,
        fps=opts.fps,scene_threshold=opts.scene_threshold,max_frames=opts.max_frames,
        allow_network=opts.allow_network,confirm_upload=opts.confirm_upload,
        fallback_offline=opts.fallback_offline,
        input_usd_per_million=opts.input_usd_per_million,
        output_usd_per_million=opts.output_usd_per_million),indent=2))

if __name__ == '__main__':
    main()
