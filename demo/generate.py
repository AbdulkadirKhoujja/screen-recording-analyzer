"""Deterministic synthetic mobile-browser recording generator.

Uses Chromium Playwright to execute simple local HTML apps, captures real browser
screens, then encodes screenshots as fixed-frame-rate synthetic MP4 recordings.
No external sites, no customer footage, no model calls.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
FPS=2
STAGES=[0,2,4,6]


def generate(kind: str, output_dir: Path) -> tuple[Path,Path]:
    if kind not in ('todo','tip'):
        raise ValueError(kind)
    output_dir.mkdir(parents=True,exist_ok=True)
    tmp=output_dir/(kind+'_screens')
    tmp.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1,
                              is_mobile=True,has_touch=True)
        page.set_content((ROOT/(kind+'.html')).read_text(encoding='utf-8'))
        action_labels=(['task list','task added','task complete','completed filter'] if kind=='todo'
                      else ['bill entry','tip selected','loading uncertain','total result'])
        for frame_no in range(16):
            t=frame_no/FPS
            if frame_no==4:
                if kind=='todo':
                    page.get_by_label('New task').fill('Buy milk')
                    page.get_by_role('button',name='Add task').click()
                else:
                    page.get_by_label('Bill amount').fill('100')
                    page.get_by_role('button',name='Choose 20 percent').click()
            if frame_no==8:
                if kind=='todo': page.get_by_role('button',name='Complete task').click()
                else: page.get_by_role('button',name='Calculate total').click()
            if frame_no==12:
                if kind=='todo': page.get_by_role('button',name='Show completed').click()
                else: page.wait_for_timeout(2400)
            page.screenshot(path=str(tmp/f'frame_{frame_no:04d}.png'),animations='disabled')
        browser.close()
    video=output_dir/f'{kind}_synthetic.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate',str(FPS),
      '-i',str(tmp/'frame_%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p',
      '-movflags','+faststart','-r',str(FPS),str(video)],check=True)
    truth={"schema":"synthetic-mobile-demo.ground-truth.v1","app":kind,
      "video":video.name,"recording_method":"Real local browser screenshots -> ffmpeg fixed 2 fps video",
      "fps":FPS,"synthetic_only":True,
      "events":[{"at_ms":ms*1000,"label":label,"visible_marker":f'STAGE {i+1}'}
         for i,(ms,label) in enumerate(zip(STAGES,action_labels))],
      "uncertainty_expected_at_ms":4000 if kind=='tip' else None,
      "narrative":"The tip demo intentionally displays a pending state before a later verified result" if kind=='tip' else 'Task creation, completion and filter states'}
    ground=output_dir/f'{kind}_ground_truth.json'
    ground.write_text(json.dumps(truth,indent=2)+'\n')
    return video,ground


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=ROOT/'assets')
    args=ap.parse_args()
    for kind in ('todo','tip'):
        v,g=generate(kind,args.out)
        print('VIDEO',v,round(v.stat().st_size/1024,1),'KiB','GROUND_TRUTH',g)

if __name__=='__main__': main()
