# MCP 集成说明

## 调用了哪些 MCP 工具

| Tool | 用途 | 在代码中的位置 |
|---|---|---|
| `list-nutrition-foods` | 拉取麦当劳在售餐品的真实营养数据（热量 / 蛋白质 / 脂肪 / 碳水 / 钠 / 钙），作为宠物的「饲料库」 | `mcd_pet/mcp_live.py` → `fetch_nutrition()`，由 `demo.py --live` 触发 |

离线快照 `data/foods.json` 就是该接口的原始返回值（158 个餐品，2026-10-15 抓取），
字段未做任何人工修改，仅额外归纳了一个 `cat` 字段用于进化判定。

## 数据如何驱动游戏

宠物身上每一个数字都由 MCP 返回的真实营养值算出，没有任何随机数：

| 游戏数值 | 计算方式 | 用到的真实字段 |
|---|---|---|
| 体重增长 | `(kcal − 200/3) ÷ 7700 × 1000` 克 | `energyKcal` |
| 脂肪肝风险 | `− fat × 0.06` 健康 | `fat` |
| 高血压 / 钠中毒 | `− sodium × 0.0016` 健康 | `sodium` |
| 心情（糖分快乐） | `+ min(carb × 0.15, 12)` | `carbohydrate` |
| 健康回复 | `+ protein × 0.05 + calcium × 0.004` | `protein` / `calcium` |
| 饱食度 | `+ kcal ÷ 200 × 45` | `energyKcal` |

`7700 kcal ≈ 1 kg 脂肪` 是营养学通用换算，猫也一样适用——所以「喂一个巨无霸胖 58 克」不是编的。

## 两种运行模式

```bash
python demo.py            # 离线：读 data/foods.json 快照，零 Token 直接跑
python demo.py --live     # 实时：走 MCP 拉当前在售餐品
```

实时模式需要 Token，且**只从环境变量读取**：

```bash
export MCD_MCP_TOKEN=你的Token
python demo.py --live
```

## 接入方式

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer ${MCD_MCP_TOKEN}" }
    }
  }
}
```

完整配置模板见 `mcp-config.example.json`（**只有环境变量占位符，不含任何真实密钥**）。

## 安全说明

- 本项目**不包含任何真实 Token / 密钥**，仓库内所有配置示例均为 `${MCD_MCP_TOKEN}` 占位符。
- Token 只在运行时从环境变量注入，不会写入任何文件（存档文件 `.mcdpet.json` 只存宠物状态）。
- MCP 服务端限流 600 次/分钟，`--live` 每次运行仅发起 1 次请求。
