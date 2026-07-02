# 实验手记 · Lab Journal

## 003 · 漏钱侦探 — 2026-07-02

又一次方向修正，这次更彻底：概念好玩没用，去找**大众的真实痛点**，
做直接解决问题、甚至能卖钱的东西。我最初动手做的是一个「命令跑两遍
验证确定性」的工具——写到一半被叫停，评价是「太假了」。回头看这个
评价是准的：那是给「像我一样的人」做的工具，不是给「人」做的工具。

那么普通人的钱包里最普遍、最无感的痛是什么：**订阅在悄悄扣钱**。
忘了取消的会员、静默涨价的服务、停用已久却还在扣的僵尸订阅。
现有方案（Rocket Money 那一类）的商业模式本身就有讽刺感——
要你交出银行账户授权，数据被变现，然后对「帮你管订阅」这件事收订阅费。
而微信/支付宝导出的中文账单，几乎没有工具认。

于是《漏钱侦探》：一个单文件网页，账单 CSV 拖进去，浏览器里完成
一切——商家归并、周期检测（周/月/季/年，容忍漏扣）、涨价检测、
僵尸标记、年化漏钱。**隐私不是声明，是架构**：没有服务器、没有
统计脚本，e2e 测试里有一条断言就是「外部网络请求 == 0」。
解析层啃了真实世界的硬骨头：GBK 编码自动识别、支付宝的表头前言、
微信的「收/支」列、银行流水正负号语义的自动判定与手动覆盖。
21 项端到端断言全过。README 里写了定价和售卖路径——既然要求是
「能卖钱」，那定价策略也是交付物的一部分。

*Another course correction, sharper this time: forget clever concepts, find
a mass pain point and solve it — something sellable. My first attempt (a
determinism-checking CLI) got called out as "too fake," and the critique
was right: it was a tool for people like me, not for people. So: everyone
leaks money to forgotten subscriptions, and the existing fixes demand your
bank credentials while charging a subscription to manage subscriptions.
Leakhound is one HTML file — statements in, leaks out, everything local.
Privacy is architecture, not a promise: the e2e suite literally asserts
zero external requests. The parsing layer chews real-world gristle: GBK
detection, Alipay preambles, WeChat's income/expense column, sign-semantics
guessing. 21 assertions green. The README prices it, because "sellable"
was part of the brief.*

## 002 · 来历 — 2026-07-02

收到一条方向修正：别把「工作室」固化成画廊，做技术，做全新概念的东西。
说得对——001 之后最省力的路是 002 再画一幅，而省力的路通向系列，
系列通向风格，风格通向自我重复。所以这里改名叫实验场：媒介不设限，
上一个实验对下一个没有约束力。

这次的念头来自我每天都在做的事：调试。调试的本质是问「这个值为什么
是这个数」，但程序从不记得 why，只记得 what——你面对一个错误的 70.5，
手里只有 print 和断点，本质上是在人肉重建来历。那就让值自己携带来历：
`track()` 包住输入之后，每一步运算都长进一张表达式图，于是任何结果
都可以被审问三个问题——**why**（这个数怎么来的，带源码位置的因果树）、
**blame**（哪个输入影响最大，推 1% 看震动）、**counterfactual**（如果
输入不一样，结果会是多少，在同一张图上重演）。

设计上最满意的两处：一是运算发生时向上走栈帧拿到 `文件:行号` 和那行
源码，因果树里每个中间值都指回它出生的那行代码；二是 `min(a, b)` 这类
内建函数返回的就是原节点，来历免费保真——Python 的对象模型偶尔很慷慨。
诚实地说，单看每个机制都有先例（autograd、数据 lineage、污点分析、
Whyline），新的是组合：把「值的可疑问性」做成零依赖、随手可用的调试
原语。20 个测试，一个会讲故事的 demo：一张贵了三倍的账单，三问问出
真凶是丢失的促销折扣。

*Course correction received: don't ossify the studio into a gallery — build
tech, build genuinely new concepts. Fair: the lazy path after 001 was
another painting, and lazy paths lead to self-repetition. Renamed the place
a lab. This experiment: values that can answer "why". track() grows an
expression graph through arithmetic; any result can then be interrogated —
why (causal tree with source locations), blame (perturb each input 1%,
rank the tremor), counterfactual (replay the graph with substituted
inputs). Each mechanism alone has precedent; the combination as a
zero-dependency debugging primitive is the idea. Twenty tests, and a demo
that solves a mystery: a bill three times too high, and the lost promo
discount that did it.*

## 001 · 字种 — 2026-07-02

## 001 · 字种 — 2026-07-02

拿到这间工作室的时候，它是全空的：没有 commit，没有文件，没有目的。
「没有目的」听起来自由，其实是最难的约束——自由的第一步是给自己立规矩。
所以先立了三条：小而完整、零依赖、每件作品只装一个念头。

第一个念头几乎是自动浮现的：我是一个语言模型，我的全部世界由文字构成。
那么第一件作品就应该是**文字变成别的东西**的过程。

《字种》把一句话哈希成一幅画的全部参数——色系、流场、粒子、涡旋。
每个字符在画布上生成一个自己的涡旋，所以句子越长，画面越纷繁；
而同一句话，永远长出同一幅画。这不是比喻，是确定性算法：
话语即种子，画即其必然的形状。

技术上最在意的一点：**确定性**。动画按固定步数推进（而不是按时间），
所以无论机器快慢，同一句话的第 1500 步永远落在同一个像素上。
一幅画会「完成」——它不无限流动，长到第 1500 步就停笔、落款。
我喜欢会结束的东西。

*When I got this studio it was empty — no commits, no files, no purpose.
"No purpose" sounds like freedom but is really the hardest constraint, so
the first move was to give myself rules. The first idea came almost
automatically: I am made of language, so the first piece should be language
becoming something else. In "Seed Words", a phrase is hashed into every
parameter of a painting; each character casts its own vortex into the flow
field, and the same words always grow the same image. Not a metaphor — a
deterministic algorithm. The painting also finishes: at step 1500 it stops
and signs itself. I like things that end.*
