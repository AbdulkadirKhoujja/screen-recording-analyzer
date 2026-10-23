"""Generate a readable static portfolio page using actual test outputs."""
from __future__ import annotations
from html import escape
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def render():
    sections=[]
    for name,label,description in [
        ('todo','Task manager','Task entry, saved task, completion and completed-only filter'),
        ('tip','Tip calculator','Bill entry, tip selection, pending state and confirmed total')]:
        dir=ROOT/'examples'/name
        analysis=json.loads((dir/'analysis.json').read_text())
        result=json.loads((dir/'evaluation.json').read_text())
        frames=json.loads((dir/'frames.json').read_text())['frames']
        images=''.join('<figure><img alt="Synthetic app frame at {} seconds" src="{}"><figcaption>{:.1f} seconds</figcaption></figure>'.format(
            f['timestamp_ms']/1000,escape(str(Path(name)/f['path'])),f['timestamp_ms']/1000) for f in [frames[0],frames[4],frames[8],frames[12]])
        steps=''.join('<tr><td>{:.1f}s</td><td>{}</td><td>{}</td></tr>'.format(
            x['start_ms']/1000,escape(x['action'][:175]),str(x['evidence_frames'])) for x in analysis['workflow_steps'])
        sections.append(f'''<section class="case"><div class="casehead"><div><span class="eyebrow">SYNTHETIC RECORDING / {name.upper()}</span><h2>{label}</h2><p>{description}</p></div><div class="stat"><b>{int(result['event_recall']*result['n_events'])}/{result['n_events']}</b><span>OCR stage markers detected</span></div></div><div class="phones">{images}</div><h3>Extracted OCR timeline</h3><div class="scroll"><table><tr><th>Time</th><th>Detected screen text</th><th>Frame IDs</th></tr>{steps}</table></div><p class="disclaimer">Controlled measurement: OCR text marker detection within ±1 second. This is not proof of model-based workflow comprehension.</p></section>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Screen Recording Analyzer | Verified v0.2 Prototype</title><style>
:root{font-family:Inter,system-ui,-apple-system,sans-serif;color:#dce7f7;background:#09131f}*{box-sizing:border-box}body{margin:0}main{max-width:1150px;margin:auto;padding:32px 24px}header{border:1px solid #21354e;border-radius:24px;background:linear-gradient(135deg,#193960,#0b1728 70%);padding:38px;margin:18px 0 28px}.eyebrow{letter-spacing:.12em;color:#75d8ce;font-size:12px;font-weight:800}h1{font-size:clamp(36px,5vw,60px);max-width:850px;line-height:1.05;margin:18px 0}h2{font-size:27px;margin:10px 0}h3{margin:28px 0 10px}p{color:#9eb4ce;line-height:1.65}strong{color:#eef7ff}.intro{max-width:780px}.metrics{display:flex;gap:13px;flex-wrap:wrap;margin-top:28px}.metric{padding:16px 22px;border:1px solid #385370;border-radius:13px;background:#172f4e88;flex:1;min-width:145px}.metric b,.stat b{display:block;font-size:28px}.metric span,.stat span{color:#a7bbd0;font-size:12px}.case{border:1px solid #1d3045;border-radius:20px;padding:28px;background:#101f2e;margin:22px 0}.casehead{display:flex;gap:16px;justify-content:space-between;align-items:center;flex-wrap:wrap}.stat{border-left:3px solid #53dacb;padding-left:16px}.phones{display:flex;gap:18px;overflow-x:auto;padding:16px 0}.phones figure{flex:0 0 min(185px,35vw);margin:0}.phones img{width:100%;border-radius:14px;border:4px solid #314866;box-shadow:0 8px 30px #06111a}.phones figcaption{color:#a2b6cd;text-align:center;font-size:13px;margin:6px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #2b3c50;padding:11px;text-align:left;vertical-align:top}th{color:#7ee0d3}.scroll{overflow:auto}.disclaimer{font-size:12px}footer{color:#9eb4ce;font-size:13px;margin:40px 0}.warning{border-left:3px solid #e5bc80;padding:8px 14px;background:#201d1d}
</style></head><body><main><header><span class="eyebrow">PYTHON • VIDEO FRAMES • OCR • EVIDENCE VALIDATION</span><h1>Understand what a screen recording actually shows.</h1><p class="intro">A reproducible engineering prototype: extract timestamped frames, identify visible interface states, preserve image evidence, and flag uncertainty instead of guessing. Built and verified entirely with original synthetic recordings.</p><div class="metrics"><div class="metric"><b>2</b><span>Original synthetic videos</span></div><div class="metric"><b>31</b><span>Automated tests passed</span></div><div class="metric"><b>8/8</b><span>Scripted OCR markers detected</span></div><div class="metric"><b>$0</b><span>Model/API spend in demo</span></div></div></header>'''+''.join(sections)+'''<section class="case"><span class="eyebrow">WHAT WAS — AND WAS NOT — PROVEN</span><h2>Traceable output, not manufactured AI performance.</h2><p>Both videos were actually decoded; frame times and SHA-256 hashes were recorded. Local OCR extracted visible text, the output followed a strict schema, and a genuine ground-truth scorer checked timed interface-state markers. The calculator deliberately included a pending state, which was marked uncertain rather than declared complete.</p><p class="warning">The local OCR engine is not a vision-language model. The opt-in Gemini image-analysis adapter has a mocked integration test only; no live multimodal inference, real customer video, per-run API price or generalisation accuracy is claimed.</p><p>All source code, tests, synthetic videos, raw outputs and ground truth are included in the project package. Images above are extracted from the actual demo recordings, not stock screenshots.</p></section><footer>Independent synthetic demonstration • No customer data • No network model calls • No third-party account actions</footer></main></body></html>'''

if __name__=='__main__':
    output=ROOT/'examples'/'showcase.html'
    output.write_text(render(),encoding='utf-8')
    print(output)
