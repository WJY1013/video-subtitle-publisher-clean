import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        self.videos = {}
    
    def upload_video(self, file_id: str, filename: str, title: str, description: str):
        """Store video metadata"""
        video_data = {
            "id": file_id,
            "filename": filename,
            "title": title,
            "description": description,
            "status": "uploaded",
            "created_at": datetime.now().isoformat(),
            "subtitles": [],
            "platforms": []
        }
        self.videos[file_id] = video_data
        logger.info(f"Video registered: {file_id}")
        return video_data
    
    def get_video(self, video_id: str) -> Optional[dict]:
        """Retrieve video metadata"""
        return self.videos.get(video_id)
    
    def list_videos(self) -> List[dict]:
        """List all videos"""
        return list(self.videos.values())
    
    def update_video_status(self, video_id: str, status: str):
        """Update video processing status"""
        if video_id in self.videos:
            self.videos[video_id]["status"] = status
            logger.info(f"Video {video_id} status updated to: {status}")
            return self.videos[video_id]
        return None
    
    def add_subtitles(self, video_id: str, subtitles: List[dict]):
        """Add generated subtitles to video"""
        if video_id in self.videos:
            self.videos[video_id]["subtitles"] = subtitles
            logger.info(f"Subtitles added to video {video_id}")
            return self.videos[video_id]
        return None
    
    def add_platforms(self, video_id: str, platforms: List[str]):
        """Mark video for publishing to platforms"""
        if video_id in self.videos:
            self.videos[video_id]["platforms"] = platforms
            logger.info(f"Video {video_id} marked for platforms: {platforms}")
            return self.videos[video_id]
        return None

video_service = VideoService()
