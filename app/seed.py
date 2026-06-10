from sqlalchemy.orm import Session

from app.models import Keyword, Setting, Source

DEFAULT_SOURCES = [
    {"name": "NVIDIA Technical Blog", "type": "rss", "url": "https://blogs.nvidia.com/feed/", "category": "ai_hardware"},
    {"name": "NVIDIA Developer Blog", "type": "rss", "url": "https://developer.nvidia.com/blog/feed/", "category": "ai_hardware"},
    {"name": "Hugging Face Blog", "type": "rss", "url": "https://huggingface.co/blog/feed.xml", "category": "llm"},
    {"name": "Hugging Face Daily Papers", "type": "rss", "url": "https://huggingface.co/papers/rss", "category": "papers"},
    {"name": "arXiv cs.CV", "type": "arxiv", "url": "https://rss.arxiv.org/rss/cs.CV", "category": "papers"},
    {"name": "arXiv cs.AI", "type": "arxiv", "url": "https://rss.arxiv.org/rss/cs.AI", "category": "papers"},
    {"name": "arXiv cs.LG", "type": "arxiv", "url": "https://rss.arxiv.org/rss/cs.LG", "category": "papers"},
    {"name": "Ultralytics Blog", "type": "rss", "url": "https://www.ultralytics.com/blog/rss.xml", "category": "vision"},
    {"name": "Roboflow Blog", "type": "rss", "url": "https://blog.roboflow.com/rss/", "category": "vision"},
    {"name": "OpenCV Blog", "type": "rss", "url": "https://opencv.org/feed/", "category": "vision"},
    {"name": "GitHub Trending Python", "type": "github_trending", "url": "https://github.com/trending/python", "category": "github"},
    {"name": "GitHub Trending AI", "type": "github_trending", "url": "https://github.com/trending?spoken_language_code=&since=daily&q=AI", "category": "github"},
    {"name": "GitHub Search: defect detection", "type": "github_search", "url": "defect detection", "category": "github"},
    {"name": "GitHub Search: anomaly detection", "type": "github_search", "url": "anomaly detection", "category": "github"},
    {"name": "GitHub Search: Jetson TensorRT", "type": "github_search", "url": "Jetson TensorRT", "category": "github"},
]

DEFAULT_KEYWORDS = [
    # English - industrial vision
    {"keyword": "defect detection", "category": "industrial", "weight": 3.0},
    {"keyword": "anomaly detection", "category": "industrial", "weight": 3.0},
    {"keyword": "industrial inspection", "category": "industrial", "weight": 3.0},
    {"keyword": "visual inspection", "category": "industrial", "weight": 2.5},
    {"keyword": "fabric defect", "category": "industrial", "weight": 3.0},
    {"keyword": "textile defect", "category": "industrial", "weight": 3.0},
    # English - edge AI
    {"keyword": "Jetson", "category": "edge_ai", "weight": 3.0},
    {"keyword": "Orin", "category": "edge_ai", "weight": 2.5},
    {"keyword": "Thor", "category": "edge_ai", "weight": 2.0},
    {"keyword": "TensorRT", "category": "edge_ai", "weight": 2.5},
    {"keyword": "ONNX", "category": "edge_ai", "weight": 2.0},
    # English - LLM/AI
    {"keyword": "VLM", "category": "llm", "weight": 2.0},
    {"keyword": "vision language model", "category": "llm", "weight": 2.0},
    {"keyword": "local LLM", "category": "llm", "weight": 2.0},
    {"keyword": "Qwen", "category": "llm", "weight": 2.0},
    {"keyword": "agent", "category": "llm", "weight": 1.5},
    {"keyword": "OpenClaw", "category": "llm", "weight": 2.0},
    # English - CV
    {"keyword": "YOLO", "category": "vision", "weight": 2.0},
    {"keyword": "segmentation", "category": "vision", "weight": 1.5},
    {"keyword": "object detection", "category": "vision", "weight": 1.5},
    {"keyword": "edge AI", "category": "edge_ai", "weight": 2.5},
    # Chinese
    {"keyword": "工业缺陷检测", "category": "industrial", "weight": 3.0},
    {"keyword": "布匹瑕疵", "category": "industrial", "weight": 3.0},
    {"keyword": "边缘部署", "category": "edge_ai", "weight": 2.5},
    {"keyword": "本地大模型", "category": "llm", "weight": 2.0},
    {"keyword": "视觉语言模型", "category": "llm", "weight": 2.0},
    {"keyword": "多模态", "category": "llm", "weight": 1.5},
    {"keyword": "智能体", "category": "llm", "weight": 1.5},
    {"keyword": "工业视觉", "category": "industrial", "weight": 3.0},
    {"keyword": "异常检测", "category": "industrial", "weight": 3.0},
]


def seed_sources(db: Session) -> None:
    """Insert default sources if not already present."""
    for s in DEFAULT_SOURCES:
        exists = db.query(Source).filter(Source.name == s["name"]).first()
        if not exists:
            db.add(Source(**s))
    db.commit()


def seed_keywords(db: Session) -> None:
    """Insert default keywords if not already present."""
    for k in DEFAULT_KEYWORDS:
        exists = db.query(Keyword).filter(Keyword.keyword == k["keyword"]).first()
        if not exists:
            db.add(Keyword(**k))
    db.commit()


DEFAULT_SETTINGS = [
    {
        "key": "enable_translation",
        "value": "false",
        "label": "中文翻译",
        "description": "自动将英文标题和摘要翻译成中文（需要配置 AI_API_KEY）",
        "value_type": "bool",
    },
    {
        "key": "enable_ai_summary",
        "value": "false",
        "label": "AI 分析摘要",
        "description": "对高分内容生成 AI 分析（需要配置 AI_API_KEY）",
        "value_type": "bool",
    },
    {
        "key": "translation_language",
        "value": "zh-CN",
        "label": "翻译目标语言",
        "description": "翻译的目标语言代码（zh-CN 简体中文 / zh-TW 繁体中文）",
        "value_type": "str",
    },
]


def seed_settings(db: Session) -> None:
    """Insert default settings if not already present."""
    for s in DEFAULT_SETTINGS:
        exists = db.query(Setting).filter(Setting.key == s["key"]).first()
        if not exists:
            db.add(Setting(**s))
    db.commit()


def seed_all(db: Session) -> None:
    seed_sources(db)
    seed_keywords(db)
    seed_settings(db)
