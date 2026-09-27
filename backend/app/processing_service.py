from __future__ import annotations

import json
import os
import re
import statistics
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

Progress = Callable[[str, int, str], None]


class Translator:
    def __init__(self) -> None:
        self.model_name = os.getenv("TRANSLATION_MODEL", "Helsinki-NLP/opus-mt-en-zh")
        self.pipeline = None
        self.error: str | None = None
        self._lock = threading.Lock()

    def _load(self) -> None:
        if self.pipeline is not None or self.error:
            return
        with self._lock:
            if self.pipeline is not None or self.error:
                return
            try:
                from transformers import pipeline
                self.pipeline = pipeline("translation", model=self.model_name)
            except Exception as exc:
                self.error = str(exc)

    def translate(self, texts: list[str]) -> tuple[list[str], str]:
        self._load()
        if self.pipeline is None:
            return [""] * len(texts), f"local translation unavailable: {self.error}"
        out: list[str] = []
        batch_size = max(1, int(os.getenv("TRANSLATION_BATCH", "8")))
        for i in range(0, len(texts), batch_size):
            try:
                batch = self.pipeline(texts[i:i + batch_size], max_length=256)
                out.extend(str(x["translation_text"]).strip() for x in batch)
            except Exception as exc:
                return out + [""] * (len(texts) - len(out)), f"local translation failed: {exc}"
        return out, f"local:{self.model_name}"


class ProcessingService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.jobs = root / "storage" / "jobs"
        self.jobs.mkdir(parents=True, exist_ok=True)
        self.ffmpeg = self._find_ffmpeg()
        self.translator = Translator()
        self.whisper = None
        self.whisper_lock = threading.Lock()

    def _find_ffmpeg(self) -> str:
        explicit = os.getenv("FFMPEG_PATH", "").strip()
        if explicit and Path(explicit).exists():
            return explicit
        if imageio_ffmpeg:
            try:
                return imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass
        return "ffmpeg"

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

    def _job(self, job_id: str) -> Path:
        return self.jobs / job_id

    def _source(self, job_id: str) -> Path:
        files = sorted(self._job(job_id).glob("source.*"))
        if not files:
            raise RuntimeError("源视频不存在")
        return files[0]

    def _load_whisper(self) -> Any:
        if self.whisper is not None:
            return self.whisper
        with self.whisper_lock:
            if self.whisper is not None:
                return self.whisper
            from faster_whisper import WhisperModel
            device = os.getenv("WHISPER_DEVICE", "cpu")
            compute = os.getenv("WHISPER_COMPUTE_TYPE", "int8" if device == "cpu" else "float16")
            self.whisper = WhisperModel(
                os.getenv("WHISPER_MODEL", "large-v3"),
                device=device,
                compute_type=compute,
                cpu_threads=int(os.getenv("WHISPER_CPU_THREADS", str(max(1, (os.cpu_count() or 4) // 2)))),
            )
            return self.whisper

    @staticmethod
    def _confidence(seg: Any) -> float:
        try:
            probs = [
                float(getattr(w, "probability", 0.0))
                for w in (getattr(seg, "words", None) or [])
                if getattr(w, "probability", None) is not None
            ]
            if probs:
                return max(0.0, min(100.0, statistics.fmean(probs) * 100))
        except Exception:
            pass
        try:
            return max(0.0, min(100.0, (float(seg.avg_logprob) + 1) * 100))
        except Exception:
            return 0.0

    @staticmethod
    def _clean_en(text: str) -> str:
        text = re.sub(r"\s+", " ", text or "").strip()
        return re.sub(r"\s+([,.!?;:])", r"\1", text)

    @staticmethod
    def _clean_zh(text: str) -> str:
        return re.sub(r"\s+", "", text or "").strip()

    @staticmethod
    def _wrap(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        cut = limit
        for i in range(limit - 1, max(0, limit // 2), -1):
            if text[i] in "，。！？；,.!?; ":
                cut = i + 1
                break
        return text[:cut].strip() + "\n" + text[cut:].strip()

    @staticmethod
    def make_hook(en_lines: list[str], zh_lines: list[str]) -> str:
        src = " ".join(en_lines[:2]).lower()
        lead = (zh_lines[0] if zh_lines else "").strip("，。！？；：,.;: ")[:30]
        if not lead:
            return "3秒先看：这段内容有一个容易忽略的关键点"
        if any(k in src for k in ("mistake", "wrong", "common")):
            prefix = "很多人都会踩的坑："
        elif any(k in src for k in ("why", "can't", "cannot")):
            prefix = "为什么总是做不到？关键在这里："
        elif any(k in src for k in ("how to", "learn", "english")):
            prefix = "学英语最容易卡住的地方："
        elif "you" in src or "your" in src:
            prefix = "你可能也正在遇到："
        else:
            prefix = "3秒先看这个关键点："
        return (prefix + lead)[:42]

    def transcribe(self, job_id: str, progress: Progress) -> tuple[list[dict[str, Any]], str, str]:
        source = self._source(job_id)
        audio = self._job(job_id) / "audio.wav"
        progress("提取音频", 7, "正在从视频提取原始音频")
        self._run([
            self.ffmpeg, "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(audio)
        ])
        progress("高精度英语识别", 18, "Whisper large-v3 正在识别并保留时间轴")
        model = self._load_whisper()
        chunks, _ = model.transcribe(
            str(audio), language="en", task="transcribe",
            beam_size=5, best_of=5, temperature=0.0,
            vad_filter=True, vad_parameters={"min_silence_duration_ms": 450},
            word_timestamps=True, condition_on_previous_text=False,
            compression_ratio_threshold=2.4, log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
        )
        segments: list[dict[str, Any]] = []
        for seg in chunks:
            text = self._clean_en(getattr(seg, "text", ""))
            start = float(getattr(seg, "start", 0.0))
            end = float(getattr(seg, "end", start))
            if text and end > start:
                segments.append({
                    "start": round(start, 3), "end": round(end, 3),
                    "en": text, "zh": "",
                    "confidence": round(self._confidence(seg), 1),
                })
        if not segments:
            raise RuntimeError("没有识别到有效英语语音，请确认视频有清晰人声")
        progress("中文翻译", 54, "正在用本地模型翻译并与英文时间轴对齐")
        zh, translator = self.translator.translate([x["en"] for x in segments])
        for item, value in zip(segments, zh):
            item["zh"] = self._clean_zh(value)
        if not any(x["zh"] for x in segments):
            raise RuntimeError("中文翻译模型不可用；为避免生成错误字幕，本程序不会使用假中文占位")
        first_en = [x["en"] for x in segments if x["start"] <= 6][:3]
        first_zh = [x["zh"] for x in segments if x["start"] <= 6][:3]
        return segments, self.make_hook(first_en, first_zh), translator

    @staticmethod
    def ass_time(seconds: float) -> str:
        total = max(0, int(round(seconds * 100)))
        h, rem = divmod(total, 360000)
        m, rem = divmod(rem, 6000)
        s, cs = divmod(rem, 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @staticmethod
    def esc(text: str) -> str:
        return (text or "").replace("{", "\\{").replace("}", "\\}")

    def make_ass(self, job_id: str, segments: list[dict[str, Any]], hook: str) -> Path:
        path = self._job(job_id) / "subtitles.ass"
        lines = [
            "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
            "ScaledBorderAndShadow: yes", "WrapStyle: 2", "",
            "[V4+ Styles]",
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
            "Style: EN,Arial,40,&H00FFFFFF,&H00FFFFFF,&H99000000,&H00000000,0,0,0,0,100,100,0,0,1,2.2,0,2,60,60,118,1",
            "Style: ZH,Microsoft YaHei,38,&H00FFFFFF,&H00FFFFFF,&H99000000,&H00000000,0,0,0,0,100,100,0,0,1,2.2,0,2,60,60,70,1",
            "Style: HOOK,Microsoft YaHei,42,&H00FFFFFF,&H00FFFFFF,&H88000000,&H00000000,700,0,0,0,100,100,0,0,1,3,0,8,110,110,85,1",
            "", "[Events]",
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"
        ]
        for seg in segments:
            start, end = self.ass_time(float(seg["start"])), self.ass_time(float(seg["end"]))
            en = self.esc(self._wrap(str(seg.get("en", "")), 52))
            zh = self.esc(self._wrap(str(seg.get("zh", "")), 24))
            lines.append(f"Dialogue: 0,{start},{end},EN,,0,0,0,,{en}")
            if zh:
                lines.append(f"Dialogue: 1,{start},{end},ZH,,0,0,0,,{zh}")
        if hook:
            lines.append(f"Dialogue: 5,0:00:00.00,0:00:03.00,HOOK,,0,0,0,,{self.esc(hook)}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
        return path

    def render(self, job_id: str, output: Path, ass: Path, review: bool, progress: Progress) -> None:
        source = self._source(job_id)
        sub_path = str(ass.resolve()).replace("\\", "/").replace(":", "\\:")
        vf = f"subtitles='{sub_path}'"
        if review:
            progress("审核代理编码", 72, "正在生成 960×540 快速审核版")
            args = [
                self.ffmpeg, "-y", "-i", str(source),
                "-vf", f"scale='min(960,iw)':-2,{vf}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output)
            ]
        else:
            progress("最终版编码", 72, "保持原画幅，不裁切、不变速，加入底部安全区双语字幕")
            args = [
                self.ffmpeg, "-y", "-i", str(source), "-vf", vf,
                "-c:v", "libx264", "-preset", "medium", "-crf", os.getenv("FINAL_CRF", "18"),
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)
            ]
        proc = self._run(args, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-4000:] or "FFmpeg 编码失败")
        if not output.exists() or output.stat().st_size < 100_000:
            raise RuntimeError("输出视频为空或异常")

    def process(self, job_id: str, progress: Progress) -> dict[str, Any]:
        segments, hook, translator = self.transcribe(job_id, progress)
        ass = self.make_ass(job_id, segments, hook)
        preview = self._job(job_id) / "review.mp4"
        self.render(job_id, preview, ass, True, progress)
        return {
            "segments": segments,
            "hook_text": hook,
            "translator": translator,
            "files": {
                "review": f"/media/{job_id}/review.mp4",
                "ass": f"/media/{job_id}/subtitles.ass"
            }
        }

    def rerender_review(self, job_id: str, segments: list[dict[str, Any]], hook: str, progress: Progress) -> None:
        ass = self.make_ass(job_id, segments, hook)
        self.render(job_id, self._job(job_id) / "review.mp4", ass, True, progress)

    def render_final(self, job_id: str, segments: list[dict[str, Any]], hook: str, progress: Progress) -> dict[str, str]:
        ass = self.make_ass(job_id, segments, hook)
        final = self._job(job_id) / "final.mp4"
        self.render(job_id, final, ass, False, progress)
        srt = self._job(job_id) / "subtitles.srt"
        srt.write_text(self.to_srt(segments), encoding="utf-8-sig")
        return {
            "final": f"/media/{job_id}/final.mp4",
            "srt": f"/media/{job_id}/subtitles.srt",
            "ass": f"/media/{job_id}/subtitles.ass"
        }

    @classmethod
    def to_srt(cls, segments: list[dict[str, Any]]) -> str:
        def ts(sec: float) -> str:
            ms = int(round(max(0, sec) * 1000))
            h, rem = divmod(ms, 3600000)
            m, rem = divmod(rem, 60000)
            s, milli = divmod(rem, 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"
        blocks = []
        for i, seg in enumerate(segments, 1):
            blocks.append(
                f"{i}\n{ts(float(seg['start']))} --> {ts(float(seg['end']))}\n"
                f"{seg.get('en','')}\n{seg.get('zh','')}\n"
            )
        return "\n".join(blocks)
