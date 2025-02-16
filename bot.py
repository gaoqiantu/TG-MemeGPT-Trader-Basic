import sqlite3
import json
import requests
import openai
#import base58
import re
import time
import asyncio
#from solana.rpc.api import Client
#from solders.transaction import Transaction
#from solders.system_program import transfer
#from solders.keypair import Keypair
from telethon import TelegramClient, events

# ✅ Load Configuration
with open("config.json") as f:
    config = json.load(f)

# ✅ SQLite Database Setup
conn = sqlite3.connect("trades.db")
cursor = conn.cursor()

# ✅ Create Tables if Not Exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_tokens (
    contract TEXT PRIMARY KEY,
    message TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS bot_responses (
    contract TEXT PRIMARY KEY,
    dogeebot_response TEXT,
    solana_alerts_response TEXT
)
""")
# ✅ Add an Assistant ID Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS assistant_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assistant_id TEXT UNIQUE
)
""")
conn.commit()

# # ✅ Convert Base58 Phantom Private Key to Hex Format
# def get_solana_keypair():
#     base58_private_key = config["solana"]["private_key"]
#     try:
#         private_key_bytes = base58.b58decode(base58_private_key)
#         keypair = Keypair.from_bytes(private_key_bytes)
#         print("✅ Solana Keypair Loaded Successfully!")
#         return keypair
#     except Exception as e:
#         print(f"❌ Error converting private key: {e}")
#         exit(1)

# # ✅ Initialize Solana Client
# solana_client = Client(config["solana"]["rpc_url"])
# private_key = get_solana_keypair()

# if solana_client.is_connected():
#     print("✅ Successfully connected to Solana Mainnet!")

# ✅ Telegram API Setup
api_id = config["telegram"]["api_id"]
api_hash = config["telegram"]["api_hash"]
channel_id = config["telegram"]["channel_id"]
telegram_client = TelegramClient("session", api_id, api_hash)

# ✅ OpenAI API Setup
client = openai.OpenAI(api_key=config["openai"]["api_key"])

# ✅ Function: Parse Telegram Message
def parse_message(text):
    """Extracts the token name, contract address, community count, fast promotion flag, and token meaning."""
    try:
        # ✅ Extract Token Name and Contract Address
        token_match = re.search(r"\[\$(.*?)\]\(https://solscan.io/token/([a-zA-Z0-9]+)\)", text)
        if token_match:
            token_name = token_match.group(1).strip()
            contract_address = token_match.group(2).strip()
        else:
            print(f"⚠️ Failed to extract token name or contract: {text}")
            return None, None, 0, False, None

        # ✅ Extract Token Meaning (inside parentheses after token link)
        meaning_match = re.search(r"https://solscan.io/token/[a-zA-Z0-9]+\)\s*\((.*?)\)", text)
        token_meaning = meaning_match.group(1).strip() if meaning_match else "No meaning provided"

        # ✅ Extract number of community promotions
        community_match = re.search(r"🟢 已在(\d+)个社区推广", text)
        community_count = int(community_match.group(1)) if community_match else 0

        # ✅ Detect "推广很迅速" (fast promotion)
        is_fast_promoted = "推广很迅速" in text

        print(f"✅ Parsed Token: [{token_name}] Contract: {contract_address}, Meaning: {token_meaning}, Communities: {community_count}, Fast Promotion: {is_fast_promoted}")
        return token_name, contract_address, community_count, is_fast_promoted, token_meaning

    except Exception as e:
        print(f"❌ Error in parse_message: {e}")
        return None, None, 0, False, None

# ✅ Function: Check if Token is Already Processed
def is_already_processed(contract_address):
    cursor.execute("SELECT contract FROM processed_tokens WHERE contract=?", (contract_address,))
    return cursor.fetchone() is not None

# ✅ Function: Store Processed Token
def store_processed_token(contract_address, message):
    cursor.execute("INSERT OR REPLACE INTO processed_tokens (contract, message) VALUES (?, ?)", (contract_address, message))
    conn.commit()

# ✅ Function: Forward Contract Address to Bots and Store Responses
async def forward_to_bots(contract_address):
    """
    Sends contract address to bot services, retrieves responses, and logs raw messages for debugging.
    """
    bots = {"@dogeebot_bot": None, "@solana_alerts_dogeebot": None}

    for bot in bots.keys():
        try:
            async with telegram_client.conversation(bot, timeout=10) as conv:
                await conv.send_message(contract_address)
                print(f"✅ 已发送合约 {contract_address} 给 {bot}")

                await asyncio.sleep(1)  # ⏳ Wait 1 second before fetching response

                response = await asyncio.wait_for(conv.get_response(), timeout=15)
                raw_text = response.text  # Original bot response
                
                # ✅ Debug log: Capture the exact response from the bot
                #print(f"📝 RAW RESPONSE from {bot}: \n{raw_text}\n")

                # ✅ Apply updated cleaning method
                cleaned_text = clean_response(raw_text)

                bots[bot] = cleaned_text
                #print(f"✅ 处理 {bot} 响应完成: {cleaned_text}")  # Debug log

        except asyncio.TimeoutError:
            print(f"⚠️ {bot} 响应超时")
            bots[bot] = "⚠️ 机器人响应超时"

        except Exception as e:
            print(f"⚠️ {bot} 发生错误: {e}")
            bots[bot] = "⚠️ 机器人响应失败"

    return bots["@dogeebot_bot"], bots["@solana_alerts_dogeebot"]

# ✅ remove urls
def clean_response(text):
    """
    Removes URLs while preserving price movements (5m, 1h, 4h).
    """
    # ✅ Extract price movements before cleaning
    price_pattern = r"(├ 5m：.*?|├ 1h：.*?|├ 4h：.*?)"
    price_matches = re.findall(price_pattern, text)
    print(f"🔍 Extracted Prices Before Cleaning: {price_matches}")  # DEBUG LOG

    # ✅ Remove only URLs, but keep price changes
    cleaned_text = re.sub(r"https?://\S+", "", text)
    print(f"📝 CLEANED TEXT BEFORE PRICE RESTORE: \n{cleaned_text}\n")  # DEBUG LOG

    # ✅ Restore price movements if they were removed
    for price in price_matches:
        if price not in cleaned_text:
            print(f"⚠️ Restoring Missing Price: {price}")  # DEBUG LOG
            # Find a position to insert the price data
            cleaned_text += f"\n{price}"

    # ✅ Fix extra spaces left behind by URL removal
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    print(f"✅ FINAL CLEANED TEXT: \n{cleaned_text}\n")  # DEBUG LOG
    return cleaned_text
# ✅ Function: Retrieve Stored Bot Responses
def get_stored_responses(contract_address):
    cursor.execute("SELECT dogeebot_response, solana_alerts_response FROM bot_responses WHERE contract=?", (contract_address,))
    result = cursor.fetchone()
    if result:
        return result[0] or "No response", result[1] or "No response"
    return "No response", "No response"
def remove_urls(text):
    """Remove all URLs starting with https:// from the given text."""
    return re.sub(r'https://\S+', '', text)
# ✅ Function: GPT-4o Analysis
async def analyze_trade(meme_name, token_meaning, community_info, dogeebot_response, solana_alerts_response):
    """
    Uses OpenAI API to analyze meme coin trading opportunities.
    Sends the cleaned bot responses while keeping all relevant data.
    """
    try:
        global assistant_id
        if not assistant_id:
            assistant_id = get_or_create_assistant()

        # ✅ Create AI Thread
        thread = client.beta.threads.create()
        print(f"✅ AI 线程: {thread.id}")

        # ✅ Construct AI Analysis Prompt
        prompt = f"""
        You are an experienced AI meme coin pump and dump trading analyst. Please first search the internet for additional sentiment and community engagement check with the token meaning {token_meaning}.
        然后用简短的中文分析此代币：
        - **代币名称**: {meme_name}
        - **代币含义**: {token_meaning}
        - **社区推广**: {community_info}
        - **当前数据**:
            - DogeeBot: {dogeebot_response}
            - Solana Alerts: {solana_alerts_response}
        请提供：
        1. **交易评分 (0-100, output only the number)**
        2. **简要分析** (限制在 **300 字内**)
        **评分标准**：
        - 市值越低，评分越高
        - 更多 "聪明钱" 参与，评分越高
        - 创建时间较短，评分越高
        - 价格变动是正向的 positive move (5m, 1h, 4h) 提高评分
        - Meme 主题，名称，含义传播力强，评分越高
        **注意：回答必须限制在 300 字以内，言简意赅，直击灵魂！**
        """

        # ✅ Send message to AI Thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        print(f"✅ 发送 GPT 请求: {message.id}")

        # ✅ Wait for AI response
        while True:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            print(f"✅ AI 运行状态: {run.status}")

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)

                # ✅ Find the AI response
                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        ai_response = msg.content[0].text.value
                        print(f"✅ GPT-4o AI 分析: {ai_response}")

                        # ✅ Extract score using regex (Only numbers 0-100)
                        score_match = re.search(r"^\s*(\d{1,3})", ai_response)
                        trade_score = int(score_match.group(1)) if score_match else 0

                        return trade_score, ai_response  # Return both the score and analysis

                return 0, "⚠️ AI 未返回有效分析"  # Return 0 if no valid response

            elif run.status in ["failed", "cancelled"]:
                return 0, f"⚠️ AI 分析失败，状态: {run.status}"

            else:
                print("⏳ 等待 AI 响应... 2 秒后重试")
                time.sleep(2)

    except openai.OpenAIError as e:
        print(f"❌ OpenAI API 错误: {e}")
        return 0, f"❌ OpenAI API 错误: {e}"

# ✅ Telegram Listener for Main Channel
@telegram_client.on(events.NewMessage(chats=channel_id)) 
async def handle_message(event):
    text = event.message.text
    token_name, contract_address, community_count, is_fast_promoted, token_meaning = parse_message(text)

    if not token_name or not contract_address:
        print("⚠️ Skipping due to failed parsing.")
        return
    
    if community_count < 2 and not is_fast_promoted:
        print(f"🚫 Ignoring {token_name}: Community count ({community_count}) < 2 and not fast promoted.")
        return  # Skip this token

    print(f"✅ Passed filter: {token_name} | Communities: {community_count} | Fast Promotion: {is_fast_promoted}")

    # ✅ **Check if Token is Already in Database**
    if is_already_processed(contract_address):
        print(f"✅ Token {token_name} already processed. Skipping processing and Discord notification.")
        return  # ✅ Early exit, no processing, no Discord message
    else:
        print(f"⚠️ Stored response for {token_name} is incomplete. Reprocessing...")

    # ✅ Store token in database before processing
    cursor.execute("INSERT OR REPLACE INTO processed_tokens (contract, message) VALUES (?, ?)", (contract_address, text))
    conn.commit()

    print(f"✅ New Meme Coin Detected: {token_name} | Meaning: {token_meaning} | Communities: {community_count} | Fast Promotion: {is_fast_promoted}")

    # ✅ Forward contract to bots and store responses
    dogeebot_response, solana_alerts_response = await forward_to_bots(contract_address)

    # ✅ Send Token Meaning to GPT Analysis
    print(f"⏳ Waiting for AI analysis of {token_name}...")
    trade_score, trade_analysis = await analyze_trade(token_name, token_meaning, community_count, dogeebot_response, solana_alerts_response)
    print(f"✅ AI Analysis Complete for {token_name} with score {trade_score}")

    if trade_analysis.startswith("❌") or trade_analysis.startswith("⚠️"):
        print(f"⚠️ AI Analysis Failed for {token_name}, skipping Discord notification.")
        return

    # ✅ Store analysis results in the database for future lookups
    cursor.execute("INSERT OR REPLACE INTO bot_responses (contract, dogeebot_response, solana_alerts_response) VALUES (?, ?, ?)",
                   (contract_address, trade_analysis, solana_alerts_response))
    conn.commit()

    # ✅ Always Send to Discord
    message = f"""\n
    **代币名称:** {token_name}
    **代币地址:** {contract_address}
    **代币含义:** {token_meaning}
    **当前社区推广数目:** {community_count}
    **推广是否快速:** {'✅' if is_fast_promoted else '❌'}
    **MemeGPT分析结果:**{trade_analysis}
    """
    send_to_discord(message)

    print(f"✅ Sent analysis of {token_name} to Discord!")

    # ✅ **NEW: Forward Contract to @GMGN_sol_bot if Score ≥ 80**
    if trade_score >= 80:
        async with telegram_client.conversation("@GMGN_sol_bot", timeout=10) as conv:
            await conv.send_message(contract_address)
            print(f"🚀 高评分代币 {token_name} (评分: {trade_score}) 已发送至 @GMGN_sol_bot")

  # ✅ Chatgpt Assistant
def get_or_create_assistant():
    """Retrieve an existing Assistant ID or create a new one if none exists."""
    cursor.execute("SELECT assistant_id FROM assistant_metadata LIMIT 1")
    result = cursor.fetchone()

    if result and result[0]:
        print(f"✅ Reusing existing Assistant: {result[0]}")
        return result[0]

    # ✅ If no existing assistant, create a new one
    assistant = client.beta.assistants.create(
        name="Meme Coin Trading Analyst",
        instructions="You are an experienced AI meme coin pump and dump trading analyst.",
        tools=[],
        model="gpt-4o",
    )
    # ✅ Store Assistant ID in the database
    cursor.execute("INSERT INTO assistant_metadata (assistant_id) VALUES (?)", (assistant.id,))
    conn.commit()

    print(f"✅ New Assistant Created: {assistant.id}")
    return assistant.id

# ✅ Function: Send to Discord
def send_to_discord(message):
    webhook_url = config["discord"]["webhook_url"]
    
    # Discord has a 2000-character limit per message
    max_length = 1900  # Keep some buffer for formatting
    
    # ✅ Split message into chunks
    if len(message) > max_length:
        parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        for part in parts:
            payload = {"content": part}
            requests.post(webhook_url, json=payload)
            time.sleep(1)  # ✅ Prevent rate limiting
    else:
        payload = {"content": message}
        requests.post(webhook_url, json=payload)
# ✅ Get or create the Assistant ID once
assistant_id = get_or_create_assistant()

# ✅ Start Bot
telegram_client.start()
telegram_client.run_until_disconnected()