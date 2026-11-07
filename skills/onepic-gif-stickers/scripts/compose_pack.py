"""Compose already-generated pose frames; never synthesize character motion."""
import argparse
import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve(base, value):
    path = Path(value)
    return path if path.is_absolute() else base / path


def text_enabled(data, item):
    return item.get("show_text", data.get("show_text", True))


def read_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    size = data.get("size", 512)
    if type(size) is not int or not 64 <= size <= 2048:
        raise ValueError("size must be an integer from 64 to 2048")
    if data.get("background", "white") not in ("white", "transparent"):
        raise ValueError("background must be white or transparent")
    if data.get("resampling", "smooth") not in ("smooth", "pixel"):
        raise ValueError("resampling must be smooth or pixel")
    threshold = data.get("alpha_threshold", 128)
    if type(threshold) is not int or not 1 <= threshold <= 255:
        raise ValueError("alpha_threshold must be 1..255")
    for key, default, lower, upper in [("font_size", max(8, round(size * .11)), 8, size),
                                       ("stroke_width", max(1, round(size / 128)), 0, size // 16)]:
        value = data.get(key, default)
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"invalid {key}")
    items = data.get("items", [])
    if not items or type(data.get("count")) is not int or data["count"] != len(items):
        raise ValueError("count must equal the non-empty item list")
    if type(data.get("show_text", True)) is not bool:
        raise ValueError("show_text must be boolean")
    for item in items:
        if type(item.get("show_text", True)) is not bool:
            raise ValueError("item show_text must be boolean")
    # 无字版保留caption作为动作标签，但不依赖中文字体。
    font = None
    if any(text_enabled(data, item) for item in items):
        font = resolve(path.parent, data["font"])
        ImageFont.truetype(str(font), 16)
    ids, captions = set(), set()
    for item in items:
        identity = item["id"]
        caption = item["caption"]
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", identity):
            raise ValueError("id must be a short safe filename component")
        if not isinstance(caption, str) or not caption.strip() or "\n" in caption or "\r" in caption:
            raise ValueError("caption must be one non-empty line")
        normalized = "".join(caption.split())
        if not 2 <= len(normalized) <= 6 and item.get("allow_long_caption") is not True:
            raise ValueError(f"{identity}: caption outside 2..6 characters needs an explicit exception")
        if identity.casefold() in ids or normalized in captions:
            raise ValueError("duplicate id or caption")
        ids.add(identity.casefold())
        captions.add(normalized)
        frames, delays = item["frames"], item["durations_ms"]
        if len(frames) < 2 or len(frames) != len(delays):
            raise ValueError(f"{identity}: frames and durations must match, at least two frames")
        if any(type(d) is not int or not 20 <= d <= 10000 or d % 10 for d in delays):
            raise ValueError(f"{identity}: durations must be 20..10000ms in 10ms increments")
        shapes = set()
        for name in frames:
            with Image.open(resolve(path.parent, name)) as image:
                image.load()
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("each source must be a single pose image")
                shapes.add(image.size)
        if len(shapes) != 1:
            raise ValueError(f"{identity}: source frame sizes differ")
    return data, font


def compose_frames(data, item, base, font_path):
    size = data.get("size", 512)
    transparent = data.get("background", "white") == "transparent"
    margin = max(4, round(size * .04))
    show_text = text_enabled(data, item)
    band = max(24, round(size * .19)) if show_text else margin
    stroke = data.get("stroke_width", max(1, round(size / 128)))
    layer = Image.new("RGBA", (size, size))
    pen = ImageDraw.Draw(layer)
    font_size = data.get("font_size", max(8, round(size * .11)))
    while show_text and font_size >= 8:
        font = ImageFont.truetype(str(font_path), font_size)
        box = pen.textbbox((0, 0), item["caption"], font=font, stroke_width=stroke)
        width, height = box[2] - box[0], box[3] - box[1]
        if width <= size - 2 * margin and height <= band - 2 * margin:
            break
        font_size -= 1
    if show_text and font_size < 8:
        raise ValueError("caption cannot fit the reserved top band")
    if show_text:
        pen.text(((size - width) / 2 - box[0], (band - height) / 2 - box[1]),
                 item["caption"], font=font, fill=data.get("caption_color", "#20242a"),
                 stroke_width=stroke, stroke_fill="white")
        if data.get("font_embolden", False) and stroke > 1:
            pen.text(((size - width) / 2 - box[0], (band - height) / 2 - box[1]),
                     item["caption"], font=font, fill=data.get("caption_color", "#20242a"),
                     stroke_width=1, stroke_fill=data.get("caption_color", "#20242a"))
    resample = Image.Resampling.NEAREST if data.get("resampling") == "pixel" else Image.Resampling.LANCZOS
    frames = []
    # 所有源帧尺寸已验证相同，同一个映射保留动作位置，不逐帧裁主体。
    for name in item["frames"]:
        with Image.open(resolve(base, name)) as source:
            frame = Image.new("RGBA", (size, size), (0, 0, 0, 0) if transparent else (255, 255, 255, 255))
            pose = ImageOps.contain(source.convert("RGBA"), (size - 2 * margin, size - band - margin), resample)
            frame.alpha_composite(pose, ((size - pose.width) // 2, band + (size - band - margin - pose.height) // 2))
            frame.alpha_composite(layer)
            frames.append(frame)
    return frames


def to_palette(frames, transparent, threshold):
    rgb = []
    for frame in frames:
        matte = Image.new("RGBA", frame.size, "white")
        matte.alpha_composite(frame)
        rgb.append(matte.convert("RGB"))
    # 整条共用调色板；透明索引255单独保留，防止背景色污染人物。
    swatch = Image.new("RGB", (64 * len(rgb), 64), "white")
    for index, frame in enumerate(rgb):
        swatch.paste(frame.resize((64, 64)), (index * 64, 0))
    palette = swatch.quantize(colors=255 if transparent else 256, method=Image.Quantize.MEDIANCUT)
    if transparent:
        entries = palette.getpalette()
        entries = (entries + [0] * 768)[:768]
        entries[765:768] = entries[:3]
        palette.putpalette(entries)
    quantized = []
    for source, frame in zip(frames, rgb):
        indexed = frame.quantize(palette=palette, dither=Image.Dither.NONE)
        if transparent:
            indexed = indexed.point(list(range(255)) + [0])
            mask = source.getchannel("A").point(lambda a: 255 if a < threshold else 0)
            indexed.paste(255, mask=mask)
            indexed.info["transparency"] = 255
        quantized.append(indexed)
    return quantized


def audit_gif(path, expected_size, expected_duration):
    frames, delays, hashes, alpha = [], [], set(), []
    with Image.open(path) as gif:
        file_format = gif.format
        loop = gif.info.get("loop")
        size = gif.size
        for index in range(gif.n_frames):
            gif.seek(index)
            delays.append(gif.info.get("duration", 0))
            frame = gif.convert("RGBA").copy()
            frames.append(frame)
            hashes.add(hashlib.sha256(frame.tobytes()).hexdigest())
            alpha.append(frame.getchannel("A").getextrema()[0] == 0)
    errors = []
    if file_format != "GIF":
        errors.append("file is not GIF format")
    if size != (expected_size, expected_size):
        errors.append("unexpected canvas")
    if len(hashes) < 2:
        errors.append("no distinct decoded motion frames")
    if loop != 0:
        errors.append("not an infinite loop")
    if not delays or any(d <= 0 for d in delays) or sum(delays) != expected_duration:
        errors.append("decoded timing differs from requested timing")
    return {"file": path.name, "format": file_format, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": list(size), "frame_count": len(frames), "distinct_frames": len(hashes),
            "durations_ms": delays, "total_ms": sum(delays), "loop": loop,
            "bytes": path.stat().st_size, "transparent_pixels_per_frame": alpha,
            "technical_status": "fail" if errors else "pass", "errors": errors}, frames


def render(manifest, output, review_frames=False):
    data, font = read_manifest(manifest)
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory is not empty; select a new revision directory")
    output.mkdir(parents=True, exist_ok=True)
    gifs = output / "gifs"
    previews = output / "review-frames"
    gifs.mkdir()
    if review_frames:
        previews.mkdir()
    reports, review, cards = [], [], []
    transparent = data.get("background", "white") == "transparent"
    for item in data["items"]:
        frames = compose_frames(data, item, manifest.parent, font)
        quantized = to_palette(frames, transparent, data.get("alpha_threshold", 128))
        path = gifs / (item["id"] + ".gif")
        options = {"transparency": 255, "background": 255} if transparent else {}
        quantized[0].save(path, save_all=True, append_images=quantized[1:],
                          duration=item["durations_ms"], loop=0, disposal=2, optimize=False, **options)
        report, decoded = audit_gif(path, data.get("size", 512), sum(item["durations_ms"]))
        if transparent and not all(report["transparent_pixels_per_frame"]):
            report["errors"].append("transparent mode has an opaque decoded frame")
            report["technical_status"] = "fail"
        report.update(id=item["id"], caption=item["caption"], show_text=text_enabled(data, item))
        reports.append(report)
        review.append({"id": item["id"], "sha256": report["sha256"], "reviewer": None,
                       "frame_review": "pending", "semantic_review": "pending", "playback": "pending",
                       "loop_seam": "pending", "issues": [], "user_acceptance": "pending"})
        # 日常交付只保存动图；异常排查时才落盘逐帧PNG与检查拼图。
        detail_link = ""
        if review_frames:
            folder = previews / item["id"]
            folder.mkdir()
            for index, frame in enumerate(decoded):
                frame.save(folder / f"{index:03}.png")
            cell, label = 160, 24
            board = Image.new("RGB", (cell * 4, (cell + label) * ((len(decoded) + 3) // 4)), "#e9edef")
            draw = ImageDraw.Draw(board)
            for index, frame in enumerate(decoded):
                x, y = index % 4 * cell, index // 4 * (cell + label)
                thumb = frame.resize((cell, cell))
                board.paste(thumb, (x, y), thumb)
                draw.text((x + 6, y + cell + 4), f"{index:02} / {report['durations_ms'][index]} ms", fill="black")
            board.save(previews / (item["id"] + ".png"))
            detail_link = f'<a href="review-frames/{item["id"]}.png">逐帧检查</a>'
        safe = html.escape(item["caption"])
        cards.append(f'<article><h2>{item["id"]} · {safe}</h2><img src="gifs/{item["id"]}.gif" alt="{safe}"><p>{report["frame_count"]}帧 / {report["total_ms"]}ms</p>{detail_link}</article>')
    save_json(output / "technical-audit.json", reports)
    save_json(output / "review.json", review)
    save_json(output / "captions.json", [{"id": i["id"], "caption": i["caption"], "show_text": text_enabled(data, i)} for i in data["items"]])
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>GIF候选预览</title><style>body{font:16px system-ui;background:#e9edef;padding:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}article{background:white;padding:16px;border-radius:12px}img{width:100%;max-width:512px;background:#eee}h2{font-size:20px}</style><h1>GIF候选预览</h1><p>正常播放并查看循环；技术检查不代表视觉通过。请记录review.json。</p><main>' + ''.join(cards) + '</main></html>'
    (output / "index.html").write_text(page, encoding="utf-8")
    if any(r["technical_status"] != "pass" for r in reports):
        raise ValueError("technical checks failed; see technical-audit.json; no ZIP created")
    # ZIP是待视觉验收的候选包，不自动宣称已经批准。无源素材或本机路径。
    with zipfile.ZipFile(output / "candidates.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file() and path.suffix != ".zip":
                archive.write(path, path.relative_to(output).as_posix())
    with zipfile.ZipFile(output / "candidates.zip") as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity error")
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-frames", action="store_true", help="Save decoded PNG frames and contact sheets for detailed review")
    args = parser.parse_args()
    reports = render(args.manifest.resolve(), args.output.resolve(), review_frames=args.review_frames)
    print(json.dumps({"count": len(reports), "technical_status": "pass", "visual_status": "pending"}))


if __name__ == "__main__":
    main()
