from fastapi import FastAPI, Request
import uvicorn
import requests
import json
import os

app = FastAPI()

# ==================== 配置 ====================
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_aa89ecdb74f8dcd3")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "yOhTGzaVURd6rh5GdJwRbebU1NaUi2kB")
COZE_API_URL = "https://8stpzzzp8k.coze.site/stream_run"
COZE_API_TOKEN = os.getenv("COZE_API_TOKEN", "")
COZE_PROJECT_ID = "7638933030429720591"

_tenant_token = None

# ==================== 飞书Token获取 ====================
def get_feishu_token():
    global _tenant_token
    if _tenant_token:
        return _tenant_token
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }, timeout=10)
    
    data = resp.json()
    if data.get("code") == 0:
        _tenant_token = data["tenant_access_token"]
        return _tenant_token
    else:
        raise Exception(f"获取飞书token失败: {data}")

# ==================== 调用扣子API ====================
def call_coze_api(user_text: str, session_id: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {COZE_API_TOKEN}"
    }
    
    payload = {
        "content": {
            "query": {
                "prompt": [
                    {
                        "type": "text",
                        "content": {
                            "text": user_text
                        }
                    }
                ],
                "type": "query",
                "session_id": session_id,
                "project_id": COZE_PROJECT_ID
            }
        }
    }
    
    try:
        resp = requests.post(COZE_API_URL, json=payload, headers=headers, timeout=60)
        result = resp.json()
        
        # 解析扣子返回
        if isinstance(result, dict):
            # 尝试多种可能的字段路径
            answer = (
                result.get("content", {}).get("answer") or
                result.get("data", {}).get("answer") or
                result.get("response") or
                result.get("text") or
                result.get("message") or
                str(result)
            )
            return answer
        return str(result)
        
    except Exception as e:
        return f"调用Agent失败: {str(e)}"

# ==================== 回复飞书消息 ====================
def reply_feishu(message_id: str, content: str):
    token = get_feishu_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": json.dumps({"text": content}),
        "msg_type": "text"
    }
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    
    if resp.json().get("code") != 0:
        print(f"回复飞书失败: {resp.text}")

# ==================== 飞书回调入口 ====================
@app.post("/feishu/callback")
async def feishu_callback(request: Request):
    data = await request.json()
    print(f"收到飞书事件: {json.dumps(data, ensure_ascii=False)}")
    
    # 1. URL验证（首次配置事件订阅时飞书会发challenge）
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}
    
    # 2. 处理消息事件
    header = data.get("header", {})
    if header.get("event_type") == "im.message.receive_v1":
        event = data.get("event", {})
        message = event.get("message", {})
        
        # 只处理文本消息
        if message.get("message_type") != "text":
            return {}
        
        # 解析消息内容
        content = json.loads(message.get("content", "{}"))
        user_text = content.get("text", "").strip()
        
        # 获取用户ID（用于扣子session）
        user_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "unknown")
        message_id = message.get("message_id")
        
        print(f"用户[{user_id}]说: {user_text}")
        
        # 调用扣子Agent
        agent_reply = call_coze_api(user_text, user_id)
        
        # 回复飞书
        reply_feishu(message_id, agent_reply)
    
    return {}

# ==================== 健康检查 ====================
@app.get("/")
async def root():
    return {"status": "running", "service": "feishu-coze-bridge"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
