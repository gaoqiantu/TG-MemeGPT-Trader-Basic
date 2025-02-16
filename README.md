# TG-MemeGPT-Trader-Basic

## 📌 项目简介 / Project Overview

TG-MemeGPT-Trader-Basic 是一个基于 Telegram 和 OpenAI ChatGPT API 的 Solana 生态 Meme 币自动交易机器人。该脚本可自动监听 Telegram 社群中的代币推广信息，结合 AI 评分系统进行交易决策，并通过 GMGN Telegram 交易机器人实现自动买卖、止盈止损。

TG-MemeGPT-Trader-Basic is a Solana-based meme token auto-trading bot leveraging Telegram and OpenAI ChatGPT API. It monitors token promotions in Telegram groups, uses AI scoring for investment decisions, and executes trades via the GMGN Telegram trading bot with automated buy/sell and stop-loss features.

---

## ✨ 亮点功能 / Key Features

- **自动监控 Telegram 社群**: 监听社群中的 Meme 币推广信息（默认监控 t.me/MomentumTrackerCN）。
- **多层过滤系统**: 仅关注推广社群数量≥3或短时间内传播迅速的代币。
- **智能代币分析**: 结合 `@solana_alerts_dogeebot` 和 `@dogeebot_bot` 提取代币信息。
- **AI 评分机制**: 通过 OpenAI GPT API 分析并评分，评分标准包括：
  - 市值低的代币评分更高
  - 参与交易的“聪明钱”越多评分越高
  - 代币创建时间越短评分越高
  - 价格短时上涨（5m, 1h, 4h）加分
  - 具备 Meme 潜力、名字和主题传播性强加分
- **自动交易执行**: 对 AI 评分≥80 的代币自动调用 `@GMGN_sol_bot` 进行下单，设置止盈止损。
- **支持 Solana 直接交易（可选）**: 通过 Phantom 钱包私钥直接连接 Solana 主网，跳过 Telegram 交易机器人，降低手续费。
- **支持 24x7 无人值守 AI 交易**: 未来可接入 AI Agent 框架或本地 AI（如 DeepSeek）实现完全自动化。

---

## 🛠️ 运行前准备 / Setup Before Running

1. **配置 `config.json`**：
    - `telegram.api_id` / `api_hash` / `channel_id` （用于监控指定 Telegram 频道, 目前的监控群是"channel_id": -1002327294921）
    - `openai.api_key` （用于 AI 分析）
    - `discord.webhook_url` （用于推送交易分析结果至 Discord 群组）
    - `solana.private_key` / `solana.rpc_url` （可选，Solana 钱包私钥，用于链上直接交易）

2. **安装依赖**（确保 Python 版本 ≥3.8）
   ```sh
   pip3 install -r requirements.txt
   ```

3. **运行脚本**
   ```sh
   python3 bot.py
   ```
   输入tg手机号： +（区号）号码，比如美国手机987-654-3210，则输入+19876543210
   接收验证码后，输入验证码。之后就可以通过session登录不用再次输入。 

**建议放在服务器运行时，将bot添加到systemd 通过systemctl自动启动和重启。**
---

## 🔗 相关资源 / Useful Links

- **GMGN 交易机器人推荐链接**: [GMGN Trading Bot](https://t.me/GMGN_sol_bot?start=i_1EB04dMg)
- **Dogee 机器人推荐链接**: [Dogee Bot](https://t.me/dogeebot_bot?start=invite-17374934069260)
- **默认社群活跃度监控**: [Momentum Tracker CN](https://t.me/MomentumTrackerCN) （"channel_id": -1002327294921）
- **兔子的唯一社群-狡兔三窟**：(https://discord.gg/zqQZ4qNXgh)
---

## 🚀 贡献 / Contributing

我们鼓励 Fork 该项目，并欢迎社区贡献者优化代码！一些潜在的改进方向：
- **接入 AI Agent 框架**（如 AutoGPT, BabyAGI）
- **主网直接交易以及策略编写（目前只写了接入）**
- **使用本地 LLM（如 DeepSeek）替代 OpenAI API**
- **优化交易策略，增加更多 AI 评估维度**

💡 **Pull Requests 欢迎！** 你的贡献将帮助该项目成长。

---

## ⚠️ 免责声明 / Disclaimer

本项目仅供学习交流，不构成任何投资建议。交易加密货币存在风险，请谨慎操作。

This project is for educational purposes only and does not constitute investment advice. Cryptocurrency trading carries risks, proceed with caution.

