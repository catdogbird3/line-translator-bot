from flask import Flask, request, abort
import os

# LINE SDK v3
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

# 初始化 Flask 應用
app = Flask(__name__)

# 環境變數（請確保 Railway 上有設置這些變數）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 確保環境變數正確
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("❌ ERROR: LINE API 環境變數未設置！請確認 Railway 設定")
    exit(1)

# 初始化 LINE API
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設置 Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
        print(f"📩 Webhook 收到訊息: {body}")  # 紀錄 Webhook 輸入
    except InvalidSignatureError:
        print("❌ Invalid Signature Error")
        abort(400)
    except Exception as e:
        print(f"❌ Webhook Exception: {e}")
        abort(500)

    return 'OK'

# 訊息處理（當使用者發送訊息時）
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        user_text = event.message.text
        reply_text = f"您說了：{user_text}"

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

        print(f"✅ 成功回覆用戶：{reply_text}")

    except Exception as e:
        print(f"❌ Error in handle_message: {e}")

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
