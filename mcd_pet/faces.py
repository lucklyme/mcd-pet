"""表情包库：ASCII 猫脸 + 台词。

每个形态一组 art（4 行），台词按当前状态从池子里取。
设计原则：一眼能看懂，能直接复制去发朋友圈。
"""

from __future__ import annotations

import random
from typing import Dict, List

# ---------------------------------------------------------------- 形态立绘

FORMS: Dict[str, Dict[str, object]] = {
    "小猫猫": {
        "art": [
            "   /\\_/\\",
            "  (=^･ω･^=)",
            "   /   ) )",
            "  (____(__)",
        ],
        "desc": "刚领养，还不知道自己即将面对什么",
    },
    "橘座": {
        "art": [
            "    /\\_/\\",
            "  （=^..^=）",
            "  /        \\",
            "  |________|",
        ],
        "desc": "体重失控，走路开始左右晃",
    },
    "麦乐鸡侠": {
        "art": [
            "   /\\_/\\",
            "  (=^･ω･^=)",
            "  /鸡 鸡 鸡 鸡\\",
            "  \\__________/",
        ],
        "desc": "吃麦乐鸡吃到基因变异",
    },
    "薯条精": {
        "art": [
            "   /\\_/\\",
            "  (=^･ω･^=)",
            "  ||||||||||",
            "  ||||||||||",
        ],
        "desc": "身体已经是一把薯条了",
    },
    "糖分恶魔": {
        "art": [
            "   /\\_/\\",
            "  (=^..^=)",
            "   \\ ~~~ /",
            "    \\___/",
        ],
        "desc": "血糖过山车，眼睛都在放光",
    },
    "巨无霸兽": {
        "art": [
            "   /\\_/\\",
            "  (=^O_O^=)",
            "  /  巨无霸  \\",
            "  \\__________/",
        ],
        "desc": "体型已接近一个汉堡",
    },
    "可乐喷泉": {
        "art": [
            "   /\\_/\\   ° °",
            "  (=^o_o^=) °",
            "   /     \\  °",
            "  (_______)",
        ],
        "desc": "体内二氧化碳严重超标",
    },
    "高血压猫": {
        "art": [
            "   /\\_/\\",
            "  (=>`д´=)",
            "   /    \\",
            "  (______)",
        ],
        "desc": "钠摄入爆表，随时可能爆炸",
    },
    "健康猫": {
        "art": [
            "   /\\_/\\",
            "  (=^ωω^=)",
            "   /    \\",
            "  (______)",
        ],
        "desc": "居然在麦当劳吃出了健康",
    },
    "麦门圣猫": {
        "art": [
            "      _/\\_",
            "   /\\_/  \\_/\\",
            "  (=^･ω･^=)  *",
            "   /      \\  *",
            "  (____(__)",
        ],
        "desc": "究极形态：营养均衡，心态平和",
    },
    "天使猫": {
        "art": [
            "     _/\\_",
            "   /\\_/  \\_",
            "  (=^·_·^=)",
            "   /     \\",
        ],
        "desc": "它去了麦当劳天堂",
    },
}

# ---------------------------------------------------------------- 台词池

LINES: Dict[str, List[str]] = {
    "饿": [
        "喵……（盯）",
        "你忍心看我这样吗",
        "我饿得可以吃掉一头牛，真的牛",
        "不给饭我就躺下了",
        "你已经好几个回合没喂我了",
    ],
    "撑": [
        "不……不能再吃了……",
        "嗝——",
        "我觉得我的世界观在晃动",
        "再喂我就原地爆炸",
        "让我静静",
    ],
    "开心": [
        "喵！这个我喜欢",
        "我可以再吃一口吗",
        "（尾巴摇成螺旋桨）",
        "你今天对我真好",
        "呼噜呼噜呼噜",
    ],
    "腻": [
        "又是这个……",
        "我上辈子是做了什么孽",
        "换一个行不行，求你了",
        "（把食物推到一边）",
        "我已经吃不出灵魂了",
    ],
    "危险": [
        "我觉得我有点不对劲",
        "心跳好快……",
        "我的毛在发光，这正常吗",
        "你……你到底想干什么",
        "我可能活不了多久了",
    ],
    "死": [
        "喵————（渐弱）",
        "替我……多吃一块麦乐鸡",
        "下辈子我想当个沙拉",
        "记得把我埋在麦当劳门口",
        "我这一生，值了（不确定）",
    ],
}

# 死因 -> 墓志铭模板
EPITAPHS: Dict[str, str] = {
    "钠中毒": "它一生摄入 {sodium:.0f} mg 钠，肾脏表示理解但不接受",
    "脂肪肝": "它吃下 {fat:.0f} g 脂肪，肝脏选择了提前退休",
    "撑死": "最后一餐是「{last}」，它说还想再来一口",
    "饿死": "它等了你 {age} 个回合，你一次都没回来",
    "过劳": "它活了 {age} 个回合，其中大部分时间在被你喂",
}


def art_of(form: str) -> List[str]:
    return list(FORMS.get(form, FORMS["小猫猫"])["art"])


def desc_of(form: str) -> str:
    return str(FORMS.get(form, FORMS["小猫猫"])["desc"])


def line_of(state: str, rng: random.Random | None = None) -> str:
    pool = LINES.get(state) or LINES["开心"]
    r = rng or random
    return r.choice(pool)


def epitaph_of(cause: str, **kw) -> str:
    tpl = EPITAPHS.get(cause, "它的一生，被 {age} 次投喂填满")
    try:
        return tpl.format(**kw)
    except (KeyError, ValueError):
        return tpl


def _w(s: str) -> int:
    """按终端显示宽度计算。

    - CJK / 全角（> U+2E80）算 2 格
    - 半角片假名（U+FF61~U+FFDC）虽然 > U+2E80，但终端只占 1 格
    """
    n = 0
    for ch in s:
        o = ord(ch)
        if 0xFF61 <= o <= 0xFFDC:      # 半角片假名，实际只占 1 格
            n += 1
        elif o > 0x2E80:               # CJK / 全角
            n += 2
        else:
            n += 1
    return n


def _pad(s: str, width: int) -> str:
    """按显示宽度右填充，超长则截断并加省略号。"""
    if _w(s) > width:
        out = ""
        for ch in s:
            if _w(out) + _w(ch) > width - 1:
                break
            out += ch
        return out + "…"
    return s + " " * (width - _w(s))


def card(
    name: str,
    form: str,
    state: str,
    weight_g: float,
    health: float,
    mood: float,
    satiety: float,
    age: int,
    rng: random.Random | None = None,
    width: int = 36,
) -> str:
    """生成一张可复制的「宠物状态卡」——朋友圈专用。"""
    art = art_of(form)
    line = line_of(state, rng)
    inner = width

    def row(left: str = "", right: str = "") -> str:
        pad = inner - _w(left) - _w(right)
        return "  │ " + left + " " * max(pad, 1) + right + " │"

    lines: List[str] = []
    lines.append("  ┌" + "─" * (inner + 2) + "┐")
    lines.append("  │ " + _pad(f"{name} · {form}", inner + 1) + "│")
    lines.append("  ├" + "─" * (inner + 2) + "┤")
    for a in art:
        lines.append("  │  " + _pad(a, inner) + "│")
    lines.append("  │" + " " * (inner + 2) + "│")
    lines.append("  │ " + _pad("「" + line + "」", inner + 1) + "│")
    lines.append("  ├" + "─" * (inner + 2) + "┤")
    lines.append(row(f"体重 {weight_g/1000:.2f} kg", f"心情 {mood:.0f}"))
    lines.append(row(f"健康 {health:.0f}", f"饱食 {satiety:.0f}"))
    lines.append("  │ " + _pad(f"年龄 {age} 回合 · {desc_of(form)}", inner + 1) + "│")
    lines.append("  └" + "─" * (inner + 2) + "┘")
    return "\n".join(lines)


def grave_card(name: str, form: str, cause: str, age: int, rng: random.Random | None = None) -> str:
    """墓碑——宠物死后的遗照。"""
    art = art_of(form)
    line = line_of("死", rng)
    inner = 36
    out: List[str] = []
    out.append("  ┌" + "─" * (inner + 2) + "┐")
    out.append("  │ " + _pad(f" RIP · {name} ", inner + 1) + "│")
    out.append("  ├" + "─" * (inner + 2) + "┤")
    for a in art:
        out.append("  │  " + _pad(a, inner) + "│")
    out.append("  │" + " " * (inner + 2) + "│")
    out.append("  │ " + _pad("「" + line + "」", inner + 1) + "│")
    out.append("  ├" + "─" * (inner + 2) + "┤")
    out.append("  │ " + _pad(f"死因：{cause}", inner + 1) + "│")
    out.append("  │ " + _pad(f"享年：{age} 回合", inner + 1) + "│")
    out.append("  └" + "─" * (inner + 2) + "┘")
    return "\n".join(out)
