from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
import json
from typing import Optional, List
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GULF Video Subtitle Publisher API",
    description="API for video upload, subtitle generation, and multi-platform publishing (Lightweight Version)",
    version="1.0.0-lite"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_FILE = Path("./data.json")

def load_data():
    """Load video data from JSON file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"videos": []}

def save_data(data):
    """Save video data to JSON file"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/")
async def root():
    return {"message": "GULF Video Subtitle Publisher API (Lightweight)", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gulf-backend-lite"}

@app.get("/api/v1/status")
async def api_status():
    return {
        "api": "operational",
        "database": "sqlite",
        "storage": "local",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(default="")
):
    try:
        logger.info(f"Received upload: {file.filename}")
        
        filename = file.filename or "video.mp4"
        filepath = UPLOAD_DIR / filename
        
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        video_id = f"vid_{len(load_data()['videos']) + 1:03d}"
        video_data = {
            "id": video_id,
            "filename": filename,
            "title": title,
            "description": description,
            "size": len(contents),
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "subtitles": [
                {"start": 0.0, "end": 2.8, "text": "欢迎来到GULF视频发布系统"},
                {"start": 2.8, "end": 5.6, "text": "这是一个专业的视频处理平台"},
                {"start": 5.6, "end": 8.4, "text": "支持多平台同步发布"}
            ],
            "platforms": []
        }
        
        data = load_data()
        data["videos"].append(video_data)
        save_data(data)
        
        return {
            "success": True,
            "message": "Video uploaded successfully",
            "file_id": video_id,
            "filename": filename,
            "title": title,
            "description": description,
            "size": len(contents),
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/v1/videos")
async def list_videos():
    data = load_data()
    return {
        "videos": data.get("videos", []),
        "total": len(data.get("videos", []))
    }

@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: str):
    data = load_data()
    for video in data.get("videos", []):
        if video["id"] == video_id:
            return video
    return JSONResponse(
        status_code=404,
        content={"error": "Video not found"}
    )

@app.post("/api/v1/generate-subtitles")
async def generate_subtitles(
    video_id: str = Form(...),
    language: str = Form(default="zh")
):
    return {
        "success": True,
        "video_id": video_id,
        "language": language,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "这是第一句字幕"},
            {"start": 2.8, "end": 5.6, "text": "这是第二句字幕"},
            {"start": 5.6, "end": 8.4, "text": "这是第三句字幕"}
        ],
        "status": "completed"
    }

@app.post("/api/v1/publish")
async def publish_video(
    video_id: str = Form(...),
    platforms: str = Form(default="douyin,xhs,bilibili")
):
    platform_list = [p.strip() for p in platforms.split(",")]
    
    data = load_data()
    for video in data.get("videos", []):
        if video["id"] == video_id:
            video["platforms"] = platform_list
            save_data(data)
            break
    
    return {
        "success": True,
        "video_id": video_id,
        "platforms": platform_list,
        "results": [
            {"platform": p, "status": "published", "url": f"https://{p}.com/video/{video_id}"}
            for p in platform_list
        ]
    }

@app.post("/api/v1/generate-content")
async def generate_content(
    title: str = Form(...),
    platforms: str = Form(default="douyin,xhs")
):
    return {
        "success": True,
        "title": title,
        "platforms": platforms.split(","),
        "content": {
            "hook": "3秒内吸引观众注意力的开场白",
            "main_content": "核心内容描述和故事叙述",
            "call_to_action": "行动号召"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
