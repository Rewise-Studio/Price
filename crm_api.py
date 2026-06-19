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
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
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
            "🆕 Новий",
            data.get("note", "")
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
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response

    except Exception as e:
        logger.error(f"Error creating order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response, 500

@app.route("/status", methods=["POST", "OPTIONS"])
def update_status():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        item_num = data.get("item_num", "")
        status = data.get("status", "")
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Вироби")
        all_rows = ws.get_all_values()
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        for i, row in enumerate(all_rows):
            if len(row) > 1 and row[1] == item_num:
                ws.update_cell(i + 1, 7, status)
                if status == "⚙️ В роботі":
                    ws.update_cell(i + 1, 9, now_str)
                elif status == "✅ Готово":
                    ws.update_cell(i + 1, 10, now_str)
                elif status == "📦 Виданий":
                    ws.update_cell(i + 1, 11, now_str)
                break
        # Check if all items issued — update order status
        order_num = item_num.rsplit("-", 1)[0]
        all_items = [r for r in all_rows[1:] if len(r) > 1 and r[0] == order_num]
        if all_items and all(r[6] == "📦 Виданий" for r in all_items if r[6]):
            ws_orders = sh.worksheet("Замовлення")
            orders = ws_orders.get_all_values()
            for i, row in enumerate(orders):
                if len(row) > 0 and row[0] == order_num:
                    ws_orders.update_cell(i + 1, 8, "📦 Виданий")
                    break
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response, 500


@app.route("/note", methods=["POST", "OPTIONS"])
def update_note():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        order_num = data.get("order_num", "")
        note = data.get("note", "")
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()
        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0] == order_num:
                ws.update_cell(i + 1, 9, note)
                break
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response, 500


@app.route("/material", methods=["POST", "OPTIONS"])
def save_material():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        name = (data.get("name") or "").strip()
        if not name:
            response = jsonify({"status": "error", "message": "Назва матеріалу обов'язкова"})
            response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
            return response, 400

        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        row_data = [
            name,
            data.get("packSize", ""),
            data.get("unit", ""),
            data.get("packPrice", ""),
            data.get("unitPrice", ""),
            data.get("supplier", ""),
            now_str,
        ]

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Матеріали")
        all_rows = ws.get_all_values()

        updated = False
        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0].strip().lower() == name.lower():
                ws.update(f"A{i + 1}:G{i + 1}", [row_data])
                updated = True
                break
        if not updated:
            ws.append_row(row_data)

        response = jsonify({"status": "ok", "updated": updated})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response
    except Exception as e:
        logger.error(f"Error saving material: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response, 500


@app.route("/economics", methods=["POST", "OPTIONS"])
def save_economics():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        service = (data.get("service") or "").strip()
        if not service:
            response = jsonify({"status": "error", "message": "Назва послуги обов'язкова"})
            response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
            return response, 400

        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        row_data = [
            service,
            data.get("price", ""),
            json.dumps(data.get("materials", []), ensure_ascii=False),
            data.get("materialsCost", ""),
            data.get("normHours", ""),
            data.get("hourRate", ""),
            data.get("timeCost", ""),
            data.get("overhead", ""),
            data.get("totalCost", ""),
            data.get("margin", ""),
            data.get("marginPct", ""),
            data.get("usdRate", ""),
            now_str,
        ]

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Економіка")
        all_rows = ws.get_all_values()

        updated = False
        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0].strip().lower() == service.lower():
                ws.update(f"A{i + 1}:M{i + 1}", [row_data])
                updated = True
                break
        if not updated:
            ws.append_row(row_data)

        response = jsonify({"status": "ok", "updated": updated})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response
    except Exception as e:
        logger.error(f"Error saving economics: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "https://rewise-studio.github.io"
        return response, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
