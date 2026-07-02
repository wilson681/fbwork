"""来历 · Origin — 让每个值都能回答「为什么」。

track() 把一个值包起来之后，它参与的每一步运算都会长成一张表达式图。
于是任何结果都可以被审问：

    why(x)                    这个值是怎么一步步算出来的（来历）
    blame(x)                  结果对哪个输入最敏感（归因）
    counterfactual(x, {a: v}) 如果输入 a 是 v，结果会是多少（反事实）

Values wrapped by track() grow an expression graph as they flow through
arithmetic. Any result can then be interrogated: why() renders its causal
tree with source locations, blame() ranks input sensitivity by numeric
perturbation, and counterfactual() re-runs the graph with substituted
inputs. Zero dependencies; this file is the whole library.
"""

from __future__ import annotations

import linecache
import operator
import os
import re
import sys
from collections import namedtuple

__all__ = ["track", "lift", "why", "blame", "counterfactual", "leaves", "V"]

_MARKS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


# ---------------------------------------------------------------- call sites

def _call_site():
    """First stack frame outside this file: (path, lineno, source line)."""
    here = __file__
    f = sys._getframe(1)
    while f is not None and f.f_code.co_filename == here:
        f = f.f_back
    if f is None:
        return None
    path, lineno = f.f_code.co_filename, f.f_lineno
    line = linecache.getline(path, lineno).strip()
    return (path, lineno, line)


def _infer_label(site):
    """Guess a leaf's name from its assignment: `speed = track(3)` → speed."""
    if site and site[2]:
        m = re.match(r"([A-Za-z_]\w*)\s*=[^=]", site[2])
        if m:
            return m.group(1)
    return None


# ------------------------------------------------------------------- the node

class V:
    """A value that remembers where it came from."""

    __slots__ = ("value", "args", "fn", "op", "label", "site")

    def __init__(self, value, *, args=(), fn=None, op=None, label=None, site=None):
        self.value = value
        self.args = args      # parent V nodes, in display order
        self.fn = fn          # callable over raw parent values (for re-eval)
        self.op = op          # display template, e.g. "{} * {}"
        self.label = label    # name, for tracked leaves
        self.site = site      # (path, lineno, source line) or None

    # -- conversions ---------------------------------------------------------
    def __repr__(self):
        return f"V({self.value!r})"

    def __str__(self):
        return str(self.value)

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __bool__(self):
        return bool(self.value)

    def __index__(self):
        return operator.index(self.value)

    # -- comparisons return plain bools (提问用 why，判断用 ==) ---------------
    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        return self.value == (other.value if isinstance(other, V) else other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.value < (other.value if isinstance(other, V) else other)

    def __le__(self, other):
        return self.value <= (other.value if isinstance(other, V) else other)

    def __gt__(self, other):
        return self.value > (other.value if isinstance(other, V) else other)

    def __ge__(self, other):
        return self.value >= (other.value if isinstance(other, V) else other)


def _wrap(x):
    return x if isinstance(x, V) else V(x)


def _binop(fn, fmt, swap=False):
    def method(self, other):
        o = _wrap(other)
        a, b = (o, self) if swap else (self, o)
        return V(fn(a.value, b.value), args=(a, b), fn=fn, op=fmt,
                 site=_call_site())
    return method


def _unop(fn, fmt):
    def method(self):
        return V(fn(self.value), args=(self,), fn=fn, op=fmt,
                 site=_call_site())
    return method


def _radd(self, other):
    # sum() 从 0 开始：省掉无意义的「0 + x」节点
    if type(other) is int and other == 0:
        return self
    return _binop(operator.add, "{} + {}", swap=True)(self, other)


for _name, _fn, _fmt in [
    ("add", operator.add, "{} + {}"),
    ("sub", operator.sub, "{} - {}"),
    ("mul", operator.mul, "{} * {}"),
    ("truediv", operator.truediv, "{} / {}"),
    ("floordiv", operator.floordiv, "{} // {}"),
    ("mod", operator.mod, "{} % {}"),
    ("pow", operator.pow, "{} ** {}"),
]:
    setattr(V, f"__{_name}__", _binop(_fn, _fmt))
    setattr(V, f"__r{_name}__", _binop(_fn, _fmt, swap=True))
V.__radd__ = _radd
V.__neg__ = _unop(operator.neg, "-{}")
V.__abs__ = _unop(operator.abs, "abs({})")


# ------------------------------------------------------------------ tracking

def track(value, label=None):
    """Wrap a value so that everything computed from it remembers why."""
    site = _call_site()
    return V(value, label=label or _infer_label(site), site=site)


def lift(fn, name=None):
    """Make any function provenance-aware: lift(math.hypot)(x, y)."""
    opname = name or getattr(fn, "__name__", "fn")

    def lifted(*args, **kwargs):
        nodes = tuple(_wrap(a) for a in args)
        raw = fn(*(n.value for n in nodes), **kwargs)
        fmt = opname + "(" + ", ".join(["{}"] * len(nodes)) + ")"
        refn = (lambda *vals: fn(*vals, **kwargs)) if kwargs else fn
        return V(raw, args=nodes, fn=refn, op=fmt, site=_call_site())

    lifted.__name__ = f"lifted_{opname}"
    return lifted


# ----------------------------------------------------------------- questions

def leaves(v):
    """Named inputs this value was computed from, in first-use order."""
    out, seen = [], set()

    def walk(n):
        if id(n) in seen:
            return
        seen.add(id(n))
        if not n.args and n.label is not None:
            out.append(n)
        for a in n.args:
            walk(a)

    walk(_require(v))
    return out


def counterfactual(v, replacements):
    """Re-run the computation with some inputs replaced: {leaf: new_value}."""
    subs = {id(k): val for k, val in replacements.items()}
    return _reeval(_require(v), subs, {})


def _reeval(n, subs, memo):
    if id(n) in memo:
        return memo[id(n)]
    if id(n) in subs:
        r = subs[id(n)]
    elif n.fn is None:
        r = n.value
    else:
        r = n.fn(*(_reeval(a, subs, memo) for a in n.args))
    memo[id(n)] = r
    return r


BlameEntry = namedtuple("BlameEntry", "label value delta elasticity leaf")


class Blame(list):
    """blame() 的结果：可迭代，也可直接 print 成表。"""

    rel = 0.01

    def __str__(self):
        if not self:
            return "blame: no numeric tracked inputs found"
        w = max(len(e.label) for e in self)
        lines = [f"blame  (each input nudged by +{self.rel:.0%})"]
        for e in self:
            el = "—" if e.elasticity is None else f"{e.elasticity:+.3g}"
            lines.append(f"  {e.label:<{w}}  {_fmt(e.value):>12}   "
                         f"Δresult {e.delta:+.6g}   elasticity {el}")
        return "\n".join(lines)


def blame(v, rel=0.01):
    """Rank tracked numeric inputs by how much the result moves when each
    is nudged by `rel` (relative). The loudest input comes first."""
    v = _require(v)
    if isinstance(v.value, bool) or not isinstance(v.value, (int, float)):
        raise TypeError("blame() needs a numeric result")
    entries = []
    for leaf in leaves(v):
        x = leaf.value
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            continue
        h = abs(x) * rel or rel
        try:
            new = counterfactual(v, {leaf: x + h})
        except Exception:
            continue
        if isinstance(new, bool) or not isinstance(new, (int, float)):
            continue
        delta = new - v.value
        elast = (delta / v.value) / rel if v.value else None
        entries.append(BlameEntry(leaf.label, x, delta, elast, leaf))
    entries.sort(key=lambda e: abs(e.delta), reverse=True)
    report = Blame(entries)
    report.rel = rel
    return report


def why(v, depth=8):
    """Render the causal tree of a value, with source locations."""
    v = _require(v)
    shared = _shared_nodes(v)
    marks, lines = {}, []

    def line_for(n):
        if n.args:
            expr = n.op.format(*(_fmt(a.value) for a in n.args))
            s = f"{_fmt(n.value)} = {expr}"
        elif n.label is not None:
            s = f"{_fmt(n.value)} ‹{n.label}›"
        else:
            s = _fmt(n.value)
        if n.args and n.site:
            path, ln, code = n.site
            s += f"   ({os.path.basename(path)}:{ln}"
            if code:
                s += f"  {_trunc(code, 64)}"
            s += ")"
        return s

    def walk(n, prefix, tail, d):
        head = prefix + ("└─ " if tail else "├─ ") if prefix or tail is not None else ""
        mark = ""
        if id(n) in shared:
            if id(n) in marks:
                lines.append(f"{head}{_fmt(n.value)}  {marks[id(n)]} (shared)")
                return
            marks[id(n)] = _MARKS[len(marks) % len(_MARKS)]
            mark = f"  {marks[id(n)]}"
        lines.append(head + line_for(n) + mark)
        if not n.args:
            return
        child_prefix = prefix + ("   " if tail else "│  ") if tail is not None else ""
        if d is not None and d <= 1:
            lines.append(child_prefix + "└─ …")
            return
        nd = None if d is None else d - 1
        for i, a in enumerate(n.args):
            walk(a, child_prefix, i == len(n.args) - 1, nd)

    walk(v, "", None, depth)
    return "\n".join(lines)


def _shared_nodes(root):
    """Op-nodes reached along more than one path (rendered once, then ①)."""
    seen, shared = set(), set()

    def walk(n):
        if id(n) in seen:
            if n.args:
                shared.add(id(n))
            return
        seen.add(id(n))
        for a in n.args:
            walk(a)

    walk(root)
    return shared


# ------------------------------------------------------------------- helpers

def _require(v):
    if not isinstance(v, V):
        raise TypeError(f"expected a tracked value (V), got {type(v).__name__};"
                        " wrap inputs with track() first")
    return v


def _fmt(x):
    if isinstance(x, float):
        return f"{x:.6g}"
    if isinstance(x, str):
        return _trunc(repr(x), 27)
    return _trunc(repr(x), 40)


def _trunc(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"
