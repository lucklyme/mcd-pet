"""mcd_pet 命令行：领养 / 喂食 / 看状态 / 等死。"""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import List, Optional

from . import faces, foods as foods_mod
from . import pet as pet_mod

SAVE = ".mcdpet.json"


def _out(s: str = "") -> None:
    sys.stdout.write(s + "\n")


def _lp(s: str, width: int) -> str:
    """按终端显示宽度左对齐填充（中文占 2 格）。"""
    w = faces._w(s)
    return s + " " * max(width - w, 1)


def _load_pet(save: str) -> pet_mod.Pet:
    if os.path.exists(save):
        return pet_mod.Pet.load(save)
    return None  # type: ignore


def cmd_adopt(args) -> int:
    p = pet_mod.Pet.adopt(args.name)
    p.save(args.save)
    _out()
    _out(f"  你领养了一只猫，它叫「{p.name}」。")
    _out(f"  初始体重 {p.weight_g/1000:.2f} kg，它现在还不知道自己即将面对什么。")
    _out()
    _out(pet_mod.status_card(p))
    _out()
    _out(f"  存档：{args.save}")
    _out("  下一步：python -m mcd_pet feed 麦乐鸡")
    _out()
    return 0


def cmd_feed(args) -> int:
    p = _load_pet(args.save)
    if p is None:
        _out("  还没有猫。先执行：python -m mcd_pet adopt")
        return 1
    f = foods_mod.get(args.food)
    if f is None:
        hits = foods_mod.search(args.food, limit=8)
        _out(f"  饲料库里没有「{args.food}」。")
        if hits:
            _out("  你是不是想找：")
            for h in hits:
                _out(f"    - {h}")
        else:
            _out("  试试：python -m mcd_pet list")
        return 1

    _out()
    _out("  " + p.feed(args.food, f))
    _out()
    _out(pet_mod.status_card(p))
    _out()
    _out(pet_mod.stats_block(p))
    if not p.alive:
        _out()
        _out(pet_mod.death_card(p))
    p.save(args.save)
    _out()
    return 0


def cmd_status(args) -> int:
    p = _load_pet(args.save)
    if p is None:
        _out("  还没有猫。先执行：python -m mcd_pet adopt")
        return 1
    _out()
    _out(pet_mod.status_card(p))
    _out()
    _out(pet_mod.stats_block(p))
    if not p.alive:
        _out()
        _out(pet_mod.death_card(p))
    _out()
    return 0


def cmd_wait(args) -> int:
    p = _load_pet(args.save)
    if p is None:
        _out("  还没有猫。先执行：python -m mcd_pet adopt")
        return 1
    _out()
    _out("  " + p.wait(args.rounds))
    _out()
    _out(pet_mod.status_card(p))
    if not p.alive:
        _out()
        _out(pet_mod.death_card(p))
    p.save(args.save)
    _out()
    return 0


def cmd_list(args) -> int:
    _out()
    _out(f"  饲料库：{foods_mod.source_label()}")
    _out()
    if args.keyword:
        names = foods_mod.search(args.keyword, limit=args.limit)
        title = f"  包含「{args.keyword}」的餐品（{len(names)} 个）"
    elif args.cat:
        names = foods_mod.by_cat(args.cat)
        title = f"  类别「{args.cat}」（{len(names)} 个）"
    else:
        names = sorted(foods_mod.load().keys())
        title = f"  全部 {len(names)} 个餐品"
    _out(title)
    _out("  " + "-" * 62)
    fs = foods_mod.load()
    for n in names[: args.limit if not args.cat else len(names)]:
        f = fs[n]
        _out(f"    {_lp(n, 26)} {f['kcal']:>5.0f}kcal  蛋白{f['protein']:>4.0f}g  "
             f"脂肪{f['fat']:>4.0f}g  钠{f['sodium']:>5.0f}mg  [{f.get('cat','')}]")
    _out()
    return 0


def cmd_cats(args) -> int:
    _out()
    _out("  饲料类别：")
    for c in foods_mod.cats():
        _out(f"    {c:<6} {len(foods_mod.by_cat(c))} 种")
    _out()
    _out("  用法：python -m mcd_pet list --cat 甜品")
    _out()
    return 0


def cmd_forms(args) -> int:
    _out()
    _out("  全部形态（共 %d 种）：" % len(faces.FORMS))
    _out()
    for name, info in faces.FORMS.items():
        _out(f"  【{name}】{info['desc']}")
        for a in info["art"]:
            _out("    " + a)
        _out()
    return 0


def cmd_recommend(args) -> int:
    p = _load_pet(args.save)
    if p is None:
        _out("  还没有猫。先执行：python -m mcd_pet adopt")
        return 1
    _out()
    _out(f"  按「{p.name}」当前状态（健康 {p.health:.0f} / 饱食 {p.satiety:.0f}）推荐：")
    _out()
    for i, (name, desc) in enumerate(pet_mod.recommend(p, n=args.n), 1):
        _out(f"    {i}. {_lp(name, 28)}{desc}")
    _out()
    return 0


def cmd_reset(args) -> int:
    if os.path.exists(args.save):
        os.remove(args.save)
    _out("  已清空存档。重新领养：python -m mcd_pet adopt")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="mcd_pet",
        description="一只靠麦当劳养活的电子猫。所有营养数据来自麦当劳 MCP 真实接口。",
    )
    ap.add_argument("--save", default=SAVE, help="存档文件路径（默认 .mcdpet.json）")
    sub = ap.add_subparsers(dest="command")

    s = sub.add_parser("adopt", help="领养一只猫")
    s.add_argument("name", nargs="?", default="", help="给它取个名")
    s.add_argument("--save", default=SAVE)
    s.set_defaults(func=cmd_adopt)

    s = sub.add_parser("feed", help="喂它吃麦当劳")
    s.add_argument("food", help="餐品名，支持模糊匹配，如 麦乐鸡 / 巨无霸")
    s.add_argument("--save", default=SAVE)
    s.set_defaults(func=cmd_feed)

    s = sub.add_parser("status", help="看它的状态卡")
    s.add_argument("--save", default=SAVE)
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("wait", help="不喂，让它等着（会饿）")
    s.add_argument("rounds", nargs="?", type=int, default=1)
    s.add_argument("--save", default=SAVE)
    s.set_defaults(func=cmd_wait)

    s = sub.add_parser("list", help="查饲料库")
    s.add_argument("keyword", nargs="?", default="")
    s.add_argument("--cat", default="", help="按类别查")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("cats", help="看饲料类别")
    s.set_defaults(func=cmd_cats)

    s = sub.add_parser("forms", help="看全部进化形态")
    s.set_defaults(func=cmd_forms)

    s = sub.add_parser("recommend", help="该喂什么")
    s.add_argument("-n", type=int, default=3)
    s.add_argument("--save", default=SAVE)
    s.set_defaults(func=cmd_recommend)

    s = sub.add_parser("reset", help="清空存档")
    s.add_argument("--save", default=SAVE)
    s.set_defaults(func=cmd_reset)

    return ap


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        _out()
        _out("  一只靠麦当劳养活的电子猫。")
        _out()
        _out("    python -m mcd_pet adopt              领养")
        _out("    python -m mcd_pet feed 麦乐鸡         喂它")
        _out("    python -m mcd_pet status              看状态")
        _out("    python -m mcd_pet forms               看全部形态")
        _out()
        _out("  或者直接看一场完整的一生：python demo.py")
        _out()
        return 0
    return args.func(args)
