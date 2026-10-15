"""一键演示：完整养一只猫，看着它怎么一步步变成别的什么东西。

零依赖、零 Token，直接跑：

    python demo.py
    python demo.py --live     # 饲料库实时走麦当劳 MCP
"""

from __future__ import annotations

import argparse
import os
import random
import sys

from mcd_pet import faces, foods as foods_mod
from mcd_pet import pet as pet_mod

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def banner() -> None:
    print()
    print("  " + "=" * 68)
    print("   mcd-pet · 一只靠麦当劳养活的电子猫".center(66))
    print("   所有营养数据来自麦当劳官方 MCP，它不是在演，它是真的在胖".center(64))
    print("  " + "=" * 68)


def main() -> int:
    ap = argparse.ArgumentParser(description="mcd-pet 一键演示")
    ap.add_argument("--live", action="store_true", help="饲料库实时走麦当劳 MCP")
    ap.add_argument("--seed", type=int, default=1024, help="随机种子（默认固定，保证可复现）")
    a = ap.parse_args()

    banner()

    # ---- 数据源
    if a.live:
        try:
            from mcd_pet.mcp_live import fetch_nutrition
            rows = fetch_nutrition()
            built = {}
            for it in rows:
                nm = (it.get("productName") or "").strip()
                if nm and nm not in built:
                    built[nm] = {
                        "kcal": float(it.get("energyKcal") or 0),
                        "protein": float(it.get("protein") or 0),
                        "fat": float(it.get("fat") or 0),
                        "carb": float(it.get("carbohydrate") or 0),
                        "sodium": float(it.get("sodium") or 0),
                        "calcium": float(it.get("calcium") or 0),
                        "cat": "其他",
                    }
            foods_mod.reload_from(built)
            src = f"LIVE · mcp.mcd.cn（{len(built)} 个真实餐品）"
        except Exception as e:  # noqa: BLE001
            print(f"\n  实时拉取失败（{e}），回退到离线快照。\n")
            src = foods_mod.source_label()
    else:
        src = foods_mod.source_label()

    print(f"\n  饲料数据源：{src}\n")

    rng = random.Random(a.seed)
    p = pet_mod.Pet.adopt("麦麦")

    print("  【第 0 天】领养")
    print(pet_mod.status_card(p, rng))

    # ---- 剧本：一条从正常走向失控的投喂路线
    script: list[tuple[str, str]] = [
        ("麦乐鸡", "你给它一块麦乐鸡。一切都很正常。"),
        ("麦乐鸡", "它很喜欢。再来一块。"),
        ("麦乐鸡", "第三块。它吃得很快。"),
        ("麦乐鸡", "第四块。你已经停不下来了。"),
        ("麦乐鸡", "第五块。它抬头看了你一眼。"),
        ("麦乐鸡", "第六块。它的眼神变了。"),
        ("麦乐鸡", "第七块。科学研究表明这已经过量了。"),
        ("麦乐鸡", "第八块。它的基因开始重组。"),
        ("巨无霸", "你觉得该补点别的。"),
        ("巨无霸", "又来一个。"),
        ("薯条", "薯条是猫的天敌，但你不管。"),
        ("薯条", "薯条 +1。"),
        ("麦旋风", "甜品。它的眼睛在放光。"),
        ("麦旋风", "再来一个。"),
        ("可乐", "配可乐，讲究。"),
        ("可乐", "再来一杯。"),
        ("巨无霸", "你说这是最后一顿。"),
        ("巨无霸", "你撒谎了。"),
        ("巨无霸", "最后一次。真的。"),
        ("薯条", "它已经站不起来了。"),
        ("巨无霸", "你把最后一块塞进它嘴里。"),
    ]

    prev_form = p.form
    for food, note in script:
        f = foods_mod.get(food)
        if f is None:
            print(f"\n  （跳过：饲料库里没有「{food}」）")
            continue
        print(f"\n  【第 {p.age + 1} 天】{note}")
        print("  " + p.feed(food, f, rng))
        # 只在形态变化或每 5 天出一次状态卡，否则输出太长
        if p.form != prev_form or p.age % 5 == 0:
            print(pet_mod.status_card(p, rng))
            prev_form = p.form
        if not p.alive:
            break

    # ---- 结局
    print("\n" + "  " + "=" * 68)
    if p.alive:
        print("  它居然还活着。")
        print(pet_mod.status_card(p, rng))
        print()
        print(pet_mod.stats_block(p))
        print()
        print("  想弄死它就继续喂：python -m mcd_pet feed 巨无霸")
    else:
        print("  它走了。")
        print()
        print(pet_mod.death_card(p, rng))
        print()
        print(pet_mod.stats_block(p))
    print("  " + "=" * 68)

    # ---- 彩蛋：全部形态一览
    print("\n  彩蛋：它本来可以变成这些形态（共 %d 种）" % len(faces.FORMS))
    for name, info in faces.FORMS.items():
        print(f"\n  【{name}】{info['desc']}")
        for line in info["art"]:
            print("    " + line)

    print("\n  完整版可以自己养：python -m mcd_pet adopt")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
