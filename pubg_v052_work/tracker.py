"""Offline template tracking of a manually selected icon in a recorded video."""
import csv
from pathlib import Path


def track_video(video_path, template_rect, search_rect, output_csv, interval=5, threshold=0.65, progress=None):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError('Install opencv-python to analyze recordings') from exc
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError('Could not open video')
    try:
        ok, first = cap.read()
        if not ok:
            raise ValueError('Video has no frames')
        h, w = first.shape[:2]
        tx, ty, tw, th = [int(v) for v in template_rect]
        sx, sy, sw, sh = [int(v) for v in search_rect]
        if min(tw, th, sw, sh) <= 0 or tx < 0 or ty < 0 or sx < 0 or sy < 0 or tx+tw > w or ty+th > h or sx+sw > w or sy+sh > h or tw > sw or th > sh:
            raise ValueError('Template/search rectangle is outside video bounds')
        template = cv2.cvtColor(first[ty:ty+th, tx:tx+tw], cv2.COLOR_BGR2GRAY)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        results = []
        frame_no = 0
        while True:
            if frame_no == 0:
                frame = first
                ok = True
            else:
                ok, frame = cap.read()
            if not ok:
                break
            if frame_no % interval == 0:
                gray = cv2.cvtColor(frame[sy:sy+sh, sx:sx+sw], cv2.COLOR_BGR2GRAY)
                match = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                _, score, _, loc = cv2.minMaxLoc(match)
                if score >= threshold:
                    results.append((round(frame_no/fps, 3), sx+loc[0]+tw/2, sy+loc[1]+th/2, round(float(score), 4)))
                if progress and frame_no % (interval * 40) == 0:
                    progress(frame_no, count)
            frame_no += 1
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['time_seconds', 'pixel_x', 'pixel_y', 'confidence'])
            writer.writerows(results)
        return len(results), frame_no
    finally:
        cap.release()
