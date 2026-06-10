from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import DailyReportOut, ItemOut
from app.services.report_service import get_daily_report, render_markdown_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/daily", response_model=DailyReportOut)
def daily_report_json(db: Session = Depends(get_db)):
    report = get_daily_report(db)

    def to_out(items):
        return [ItemOut.model_validate(i) for i in items]

    return DailyReportOut(
        date=report["date"],
        total_items=report["total_items"],
        top_items=to_out(report["top_items"]),
        top_reproduce=to_out(report["top_reproduce"]),
        top_content=to_out(report["top_content"]),
        top_industrial=to_out(report["top_industrial"]),
        top_jetson=to_out(report["top_jetson"]),
        top_llm_agent=to_out(report["top_llm_agent"]),
    )


@router.get("/daily.md", response_class=PlainTextResponse)
def daily_report_markdown(db: Session = Depends(get_db)):
    report = get_daily_report(db)
    md = render_markdown_report(report)
    return PlainTextResponse(content=md, media_type="text/markdown")
