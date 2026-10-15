"""宠物状态机。

所有数值都由麦当劳 MCP 返回的真实营养数据驱动：
  热量 -> 体重（7700 kcal ≈ 1 kg 脂肪，猫也一样）
  脂肪 -> 脂肪肝风险
  钠   -> 高血压 / 肾脏负担
  碳水 -> 心情（糖分快乐）与蛀牙
  蛋白质/钙 -> 健康加成
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import faces
from . import foods as foods_mod

# 一只 3 kg 的猫，每回合大约需要的热量
DAILY_KCAL = 200.0
# 7700 kcal 折合 1 kg 脂肪
KCAL_PER_KG_FAT = 7700.0

NAMES = ["麦麦", "薯条", "咕咕", "鸡块", "圆筒", "芝士", "阿派", "可乐", "板烧", "鱼鱼"]


@dataclass
class Pet:
    name: str
    weight_g: float = 3200.0
    satiety: float = 60.0      # 饱食度 0-100
    mood: float = 70.0         # 心情 0-100
    health: float = 100.0      # 健康 0-100
    age: int = 0               # 经历回合数
    form: str = "小猫猫"
    alive: bool = True
    cause: str = ""
    last_food: str = ""
    last_cat: str = ""
    total: Dict[str, float] = field(default_factory=lambda: {
        "kcal": 0.0, "fat": 0.0, "sodium": 0.0, "carb": 0.0,
        "protein": 0.0, "calcium": 0.0, "meals": 0.0,
    })
    eaten: Dict[str, int] = field(default_factory=dict)   # 类别 -> 次数
    history: List[str] = field(default_factory=list)

    # ------------------------------------------------------------ 派生指标

    @property
    def bmi_note(self) -> str:
        kg = self.weight_g / 1000
        if kg < 3.0:
            return "偏瘦"
        if kg < 5.0:
            return "标准"
        if kg < 7.0:
            return "超重"
        if kg < 10.0:
            return "肥胖"
        return "移动的猪"

    @property
    def bigmac_equiv(self) -> float:
        """体重折合多少个巨无霸的热量（按累计摄入算）。"""
        return self.total["kcal"] / 513.0

    def state(self) -> str:
        if not self.alive:
            return "死"
        if self.health < 25:
            return "危险"
        if self.satiety < 20:
            return "饿"
        if self.satiety > 95:
            return "撑"
        if self.mood < 30:
            return "腻"
        return "开心"

    # ------------------------------------------------------------ 行为

    def feed(self, food_name: str, food: dict, rng: random.Random | None = None) -> str:
        """喂一次，返回这次发生了什么（一句话）。"""
        if not self.alive:
            return f"{self.name} 已经不在了。你还要喂？"

        r = rng or random.Random()
        self.age += 1
        self.total["meals"] += 1
        self.last_food = food_name
        cat = food.get("cat", "其他")
        self.last_cat = cat
        self.eaten[cat] = self.eaten.get(cat, 0) + 1

        kcal = float(food.get("kcal", 0))
        fat = float(food.get("fat", 0))
        sodium = float(food.get("sodium", 0))
        carb = float(food.get("carb", 0))
        protein = float(food.get("protein", 0))
        calcium = float(food.get("calcium", 0))

        for k, v in (("kcal", kcal), ("fat", fat), ("sodium", sodium),
                     ("carb", carb), ("protein", protein), ("calcium", calcium)):
            self.total[k] += v

        # 体重：超出本回合基础代谢的部分才囤成脂肪
        surplus = max(kcal - DAILY_KCAL / 3.0, 0.0)
        gain = surplus / KCAL_PER_KG_FAT * 1000.0
        self.weight_g += gain

        # 饱食度：按占每日需求的比例加
        self.satiety = min(100.0, self.satiety + kcal / DAILY_KCAL * 45.0)

        # 心情：糖分快乐，但重复投喂会腻
        same = self.eaten.get(cat, 0)
        if same >= 3:
            self.mood -= 6.0
            mood_note = "（吃腻了）"
        else:
            self.mood += min(carb * 0.15, 12.0)
            mood_note = ""
        self.mood = max(0.0, min(100.0, self.mood))

        # 健康：脂肪和钠扣分，蛋白质和钙加分，撑着也扣分
        was_full = self.satiety >= 100.0          # 喂之前就已经撑了
        delta = 0.0
        delta -= fat * 0.06
        delta -= sodium * 0.0016
        delta += protein * 0.05
        delta += calcium * 0.004
        if self.satiety > 95:
            delta -= (self.satiety - 95) * 0.5
        if was_full:
            delta -= 2.0                          # 硬塞，它已经开始不配合了
        self.health = max(0.0, min(100.0, self.health + delta))

        self.history.append(f"第{self.age}回合 喂了「{food_name}」")

        # 形态与生死判定
        prev_form = self.form
        self.form = self._evolve(r)

        if self.health <= 0:
            self.alive = False
            self.cause = self._cause()
            self.form = "天使猫"
            return f"{self.name} 吃了「{food_name}」之后，倒下了。死因：{self.cause}"

        msg = (f"{self.name} 吃掉了「{food_name}」"
               f"（{kcal:.0f} kcal / 脂肪 {fat:.0f}g / 钠 {sodium:.0f}mg）")
        if gain > 0:
            msg += f"，胖了 {gain:.1f} g"
        if mood_note:
            msg += f" {mood_note}"
        if self.form != prev_form:
            msg += f"\n  ✨ 进化：{prev_form} → {self.form}！{faces.desc_of(self.form)}"
        return msg

    def wait(self, rounds: int = 1) -> str:
        """不喂，让它饿着等。"""
        if not self.alive:
            return f"{self.name} 已经不在了。"
        notes = []
        for _ in range(rounds):
            self.age += 1
            self.satiety = max(0.0, self.satiety - 22.0)
            self.mood = max(0.0, self.mood - 8.0)
            if self.satiety <= 0:
                self.health = max(0.0, self.health - 12.0)
            # 饿着也会瘦
            self.weight_g = max(1500.0, self.weight_g - 25.0)
            notes.append(f"第{self.age}回合：饱食度降到 {self.satiety:.0f}")
            if self.health <= 0:
                self.alive = False
                self.cause = "饿死"
                self.form = "天使猫"
                notes.append(f"{self.name} 饿死了。")
                break
        return "\n".join(notes)

    # ------------------------------------------------------------ 判定

    def _evolve(self, rng: random.Random) -> str:
        e = self.eaten
        kg = self.weight_g / 1000
        kinds = len([c for c, n in e.items() if n > 0])

        # 究极形态：活得久、吃得杂、还健康
        if self.age >= 12 and kinds >= 4 and self.health >= 80 and kg < 6.5:
            return "麦门圣猫"
        # 钠爆表（放到食物系形态之后，否则一上来就锁死成高血压猫）
        if self.total["sodium"] >= 8000:
            return "高血压猫"
        if e.get("鸡", 0) >= 8:
            return "麦乐鸡侠"
        if e.get("薯条", 0) >= 8:
            return "薯条精"
        if e.get("甜品", 0) >= 8:
            return "糖分恶魔"
        if e.get("牛肉", 0) >= 6:
            return "巨无霸兽"
        if e.get("饮料", 0) >= 12:
            return "可乐喷泉"
        if e.get("沙拉", 0) >= 5 and kg < 5.0:
            return "健康猫"
        if kg >= 6.5:
            return "橘座"
        return "小猫猫"

    def _cause(self) -> str:
        # 优先报「有数据支撑」的死因，撑死留作兜底——
        # 毕竟「它吃了 8920 mg 钠」比「它吃多了」更有说服力。
        if self.total["sodium"] >= 8000:
            return "钠中毒"
        if self.total["fat"] >= 300:
            return "脂肪肝"
        if self.satiety > 95:
            return "撑死"
        if self.satiety <= 0:
            return "饿死"
        return "过劳"

    # ------------------------------------------------------------ 存档

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)

    def to_dict(self) -> dict:
        return {
            "name": self.name, "weight_g": self.weight_g, "satiety": self.satiety,
            "mood": self.mood, "health": self.health, "age": self.age,
            "form": self.form, "alive": self.alive, "cause": self.cause,
            "last_food": self.last_food, "last_cat": self.last_cat,
            "total": self.total, "eaten": self.eaten, "history": self.history,
        }

    @classmethod
    def load(cls, path: str) -> "Pet":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        p = cls(name=d["name"])
        for k, v in d.items():
            setattr(p, k, v)
        return p

    @classmethod
    def adopt(cls, name: str = "") -> "Pet":
        r = random.Random()
        return cls(name=name or r.choice(NAMES))


# ---------------------------------------------------------------- 展示

def status_card(pet: Pet, rng: random.Random | None = None) -> str:
    return faces.card(
        name=pet.name, form=pet.form, state=pet.state(),
        weight_g=pet.weight_g, health=pet.health, mood=pet.mood,
        satiety=pet.satiety, age=pet.age, rng=rng,
    )


def death_card(pet: Pet, rng: random.Random | None = None) -> str:
    return faces.grave_card(pet.name, pet.form, pet.cause, pet.age, rng) + "\n\n  " + \
        faces.epitaph_of(pet.cause, sodium=pet.total["sodium"], fat=pet.total["fat"],
                         last=pet.last_food, age=pet.age)


def stats_block(pet: Pet) -> str:
    t = pet.total
    return "\n".join([
        f"  累计摄入    {t['kcal']:.0f} kcal（≈ {pet.bigmac_equiv:.2f} 个巨无霸）",
        f"  脂肪 {t['fat']:.0f} g    钠 {t['sodium']:.0f} mg    碳水 {t['carb']:.0f} g",
        f"  蛋白质 {t['protein']:.0f} g    钙 {t['calcium']:.0f} mg",
        f"  投喂次数 {int(t['meals'])}    体重评价：{pet.bmi_note}",
    ])


def recommend(pet: Pet, n: int = 3) -> List[Tuple[str, str]]:
    """按当前状态推荐该喂什么（纯数据驱动的建议）。"""
    fs = foods_mod.load()
    scored = []
    for name, f in fs.items():
        score = 0.0
        if pet.health < 50:
            score += f.get("protein", 0) * 2 + f.get("calcium", 0) * 0.2
            score -= f.get("sodium", 0) * 0.02 + f.get("fat", 0) * 1.5
        else:
            score += f.get("protein", 0) - f.get("fat", 0) * 0.8
            score -= f.get("sodium", 0) * 0.005
        if pet.satiety > 80:
            score -= f.get("kcal", 0) * 0.02
        if pet.satiety < 30:
            score += f.get("kcal", 0) * 0.01
        scored.append((score, name))
    scored.sort(reverse=True)
    out = []
    for _, name in scored[:n]:
        f = fs[name]
        out.append((name, f"{f['kcal']:.0f} kcal / 蛋白 {f['protein']:.0f}g / 钠 {f['sodium']:.0f}mg"))
    return out
