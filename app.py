from flask import Flask, request, abort
import requests
import os
import uuid
import json
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
TRANSLATOR_KEY = os.getenv('TRANSLATOR_KEY')
TRANSLATOR_ENDPOINT = os.getenv('TRANSLATOR_ENDPOINT')
TRANSLATOR_LOCATION = os.getenv('TRANSLATOR_LOCATION')

# 確保變數正確
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("❌ LINE API 環境變數未設置！請確認 Railway 變數設定！")
    exit(1)

if not TRANSLATOR_KEY or not TRANSLATOR_ENDPOINT or not TRANSLATOR_LOCATION:
    print("❌ Translator API 環境變數未設置！請確認 Railway 變數設定！")
    exit(1)

# 初始化 LINE Messaging API
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def test_line_api():
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            profile = line_bot_api.get_bot_info()
            print(f"✅ LINE API 測試成功！Bot ID: {profile.bot_id}")
    except Exception as e:
        print(f"❌ LINE API 測試失敗: {e}")

def test_translator_key():
    path = '/translate'
    constructed_url = TRANSLATOR_ENDPOINT + path

    params = {'api-version': '3.0', 'from': 'en', 'to': ['fr']}
    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{'text': 'Hello'}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        print(f"Translator API Response: {response.status_code} {response.text}")
        response.raise_for_status()
        print("✅ Translator API Key 測試成功！")
    except Exception as e:
        print(f"❌ Translator API Key 測試失敗: {e}")

@app.route("/callback", methods=['POST'])
def callback():
    try:
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        print(f"📩 收到 Webhook Body: {body}")
        handler.handle(body, signature)
        print("✅ Webhook 處理成功！")
    except InvalidSignatureError:
        print("❌ Invalid Signature Error")
        abort(400)
    except Exception as e:
        print(f"❌ Webhook Exception: {e}")
        abort(500)
    return 'OK'

@handler.add("message", "text")
def handle_message(event):
    try:
        user_text = event.message.text
        print(f"👤 使用者訊息: {user_text}")

        translated_text = translate_text(user_text)
        print(f"📝 翻譯結果: {translated_text}")

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=translated_text)]
                )
            )
        print("✅ 成功回覆使用者！")
    except Exception as e:
        print(f"❌ Error in handle_message: {e}")

def translate_text(text):
    path = '/translate'
    constructed_url = TRANSLATOR_ENDPOINT + path

    params = {'api-version': '3.0', 'to': ['en']}
    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
        'Content-type': 'application/json'
    }
    body = [{'text': text}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        return result[0]['translations'][0]['text']
    except Exception as e:
        print(f"❌ 翻譯 API 錯誤: {e}")
        return "翻譯錯誤"

if __name__ == "__main__":
    test_line_api()
    test_translator_key()
    app.run(host='0.0.0.0', port=8000)
