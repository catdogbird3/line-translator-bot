from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import requests
import os

app = Flask(__name__)

# LINE
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Translator
TRANSLATOR_KEY = os.getenv('TRANSLATOR_KEY')
TRANSLATOR_ENDPOINT = os.getenv('TRANSLATOR_ENDPOINT')
TRANSLATOR_LOCATION = os.getenv('TRANSLATOR_LOCATION')

print(f"LINE_CHANNEL_ACCESS_TOKEN: {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}")
print(f"LINE_CHANNEL_SECRET: {os.getenv('LINE_CHANNEL_SECRET')}")
print(f"TRANSLATOR_KEY: {os.getenv('TRANSLATOR_KEY')}")
print(f"TRANSLATOR_ENDPOINT: {os.getenv('TRANSLATOR_ENDPOINT')}")
print(f"TRANSLATOR_LOCATION: {os.getenv('TRANSLATOR_LOCATION')}")

@app.route("/callback", methods=['POST'])
def callback():
    try:
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        print(f"Request Body: {body}")  # 印出 LINE 傳進來的訊息

        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Signature Error!")  # 簽名驗證錯
        abort(400)
    except Exception as e:
        print(f"Unhandled Error: {e}")  # **這裡可以看到所有錯誤**
        abort(500)

    return 'OK'


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

def translate_text(text):
    path = '/translate'
    constructed_url = TRANSLATOR_ENDPOINT + path
    params = {
        'api-version': '3.0',
        'to': ['en']
    }
    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
        'Content-type': 'application/json'
    }
    body = [{'text': text}]
    response = requests.post(constructed_url, params=params, headers=headers, json=body)
    result = response.json()
    return result[0]['translations'][0]['text']

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
