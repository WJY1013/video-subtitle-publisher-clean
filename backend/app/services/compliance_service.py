import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class ComplianceService:
    PLATFORM_RULES = {
        "douyin": {
            "required": ["authentic", "clear", "safe"],
            "warnings": ["不要使用未经验证的耸人听闻的表述", "避免政治敏感或有争议的内容框架"],
        },
        "xhs": {
            "required": ["honest", "clear", "disclose"],
            "warnings": ["清楚地披露任何赞助信息", "避免夸大的健康或产品宣传"],
        },
        "kuaishou": {
            "required": ["authentic", "human", "clear"],
            "warnings": ["避免操纵性的参与引导", "保持内容真实和真诚"],
        },
        "bilibili": {
            "required": ["accurate", "licensed", "clear"],
            "warnings": ["仅使用获得许可的媒体素材", "为事实宣传注明来源"],
        },
    }
    
    def evaluate_content(self, title: str, description: str, platforms: List[str]) -> Dict:
        """Evaluate content compliance across platforms"""
        combined = f"{title} {description}".lower()
        warnings = []
        risks = []
        
        risk_terms = [
            ("保证", "high"),
            ("秒杀", "high"),
            ("免费", "medium"),
            ("必须", "medium")
        ]
        
        for term, risk_level in risk_terms:
            if term in combined:
                risks.append({"term": term, "level": risk_level})
        
        for platform in platforms:
            rules = self.PLATFORM_RULES.get(platform, {})
            if rules:
                warnings.extend(rules.get("warnings", []))
        
        status = "pass" if not risks else ("warning" if any(r["level"] == "medium" for r in risks) else "fail")
        
        return {
            "status": status,
            "risks": risks,
            "warnings": list(set(warnings)),
            "platforms_checked": platforms
        }

compliance_service = ComplianceService()
