"""origin.py 的测试。运行：python3 -m unittest test_origin -v"""

import math
import unittest

from origin import V, blame, counterfactual, leaves, lift, track, why


class TestArithmetic(unittest.TestCase):
    def test_passthrough(self):
        a = track(2)
        self.assertEqual((a + 3).value, 5)
        self.assertEqual((3 + a).value, 5)
        self.assertEqual(((a + 3) * 4 - 1).value, 19)
        self.assertEqual((10 - a).value, 8)
        self.assertEqual((a ** 3).value, 8)
        self.assertEqual((7 // a).value, 3)
        self.assertEqual((7 % a).value, 1)
        self.assertEqual((-a).value, -2)
        self.assertEqual(abs(track(-4)).value, 4)
        self.assertAlmostEqual((1 / a).value, 0.5)

    def test_conversions_and_comparisons(self):
        a = track(2.5)
        self.assertEqual(float(a), 2.5)
        self.assertEqual(int(a), 2)
        self.assertTrue(a > 2)
        self.assertTrue(a == 2.5)
        self.assertTrue(track(1) < track(2))
        self.assertTrue(bool(track(1)))
        self.assertFalse(bool(track(0)))

    def test_strings_concat(self):
        s = track("he", "greeting") + "llo"
        self.assertEqual(s.value, "hello")

    def test_min_max_keep_provenance(self):
        a, b = track(1, "a"), track(2, "b")
        self.assertIs(min(a, b), a)
        self.assertIs(max(a, b), b)

    def test_sum_elides_zero_seed(self):
        items = [track(1, "x"), track(2, "y"), track(3, "z")]
        total = sum(items)
        self.assertEqual(total.value, 6)
        self.assertEqual([l.label for l in leaves(total)], ["x", "y", "z"])


class TestGraph(unittest.TestCase):
    def test_parents_and_order(self):
        a, b = track(2, "a"), track(3, "b")
        c = a + b
        self.assertEqual(c.args, (a, b))
        r = 10 - a  # reflected op: constant appears on the left
        self.assertEqual(r.args[0].value, 10)
        self.assertIs(r.args[1], a)

    def test_label_inference_from_assignment(self):
        speed = track(9)
        self.assertEqual(speed.label, "speed")

    def test_leaves_order_and_dedup(self):
        a, b = track(1, "a"), track(2, "b")
        v = (a + b) * a
        self.assertEqual([l.label for l in leaves(v)], ["a", "b"])


class TestWhy(unittest.TestCase):
    def test_tree_contains_labels_ops_and_site(self):
        price = track(19.99, "price")
        qty = track(3, "qty")
        total = price * qty
        text = why(total)
        self.assertIn("59.97 = 19.99 * 3", text)
        self.assertIn("‹price›", text)
        self.assertIn("‹qty›", text)
        self.assertIn("test_origin.py:", text)

    def test_shared_subexpression_marked_once(self):
        a, b = track(2, "a"), track(3, "b")
        s = a + b
        t = s * s
        text = why(t)
        self.assertEqual(text.count("①"), 2)       # 一次标记，一次引用
        self.assertEqual(text.count("= 2 + 3"), 1)  # 只展开一遍
        self.assertIn("(shared)", text)

    def test_depth_truncation(self):
        v = track(1, "v")
        for _ in range(10):
            v = v + 1
        self.assertIn("…", why(v, depth=2))
        self.assertNotIn("…", why(v, depth=None))

    def test_requires_tracked_value(self):
        with self.assertRaises(TypeError):
            why(42)


class TestCounterfactual(unittest.TestCase):
    def test_substitute_one_leaf(self):
        price = track(30.0, "price")
        promo = track(0.0, "promo")
        bill = price * (1 - promo)
        self.assertAlmostEqual(counterfactual(bill, {promo: 0.5}), 15.0)
        self.assertAlmostEqual(bill.value, 30.0)  # 原值不动

    def test_substitute_many(self):
        a, b = track(2, "a"), track(3, "b")
        v = a * 10 + b
        self.assertEqual(counterfactual(v, {a: 5, b: 7}), 57)

    def test_shared_node_reevaluated_once(self):
        calls = []

        def spy(x):
            calls.append(x)
            return x * 2

        a = track(4, "a")
        d = lift(spy)(a)
        v = d + d
        self.assertEqual(counterfactual(v, {a: 5}), 20)
        self.assertEqual(calls, [4, 5])  # 一次原始求值 + 一次重演


class TestBlame(unittest.TestCase):
    def test_ranking(self):
        price = track(100.0, "price")
        qty = track(2, "qty")
        fee = track(1.0, "fee")
        total = price * qty + fee
        report = blame(total)
        self.assertEqual({e.label for e in report[:2]}, {"price", "qty"})
        self.assertEqual(report[-1].label, "fee")
        self.assertAlmostEqual(report[0].delta, 2.0)
        self.assertAlmostEqual(report[0].elasticity, 0.995, places=2)

    def test_table_renders(self):
        a = track(3.0, "a")
        text = str(blame(a * 2))
        self.assertIn("blame", text)
        self.assertIn("a", text)

    def test_needs_numeric(self):
        with self.assertRaises(TypeError):
            blame(track("hi", "s") + "!")


class TestLift(unittest.TestCase):
    def test_lift_stdlib_function(self):
        x, y = track(3.0, "x"), track(4.0, "y")
        r = lift(math.hypot)(x, y)
        self.assertEqual(r.value, 5.0)
        self.assertIn("hypot(3, 4)", why(r))
        self.assertAlmostEqual(counterfactual(r, {y: 0.0}), 3.0)

    def test_lift_with_kwargs(self):
        r = lift(round)(track(3.14159, "pi"), ndigits=2)
        self.assertEqual(r.value, 3.14)
        self.assertEqual(counterfactual(r, {leaves(r)[0]: 2.71828}), 2.72)


if __name__ == "__main__":
    unittest.main()
