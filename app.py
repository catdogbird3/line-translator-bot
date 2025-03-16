from flask import Flask, request, abort
import os
import re
import requests
import uuid
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT")
TRANSLATOR_LOCATION = os.getenv("TRANSLATOR_LOCATION")

# 確保所有變數都正確設定
if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, TRANSLATOR_KEY, TRANSLATOR_ENDPOINT, TRANSLATOR_LOCATION]):
    print("❌ ERROR: 環境變數未設定完整，請確認 Railway 設定")
    exit(1)

# 初始化 LINE API
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    """處理 LINE Webhook 事件"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
        print(f"📩 收到 Webhook 訊息: {body}")
    except InvalidSignatureError:
        print("❌ Invalid Signature Error")
        abort(400)
    except Exception as e:
        print(f"❌ Webhook Exception: {e}")
        abort(500)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """當收到群組訊息時，翻譯成英文並回應"""
    try:
        user_id = event.source.user_id  # 取得發訊息者的 ID
        group_id = event.source.group_id if hasattr(event.source, "group_id") else "私聊"
        user_message = event.message.text  # 取得訊息內容
        
        # 翻譯訊息
        translated_text = translate_text(user_message)

        # 嘗試獲取用戶名稱（僅適用於群組）
        display_name = "未知用戶"
        if group_id != "私聊":
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                profile = line_bot_api.get_group_member_profile(group_id, user_id)
                display_name = profile.display_name

        # 組合回覆訊息（翻譯後的內容）
        reply_text = f"📢 {display_name} 說：{translated_text}"
        
        # 回覆訊息到群組
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

        print(f"✅ 翻譯成功：{display_name} 說 {user_message} → {translated_text}")

    except Exception as e:
        print(f"❌ Error in handle_message: {e}")
        
def translate_text(text):
    """使用 Azure Translator API 進行翻譯"""
    if len(text) > 5000:
        return "❌ 超過 5,000 字元限制，請分段翻譯！"

    path = "/translate"
    constructed_url = TRANSLATOR_ENDPOINT + path

    params = {
        'api-version': '3.0',
        'to': ['en']
    }
    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{'text': text}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        return result[0]['translations'][0]['text']
    except Exception as e:
        print(f"❌ 翻譯 API 錯誤: {e}")
        return "翻譯失敗"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railway 會提供 PORT 變數
    app.run(host="0.0.0.0", port=port)
