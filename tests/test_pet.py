"""mcd-pet 测试套件。"""

from __future__ import annotations

import os
import random
import tempfile
import unittest

from mcd_pet import faces, foods
from mcd_pet.pet import Pet, status_card, stats_block
from mcd_pet.cli import main


def feed(p: Pet, name: str, rng: random.Random | None = None):
    f = foods.get(name)
    assert f is not None, f"饲料库里找不到「{name}」"
    return p.feed(name, f, rng)


class TestFoods(unittest.TestCase):
    def test_library_is_real_and_nonempty(self):
        fs = foods.load()
        self.assertGreater(len(fs), 100)
        for name, f in list(fs.items())[:20]:
            self.assertIn("kcal", f)
            self.assertIn("sodium", f)

    def test_fuzzy_match_picks_shortest(self):
        """真实餐品名带规格后缀（麦乐鸡5块），简写必须能命中。"""
        for kw in ("麦乐鸡", "巨无霸", "薯条", "可乐", "麦旋风"):
            hit = foods.get(kw)
            self.assertIsNotNone(hit, f"简写「{kw}」没匹配上")
            self.assertIn(kw, hit["name"])

    def test_unknown_food_returns_none(self):
        self.assertIsNone(foods.get("不存在的汉堡"))


class TestPet(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(7)

    def test_adopt_initial_state(self):
        p = Pet.adopt("测试猫")
        self.assertEqual(p.name, "测试猫")
        self.assertTrue(p.alive)
        self.assertEqual(p.health, 100.0)
        self.assertEqual(p.form, "小猫猫")

    def test_feed_increases_weight_and_satiety(self):
        p = Pet.adopt("a")
        w0, s0 = p.weight_g, p.satiety
        feed(p, "巨无霸", self.rng)
        self.assertGreater(p.weight_g, w0)
        self.assertGreater(p.satiety, s0)
        self.assertEqual(p.age, 1)

    def test_weight_gain_uses_real_kcal_to_fat_conversion(self):
        """7700 kcal ≈ 1 kg 脂肪，超出基础代谢的部分才囤。"""
        p = Pet.adopt("a")
        f = foods.get("巨无霸")
        surplus = f["kcal"] - 200.0 / 3.0
        expected = surplus / 7700.0 * 1000.0
        w0 = p.weight_g
        feed(p, "巨无霸", self.rng)
        self.assertAlmostEqual(p.weight_g - w0, expected, places=6)

    def test_repeat_feeding_lowers_mood(self):
        p = Pet.adopt("a")
        for _ in range(4):
            feed(p, "麦乐鸡", self.rng)
        self.assertLess(p.mood, 70.0)          # 初始 70
        self.assertEqual(p.eaten.get("鸡"), 4)

    def test_evolve_to_mcnugget_hero(self):
        p = Pet.adopt("a")
        for _ in range(8):
            feed(p, "麦乐鸡", self.rng)
            if not p.alive:
                break
        self.assertEqual(p.form, "麦乐鸡侠")

    def test_sodium_overflow_gives_hypertension(self):
        p = Pet.adopt("a")
        p.total["sodium"] = 8500.0
        self.assertEqual(p._evolve(self.rng), "高血压猫")

    def test_death_sets_cause_and_dead(self):
        p = Pet.adopt("a")
        p.health = 1.0
        p.total["sodium"] = 9000.0
        feed(p, "巨无霸", self.rng)
        self.assertFalse(p.alive)
        self.assertEqual(p.cause, "钠中毒")
        self.assertEqual(p.form, "天使猫")

    def test_starve_to_death(self):
        p = Pet.adopt("a")
        for _ in range(30):
            p.wait(1)
            if not p.alive:
                break
        self.assertFalse(p.alive)
        self.assertEqual(p.cause, "饿死")

    def test_cannot_feed_after_death(self):
        p = Pet.adopt("a")
        p.alive = False
        self.assertIn("已经不在了", feed(p, "麦乐鸡", self.rng))

    def test_save_and_load_roundtrip(self):
        p = Pet.adopt("存档猫")
        feed(p, "巨无霸", self.rng)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pet.json")
            p.save(path)
            q = Pet.load(path)
        self.assertEqual(q.name, "存档猫")
        self.assertEqual(q.age, p.age)
        self.assertAlmostEqual(q.weight_g, p.weight_g, places=6)
        self.assertEqual(q.form, p.form)


class TestFaces(unittest.TestCase):
    def test_all_forms_have_art_and_desc(self):
        for name, info in faces.FORMS.items():
            self.assertTrue(info["art"], name)
            self.assertTrue(info["desc"], name)

    def test_card_lines_are_same_display_width(self):
        """卡片每行显示宽度必须一致，否则边框会歪。"""
        for form in faces.FORMS:
            c = faces.card("麦麦", form, "开心", 3200.0, 100, 70, 60, 1,
                           rng=random.Random(1))
            widths = {faces._w(line) for line in c.splitlines()}
            self.assertEqual(len(widths), 1, f"「{form}」卡片宽度不一致：{widths}")

    def test_grave_card_lines_are_same_display_width(self):
        for form in faces.FORMS:
            c = faces.grave_card("麦麦", form, "钠中毒", 20, rng=random.Random(1))
            widths = {faces._w(line) for line in c.splitlines()}
            self.assertEqual(len(widths), 1, f"「{form}」墓碑宽度不一致：{widths}")

    def test_halfwidth_kana_counts_as_one_column(self):
        # ･ 是半角片假名（U+FF65），终端只占 1 格，不能按全角算
        self.assertEqual(faces._w("･"), 1)
        self.assertEqual(faces._w("麦"), 2)

    def test_epitaph_formats(self):
        s = faces.epitaph_of("钠中毒", sodium=8920.0)
        self.assertIn("8920", s)


class TestCLI(unittest.TestCase):
    def test_help_runs(self):
        self.assertEqual(main([]), 0)

    def test_adopt_then_feed_then_status(self):
        with tempfile.TemporaryDirectory() as d:
            save = os.path.join(d, "p.json")
            self.assertEqual(main(["adopt", "小白", "--save", save]), 0)
            self.assertEqual(main(["feed", "麦乐鸡", "--save", save]), 0)
            self.assertEqual(main(["status", "--save", save]), 0)
            self.assertTrue(os.path.exists(save))

    def test_feed_unknown_food_fails_gracefully(self):
        with tempfile.TemporaryDirectory() as d:
            save = os.path.join(d, "p.json")
            main(["adopt", "小白", "--save", save])
            self.assertEqual(main(["feed", "佛跳墙", "--save", save]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
