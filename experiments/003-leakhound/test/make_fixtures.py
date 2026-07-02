#!/usr/bin/env python3
"""生成测试夹具：银行 CSV（负数=支出）与支付宝格式 CSV（GBK 编码）。"""

import os
import random

HERE = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(HERE, exist_ok=True)
random.seed(7)


def bank_csv():
    rows = ["Date,Description,Amount"]
    # NETFLIX 月付 -55.00，2025-10 起 -59.00（涨价）
    for m in range(1, 13):
        y, mo = (2025, m) if m <= 12 else (2026, m - 12)
        amt = -55.00 if m < 10 else -59.00
        rows.append(f"2025-{m:02d}-05,NETFLIX.COM 1234567890,{amt:.2f}")
    for i in range(60):
        m, d = random.randint(1, 12), random.randint(1, 28)
        rows.append(f"2025-{m:02d}-{d:02d},POS PURCHASE STORE {i},-{random.uniform(3, 200):.2f}")
    for m in range(1, 13):
        rows.append(f"2025-{m:02d}-25,SALARY ACME CORP,8000.00")
    rows.sort()
    path = os.path.join(HERE, "bank.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(["Date,Description,Amount"] + [r for r in rows if not r.startswith("Date")]))
    return path


def alipay_gbk():
    lines = [
        "支付宝交易记录明细查询",
        "账号:[demo@example.com]",
        "起始日期:[2025-01-01 00:00:00]    终止日期:[2025-12-31 23:59:59]",
        "---------------------------------交易记录明细列表------------------------------------",
        "交易创建时间,交易对方,商品名称,金额（元）,收/支,交易状态",
    ]
    for m in range(1, 13):
        lines.append(f"2025-{m:02d}-09 08:30:12,哔哩哔哩大会员,连续包月,25.00,支出,交易成功")
    for i in range(40):
        m, d = random.randint(1, 12), random.randint(1, 28)
        lines.append(f"2025-{m:02d}-{d:02d} 12:00:00,盒马鲜生,日用品,{random.uniform(10, 300):.2f},支出,交易成功")
    lines.append("2025-06-15 10:00:00,张三,转账,500.00,收入,交易成功")
    lines.append("2025-07-01 10:00:00,某商店,退货,88.00,支出,退款成功")
    lines.append("------------------------------------------------------------------------------------")
    lines.append("共66笔记录")
    path = os.path.join(HERE, "alipay_gbk.csv")
    with open(path, "w", encoding="gbk") as f:
        f.write("\n".join(lines))
    return path


if __name__ == "__main__":
    print(bank_csv())
    print(alipay_gbk())
