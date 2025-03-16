import os
from flask import Flask, request, abort

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    print("📩 收到 Webhook 訊息")
    return 'OK', 200  # 永遠回傳 200 OK，避免 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railway 會提供 PORT 變數
    app.run(host="0.0.0.0", port=port)
