from flask import Flask, request, abort

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    print("📩 收到 Webhook 訊息")
    return 'OK', 200  # 永遠回傳 200 OK，避免 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
