import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class PlatformService:
    PLATFORMS = {
        "douyin": {"name": "抖音", "max_duration": 3600, "format": "mp4"},
        "xhs": {"name": "小红书", "max_duration": 1800, "format": "mp4"},
        "bilibili": {"name": "B站", "max_duration": 7200, "format": "mp4"},
        "kuaishou": {"name": "快手", "max_duration": 3600, "format": "mp4"},
        "wevideo": {"name": "WeVideo", "max_duration": 3600, "format": "mp4"},
        "weibo": {"name": "微博", "max_duration": 600, "format": "mp4"}
    }
    
    def get_platform_specs(self, platform: str) -> Dict:
        """Get technical specifications for a platform"""
        return self.PLATFORMS.get(platform, {})
    
    def get_all_platforms(self) -> Dict:
        """Get all available platforms"""
        return self.PLATFORMS
    
    def validate_video_for_platform(self, platform: str, duration: int, format: str) -> Dict:
        """Validate if video meets platform requirements"""
        specs = self.get_platform_specs(platform)
        
        if not specs:
            return {"valid": False, "error": "Unknown platform"}
        
        issues = []
        
        if duration > specs.get("max_duration", 3600):
            issues.append(f"Duration exceeds limit of {specs['max_duration']}s")
        
        if format != specs.get("format"):
            issues.append(f"Format must be {specs['format']}")
        
        return {
            "valid": len(issues) == 0,
            "platform": platform,
            "issues": issues
        }
    
    def prepare_content_for_platform(self, platform: str, title: str, description: str) -> Dict:
        """Prepare content specifically for a platform"""
        platform_specs = self.get_platform_specs(platform)
        
        return {
            "platform": platform,
            "platform_name": platform_specs.get("name", platform),
            "title": self._adapt_title(title, platform),
            "description": self._adapt_description(description, platform),
            "hashtags": self._generate_hashtags(platform),
            "optimal_duration": platform_specs.get("max_duration", 3600)
        }
    
    @staticmethod
    def _adapt_title(title: str, platform: str) -> str:
        """Adapt title for specific platform"""
        max_lengths = {"douyin": 30, "xhs": 30, "weibo": 20, "bilibili": 80}
        max_len = max_lengths.get(platform, 50)
        
        if len(title) > max_len:
            return title[:max_len-3] + "..."
        return title
    
    @staticmethod
    def _adapt_description(desc: str, platform: str) -> str:
        """Adapt description for specific platform"""
        max_lengths = {"douyin": 150, "xhs": 2000, "weibo": 140, "bilibili": 5000}
        max_len = max_lengths.get(platform, 500)
        
        if len(desc) > max_len:
            return desc[:max_len-3] + "..."
        return desc
    
    @staticmethod
    def _generate_hashtags(platform: str) -> List[str]:
        """Generate platform-specific hashtags"""
        hashtags = {
            "douyin": ["#抖音", "#视频", "#原创"],
            "xhs": ["#小红书", "#笔记", "#分享"],
            "bilibili": ["#B站", "#视频", "#内容"],
        }
        return hashtags.get(platform, [])

platform_service = PlatformService()
