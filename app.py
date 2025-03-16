from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import requests
import os
import uuid
import json

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
TRANSLATOR_KEY = os.getenv('TRANSLATOR_KEY')
TRANSLATOR_ENDPOINT = os.getenv('TRANSLATOR_ENDPOINT')  # https://eastasia.api.cognitive.microsoft.com
TRANSLATOR_LOCATION = os.getenv('TRANSLATOR_LOCATION')  # eastasia

# 初始化 LINE BOT
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Translator Key 測試 ---
def test_translator_key():
    path = '/translate'
    constructed_url = TRANSLATOR_ENDPOINT + path

    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': ['fr']  # 測試翻譯到法文
    }

    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': 'Hello'}]

    try:
        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        response = request.json()
        if request.status_code == 200:
            print("✅ Translator API Key is valid!")
        else:
            print(f"❌ Translator API Key test failed! Status: {request.status_code}, Response: {response}")
    except Exception as e:
        print(f"❌ Error testing Translator API Key: {e}")

# 呼叫 Key 測試
test_translator_key()

# --- 翻譯函數 ---
def translate_text(text):
    path = '/translator/text/v3.0/translate'
    constructed_url = TRANSLATOR_ENDPOINT + path

    params = {
        'api-version': '3.0',
        'from': 'auto',
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
        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        response = request.json()
        print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4))
        return response[0]['translations'][0]['text']
    except Exception as e:
        print(f"Error in translate_text: {e}")
        return "Translation failed"

# --- LINE Webhook ---
@app.route("/callback", methods=['POST'])
def callback():
    try:
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        print(f"Request Body: {body}")
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Signature Error!")
        abort(400)
    except Exception as e:
        print(f"Webhook Error: {e}")
        abort(500)
    return 'OK'

# --- 處理訊息事件 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_text = event.message.text
        print(f"Received message: {user_text}")
        translated_text = translate_text(user_text)
        print(f"Translated: {translated_text}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=translated_text)
        )
    except Exception as e:
        print(f"Error in handle_message: {e}")

# --- 啟動 Flask ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
