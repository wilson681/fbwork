# 002 · 来历 · Origin

**念头**：调试的本质是问「这个值为什么是这个数」，但程序只记得 *what*，从不记得 *why*。
那就让值随身携带自己的来历——**可疑问的值（interrogable values）**。

Debugging is asking *why is this value what it is* — yet programs only
remember *what*, never *why*. Origin makes values carry their own history,
so any result can be interrogated.

零依赖，单文件（[`origin.py`](origin.py)），纯标准库，Python 3.9+。

## 三个问题 · Three questions

用 `track()` 包住输入，之后所有算出来的值都可以回答三个问题：

```python
from origin import track, why, blame, counterfactual

plan_price   = track(30.0, "plan_price")
gb_used      = track(47, "gb_used")
free_gb      = track(20, "free_gb")
overage_rate = track(1.5, "overage_rate")
promo        = track(0.0, "promo_discount")   # 本应是 0.3！

overage = (gb_used - free_gb) * overage_rate
bill = (plan_price + overage) * (1 - promo)
```

**问题一：这个数是怎么来的？** — `why(bill)` 打印带源码位置的因果树：

```
70.5 = 70.5 * 1   (demo.py:15  bill = (plan_price + overage) * (1 - promo))
├─ 70.5 = 30 + 40.5   (demo.py:15  bill = (plan_price + overage) * (1 - promo))
│  ├─ 30 ‹plan_price›
│  └─ 40.5 = 27 * 1.5   (demo.py:14  overage = (gb_used - free_gb) * overage_rate)
│     ├─ 27 = 47 - 20   (demo.py:14  overage = (gb_used - free_gb) * overage_rate)
│     │  ├─ 47 ‹gb_used›
│     │  └─ 20 ‹free_gb›
│     └─ 1.5 ‹overage_rate›
└─ 1 = 1 - 0   (demo.py:15  bill = (plan_price + overage) * (1 - promo))
   ├─ 1
   └─ 0 ‹promo_discount›
```

**问题二：哪个输入影响最大？** — `blame(bill)` 把每个输入各推 1%，按结果的震动排序：

```
blame  (each input nudged by +1%)
  gb_used                   47   Δresult +0.705   elasticity +1
  promo_discount             0   Δresult -0.705   elasticity -1
  overage_rate             1.5   Δresult +0.405   elasticity +0.574
  ...
```

**问题三：如果输入不一样，结果会是多少？** — `counterfactual` 在同一张图上重演：

```python
counterfactual(bill, {promo: 0.3})                 # → 49.35
counterfactual(bill, {promo: 0.3, gb_used: 22})    # → 23.10（上个月的账单）
```

完整故事见 [`demo.py`](demo.py)：`python3 demo.py`。

## API

| 函数 | 作用 |
|------|------|
| `track(value, label=None)` | 包住一个输入。不给 `label` 时自动从赋值语句推断变量名 |
| `why(v, depth=8)` | 返回因果树字符串；`depth=None` 展开全部；共享子式只展开一次，其余标 ① |
| `blame(v, rel=0.01)` | 每个数值输入相对推动 `rel`，按 `|Δresult|` 排序；可迭代也可直接 print |
| `counterfactual(v, {leaf: new})` | 替换若干输入后重演整张图，返回裸值（原图不动） |
| `leaves(v)` | 这个值依赖的所有具名输入，按首次使用顺序 |
| `lift(fn)` | 让任意函数带上来历：`lift(math.hypot)(x, y)` |

## 原理 · How it works

- **表达式图**：运算符重载让每次运算生成一个节点，记下父节点、可重演的函数、显示模板。
- **源码位置**：运算发生时向上走栈帧，取第一个库外帧的 `文件:行号`，用 `linecache` 取出那行源码。叶子的名字从 `speed = track(9)` 这样的赋值行里正则推断。
- **归因**：有限差分——把每个叶子推动 1% 后在图上重演（备忘录化，共享子式只算一次），看结果动多少。值为 0 的叶子改为绝对推动 `rel`。
- **反事实**：同一次重演机制，替换任意叶子。

## 相关思想 · Honest lineage

单独看，每个机制都有先例：autograd 用精确梯度做敏感度（为了训练，不为了调试）、
Spark 等数据系统有 lineage（表级，不到值级）、污点分析追踪数据流（为了安全）、
研究界有过 Whyline（问 why 的调试器，重量级）。
这里的组合才是念头本身：**把「值的可疑问性」做成日常调试原语**——
why / blame / counterfactual 三问一体，一个文件，随手可用。

## 边界 · Limitations

- 只看**数据流**：`if` 选了哪个分支不入图，来历只跟着被选中的那个值走。
- `and` / `or` 无法重载（Python 限制）；比较运算返回裸 `bool`（判断用 `==`，提问用 `why`）。
- 容器和任意函数走 `lift()`；每次运算都建节点，适合调试场景，别放进热循环。
- `blame` 是局部敏感度（有限差分），不是全局归因。

## 测试 · Tests

```
python3 -m unittest test_origin -v    # 20 tests
```
