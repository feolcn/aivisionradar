import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.routers import api_crawl, api_items, api_keywords, api_reports, api_sources, web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def setup_scheduler(app: FastAPI) -> None:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    from app.db import SessionLocal
    from app.services import crawl_service

    scheduler = AsyncIOScheduler()

    def crawl_job():
        db = SessionLocal()
        try:
            crawl_service.crawl_all(db)
        finally:
            db.close()

    scheduler.add_job(
        crawl_job,
        "interval",
        hours=settings.CRAWL_INTERVAL_HOURS,
        id="crawl_all",
    )
    scheduler.add_job(
        crawl_job,
        CronTrigger(hour=settings.DAILY_REPORT_HOUR, minute=0),
        id="daily_report_crawl",
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Scheduler started (crawl every %dh)", settings.CRAWL_INTERVAL_HOURS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.ENABLE_SCHEDULER:
        setup_scheduler(app)
    yield
    if settings.ENABLE_SCHEDULER and hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Vision Radar — 面向 AI 工程师和工业视觉工程师的信息雷达系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(api_items.router)
app.include_router(api_sources.router)
app.include_router(api_keywords.router)
app.include_router(api_crawl.router)
app.include_router(api_reports.router)
