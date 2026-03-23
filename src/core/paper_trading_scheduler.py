"""模拟盘调度器：60 秒间隔扫描建仓/平仓。"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.paper_trading_engine import ENGINE

logger = logging.getLogger(__name__)


class PaperTradingScheduler:
    def __init__(self, timezone: str = "UTC", interval_seconds: int = 60):
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self.interval_seconds = max(15, int(interval_seconds))
        self._running = False

    async def _scan_job(self):
        if self._running:
            logger.info("[模拟盘] 上轮扫描仍在执行，跳过本轮")
            return
        self._running = True
        try:
            result = await ENGINE.scan_once()
            logger.info(
                "[模拟盘] 扫描完成: opened=%s closed=%s status=%s",
                result.get("opened", 0),
                result.get("closed", 0),
                result.get("status", "?"),
            )
        except Exception as e:
            logger.exception(f"[模拟盘] 扫描异常: {e}")
        finally:
            self._running = False

    def start(self):
        self.scheduler.add_job(
            self._scan_job,
            "interval",
            seconds=self.interval_seconds,
            id="paper_trading_scan",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self.scheduler.start()
        logger.info(f"模拟盘调度器已启动，扫描间隔 {self.interval_seconds}s")

    def shutdown(self):
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass
        logger.info("模拟盘调度器已关闭")
