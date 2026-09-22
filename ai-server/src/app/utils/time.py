from datetime import datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """返回北京时间"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)
