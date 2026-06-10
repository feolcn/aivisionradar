# 🛰 AIVisionRadar

> 面向 AI 工程师、工业视觉工程师、边缘 AI 工程师的技术情报雷达系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目介绍

AIVisionRadar 是一个开源的技术情报聚合与推荐系统。它自动抓取 RSS、arXiv、GitHub Trending、GitHub Search、Hugging Face 等公开信息源，根据用户配置的关键词自动打分排序，并生成每日技术情报推荐。

**目标用户：** AI 工程师、工业视觉工程师、边缘 AI 工程师、技术内容创作者

## 项目截图

> 截图待补充（运行后访问 http://localhost:8000）

## 功能列表

- **多源聚合**：RSS/Atom、arXiv、GitHub Trending、GitHub Search API、Hugging Face Blog
- **关键词打分**：基于可配置关键词的多维度相关性评分
- **AI 摘要**：可选接入 OpenAI 兼容 API，生成中文分析摘要（无 API Key 时优雅降级）
- **每日日报**：按类别分类展示 Top 内容，支持 Markdown 导出
- **Web 管理界面**：信息源管理、关键词管理、情报浏览、状态管理
- **REST API**：完整 API 供第三方客户端调用
- **CLI 工具**：命令行快速操作
- **定时任务**：可配置自动抓取（APScheduler）
- **Docker 支持**：一键部署

## 快速开始

### 方式一：本地运行

```bash
# 1. 克隆项目
git clone https://github.com/yourname/aivisionradar.git
cd aivisionradar

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入可选配置（GITHUB_TOKEN、AI_API_KEY 等）

# 5. 初始化数据库
python -m app.cli init-db

# 6. 导入默认信息源和关键词
python -m app.cli seed

# 7. 执行首次抓取
python -m app.cli crawl

# 8. 启动 Web 服务
uvicorn app.main:app --reload
```

访问 http://localhost:8000

### 方式二：Docker

```bash
cp .env.example .env
docker compose up --build
```

访问 http://localhost:8000

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./data/aivisionradar.db` | 数据库连接字符串，支持 PostgreSQL |
| `ENABLE_SCHEDULER` | `false` | 是否启用定时自动抓取 |
| `GITHUB_TOKEN` | 空 | GitHub API Token（用于 GitHub Search，无则跳过） |
| `AI_BASE_URL` | 空 | OpenAI 兼容 API Base URL |
| `AI_API_KEY` | 空 | AI API Key（无则使用模板摘要） |
| `AI_MODEL` | `gpt-4o-mini` | 使用的 AI 模型名称 |
| `CRAWL_INTERVAL_HOURS` | `6` | 自动抓取间隔（小时） |
| `DAILY_REPORT_HOUR` | `8` | 每日日报生成时间（小时，24h制） |

## CLI 命令

```bash
python -m app.cli init-db      # 初始化数据库
python -m app.cli seed         # 导入默认信息源和关键词
python -m app.cli crawl        # 执行抓取并打分
python -m app.cli score        # 重新对所有内容打分
python -m app.cli summarize    # 对高分内容生成 AI 摘要
python -m app.cli report       # 输出今日日报（Markdown）
```

## 默认信息源

| 名称 | 类型 | 分类 |
|------|------|------|
| NVIDIA Technical Blog | RSS | AI硬件 |
| NVIDIA Developer Blog | RSS | AI硬件 |
| Hugging Face Blog | RSS | LLM |
| Hugging Face Daily Papers | RSS | 论文 |
| arXiv cs.CV | arXiv RSS | 论文 |
| arXiv cs.AI | arXiv RSS | 论文 |
| arXiv cs.LG | arXiv RSS | 论文 |
| Ultralytics Blog | RSS | 视觉 |
| Roboflow Blog | RSS | 视觉 |
| OpenCV Blog | RSS | 视觉 |
| GitHub Trending Python | GitHub Trending | GitHub |
| GitHub Trending AI | GitHub Trending | GitHub |
| GitHub Search: defect detection | GitHub Search | GitHub |
| GitHub Search: anomaly detection | GitHub Search | GitHub |
| GitHub Search: Jetson TensorRT | GitHub Search | GitHub |

## 关键词打分逻辑

**总分公式：**
```
total_score = relevance * 0.45 + reproduce * 0.25 + content * 0.2 + monetization * 0.1
```

**相关性分数（relevance_score）：**
- 每命中一个关键词：+keyword.weight
- 标题命中：×2
- 工业视觉关键词：额外 +3
- Jetson/TensorRT/ONNX：额外 +2
- 本地大模型/Agent：额外 +2

**复现价值（reproduce_score）：**
- GitHub 仓库：+3
- 含 code/demo/pretrained/weights：+2
- 含 TensorRT/ONNX/Jetson/Docker：+2
- Stars ≥ 10000: +5，≥ 1000: +4，≥ 100: +2

**内容价值（content_score）：**
- 含 benchmark/tutorial/guide/deploy/how-to：+2
- Stars 同复现价值加成

**变现价值（monetization_score）：**
- 含 industrial/inspection/defect/automation：+3
- 含 local/self-hosted/边缘/本地：+2

## AI 摘要配置

配置以下环境变量启用 AI 摘要（兼容所有 OpenAI API 格式）：

```env
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-xxxx
AI_MODEL=gpt-4o-mini
```

**未配置时**，系统正常运行，AI 摘要字段显示提示信息。

AI 摘要包括：
- `ai_summary`：内容简介（中文，2-3句）
- `why_relevant`：为什么值得关注
- `reproduce_suggestion`：RTX 3090 / Jetson 复现建议
- `content_ideas`：公众号/视频号/GitHub 创作思路

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

主要 API 端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/items` | 获取情报列表（支持分页、筛选） |
| GET | `/api/items/{id}` | 获取情报详情 |
| POST | `/api/items/{id}/status` | 更新状态 |
| GET | `/api/sources` | 信息源列表 |
| POST | `/api/sources` | 添加信息源 |
| PUT | `/api/sources/{id}` | 更新信息源 |
| DELETE | `/api/sources/{id}` | 删除信息源 |
| GET | `/api/keywords` | 关键词列表 |
| POST | `/api/keywords` | 添加关键词 |
| PUT | `/api/keywords/{id}` | 更新关键词 |
| DELETE | `/api/keywords/{id}` | 删除关键词 |
| POST | `/api/crawl/run` | 触发抓取 |
| POST | `/api/crawl/summarize` | 触发 AI 摘要 |
| GET | `/api/reports/daily` | 今日日报（JSON） |
| GET | `/api/reports/daily.md` | 今日日报（Markdown） |

## Roadmap

- [ ] PostgreSQL 支持（只需修改 DATABASE_URL）
- [ ] Flutter 移动端 App
- [ ] 邮件/Webhook 日报推送
- [ ] 更多信息源（YouTube、Twitter/X、LinkedIn）
- [ ] 向量相似度搜索
- [ ] 用户标注数据训练个性化排序
- [ ] RSS 自定义 Feed 输出
- [ ] Telegram Bot 推送

## 贡献指南

欢迎提交 PR 和 Issue！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -m 'feat: add my feature'`
4. 推送分支：`git push origin feature/my-feature`
5. 发起 Pull Request

请确保：
- 代码通过 `ruff check .`
- 测试通过 `pytest`
- 不要提交 `.env` 文件或数据库文件

## 免责声明

- 本项目**仅聚合公开信息源**，不抓取需要登录或付费的内容。
- 本项目**不绕过**任何网站的登录验证或付费墙。
- AI 摘要由第三方 AI 服务生成，**不保证准确性**，重要信息请以原始链接为准。
- 用户应遵守各信息源网站的服务条款（Terms of Service）和 robots.txt。
- 本项目抓取频率较低，请勿修改配置进行高频抓取以免对目标网站造成压力。
- 本项目不存储第三方全文内容，仅保存标题、链接、发布时间、来源和公开摘要。

## License

[MIT](LICENSE) © AIVisionRadar Contributors
