from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import asyncio

app = FastAPI()

COZE_API_TOKEN = os.getenv("COZE_API_TOKEN")
COZE_BOT_ID = "你的扣子Bot ID"

@app.post("/feishu/callback")
async def feishu_callback(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # 处理飞书校验请求
    if "challenge" in data:
        return {"challenge": data["challenge"]}
    
    # 立即返回200，后台异步处理
    if data.get("header", {}).get("event_type") == "im.message.receive_v1":
        background_tasks.add_task(process_message, data)
    
    return {"status": "ok"}

def process_message(data):
    message = data["event"]["message"]
    chat_id = message["chat_id"]
    content = message["content"]["text"]
    
    # 调用扣子API
    coze_response = call_coze(content)
    
    # 回复飞书
    send_feishu_message(chat_id, coze_response)

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
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    return response.json()["messages"][0]["content"]

def send_feishu_message(chat_id, text):
    # 这里用飞书Webhook或应用消息API回复
    pass
