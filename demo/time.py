from datetime import UTC, datetime


def main() -> None:
    print(UTC, datetime.now(UTC))
    now = datetime.now(UTC)
    # 通过Python 的 f-string 日期时间格式化语法，按照指定的格式输出
    # %y:两位数年份, %m:月份, %d:日期, %H:小时(24小时制), %M:分钟, %S:秒
    str = f"[{now:%Y-%m-%d %H:%M:%S}]"
    print(str)


main()
