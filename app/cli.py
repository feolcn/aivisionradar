"""CLI entry point: python -m app.cli <command>"""
import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

COMMANDS = ["init-db", "seed", "crawl", "score", "summarize", "report"]


def cmd_init_db():
    from app.db import init_db
    init_db()
    print("Database initialized.")


def cmd_seed():
    from app.db import SessionLocal
    from app.seed import seed_all
    db = SessionLocal()
    try:
        seed_all(db)
        print("Default sources and keywords seeded.")
    finally:
        db.close()


def cmd_crawl():
    from app.db import SessionLocal
    from app.services import crawl_service
    db = SessionLocal()
    try:
        result = crawl_service.crawl_all(db)
        print(f"Crawl complete: {result['total_new']} new items, {result['scored']} scored")
        for name, count in result["sources"].items():
            print(f"  {name}: {count} new")
    finally:
        db.close()


def cmd_score():
    from app.db import SessionLocal
    from app.services.scoring_service import rescore_all
    db = SessionLocal()
    try:
        count = rescore_all(db)
        print(f"Scored {count} items.")
    finally:
        db.close()


def cmd_summarize():
    from app.db import SessionLocal
    from app.services.summary_service import summarize_pending

    async def run():
        db = SessionLocal()
        try:
            count = await summarize_pending(db)
            print(f"Summarized {count} items.")
        finally:
            db.close()

    asyncio.run(run())


def cmd_report():
    from app.db import SessionLocal
    from app.services.report_service import get_daily_report, render_markdown_report
    db = SessionLocal()
    try:
        report = get_daily_report(db)
        md = render_markdown_report(report)
        print(md)
    finally:
        db.close()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python -m app.cli <command>")
        print(f"Commands: {', '.join(COMMANDS)}")
        sys.exit(1)

    command = sys.argv[1]
    dispatch = {
        "init-db": cmd_init_db,
        "seed": cmd_seed,
        "crawl": cmd_crawl,
        "score": cmd_score,
        "summarize": cmd_summarize,
        "report": cmd_report,
    }
    dispatch[command]()


if __name__ == "__main__":
    main()
