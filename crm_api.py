import os
import json
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

# Telegram-повідомлення про нові замовлення (той самий канал/група, що й бот)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8973167605:AAEea9K77DDQWLGrRvSc7BJFeLSRuuDtDOo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-5226279696")

app = Flask(__name__)


def send_telegram_notification(text):
    """Надсилає повідомлення в Telegram-групу. Помилка тут НЕ повинна ламати створення замовлення."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Telegram notify failed: {e}")


def _extract_amount(s):
    digits = "".join(ch for ch in str(s) if ch.isdigit())
    return int(digits) if digits else 0


def build_order_message(order_num, data):
    """Формує текст у тому ж стилі, що й повідомлення з Telegram-бота."""
    client_name = data.get("client", "")
    phone = data.get("phone", "")
    manager = data.get("manager", "")
    date_str = data.get("date", "")
    deadline = data.get("deadline", "")
    payment = data.get("payment", "")

    items_text = ""
    total = 0
    for i, item in enumerate(data.get("items", []), 1):
        item_num = f"{order_num}-{i}"
        item_type = item.get("type", "")
        item_brand = item.get("brand", "")
        services = item.get("services", "")
        item_total = _extract_amount(item.get("total", "0"))
        total += item_total
        label = f"{item_type} — {item_brand}" if item_brand else item_type
        items_text += f"\n👜 {item_num} — {label}\n  • {services} — {item_total} ₴\n"

    deadline_line = ""
    if "Терміново" in deadline:
        deadline_line = f"🔥 {deadline}\n"
    elif deadline:
        deadline_line = f"📆 {deadline}\n"

    return (
        f"📋 <b>REWISE STUDIO — Нове замовлення</b>\n\n"
        f"🔖 {order_num}\n"
        f"👤 {client_name}\n"
        f"📞 {phone}\n"
        f"👨‍💼 Прийняв: {manager}\n"
        f"📅 {date_str}\n"
        f"{deadline_line}"
        f"{items_text}\n"
        f"💰 Разом: {total} ₴\n"
        f"💳 Оплата: {payment}\n\n"
        f"Остаточна вартість узгоджується після огляду виробу\n\n"
        f"Rewise Studio"
    )


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


def get_next_tailor_num():
    """Лічильник замовлень на виготовлення — Налаштування, комірка B3."""
    client = get_sheets_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet("Налаштування")
    current = ws.cell(3, 2).value or 0
    next_num = int(current) + 1
    ws.update_cell(3, 2, next_num)
    return f"RW-V-{next_num:04d}"


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
        # Колонки: A Номер | B Дата | C Приймальник | D Клієнт | E Телефон |
        #          F Оплата | G Термін | H Статус | I Примітка |
        #          J Месенджер | K Спосіб передоплати | L Сума доплати |
        #          M Спосіб доплати | N Сповіщено
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
            data.get("note", ""),
            data.get("messenger", ""),          # J
            data.get("prepayMethod", ""),        # K спосіб передоплати
            "",                                   # L сума доплати (при видачі)
            "",                                   # M спосіб доплати (при видачі)
            "",                                   # N сповіщено
            "",                                   # O нараховано бонусів
            ""                                    # P списано бонусів
        ])

        # Вироби
        # Колонки: A Номер замовлення | B Номер виробу | C Тип | D Бренд |
        #          E Послуги | F Сума | G Статус | H Дата прийому |
        #          I Дата в роботі | J Дата готово | K Дата видачі | L Сповіщено
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
                "", "", "",
                ""                                # L сповіщено
            ])

        response = jsonify({"status": "ok", "order_num": order_num})
        response.headers["Access-Control-Allow-Origin"] = "*"

        # Сповіщення в Telegram — не блокує відповідь клієнту у разі помилки
        try:
            send_telegram_notification(build_order_message(order_num, data))
        except Exception as e:
            logger.error(f"Telegram notify error: {e}")

        return response
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/status", methods=["POST", "OPTIONS"])
def update_status():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
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

        # Оновлюємо загальний статус замовлення на основі статусів виробів.
        # Логіка:
        #   всі видані                       → 📦 Виданий
        #   частина видана, частина ні        → 🔸 Частково видано
        #   є готові (але не всі видані)       → ✅ Готово
        #   є в роботі                        → ⚙️ В роботі
        #   інакше                            → 🆕 Новий
        order_num = item_num.rsplit("-", 1)[0]
        all_items = [r for r in all_rows[1:] if len(r) > 0 and r[0] == order_num]
        # перечитуємо актуальні значення статусів (після оновлення поточного)
        statuses = []
        for r in all_items:
            s = r[6] if len(r) > 6 else ""
            # поточний рядок міг щойно змінитися — врахуємо це
            if len(r) > 1 and r[1] == item_num:
                s = status
            statuses.append(s)

        def order_status(sts):
            if not sts:
                return "🆕 Новий"
            issued = sum(1 for s in sts if s == "📦 Виданий")
            if issued == len(sts):
                return "📦 Виданий"
            if issued > 0:
                return "🔸 Частково видано"
            if any(s == "✅ Готово" for s in sts):
                return "✅ Готово"
            if any(s == "⚙️ В роботі" for s in sts):
                return "⚙️ В роботі"
            return "🆕 Новий"

        new_order_status = order_status(statuses)
        ws_orders = sh.worksheet("Замовлення")
        orders = ws_orders.get_all_values()
        for i, row in enumerate(orders):
            if len(row) > 0 and row[0] == order_num:
                ws_orders.update_cell(i + 1, 8, new_order_status)
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/note", methods=["POST", "OPTIONS"])
def update_note():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
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
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  СПОВІЩЕННЯ КЛІЄНТА (відмітка "сповіщено" по виробу)
#  Вироби, колонка L (12) = дата/час сповіщення або "" якщо знято
# ══════════════════════════════════════════════════════════════════════
@app.route("/notify", methods=["POST", "OPTIONS"])
def mark_notified():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        item_num = data.get("item_num", "")
        notified = data.get("notified", True)  # True → ставимо дату, False → знімаємо

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Вироби")
        all_rows = ws.get_all_values()
        val = datetime.now().strftime("%d.%m.%Y %H:%M") if notified else ""

        for i, row in enumerate(all_rows):
            if len(row) > 1 and row[1] == item_num:
                ws.update_cell(i + 1, 12, val)  # L
                break

        response = jsonify({"status": "ok", "value": val})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error marking notified: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  ДОПЛАТА ПРИ ВИДАЧІ
#  Замовлення: L (12) сума доплати | M (13) спосіб доплати
# ══════════════════════════════════════════════════════════════════════
@app.route("/settle", methods=["POST", "OPTIONS"])
def settle_order():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        order_num = data.get("order_num", "")
        amount = data.get("amount", "")
        method = data.get("method", "")

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()

        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0] == order_num:
                ws.update_cell(i + 1, 12, str(amount))   # L сума доплати
                ws.update_cell(i + 1, 13, method)         # M спосіб доплати
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error settling order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  МАТЕРІАЛИ
#  Лист "Матеріали":
#  A Назва | B Розмір упаковки | C Одиниця | D Ціна упаковки ₴ |
#  E Курс покупки | F Ціна упаковки $ | G Ціна за од. $ | H Постачальник | I Оновлено
# ══════════════════════════════════════════════════════════════════════

@app.route("/material", methods=["POST", "OPTIONS"])
def save_material():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        pack_size = float(data.get("packSize", 0) or 0)
        unit = data.get("unit", "")
        pack_price_uah = float(data.get("packPriceUah", 0) or 0)
        buy_rate = float(data.get("buyRate", 0) or 0)
        supplier = data.get("supplier", "")

        # Розрахунок доларових цін
        pack_price_usd = round(pack_price_uah / buy_rate, 4) if buy_rate else 0
        unit_price_usd = round(pack_price_usd / pack_size, 6) if pack_size else 0

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Матеріали")
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        row_values = [
            name, pack_size, unit, pack_price_uah,
            buy_rate, pack_price_usd, unit_price_usd, supplier, now_str
        ]

        # Якщо матеріал з такою назвою вже є — оновлюємо, інакше додаємо
        all_rows = ws.get_all_values()
        found = False
        for i, row in enumerate(all_rows):
            if i == 0:
                continue  # заголовок
            if len(row) > 0 and row[0].strip() == name:
                for col, val in enumerate(row_values, start=1):
                    ws.update_cell(i + 1, col, val)
                found = True
                break
        if not found:
            ws.append_row(row_values)

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error saving material: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/material/delete", methods=["POST", "OPTIONS"])
def delete_material():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        name = data.get("name", "").strip()

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Матеріали")
        all_rows = ws.get_all_values()

        for i, row in enumerate(all_rows):
            if i == 0:
                continue
            if len(row) > 0 and row[0].strip() == name:
                ws.delete_rows(i + 1)
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error deleting material: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  ЕКОНОМІКА (збереження розрахунків собівартості)
#  Лист "Економіка":
#  A Послуга | B Ціна | C Матеріали(JSON) | D Собів. матеріалів | E Норма-год |
#  F ₴/год | G Собів. часу | H Накладні | I Повна собів. | J Маржа |
#  K Маржа % | L Курс $ | M Оновлено
# ══════════════════════════════════════════════════════════════════════

@app.route("/economics", methods=["POST", "OPTIONS"])
def save_economics():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Економіка")
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        ws.append_row([
            data.get("service", ""),
            data.get("price", 0),
            json.dumps(data.get("materials", []), ensure_ascii=False),
            data.get("materialsCost", 0),
            data.get("normHours", 0),
            data.get("hourRate", 0),
            data.get("timeCost", 0),
            data.get("overhead", 0),
            data.get("totalCost", 0),
            data.get("margin", 0),
            data.get("marginPct", 0),
            data.get("usdRate", 0),
            now_str
        ])

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error saving economics: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/economics/delete", methods=["POST", "OPTIONS"])
def delete_economics():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        # Ідентифікуємо рядок за послугою + датою оновлення (унікальна пара)
        service = data.get("service", "").strip()
        updated = data.get("updated", "").strip()

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Економіка")
        all_rows = ws.get_all_values()

        for i, row in enumerate(all_rows):
            if i == 0:
                continue  # заголовок
            row_service = row[0].strip() if len(row) > 0 else ""
            row_updated = row[12].strip() if len(row) > 12 else ""
            if row_service == service and row_updated == updated:
                ws.delete_rows(i + 1)
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error deleting economics: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/economics/update", methods=["POST", "OPTIONS"])
def update_economics():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        match_service = data.get("matchService", "").strip()
        match_updated = data.get("matchUpdated", "").strip()

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Економіка")
        all_rows = ws.get_all_values()
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        new_values = [
            data.get("service", ""),
            data.get("price", 0),
            json.dumps(data.get("materials", []), ensure_ascii=False),
            data.get("materialsCost", 0),
            data.get("normHours", 0),
            data.get("hourRate", 0),
            data.get("timeCost", 0),
            data.get("overhead", 0),
            data.get("totalCost", 0),
            data.get("margin", 0),
            data.get("marginPct", 0),
            data.get("usdRate", 0),
            now_str
        ]

        for i, row in enumerate(all_rows):
            if i == 0:
                continue
            row_service = row[0].strip() if len(row) > 0 else ""
            row_updated = row[12].strip() if len(row) > 12 else ""
            if row_service == match_service and row_updated == match_updated:
                for col, val in enumerate(new_values, start=1):
                    ws.update_cell(i + 1, col, val)
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating economics: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  РЕДАГУВАННЯ ЗАМОВЛЕННЯ (клієнт / оплата / термін)
# ══════════════════════════════════════════════════════════════════════
@app.route("/order/update", methods=["POST", "OPTIONS"])
def update_order():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        order_num = data.get("order_num", "")

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()

        # Мапа поле → номер колонки
        field_cols = {
            "client": 4, "phone": 5, "payment": 6, "deadline": 7,
            "note": 9, "messenger": 10, "prepayMethod": 11
        }
        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0] == order_num:
                for field, col in field_cols.items():
                    if field in data:
                        ws.update_cell(i + 1, col, data[field])
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  РЕДАГУВАННЯ ВИРОБІВ ЗАМОВЛЕННЯ (перезапис усіх виробів замовлення)
#  Приймає order_num + items[] — видаляє старі рядки цього замовлення,
#  додає нові. Статуси та дати зберігаються для наявних (за номером виробу).
# ══════════════════════════════════════════════════════════════════════
@app.route("/items/update", methods=["POST", "OPTIONS"])
def update_items():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        order_num = data.get("order_num", "")
        items = data.get("items", [])

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Вироби")
        all_rows = ws.get_all_values()

        # Зберігаємо існуючі статуси/дати за номером виробу
        existing = {}
        for row in all_rows[1:]:
            if len(row) > 1 and row[0] == order_num:
                existing[row[1]] = row  # номер виробу → рядок

        # Видаляємо старі рядки цього замовлення (з кінця)
        for i in range(len(all_rows) - 1, 0, -1):
            if len(all_rows[i]) > 0 and all_rows[i][0] == order_num:
                ws.delete_rows(i + 1)

        # Додаємо оновлені
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        for idx, item in enumerate(items, 1):
            item_num = f"{order_num}-{idx}"
            old = existing.get(item_num)
            status = old[6] if old and len(old) > 6 else "🆕 Новий"
            d_in = old[7] if old and len(old) > 7 else now_str
            d_work = old[8] if old and len(old) > 8 else ""
            d_ready = old[9] if old and len(old) > 9 else ""
            d_issued = old[10] if old and len(old) > 10 else ""
            notified = old[11] if old and len(old) > 11 else ""
            ws.append_row([
                order_num, item_num,
                item.get("type", ""), item.get("brand", ""),
                item.get("services", ""), item.get("total", ""),
                status, d_in, d_work, d_ready, d_issued, notified
            ])

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating items: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  БОНУСИ
#  Замовлення: O (15) нараховано | P (16) списано
# ══════════════════════════════════════════════════════════════════════
@app.route("/bonus", methods=["POST", "OPTIONS"])
def update_bonus():
    """Оновлення бонусів замовлення (O нараховано / P списано)."""
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        order_num = data.get("order_num", "")
        accrued = data.get("accrued", None)   # нараховано
        spent = data.get("spent", None)       # списано

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()

        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0] == order_num:
                if accrued is not None:
                    ws.update_cell(i + 1, 15, str(accrued))  # O
                if spent is not None:
                    ws.update_cell(i + 1, 16, str(spent))    # P
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating bonus: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  РУЧНИЙ РЕЙТИНГ КЛІЄНТА
#  Замовлення: Q (17) Рейтинг вручну — пишемо в останній рядок цього телефону
#  Значення: "green" | "yellow" | "red" | "" (авто)
# ══════════════════════════════════════════════════════════════════════
@app.route("/client/rating", methods=["POST", "OPTIONS"])
def set_client_rating():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        phone = str(data.get("phone", "")).strip()
        rating = data.get("rating", "")

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()

        target_row = None
        for i, row in enumerate(all_rows):
            if i == 0:
                continue
            if len(row) > 4 and str(row[4]).strip() == phone:
                target_row = i + 1  # останній збіг
        if target_row:
            ws.update_cell(target_row, 17, rating)  # Q

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error setting client rating: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  ЗАДАЧІ
#  Лист "Задачі": A Текст | B Замовлення | C Статус | D Створено | E Виконано | F Дедлайн
# ══════════════════════════════════════════════════════════════════════
@app.route("/task", methods=["POST", "OPTIONS"])
def create_task():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Задачі")
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        ws.append_row([
            data.get("text", ""),
            data.get("order", ""),
            "ні",
            now_str,
            "",
            data.get("deadline", "")
        ])
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/task/toggle", methods=["POST", "OPTIONS"])
def toggle_task():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        text = data.get("text", "")
        created = data.get("created", "")
        done = data.get("done", True)

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Задачі")
        all_rows = ws.get_all_values()
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M") if done else ""

        for i, row in enumerate(all_rows):
            if i == 0:
                continue
            r_text = row[0] if len(row) > 0 else ""
            r_created = row[3] if len(row) > 3 else ""
            if r_text == text and r_created == created:
                ws.update_cell(i + 1, 3, "так" if done else "ні")
                ws.update_cell(i + 1, 5, now_str)
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error toggling task: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/task/delete", methods=["POST", "OPTIONS"])
def delete_task():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        text = data.get("text", "")
        created = data.get("created", "")

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Задачі")
        all_rows = ws.get_all_values()

        for i, row in enumerate(all_rows):
            if i == 0:
                continue
            r_text = row[0] if len(row) > 0 else ""
            r_created = row[3] if len(row) > 3 else ""
            if r_text == text and r_created == created:
                ws.delete_rows(i + 1)
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  ВИГОТОВЛЕННЯ
#  Лист "Виготовлення":
#  A Номер | B Дата створення | C Приймальник | D Ім'я клієнта | E Телефон |
#  F Месенджер | G Виріб | H Матеріал | I Мірки | J Умови | K Вартість |
#  L Оплата | M Спосіб передоплати | N Сума доплати | O Спосіб доплати |
#  P Термін | Q Статус | R Примітка | S Фото
# ══════════════════════════════════════════════════════════════════════
@app.route("/tailor", methods=["POST", "OPTIONS"])
def create_tailor():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        num = get_next_tailor_num()

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Виготовлення")
        ws.append_row([
            num,
            data.get("date", ""),
            data.get("manager", ""),
            data.get("client", ""),
            data.get("phone", ""),
            data.get("messenger", ""),
            data.get("product", ""),
            data.get("material", ""),
            data.get("measurements", ""),
            data.get("terms", ""),
            data.get("price", ""),
            data.get("payment", ""),
            data.get("prepayMethod", ""),
            "",                              # N сума доплати
            "",                              # O спосіб доплати
            data.get("deadline", ""),
            "🆕 Новий",
            data.get("note", ""),
            data.get("photo", ""),
            data.get("sketch", "")              # T Референс — фото-зразок, за яким шиємо
        ])

        response = jsonify({"status": "ok", "order_num": num})
        response.headers["Access-Control-Allow-Origin"] = "*"

        try:
            send_telegram_notification(
                f"✂️ <b>REWISE STUDIO — Виготовлення</b>\n\n"
                f"🔖 {num}\n"
                f"👤 {data.get('client','')}\n"
                f"📞 {data.get('phone','')}\n"
                f"👨‍💼 Прийняв: {data.get('manager','')}\n"
                f"📅 {data.get('date','')}\n\n"
                f"🧵 {data.get('product','')}\n"
                f"🎨 Матеріал: {data.get('material','')}\n"
                f"💰 Вартість: {data.get('price','')}\n"
                f"📆 Термін: {data.get('deadline','')}\n\n"
                f"Rewise Studio"
            )
        except Exception as e:
            logger.error(f"Telegram notify (tailor) error: {e}")

        return response
    except Exception as e:
        logger.error(f"Error creating tailor order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/tailor/update", methods=["POST", "OPTIONS"])
def update_tailor():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        num = data.get("order_num", "")

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Виготовлення")
        all_rows = ws.get_all_values()

        field_cols = {
            "client": 4, "phone": 5, "messenger": 6, "product": 7,
            "material": 8, "measurements": 9, "terms": 10, "price": 11,
            "payment": 12, "prepayMethod": 13, "settleAmount": 14,
            "settleMethod": 15, "deadline": 16, "status": 17,
            "note": 18, "photo": 19, "sketch": 20
        }
        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0] == num:
                for field, col in field_cols.items():
                    if field in data:
                        ws.update_cell(i + 1, col, data[field])
                break

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating tailor order: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  ПРАЙС
#  Лист "Прайс": A категорія | B (службова) | C відділ | D послуга |
#                E одиниця | F ціна | + колонка "Активна" (шукається за назвою)
# ══════════════════════════════════════════════════════════════════════
def _price_sheet(sh):
    return sh.worksheet("Прайс")


def _active_col_index(rows):
    """Шукає колонку 'Активна' у шапці. Повертає 1-based індекс або None."""
    if not rows:
        return None
    header = rows[0]
    for i, name in enumerate(header):
        if str(name).strip().lower() in ("активна", "активність", "active"):
            return i + 1
    return None


def _term_col_index(rows):
    """Шукає колонку терміну ('Термін'/'Строк'/'Срок'/'…виконання') у шапці."""
    if not rows:
        return None
    header = rows[0]
    for i, name in enumerate(header):
        lbl = str(name).strip().lower()
        if ("термін" in lbl) or ("строк" in lbl) or ("срок" in lbl) or ("виконан" in lbl):
            return i + 1
    return None


def _find_price_row(rows, category, dept, service):
    """Знаходить 1-based номер рядка за категорією, відділом і назвою послуги."""
    for i, row in enumerate(rows):
        if i == 0:
            continue
        c = row[0].strip() if len(row) > 0 else ""
        d = row[2].strip() if len(row) > 2 else ""
        s = row[3].strip() if len(row) > 3 else ""
        if c == category and d == dept and s == service:
            return i + 1
    return None


@app.route("/price/update", methods=["POST", "OPTIONS"])
def price_update():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = _price_sheet(sh)
        rows = ws.get_all_values()

        row = _find_price_row(rows, data.get("category",""), data.get("department",""), data.get("service",""))
        if not row:
            response = jsonify({"status": "error", "message": "Послугу не знайдено"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response, 404

        if "price" in data:
            ws.update_cell(row, 6, data["price"])
        if "unit" in data:
            ws.update_cell(row, 5, data["unit"])
        if "newName" in data and data["newName"]:
            ws.update_cell(row, 4, data["newName"])
        if "active" in data:
            col = _active_col_index(rows)
            if col:
                ws.update_cell(row, col, "так" if data["active"] else "ні")
        if "term" in data:
            tcol = _term_col_index(rows)
            if tcol:
                ws.update_cell(row, tcol, str(data.get("term", "")))

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating price: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/price/add", methods=["POST", "OPTIONS"])
def price_add():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        category = data.get("category", "")
        dept = data.get("department", "")
        service = data.get("service", "")
        unit = data.get("unit", "")
        price = data.get("price", "")

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = _price_sheet(sh)
        rows = ws.get_all_values()

        # Службову колонку B копіюємо з існуючого рядка тієї ж категорії
        col_b = ""
        width = len(rows[0]) if rows else 6
        for i, row in enumerate(rows):
            if i == 0:
                continue
            if len(row) > 1 and row[0].strip() == category:
                col_b = row[1]
                break

        new_row = [category, col_b, dept, service, unit, str(price)]
        active_col = _active_col_index(rows)
        term_col = _term_col_index(rows)
        while len(new_row) < width:
            new_row.append("")
        if active_col:
            new_row[active_col - 1] = "так"
        if term_col:
            while len(new_row) < term_col:
                new_row.append("")
            new_row[term_col - 1] = str(data.get("term", ""))

        ws.append_row(new_row)

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error adding price row: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


@app.route("/price/delete", methods=["POST", "OPTIONS"])
def price_delete():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = _price_sheet(sh)
        rows = ws.get_all_values()

        row = _find_price_row(rows, data.get("category",""), data.get("department",""), data.get("service",""))
        if row:
            ws.delete_rows(row)

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error deleting price row: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  НАЛАШТУВАННЯ (лист "Налаштування": ключ у колонці A, значення у B)
# ══════════════════════════════════════════════════════════════════════
@app.route("/settings/update", methods=["POST", "OPTIONS"])
def settings_update():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json()
        items = data.get("items", {})  # { "Бонус %": 3, ... }

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Налаштування")
        rows = ws.get_all_values()

        for key, value in items.items():
            found = None
            for i, row in enumerate(rows):
                if len(row) > 0 and str(row[0]).strip() == key:
                    found = i + 1
                    break
            if found:
                ws.update_cell(found, 2, str(value))
            else:
                ws.append_row([key, str(value)])

        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# ══════════════════════════════════════════════════════════════════════
#  БРЕНДИ (лист "Бренди": один стовпець A, заголовок "Бренд")
# ══════════════════════════════════════════════════════════════════════
@app.route("/brands/add", methods=["POST", "OPTIONS"])
def brands_add():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    try:
        data = request.get_json() or {}
        brands = data.get("brands", [])
        if isinstance(brands, str):
            brands = [brands]
        brands = [str(b).strip() for b in brands if str(b).strip()]
        if not brands:
            response = jsonify({"status": "ok", "added": 0})
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet("Бренди")
        except Exception:
            ws = sh.add_worksheet(title="Бренди", rows=200, cols=1)
            ws.update_cell(1, 1, "Бренд")

        existing = set()
        for row in ws.get_all_values():
            if row and str(row[0]).strip():
                existing.add(str(row[0]).strip().lower())

        added = 0
        for b in brands:
            if b.lower() not in existing:
                ws.append_row([b])
                existing.add(b.lower())
                added += 1

        response = jsonify({"status": "ok", "added": added})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error adding brands: {e}")
        response = jsonify({"status": "error", "message": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
