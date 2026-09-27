from __future__ import annotations

import json
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .processing_service import ProcessingService

ROOT = Path(__file__).resolve().parents[2]
STORAGE = ROOT / "storage"
JOBS = STORAGE / "jobs"
JOBS.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="GULF Subtitle + Text V2",
    description="Local-first, review-first subtitle and hook generation.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = ProcessingService(ROOT)
locks: dict[str, threading.Lock] = {}


class Review(BaseModel):
    segments: list[dict[str, Any]] = Field(default_factory=list)
    hook_text: str = ""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def folder(job_id: str) -> Path:
    return JOBS / job_id


def read_meta(job_id: str) -> dict[str, Any]:
    p = folder(job_id) / "meta.json"
    if not p.exists():
        raise HTTPException(404, "任务不存在")
    return json.loads(p.read_text("utf-8"))


def write_meta(job_id: str, data: dict[str, Any]) -> None:
    p = folder(job_id) / "meta.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def update(job_id: str, **fields: Any) -> dict[str, Any]:
    with locks.setdefault(job_id, threading.Lock()):
        data = read_meta(job_id)
        data.update(fields)
        data["updated_at"] = now()
        write_meta(job_id, data)
        return data


def normalize_segments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for item in items:
        try:
            start = float(item["start"])
            end = float(item["end"])
            en = str(item.get("en", "")).strip()
            zh = str(item.get("zh", "")).strip()
            confidence = float(item.get("confidence", 0))
        except Exception:
            continue
        if en and end > start:
            segments.append(
                {
                    "start": start,
                    "end": end,
                    "en": en,
                    "zh": zh,
                    "confidence": max(0.0, min(100.0, confidence)),
                }
            )
    segments.sort(key=lambda x: x["start"])
    return segments


def run_processing(job_id: str) -> None:
    try:
        update(job_id, status="processing", stage="准备", progress=2, message="开始处理视频")
        result = processor.process(
            job_id,
            lambda stage, progress, message: update(
                job_id, stage=stage, progress=progress, message=message
            ),
        )
        update(
            job_id,
            **result,
            status="review",
            stage="审片",
            progress=100,
            message="审核代理已生成，请检查字幕与前三秒说明",
        )
    except Exception as exc:
        update(
            job_id,
            status="failed",
            stage="失败",
            progress=100,
            error=str(exc),
            message="处理失败",
        )


def review_task(job_id: str, segments: list[dict[str, Any]], hook: str) -> None:
    try:
        processor.rerender_review(
            job_id,
            segments,
            hook,
            lambda stage, progress, message: update(
                job_id, stage=stage, progress=progress, message=message
            ),
        )
        update(
            job_id,
            status="review",
            stage="审片",
            progress=100,
            message="审核预览已更新",
            files={
                "review": f"/media/{job_id}/review.mp4",
                "ass": f"/media/{job_id}/subtitles.ass",
            },
        )
    except Exception as exc:
        update(job_id, status="failed", stage="失败", progress=100, error=str(exc), message="预览更新失败")


def final_task(job_id: str, segments: list[dict[str, Any]], hook: str) -> None:
    try:
        files = processor.render_final(
            job_id,
            segments,
            hook,
            lambda stage, progress, message: update(
                job_id, stage=stage, progress=progress, message=message
            ),
        )
        update(
            job_id,
            status="approved",
            stage="已完成",
            progress=100,
            message="最终版已生成，可保存到本机后手动发布",
            files=files,
        )
    except Exception as exc:
        update(job_id, status="failed", stage="失败", progress=100, error=str(exc), message="最终版生成失败")


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "message": "GULF Subtitle + Text V2",
            "status": "running",
            "ui": "/ui/",
            "workflow": "upload -> transcribe -> translate -> review -> approve",
        }
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "gulf-subtitle-v2"}


@app.get("/api/v1/status")
async def api_status() -> dict[str, Any]:
    return {
        "api": "operational",
        "version": app.version,
        "storage": "local",
        "ffmpeg": processor.ffmpeg,
        "whisper_model": "local",
    }


@app.post("/api/v1/jobs")
async def create_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(400, "没有收到视频文件")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}:
        raise HTTPException(400, "仅支持 MP4 / MOV / MKV / WEBM / M4V / AVI")

    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    job = folder(job_id)
    job.mkdir(parents=True, exist_ok=False)
    source = job / f"source{suffix}"

    size = 0
    with source.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)

    meta = {
        "id": job_id,
        "filename": Path(file.filename).name,
        "size": size,
        "created_at": now(),
        "updated_at": now(),
        "status": "queued",
        "stage": "排队",
        "progress": 0,
        "message": "视频已收到",
        "segments": [],
        "hook_text": "",
        "translator": "",
        "files": {},
    }
    write_meta(job_id, meta)
    background_tasks.add_task(run_processing, job_id)
    return meta


@app.get("/api/v1/jobs")
async def jobs() -> dict[str, Any]:
    result = []
    for p in JOBS.iterdir():
        if (p / "meta.json").exists():
            try:
                result.append(json.loads((p / "meta.json").read_text("utf-8")))
            except Exception:
                pass
    result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"jobs": result, "total": len(result)}


@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    return read_meta(job_id)


@app.put("/api/v1/jobs/{job_id}/review")
async def save_review(
    job_id: str, payload: Review, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    data = read_meta(job_id)
    if data.get("status") != "review":
        raise HTTPException(409, "当前任务尚未进入审片状态")

    segments = normalize_segments(payload.segments)
    if not segments:
        raise HTTPException(400, "没有可用字幕")

    hook = payload.hook_text.strip()
    update(
        job_id,
        segments=segments,
        hook_text=hook,
        status="rendering_review",
        stage="更新审核预览",
        progress=5,
        message="正在应用你的修改并重新生成审核预览",
    )
    background_tasks.add_task(review_task, job_id, segments, hook)
    return {"success": True, "status": "rendering_review"}


@app.post("/api/v1/jobs/{job_id}/approve")
async def approve(
    job_id: str, payload: Review, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    data = read_meta(job_id)
    if data.get("status") != "review":
        raise HTTPException(409, "只有审核预览完成后才能通过")

    segments = normalize_segments(payload.segments)
    if not segments:
        raise HTTPException(400, "没有可用字幕")

    hook = payload.hook_text.strip()
    update(
        job_id,
        segments=segments,
        hook_text=hook,
        status="rendering_final",
        stage="生成最终版",
        progress=5,
        message="正在生成最终高清版",
    )
    background_tasks.add_task(final_task, job_id, segments, hook)
    return {"success": True, "status": "rendering_final"}


@app.post("/api/v1/jobs/{job_id}/reject")
async def reject(job_id: str) -> dict[str, Any]:
    data = read_meta(job_id)
    if data.get("status") not in {"review", "failed"}:
        raise HTTPException(409, "当前任务不能删除")

    shutil.rmtree(folder(job_id), ignore_errors=True)
    locks.pop(job_id, None)
    return {"success": True, "deleted": job_id}


@app.get("/media/{job_id}/{filename}")
async def media(job_id: str, filename: str) -> FileResponse:
    base = folder(job_id).resolve()
    target = (base / Path(filename).name).resolve()
    if base not in target.parents or not target.is_file():
        raise HTTPException(404, "文件不存在")
    return FileResponse(target)


FRONTEND = ROOT / "frontend"
if FRONTEND.exists():
    app.mount("/ui", StaticFiles(directory=FRONTEND, html=True), name="ui")


@app.get("/app", response_model=None)
async def app_page():
    page = FRONTEND / "index.html"
    if page.exists():
        return FileResponse(page)
    return JSONResponse({"error": "frontend missing"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
