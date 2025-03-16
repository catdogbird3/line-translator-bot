from flask import Flask, request, abort
import os
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

# 從環境變數讀取 Channel Secret 和 Access Token
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 確保變數正確設定
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("❌ ERROR: 環境變數未設置，請確認 Railway 設定")
    exit(1)

# 設定 LINE Bot API
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    """處理 LINE Webhook 訊息"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
        print(f"📩 Webhook 收到訊息: {body}")
    except InvalidSignatureError:
        print("❌ Invalid Signature Error")
        abort(400)
    except Exception as e:
        print(f"❌ Webhook Exception: {e}")
        abort(500)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """當用戶發送文字訊息時，回覆相同的訊息"""
    try:
        user_message = event.message.text
        reply_text = f"您說了：{user_message}"

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
