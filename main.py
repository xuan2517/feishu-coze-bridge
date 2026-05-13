from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

COZE_API_TOKEN = os.getenv("COZE_API_TOKEN")
COZE_BOT_ID = "你的扣子Bot ID"  # 从扣子 API 设置里复制
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/eeeeab91-4a94-4239-ac1e-f1fb5808dea9"

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    data = await request.json()
    
    # 解析飞书消息
    chat_id = data.get("chat_id", "")
    text = data.get("text", "")
    
    if not text:
        return {"status": "ok"}
    
    # 调用扣子 API
    coze_response = call_coze(text)
    
    # 回复飞书群
    send_feishu_message(coze_response)
    
    return {"status": "ok"}

def call_coze(query):
    url = "https://api.coze.cn/open_api/v2/chat"
    headers = {
        "Authorization": f"Bearer {COZE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "bot_id": COZE_BOT_ID,
        "user": "feishu_user",
        "query": query,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()
        return result["messages"][0]["content"]
    except Exception as e:
        return f"调用失败：{str(e)}"

def send_feishu_message(text):
    payload = {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }
    try:
        requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
    except Exception as e:
        print(f"发送失败：{str(e)}")

@app.get("/")
async def root():
    return {"status": "running"}
