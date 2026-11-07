import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location("compose", Path(__file__).parents[1] / "scripts/compose_pack.py")
compose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compose)


class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        choices = [os.environ.get("TEST_FONT", ""), "C:/Windows/Fonts/msyhbd.ttc",
                   "C:/Windows/Fonts/arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   "/System/Library/Fonts/Supplemental/Arial.ttf"]
        self.font = next((p for p in choices if p and Path(p).is_file()), None)
        if not self.font:
            self.skipTest("set TEST_FONT to a local TTF/TTC")
        for index, x in enumerate([8, 36, 36, 8]):
            frame = Image.new("RGBA", (64, 64))
            draw = ImageDraw.Draw(frame)
            draw.rectangle((x, 20, x + 12, 44), fill=(25, 80, 160, 255))
            frame.save(self.root / f"{index}.png")
        self.data = {"size": 128, "font": self.font, "count": 1,
                     "items": [{"id": "01", "caption": "OK", "frames": [f"{i}.png" for i in range(4)],
                                "durations_ms": [100, 200, 300, 400]}]}

    def run_render(self, review_frames=False):
        path = self.root / "render.json"
        path.write_text(json.dumps(self.data), encoding="utf-8")
        return compose.render(path, self.root / "out", review_frames=review_frames)

    def test_default_delivery_has_no_frame_cache_or_broken_detail_link(self):
        self.run_render()
        self.assertFalse((self.root / "out/review-frames").exists())
        self.assertNotIn('href="review-frames/', (self.root / "out/index.html").read_text(encoding="utf-8"))
        with zipfile.ZipFile(self.root / "out/candidates.zip") as archive:
            self.assertFalse(any(n.startswith("review-frames/") for n in archive.namelist()))

    def test_detailed_review_exports_decoded_frames_and_contact_sheet(self):
        result = self.run_render(review_frames=True)[0]
        self.assertEqual(len(list((self.root / "out/review-frames/01").glob("*.png"))), result["frame_count"])
        self.assertTrue((self.root / "out/review-frames/01.png").is_file())
        self.assertIn('href="review-frames/01.png"', (self.root / "out/index.html").read_text(encoding="utf-8"))

    def test_nonuniform_timing_and_candidate_package(self):
        result = self.run_render()[0]
        self.assertEqual(result["total_ms"], 1000)
        self.assertGreater(result["distinct_frames"], 1)
        self.assertEqual(result["loop"], 0)
        with zipfile.ZipFile(self.root / "out/candidates.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len([n for n in archive.namelist() if n.startswith("gifs/")]), 1)
            report = json.loads(archive.read("review.json"))
            self.assertEqual(report[0]["playback"], "pending")
            self.assertEqual(report[0]["sha256"], result["sha256"])
            self.assertNotIn(self.font.encode(), archive.read("technical-audit.json"))

    def test_transparency_and_disposal_no_trail(self):
        self.data["background"] = "transparent"
        result = self.run_render()[0]
        self.assertTrue(all(result["transparent_pixels_per_frame"]))
        with Image.open(self.root / "out/gifs/01.gif") as gif:
            frames = []
            for i in range(gif.n_frames):
                gif.seek(i)
                frames.append(gif.convert("RGBA").copy())
            # 角色从左到右再返回，左侧原位置必须恢复透明。
            self.assertGreater(frames[0].getpixel((38, 60))[3], 0)
            self.assertEqual(frames[1].getpixel((38, 60))[3], 0)
            self.assertEqual(frames[0].tobytes(), frames[-1].tobytes())

    def test_static_frames_rejected_without_zip(self):
        self.data["items"][0]["frames"] = ["0.png"] * 4
        with self.assertRaisesRegex(ValueError, "technical checks failed"):
            self.run_render()
        self.assertFalse((self.root / "out/candidates.zip").exists())

    def test_existing_revision_not_overwritten(self):
        self.run_render()
        original = (self.root / "out/gifs/01.gif").read_bytes()
        with self.assertRaisesRegex(ValueError, "not empty"):
            self.run_render()
        self.assertEqual((self.root / "out/gifs/01.gif").read_bytes(), original)

    def test_bad_timing_and_count(self):
        self.data["items"][0]["durations_ms"][0] = 103
        with self.assertRaisesRegex(ValueError, "10ms"):
            self.run_render()
        self.data["items"][0]["durations_ms"][0] = 100
        self.data["count"] = 2
        with self.assertRaisesRegex(ValueError, "count"):
            self.run_render()

    def test_mixed_source_sizes_rejected(self):
        Image.new("RGBA", (65, 64)).save(self.root / "1.png")
        with self.assertRaisesRegex(ValueError, "sizes differ"):
            self.run_render()

    def test_custom_count_and_small_canvas(self):
        self.data["size"] = 64
        self.data["items"].append(dict(self.data["items"][0], id="02", caption="HI"))
        self.data["count"] = 2
        reports = self.run_render()
        self.assertEqual(len(reports), 2)
        self.assertTrue(all(r["size"] == [64, 64] for r in reports))

    def test_duplicate_caption_and_unsafe_id_rejected(self):
        self.data["items"].append(dict(self.data["items"][0], id="02"))
        self.data["count"] = 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_render()
        self.data["items"].pop()
        self.data["count"] = 1
        self.data["items"][0]["id"] = "../escape"
        with self.assertRaisesRegex(ValueError, "filename"):
            self.run_render()

    def test_textless_pack_needs_no_font_and_ignores_caption_pixels(self):
        self.data.pop("font")
        self.data["show_text"] = False
        self.data["items"].append(dict(self.data["items"][0], id="02", caption="HI"))
        self.data["count"] = 2
        reports = self.run_render()
        self.assertTrue(all(r["show_text"] is False for r in reports))
        self.assertEqual((self.root / "out/gifs/01.gif").read_bytes(),
                         (self.root / "out/gifs/02.gif").read_bytes())
        # 无字时可用整个安全区；主体不再向下避让字幕。
        self.data["background"] = "transparent"
        frames = compose.compose_frames(self.data, self.data["items"][0], self.root, None)
        top = frames[0].getchannel("A").getbbox()[1]
        self.assertLess(top, 50)

    def test_per_item_text_override_and_default(self):
        item = self.data["items"][0]
        self.assertTrue(compose.text_enabled(self.data, item))
        self.data["show_text"] = False
        self.data["background"] = "transparent"
        plain = compose.compose_frames(self.data, item, self.root, None)[0]
        item["show_text"] = True
        labelled = compose.compose_frames(self.data, item, self.root, self.font)[0]
        self.assertIsNone(plain.getchannel("A").crop((0, 0, 128, 24)).getbbox())
        self.assertIsNotNone(labelled.getchannel("A").crop((0, 0, 128, 24)).getbbox())
        self.assertTrue(self.run_render()[0]["show_text"])

    def test_text_switch_rejects_string_boolean(self):
        self.data["show_text"] = "false"
        with self.assertRaisesRegex(ValueError, "boolean"):
            self.run_render()


if __name__ == "__main__":
    unittest.main()
