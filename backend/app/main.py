from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GULF Video Subtitle Publisher API",
    description="API for video upload, subtitle generation, and multi-platform publishing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "GULF Video Subtitle Publisher API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gulf-backend"}

@app.get("/api/v1/status")
async def api_status():
    return {
        "api": "operational",
        "database": "connected",
        "storage": "available",
        "timestamp": "2024-09-27"
    }

@app.post("/api/v1/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(default="")
):
    try:
        logger.info(f"Received upload: {file.filename}")
        
        filename = file.filename
        filepath = f"/tmp/{filename}"
        
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        return {
            "success": True,
            "message": "Video uploaded successfully",
            "file_id": "vid_001",
            "filename": filename,
            "title": title,
            "description": description,
            "size": len(contents),
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/v1/videos")
async def list_videos():
    return {
        "videos": [
            {
                "id": "vid_001",
                "title": "Sample Video 1",
                "status": "completed",
                "platforms": ["douyin", "xhs", "bilibili"]
            }
        ],
        "total": 1
    }

@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: str):
    return {
        "id": video_id,
        "title": "Sample Video",
        "description": "A sample video for testing",
        "status": "completed",
        "duration": 120,
        "subtitles": [
            {"start": 0, "end": 3, "text": "Welcome to GULF"},
            {"start": 3, "end": 6, "text": "Video Subtitle Publisher"}
        ],
        "platforms": ["douyin", "xhs", "bilibili", "kuaishou"],
        "created_at": "2024-09-27T10:00:00Z"
    }

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
