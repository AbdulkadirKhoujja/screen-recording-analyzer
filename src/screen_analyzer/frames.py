"""Extract actual decoded video frames, frame timestamps and reproducible OCR."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any
import cv2


def probe_video(video: Path) -> dict[str, Any]:
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate:format=duration",
        "-of", "json", str(video)], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if not data.get("streams"):
        raise ValueError("No video stream found")
    stream = data["streams"][0]
    duration_ms = int(round(float(data["format"]["duration"]) * 1000))
    if not 100 <= duration_ms <= 180_000:
        raise ValueError("Expected short video duration (0.1 to 180 seconds)")
    if int(stream["width"]) * int(stream["height"]) > 3840 * 2160:
        raise ValueError("Video resolution exceeds safety limit")
    return {"duration_ms": duration_ms,"width": stream["width"],"height":stream["height"],
            "avg_frame_rate":stream["avg_frame_rate"]}


def decode(video: Path, target_fps: float, scene_threshold: float, out: Path,
           *, max_frames: int=120) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 0.5 <= target_fps <= 3:
        raise ValueError("--fps must be between 0.5 and 3")
    if not 0 <= scene_threshold <= 1:
        raise ValueError("Scene threshold must be from 0 to 1")
    meta = probe_video(video)
    frame_dir = out / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError("OpenCV cannot open the provided video")
    capture_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if capture_fps <= 0:
        capture.release()
        raise ValueError("Video has invalid source frame rate")
    frames: list[dict[str, Any]] = []
    next_time_ms = 0.0
    last_thumb = None
    frame_index = 0
    last_ts = -1
    try:
        while True:
            ok, image = capture.read()
            if not ok:
                break
            # Actual stream time as OpenCV's decoded frame presentation timestamp;
            # explicit frame-index fallback for unreliable POS_MSEC implementations.
            pos_ms = capture.get(cv2.CAP_PROP_POS_MSEC)
            fallback_ms = frame_index * 1000 / capture_fps
            t_ms = round(pos_ms if pos_ms >= 0 and abs(pos_ms - fallback_ms) < 1000 else fallback_ms)
            frame_index += 1
            if t_ms <= last_ts:
                t_ms = round(fallback_ms)
            thumb = cv2.cvtColor(cv2.resize(image, (96, 96)), cv2.COLOR_BGR2GRAY)
            change = (cv2.absdiff(thumb, last_thumb).mean() / 255.0) if last_thumb is not None else 0.0
            is_scene = bool(last_thumb is not None and scene_threshold > 0 and change >= scene_threshold)
            should_sample = t_ms + (500 / capture_fps) >= next_time_ms
            last_thumb = thumb
            last_ts = t_ms
            if not should_sample and not is_scene:
                continue
            if len(frames) >= max_frames:
                raise ValueError("Selected frames exceed --max-frames; increase sampling interval")
            frame_id = len(frames)
            filename = f"f{frame_id:04d}_{t_ms:07d}ms.jpg"
            file = frame_dir / filename
            # Quality 92 makes OCR reliable without ballooning sample data.
            if not cv2.imwrite(str(file), image, [cv2.IMWRITE_JPEG_QUALITY, 92]):
                raise IOError("Unable to encode extracted frame")
            frames.append({"id":frame_id,"timestamp_ms":t_ms,
                           "path":str(file.relative_to(out)),"sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
                           "scene_transition":is_scene})
            if should_sample:
                next_time_ms = (int(t_ms/(1000/target_fps)) + 1)*(1000/target_fps)
    finally:
        capture.release()
    if not frames:
        raise ValueError("Could not extract any frames")
    (out/"frames.json").write_text(json.dumps({"video":str(video.name),
      "metadata":meta,"frames":frames},indent=2)+"\n",encoding="utf-8")
    return frames,meta


def extract_ocr(frames: list[dict[str, Any]], out: Path) -> list[dict[str, Any]]:
    import pytesseract
    from PIL import Image
    results=[]
    for f in frames:
        image=Image.open(out / f["path"])
        data=pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT,
                                        config="--psm 11")
        items=[]
        for i,word in enumerate(data["text"]):
            word=word.strip()
            try: confidence=float(data["conf"][i])
            except (ValueError,TypeError): continue
            if word and confidence >= 50:
                items.append({"text":word,"confidence":round(confidence,1)})
        results.append({"frame_id":f["id"],"timestamp_ms":f["timestamp_ms"],
                        "tokens":items,"text":" ".join(item["text"] for item in items)})
    (out/"ocr.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    return results
