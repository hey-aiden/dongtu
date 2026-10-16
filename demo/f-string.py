"""
f-string 语法：
1. 变量与表达式插值

2. 格式说明符 f"{表达式:格式说明符}"
常用格式说明符：
   - .Nf         保留 N 位小数
   - .Ns         截取字符串前 N 个字符
   - <N >N ^N    左对齐 / 右对齐 / 居中(宽度 N)
   - 填充字符    配合对齐使用,如 *^10、0>5
   - + - (空格)  控制正负号显示
   - , _         千位分隔符
   - %           百分比
   - b o x X d   进制转换(加 # 显示 0x 等前缀)
   - e E f g     科学计数法

3. 日期格式化
常用日期格式符：
   - %Y %y           四位 / 两位年份
   - %m %d           月(01-12) / 日(01-31)
   - %H %M %S        时(24h) / 分 / 秒
   - %I %p           12 小时制 + AM/PM
   - %A %a %B %b     星期 / 月份的完整名与缩写
   - %j              一年中的第几天(001-366)
   - %U %W           一年中的第几周(周日 / 周一起算)
   - %f              微秒(6 位)
   - %z %Z           UTC 偏移 / 时区名
"""

from datetime import datetime


def main() -> None:
    name = "aiden"

    # 1. 变量与表达式插值
    print(f"author: {name}")

    # 2. 格式说明符 f"{表达式:格式说明符}"
    num = 3.1415926
    print(f"保留两位小数: {num:.2f}")

    # 宽度与对齐
    print(f"左对齐:   |{name:<10}|")
    print(f"右对齐:   |{name:>10}|")
    print(f"居中:     |{name:^10}|")
    print(f"填充居中: |{name:*^10}|")

    # 数字填充与符号
    n = 42
    print(f"补零:     {n:05d}")
    print(f"正号:     {n:+d}")
    print(f"空格对齐负号: {n: d}  {-n: d}")

    # 千位分隔符
    print(f"千位分隔: {1234567890:,}")

    # 百分比 / 科学计数
    print(f"百分比:   {0.1234:.1%}")
    print(f"科学计数: {num:.2e}")

    # 进制转换
    print(f"进制:     {255:b} {255:o} {255:x} {255:X} {255:#x}")

    # 字符串截断
    print(f"截断:     {'hello world':.5s}")

    # 3. 日期格式化
    now = datetime.now()
    print(f"日期时间: {now:%Y-%m-%d %H:%M:%S}")
    print(f"年月日:   {now:%Y-%m-%d}")
    print(f"时间:     {now:%H:%M:%S}")
    print(f"12 小时制: {now:%I:%M:%S %p}")
    print(f"两位年份: {now:%y/%m/%d}")
    print(f"微秒:     {now:%f}")
    print(f"星期/月份: {now:%A %B %d}")
    print(f"缩写:     {now:%a %b %d}")
    print(f"第几天:   {now:%j}")
    print(f"第几周:   {now:%U}")


main()
