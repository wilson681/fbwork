"""演示：一张看不懂的账单，三个问题问清楚。运行：python3 demo.py"""

from origin import blame, counterfactual, track, why

# 客户投诉：上个月账单 23.1 元，这个月 70.5 元。为什么翻了三倍？
# 账务系统里只有一个最终数字。但如果计费时用 track() 包住输入——

plan_price = track(30.0, "plan_price")     # 月费
gb_used = track(47, "gb_used")             # 本月用量（上月 22）
free_gb = track(20, "free_gb")             # 免费额度
overage_rate = track(1.5, "overage_rate")  # 超额单价
promo = track(0.0, "promo_discount")       # 促销折扣（本应是 0.3！）

overage = (gb_used - free_gb) * overage_rate
bill = (plan_price + overage) * (1 - promo)

# ——那么这个数字就可以被审问了。

print("本月账单:", bill)
print()
print("── 问题一:这个数是怎么来的? ── why(bill)")
print(why(bill))
print()
print("── 问题二:哪个输入影响最大? ── blame(bill)")
print(blame(bill))
print()
print("── 问题三:如果促销折扣没丢,账单是多少? ── counterfactual")
print(f"  promo=0.3 时: {counterfactual(bill, {promo: 0.3}):.2f}")
print(f"  且用量和上月一样时: {counterfactual(bill, {promo: 0.3, gb_used: 22}):.2f}")
print()
print("结论:用量涨了不假,但真正的事故是 promo_discount 变成了 0。")
