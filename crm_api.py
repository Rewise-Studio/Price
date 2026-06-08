import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

app = Flask(__name__)

def get_sheets_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS", "")
    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def get_next_order_num():
    client = get_sheets_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet("Налаштування")
    current = ws.cell(2, 2).value or 0
    next_num = int(current) + 1
    ws.update_cell(2, 2, next_num)
    return f"RW-{next_num:04d}"

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "service": "Rewise CRM API"})

@app.route("/order", methods=["POST", "OPTIONS"])
def create_order():
    # CORS headers
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        data = request.get_json()
        order_num = get_next_order_num()
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)

        # Замовлення
        ws_orders = sh.worksheet("Замовлення")
        ws_orders.append_row([
            order_num,
            data.get("date", ""),
            data.get("manager", ""),
            data.get("client", ""),
            data.get("phone", ""),
            data.get("payment", ""),
            data.get("deadline", ""),
            "🆕 Новий"
        ])

        # Вироби
        ws_items = sh.worksheet("Вироби")
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        for i, item in enumerate(data.get("items", []), 1):
            ws_items.append_row([
                order_num,
                f"{order_num}-{i}",
                item.get("type", ""),
                item.get("brand", ""),
                item.get("services", ""),
                item.get("total", ""),
                "🆕 Новий",
                now_str,
                "", "", ""
            ])

        response = jsonify({"status": "ok", "order_num": order_num})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        logger.error(f"Error creating order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
