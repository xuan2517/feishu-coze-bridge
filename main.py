from fastapi import FastAPI, Request
import requests

app = FastAPI()

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/eeeeab91-4a94-4239-ac1e-f1fb5808dea9"

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    data = await request.json()
    
    # 解析飞书消息
    text = data.get("text", "")
    
    if not text:
        return {"status": "ok"}
    
    # 简单回复（这里可以接入任何 AI 服务，暂时用固定回复测试）
    reply = f"收到：{text}"
    
    # 回复飞书群
    send_feishu_message(reply)
    
    return {"status": "ok"}

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
