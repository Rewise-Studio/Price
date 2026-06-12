import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = -5226279696
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

# ─── Google Sheets ───────────────────────────────────────────────────────────

def get_sheets_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS", "")
    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def get_partners():
    try:
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Партнери")
        values = ws.col_values(1)
        return [v for v in values if v and v != "Имя"]
    except Exception as e:
        logger.error(f"Error getting partners: {type(e).__name__}: {e}")
        return ["Сергей"]

def get_next_order_num():
    try:
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Налаштування")
        current = ws.cell(2, 2).value or 0
        next_num = int(current) + 1
        ws.update_cell(2, 2, next_num)
        return f"RW-{next_num:04d}"
    except Exception as e:
        logger.error(f"Error getting order num: {e}")
        now = datetime.now()
        return "RW-" + now.strftime("%y%m%d-%H%M")

def log_order(data, order_num, payment, deadline, manager):
    try:
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Лист Замовлення
        ws_orders = sh.worksheet("Замовлення")
        ws_orders.append_row([
            order_num,
            now_str,
            manager,
            data["client"],
            data["phone"],
            payment,
            deadline,
            "🆕 Новий"
        ])

        # Лист Вироби
        ws_items = sh.worksheet("Вироби")
        for i, item in enumerate(data["items"], 1):
            item_num = f"{order_num}-{i}"
            svcs_str = ", ".join([s["name"] for s in item["svcs"]])
            total = sum(s["total"] for s in item["svcs"])
            prefix = "от " if any(s["approx"] for s in item["svcs"]) else ""
            ws_items.append_row([
                order_num,
                item_num,
                item["type_label"],
                item["brand"],
                svcs_str,
                f"{prefix}{total:,} ₴".replace(",", " "),
                "🆕 Новий",
                now_str,
                "", "", ""
            ])
    except Exception as e:
        logger.error(f"Error logging order: {e}")

def get_active_orders():
    try:
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()
        active = [r for r in all_rows[1:] if len(r) > 7 and r[7] not in ["📦 Виданий"]]
        return active
    except Exception as e:
        logger.error(f"Error getting active orders: {e}")
        return []

def get_active_items(order_num=None):
    try:
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Вироби")
        all_rows = ws.get_all_values()
        items = [r for r in all_rows[1:] if len(r) > 6 and r[6] not in ["📦 Виданий"]]
        if order_num:
            items = [r for r in items if r[0] == order_num]
        return items
    except Exception as e:
        logger.error(f"Error getting active items: {e}")
        return []

def update_item_status(item_num, status):
    try:
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
                elif status == "⏳ Відкладено":
                    pass
                break
        # Проверяем все ли изделия заказа выданы
        order_num = item_num.rsplit("-", 1)[0]
        all_items = [r for r in all_rows[1:] if len(r) > 1 and r[0] == order_num]
        if all_items and all(r[6] == "📦 Виданий" for r in all_items):
            ws_orders = sh.worksheet("Замовлення")
            orders = ws_orders.get_all_values()
            for i, row in enumerate(orders):
                if len(row) > 0 and row[0] == order_num:
                    ws_orders.update_cell(i + 1, 8, "📦 Виданий")
                    break
    except Exception as e:
        logger.error(f"Error updating item status: {e}")

def update_order_price(order_num, price_str):
    try:
        client = get_sheets_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet("Замовлення")
        all_rows = ws.get_all_values()
        for i, row in enumerate(all_rows):
            if len(row) > 0 and row[0] == order_num:
                # Добавляем подтверждённую сумму в статус
                ws.update_cell(i + 1, 8, "✅ Підтверджено")
                break
    except Exception as e:
        logger.error(f"Error updating order price: {e}")


# ─── Состояния диалога ────────────────────────────────────────────────────────

(MANAGER, NAME, PHONE, ITEM_TYPE, BRAND, DEPT, SERVICE,
 MANUAL_SVC_NAME, MANUAL_SVC_PRICE, QTY, EXTRA200, NEXT,
 PAYMENT, PREPAY_AMOUNT, DEADLINE,
 CONFIRM_ORDER, CONFIRM_PRICE,
 ISSUED_ORDER, ISSUED_ITEM,
 STATUS_ORDER, STATUS_ITEM, STATUS_CHOOSE) = range(22)

BTN_BACK = "↩️ Назад"
BTN_CANCEL = "❌ Скасувати"
BTN_MANUAL = "✏️ Ввести вручну"

STATUSES = ["⚙️ В роботі", "✅ Готово", "⏳ Відкладено", "📦 Виданий"]

DEPTS = {
    "shoes": [
        ("cleaning", "Чистка / Базовий догляд"),
        ("painting", "Фарбування / Реставрація"),
        ("heels",    "Каблуки та набійки"),
        ("sole",     "Підошва"),
        ("zippers",  "Блискавки"),
        ("hardware", "Фурнітура"),
        ("sewing",   "Швейні роботи та деталі"),
        ("stretch",  "Розтяжка"),
    ],
    "bags": [
        ("cleaning", "Чистка / Базовий догляд"),
        ("painting", "Фарбування / Реставрація"),
        ("handles",  "Ручки та ремінь"),
        ("zippers",  "Блискавки"),
        ("hardware", "Фурнітура"),
        ("sewing",   "Швейні роботи та деталі"),
        ("lining",   "Підкладка"),
        ("edges",    "Реставрація урізів"),
        ("belt",     "Поясний ремінь"),
    ],
}

SERVICES = {
    'shoes': {
        'cleaning': [
            ('Чистка — літнє взуття', 'пара', 1200, False),
            ('Чистка — низьке взуття', 'пара', 1400, False),
            ('Чистка — середнє взуття', 'пара', 1600, False),
            ('Чистка — високі чоботи', 'пара', 1800, False),
            ('Чистка — UGG та хутряне', 'пара', 1400, False),
            ('Базовий догляд — низьке взуття', 'пара', 1400, False),
            ('Базовий догляд — середнє взуття', 'пара', 1600, False),
            ('Базовий догляд — високі чоботи', 'пара', 1800, False),
            ('Базовий догляд — UGG та хутряне', 'пара', 1400, False),
        ],
        'painting': [
            ('Фарбування — літнє взуття', 'пара', 1400, False),
            ('Фарбування — низьке взуття', 'пара', 1800, False),
            ('Фарбування — середнє взуття', 'пара', 2000, False),
            ('Фарбування — високі чоботи', 'пара', 2800, False),
            ('Фарбування — UGG та хутряне', 'пара', 1800, False),
            ('Фарбування / відбілювання Midsole (бокова частина підошви)', 'пара', 1100, False),
            ('Відбілювання підошви взуття Loro Piana', 'пара', 1100, False),
            ('Фарбування каблуків', 'пара', 900, False),
            ('Фарбування ранта взуття', 'пара', 700, False),
            ('Фарбування танкетки', 'пара', 1200, False),
            ('Глясаж — полірування гладкої шкіри до блиску (окрема послуга)', 'пара', 600, False),
            ('Реставрація — літнє взуття', 'пара', 1600, True),
            ('Реставрація — низьке взуття', 'пара', 2000, True),
            ('Реставрація — середнє взуття', 'пара', 2200, True),
            ('Реставрація — високі чоботи', 'пара', 3200, True),
            ('Реставрація — UGG та хутряне', 'пара', 2400, True),
            ('Реставрація носочної частини взуття', 'пара', 1200, True),
            ('Реставрація каблуків (гладка шкіра)', 'пара', 900, True),
            ('Реставрація каблуків (лакова шкіра)', 'пара', 1200, True),
            ('Реставрація устілок — відкрите літнє взуття', 'пара', 1200, True),
            ('Усунення пошкоджень верху взуття', '1 место', 1000, True),
        ],
        'heels': [
            ('Набійки листові', 'пара', 700, False),
            ('Набійки формовані', 'пара', 850, False),
            ('Набійки штифтові поліуретанові', 'пара', 550, False),
            ('Набійки металеві', 'пара', 700, False),
            ('Нарощування каблуків', 'пара', 400, False),
            ('Вирівнювання каблука під набійку', 'пара', 250, False),
            ('Демонтаж металевого штифта', 'пара', 250, False),
            ('Заміна каблуків без обтяжки', 'пара', 1800, False),
            ('Заміна каблуків з обтяжкою шкірою', 'пара', 2600, False),
            ('Заміна обтяжки каблуків — нова набійка включена', 'пара', 2400, False),
            ('Заміна обтяжки танкетки', 'пара', 2600, False),
            ('Закріплення каблука', '1 шт.', 400, False),
        ],
        'sole': [
            ('Профілактика жіноча', 'пара', 1200, False),
            ('Профілактика чоловіча', 'пара', 1200, False),
            ('Профілактика жіноча комбінована', 'пара', 1500, False),
            ('Профілактика на всю площу підошви', 'пара', 1400, False),
            ('Профілактика повний слід спортивного взуття', 'пара', 1800, False),
            ('Нарощування носочної частини підошви', 'пара', 400, False),
            ('Полірування ранта взуття', 'пара', 400, False),
            ('Локальна підклейка', '1 место', 300, False),
            ('Підклейка підошви по периметру', 'пара', 600, False),
            ('Переклейка підошви / сліду', 'пара', 900, False),
            ('Переклейка + прошивка підошви', 'пара', 1400, False),
            ('Підклейка / переклейка устілок', 'пара', 400, False),
            ('Прошивка підошви', 'пара', 800, False),
            ('Прошивка підошви сегментами', 'пара', 600, False),
            ('Виготовлення та заміна основних устілок із картону', 'пара', 700, False),
            ('Перетяжка основних устілок — відкрите взуття', 'пара', 2600, False),
            ('Перетяжка устілок у носочній частині — відкрите взуття', 'пара', 1600, False),
            ('Тиснення брендового лого на устілці', 'пара', 600, False),
            ('Заміна задників взуття', 'пара', 900, False),
            ('Заміна задників з розбором підошви', 'пара', 1300, False),
            ('Заміна гумової підошви', 'пара', 2400, False),
            ('Заміна підошви кожволон', 'пара', 3000, False),
            ('Заміна шкіряної підошви — клейовий метод', 'пара', 4000, False),
            ('Заміна шкіряної підошви — прошивний метод', 'пара', 6000, False),
            ('Заміна підошви Loro Piana', 'пара', 4000, False),
            ('Заміна підошви Golden Goose', 'пара', 4000, False),
            ('Заміна супінатора', '1 шт.', 600, False),
        ],
        'sewing': [
            ('Відновлення машинної строчки (одне місце)', '1 место', 300, False),
            ('Відновлення ручної строчки (одне місце)', '1 место', 500, False),
            ('Виготовлення та заміна шкіряних устілок — закрите взуття', 'пара', 900, False),
            ('Виготовлення та заміна шкіряних устілок — відкрите взуття', 'пара', 900, False),
            ('Заміна підкладки задника із сітки', 'пара', 1600, False),
            ('Заміна підкладки задника Balenciaga', 'пара', 1800, False),
            ('Заміна кармана задника зі шкіри', 'пара', 1300, False),
            ('Заміна підкладки задника зі шкіри', 'пара', 2000, False),
            ('Внутрішня латка', '1 шт.', 450, False),
            ('Декоративна латка', '1 шт.', 600, False),
            ('Виготовлення та заміна нової деталі взуття', '1 шт.', 700, False),
            ('Заміна союзки у кросівках', 'пара', 1600, False),
            ('Внутрішня латка у носочній частині кросівок', '1 шт.', 400, False),
            ('Заміна деталей верху у босоніжках', 'пара', 2800, False),
            ('Ушивання халяви — по висоті', 'пара', 1600, False),
            ('Ушивання халяви — по ширині', 'пара', 2000, False),
            ('Заміна резинок з обтяжкою шкірою', 'пара', 900, False),
            ('Заміна резинок на пряжках взуття', 'пара', 500, False),
            ('Заміна взуттєвої резинки в халяві', '1 шт.', 500, False),
            ('Вшивання резинок в халяву', 'пара', 1600, False),
            ('Заміна липучок', 'пара', 550, False),
            ('Виготовлення та заміна ремінців взуття', 'пара', 1600, False),
        ],
        'zippers': [
            ('Заміна блискавки до 20 см (без вартості матеріалу)', '1 шт.', 700, False),
            ('Заміна блискавки від 21 см (без вартості матеріалу)', '1 шт.', 900, False),
            ('Заміна бігунка блискавки', '1 шт.', 300, False),
            ('Врізання блискавки у халяву (без вартості матеріалу)', 'пара', 2200, False),
        ],
        'stretch': [
            ('Розтяжка взуття у підйомі / ширина', 'пара', 600, False),
            ('Розтяжка халяви чобіт / черевиків', 'пара', 1000, False),
        ],
        'hardware': [
            ('Заміна гачків + резинка', 'пара', 500, False),
            ('Заміна пряжки (без вартості матеріалу)', 'пара', 450, False),
            ('Заміна блочка та люверса', '1 шт.', 200, False),
            ('Заміна кнопки (без розбору виробу)', '1 шт.', 200, False),
        ],
    },
    'bags': {
        'cleaning': [
            ('Чистка — шкіряна сумка S', '1 шт.', 1400, False),
            ('Чистка — шкіряна сумка M', '1 шт.', 1600, False),
            ('Чистка — шкіряна сумка L', '1 шт.', 1800, False),
            ('Чистка — текстильна сумка S', '1 шт.', 1400, False),
            ('Чистка — текстильна сумка M', '1 шт.', 1600, False),
            ('Чистка — текстильна сумка L', '1 шт.', 1800, False),
        ],
        'painting': [
            ('Фарбування — шкіряна сумка S', '1 шт.', 1800, False),
            ('Фарбування — шкіряна сумка M', '1 шт.', 2200, False),
            ('Фарбування — шкіряна сумка L', '1 шт.', 2600, False),
            ('Фарбування — поясний ремінь', '1 шт.', 1400, False),
            ('Реставрація — шкіряна сумка S', '1 шт.', 2200, True),
            ('Реставрація — шкіряна сумка M', '1 шт.', 2700, True),
            ('Реставрація — шкіряна сумка L', '1 шт.', 3200, True),
            ('Локальна реставрація шкіри сумки', '1 место', 1000, True),
            ('Реставрація кутиків сумки', '1 место', 450, True),
            ('Реставрация ручок сумки', 'пара', 1600, True),
            ('Реставрація плечового ременя сумки', '1 шт.', 1600, True),
        ],
        'edges': [
            ('Торцювання урізу шкіри', '1 см', 12, False),
            ('Торцювання ручок сумки (2 сторони)', 'пара', 1200, False),
            ('Торцювання ручок сумки (4 сторони)', 'пара', 1400, False),
            ('Торцювання плечового ременя сумки', '1 шт.', 1400, False),
            ('Торцювання тренчика / пулера / тримача ручок', '1 шт.', 400, False),
        ],
        'sewing': [
            ('Відновлення машинного шва сумки', '1 место', 300, False),
            ('Підклейка шкіри / деталі сумки', '1 место', 300, False),
            ('Ремонт кріплення ручок сумки (без заміни деталей)', '1 шт.', 450, False),
            ('Виготовлення шкіряного пулера на бігунок', '1 шт.', 500, False),
            ('Виготовлення та заміна тренчика сумки', '1 шт.', 500, False),
            ('Виготовлення та перешивання деталей сумки', '1 шт.', 900, False),
            ('Виготовлення та заміна настрочних кріплень ручок сумки', '1 шт.', 600, False),
            ('Виготовлення та заміна втачних кріплень ручок сумки', '1 шт.', 400, False),
            ('Заміна канту у гаманці / клатчі', '1 шт.', 1200, False),
            ('Заміна окантовки сумки — кедер', '1 шт.', 1200, False),
        ],
        'hardware': [
            ('Заміна карабіна сумки (без вартості матеріалу)', '1 шт.', 250, False),
            ('Заміна пряжки ременя сумки (без вартості матеріалу)', '1 шт.', 250, False),
            ('Заміна кнопки / заклепки / люверса сумки', '1 шт.', 200, False),
            ('Заміна магніту сумки (без вартості матеріалу)', '1 шт.', 500, False),
            ('Встановлення декоративної латки', '1 шт.', 900, False),
            ('Встановлення внутрішньої латки', '1 шт.', 450, False),
            ('Встановлення кільця / напівкільця (без вартості матеріалу)', '1 шт.', 250, False),
        ],
        'zippers': [
            ('Заміна блискавки сумки до 25 см (без вартості матеріалу)', '1 шт.', 1400, False),
            ('Заміна блискавки сумки від 25 см (без вартості матеріалу)', '1 шт.', 1600, False),
            ('Заміна блискавки у гаманці / органайзері (без вартості матеріалу)', '1 шт.', 1800, False),
            ('Заміна блискавки рюкзака / великої сумки (без вартості матеріалу)', '1 шт.', 1600, False),
            ('Заміна бігунка блискавки сумки', '1 шт.', 300, False),
        ],
        'handles': [
            ('Вкорочення плечового ременя сумки', '1 шт.', 450, False),
            ('Заміна плечового ременя сумки з підбором шкіри', '1 шт.', 2000, False),
            ('Заміна ручок сумки типу шопер', 'пара', 1600, False),
            ('Заміна ручок шкіряної сумки з підбором шкіри', 'пара', 2800, False),
            ('Заміна ручок рюкзака з наповнювачем', 'пара', 3200, False),
            ('Пробивання отворів в плечовому ремені', '1 шт.', 200, False),
        ],
        'lining': [
            ('Заміна підкладки — сумка S', '1 шт.', 1800, False),
            ('Заміна підкладки — сумка M', '1 шт.', 2200, False),
            ('Заміна підкладки — сумка L', '1 шт.', 2600, False),
            ('Заміна підкладки — гаманець / органайзер', '1 шт.', 2600, False),
        ],
        'belt': [
            ('Пробивання отворів', '1 шт.', 200, False),
            ('Вкорочення шкіряного поясного ременя', '1 шт.', 450, False),
            ('Вкорочення поясного ременя з перешиванням пряжки', '1 шт.', 600, False),
            ('Заміна підкладу поясного ременя', '1 шт.', 2000, False),
            ('Реставрація поясного ременя (проклейка, прошивка)', '1 шт.', 800, False),
        ],
    },
}


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def fmt(n):
    return f"{n:,}".replace(",", " ") + " ₴"

def kb(buttons, cols=2, add_back=False, add_cancel=False):
    rows = []
    for i in range(0, len(buttons), cols):
        rows.append(list(buttons[i:i+cols]))
    extra = []
    if add_back:
        extra.append(BTN_BACK)
    if add_cancel:
        extra.append(BTN_CANCEL)
    if extra:
        rows.append(extra)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

def get_data(ctx):
    if "order" not in ctx.user_data:
        ctx.user_data["order"] = {
            "client": "", "phone": "", "manager": "",
            "items": [],
            "cur": {"type": None, "type_label": "", "brand": "", "svcs": []},
            "total_fixed": 0, "total_approx": 0, "has_approx": False,
        }
    return ctx.user_data["order"]

def commit_item(d):
    cur = d["cur"]
    if cur["svcs"]:
        for svc in cur["svcs"]:
            if svc["approx"]:
                d["total_approx"] += svc["total"]
            else:
                d["total_fixed"] += svc["total"]
        d["items"].append({
            "type_label": cur["type_label"],
            "brand": cur["brand"],
            "svcs": list(cur["svcs"])
        })
    d["cur"] = {"type": None, "type_label": "", "brand": "", "svcs": []}


# ─── /start — новый заказ ─────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    get_data(ctx)
    partners = get_partners()
    await update.message.reply_text(
        "👋 Rewise Studio\n\nХто приймає замовлення?",
        reply_markup=kb(partners, cols=2, add_cancel=True)
    )
    return MANAGER

async def get_manager(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    d = get_data(ctx)
    d["manager"] = text
    await update.message.reply_text("*Ім'я клієнта?*", parse_mode="Markdown",
        reply_markup=kb([], add_back=True, add_cancel=True))
    return NAME

async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        partners = get_partners()
        await update.message.reply_text("Хто приймає замовлення?",
            reply_markup=kb(partners, cols=2, add_cancel=True))
        return MANAGER
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    get_data(ctx)["client"] = text
    await update.message.reply_text("📞 *Номер телефону?*", parse_mode="Markdown",
        reply_markup=kb([], add_back=True, add_cancel=True))
    return PHONE

async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("*Ім'я клієнта?*", parse_mode="Markdown",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return NAME
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    d = get_data(ctx)
    d["phone"] = text
    d["cur"] = {"type": None, "type_label": "", "brand": "", "svcs": []}
    is_first = len(d["items"]) == 0
    msg = "Який виріб приніс клієнт?" if is_first else "+ Ще одна річ — який виріб?"
    await update.message.reply_text(msg,
        reply_markup=kb(["👟 Взуття", "👜 Сумка / Аксесуар"], cols=2, add_back=True, add_cancel=True))
    return ITEM_TYPE

async def get_item_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("📞 *Номер телефону?*", parse_mode="Markdown",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return PHONE
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    d = get_data(ctx)
    if "Обувь" in text:
        d["cur"]["type"] = "shoes"
        d["cur"]["type_label"] = "Обувь"
    else:
        d["cur"]["type"] = "bags"
        d["cur"]["type_label"] = "Сумка"
    await update.message.reply_text("🏷 Бренд и модель?\n_(или «без бренда»)_", parse_mode="Markdown",
        reply_markup=kb([], add_back=True, add_cancel=True))
    return BRAND

async def get_brand(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        d = get_data(ctx)
        is_first = len(d["items"]) == 0
        msg = "Який виріб приніс клієнт?" if is_first else "+ Ще одна річ — який виріб?"
        await update.message.reply_text(msg,
            reply_markup=kb(["👟 Взуття", "👜 Сумка / Аксесуар"], cols=2, add_back=True, add_cancel=True))
        return ITEM_TYPE
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    d = get_data(ctx)
    d["cur"]["brand"] = text
    depts = DEPTS[d["cur"]["type"]]
    dept_buttons = [label for _, label in depts]
    await update.message.reply_text(
        f"*{d['cur']['type_label']} — {d['cur']['brand']}*\n\nЯкий відділ?",
        parse_mode="Markdown",
        reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
    return DEPT

async def get_dept(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("🏷 Бренд и модель?\n_(или «без бренда»)_", parse_mode="Markdown",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return BRAND
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    d = get_data(ctx)
    depts = DEPTS[d["cur"]["type"]]
    dept_id = next((did for did, dlabel in depts if dlabel == text), None)
    if not dept_id:
        dept_buttons = [label for _, label in depts]
        await update.message.reply_text("Оберіть відділ зі списку.",
            reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
        return DEPT
    ctx.user_data["dept_id"] = dept_id
    ctx.user_data["dept_label"] = text
    svcs = SERVICES[d["cur"]["type"]][dept_id]
    svc_buttons = [f"{name} — {'от ' if a else ''}{fmt(p)}" for name, u, p, a in svcs]
    svc_buttons.append(BTN_MANUAL)
    await update.message.reply_text(f"*{text}*\n\nОберіть послугу:", parse_mode="Markdown",
        reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
    return SERVICE

async def get_service(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        d = get_data(ctx)
        depts = DEPTS[d["cur"]["type"]]
        dept_buttons = [label for _, label in depts]
        await update.message.reply_text(
            f"*{d['cur']['type_label']} — {d['cur']['brand']}*\n\nЯкий відділ?",
            parse_mode="Markdown",
            reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
        return DEPT
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("✏️ Введіть назву послуги:",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return MANUAL_SVC_NAME
    d = get_data(ctx)
    dept_id = ctx.user_data["dept_id"]
    svcs = SERVICES[d["cur"]["type"]][dept_id]
    chosen = next(((n, u, p, a) for n, u, p, a in svcs
                   if f"{n} — {'от ' if a else ''}{fmt(p)}" == text), None)
    if not chosen:
        svc_buttons = [f"{n} — {'от ' if a else ''}{fmt(p)}" for n, u, p, a in svcs]
        svc_buttons.append(BTN_MANUAL)
        await update.message.reply_text("Оберіть послугу зі списку.",
            reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
        return SERVICE
    ctx.user_data["chosen_svc"] = chosen
    await update.message.reply_text(f"Кількість ({chosen[1]}):",
        reply_markup=kb(["1", "2", "3", "Більше"], cols=4, add_back=True, add_cancel=True))
    return QTY

async def get_manual_svc_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        d = get_data(ctx)
        dept_id = ctx.user_data["dept_id"]
        dept_label = ctx.user_data["dept_label"]
        svcs = SERVICES[d["cur"]["type"]][dept_id]
        svc_buttons = [f"{n} — {'от ' if a else ''}{fmt(p)}" for n, u, p, a in svcs]
        svc_buttons.append(BTN_MANUAL)
        await update.message.reply_text(f"*{dept_label}*\n\nОберіть послугу:", parse_mode="Markdown",
            reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
        return SERVICE
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    ctx.user_data["manual_svc_name"] = text
    await update.message.reply_text("💰 Введіть ціну (тільки цифри):",
        reply_markup=kb([], add_back=True, add_cancel=True))
    return MANUAL_SVC_PRICE

async def get_manual_svc_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("✏️ Введіть назву послуги:",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return MANUAL_SVC_NAME
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    try:
        price = int(text.replace(" ", "").replace("₴", ""))
    except ValueError:
        await update.message.reply_text("Введіть ціну цифрами, наприклад: 500")
        return MANUAL_SVC_PRICE
    ctx.user_data["chosen_svc"] = (f"📝 {ctx.user_data['manual_svc_name']}", "шт.", price, False)
    await update.message.reply_text("Количество:",
        reply_markup=kb(["1", "2", "3", "Більше"], cols=4, add_back=True, add_cancel=True))
    return QTY

async def get_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        d = get_data(ctx)
        dept_id = ctx.user_data["dept_id"]
        dept_label = ctx.user_data["dept_label"]
        svcs = SERVICES[d["cur"]["type"]][dept_id]
        svc_buttons = [f"{n} — {'от ' if a else ''}{fmt(p)}" for n, u, p, a in svcs]
        svc_buttons.append(BTN_MANUAL)
        await update.message.reply_text(f"*{dept_label}*\n\nОберіть послугу:", parse_mode="Markdown",
            reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
        return SERVICE
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    chosen = ctx.user_data["chosen_svc"]
    name, unit, price, approx = chosen
    try:
        qty = int(text)
    except ValueError:
        qty = 1
    total = price * qty
    ctx.user_data["pending_svc"] = {
        "name": name, "unit": unit, "price": price,
        "approx": approx, "qty": qty, "total": total, "extra200": False
    }
    dept_id = ctx.user_data.get("dept_id", "")
    if dept_id in ("cleaning", "painting"):
        await update.message.reply_text(
            "Дополнительный цвет или материал?\n_(замша + кожа, лак и т.д.)_",
            parse_mode="Markdown",
            reply_markup=kb(["✅ Так — +200 ₴", "❌ Ні"], cols=2, add_back=True, add_cancel=True))
        return EXTRA200
    return await save_service(update, ctx, extra200=False)

async def get_extra200(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        chosen = ctx.user_data["chosen_svc"]
        await update.message.reply_text(f"Кількість ({chosen[1]}):",
            reply_markup=kb(["1", "2", "3", "Більше"], cols=4, add_back=True, add_cancel=True))
        return QTY
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    return await save_service(update, ctx, extra200="Да" in text)

async def save_service(update, ctx, extra200):
    d = get_data(ctx)
    svc = ctx.user_data["pending_svc"]
    if extra200:
        svc["extra200"] = True
        svc["total"] += 200
    if svc["approx"]:
        d["has_approx"] = True
    d["cur"]["svcs"].append(svc)
    price_str = f"{'от ' if svc['approx'] else ''}{fmt(svc['total'])}"
    extra_str = " + 200 ₴ (дод. матеріал)" if extra200 else ""
    await update.message.reply_text(
        f"✓ Додано: {svc['name']}\n{price_str}{extra_str}",
        reply_markup=kb(["➕ Ще одна послуга", "➕ Ще одна річ", "✅ Завершити замовлення"], cols=1, add_cancel=True))
    return NEXT

async def get_next(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if "услуга" in text.lower():
        depts = DEPTS[d["cur"]["type"]]
        dept_buttons = [label for _, label in depts]
        await update.message.reply_text("Який відділ?",
            reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
        return DEPT
    elif "вещь" in text.lower():
        commit_item(d)
        await update.message.reply_text("Який виріб?",
            reply_markup=kb(["👟 Взуття", "👜 Сумка / Аксесуар"], cols=2, add_back=True, add_cancel=True))
        return ITEM_TYPE
    elif "завершить" in text.lower():
        commit_item(d)
        await update.message.reply_text("💳 Тип оплати?",
            reply_markup=kb(["💳 Передоплата", "📦 Післяоплата"], cols=2, add_cancel=True))
        return PAYMENT
    else:
        await update.message.reply_text("Оберіть дію:",
            reply_markup=kb(["➕ Ще одна послуга", "➕ Ще одна річ", "✅ Завершити замовлення"], cols=1, add_cancel=True))
        return NEXT

async def get_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    ctx.user_data["payment_type"] = text
    if "Предоплата" in text:
        await update.message.reply_text("💰 Введіть суму передоплати (тільки цифри):",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return PREPAY_AMOUNT
    ctx.user_data["payment"] = text
    await update.message.reply_text("📅 Термін виконання?",
        reply_markup=kb(["⚡ Терміново", "🕐 Без терміну", "📅 Вказати дату"], cols=2, add_back=True, add_cancel=True))
    return DEADLINE

async def get_prepay_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("💳 Тип оплати?",
            reply_markup=kb(["💳 Передоплата", "📦 Післяоплата"], cols=2, add_cancel=True))
        return PAYMENT
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    try:
        amount = int(text.replace(" ", "").replace("₴", ""))
        ctx.user_data["payment"] = f"Передоплата: {fmt(amount)}"
    except ValueError:
        await update.message.reply_text("Введіть суму цифрами, наприклад: 500")
        return PREPAY_AMOUNT
    await update.message.reply_text("📅 Термін виконання?",
        reply_markup=kb(["⚡ Терміново", "🕐 Без терміну", "📅 Вказати дату"], cols=2, add_back=True, add_cancel=True))
    return DEADLINE

async def get_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("💳 Тип оплати?",
            reply_markup=kb(["💳 Передоплата", "📦 Післяоплата"], cols=2, add_cancel=True))
        return PAYMENT
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if "Указать дату" in text:
        await update.message.reply_text("Введіть дату (наприклад: 10.06 або п'ятниця):",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return DEADLINE
    ctx.user_data["deadline"] = text
    await finish_order(update, ctx)
    return ConversationHandler.END

async def finish_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    total = d["total_fixed"] + d["total_approx"]
    now = datetime.now()
    order_num = get_next_order_num()
    now_str = now.strftime("%d.%m.%Y | %H:%M")
    payment = ctx.user_data.get("payment", "—")
    deadline = ctx.user_data.get("deadline", "Без срока")
    prefix = "от " if d["has_approx"] else ""

    lines = [
        "📋 *REWISE STUDIO — Нове замовлення*", "",
        f"🔖 *{order_num}*",
        f"👤 {d['client']}",
        f"📞 {d['phone']}",
        f"👨‍💼 Прийняв: {d['manager']}",
        f"📅 {now_str}", "",
    ]
    for i, item in enumerate(d["items"], 1):
        icon = "👟" if "Обув" in item["type_label"] else "👜"
        item_num = f"{order_num}-{i}"
        lines.append(f"{icon} *{item_num} — {item['type_label']} — {item['brand']}*")
        for svc in item["svcs"]:
            price_str = f"{'от ' if svc['approx'] else ''}{fmt(svc['total'])}"
            extra = " +200 ₴" if svc.get("extra200") else ""
            warn = " ⚠️ уточнить" if svc["approx"] else ""
            lines.append(f"  • {svc['name']} — {price_str}{extra}{warn}")
        lines.append("")

    lines.append(f"💰 *Разом: {prefix}{fmt(total)}*")
    if d["has_approx"]:
        lines.append("⚠️ _Є позиції для уточнення після огляду_")
    lines.append(f"💳 Оплата: {payment}")
    if "Срочно" in deadline:
        lines.append("⚡ *СРОЧНО*")
    elif deadline not in ("Без срока", "🕐 Без терміну"):
        lines.append(f"📅 Термін: {deadline}")
    lines.append("")
    lines.append("_Остаточна вартість узгоджується після огляду виробу_")
    lines.append("\nRewise Studio")

    await update.message.reply_text(
        f"✅ Замовлення *{order_num}* сформовано!\n\n💰 {prefix}{fmt(total)}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove())
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text="\n".join(lines), parse_mode="Markdown")
    log_order(d, order_num, payment, deadline, d["manager"])
    await update.message.reply_text(
        "Карточка отправлена в канал ✓\n\nДля нового заказа нажми /start",
        reply_markup=ReplyKeyboardRemove())


# ─── /confirm — подтверждение финальной цены ─────────────────────────────────

async def confirm_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = get_active_orders()
    if orders:
        buttons = []
        for row in reversed(orders[-10:]):
            order_num = row[0] if len(row) > 0 else "—"
            client_name = row[3] if len(row) > 3 else "—"
            buttons.append(f"{order_num} | {client_name}")
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Оберіть замовлення:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
    else:
        await update.message.reply_text("Введіть номер замовлення:",
            reply_markup=kb([], add_cancel=True))
    return CONFIRM_ORDER

async def confirm_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("Введіть номер замовлення (наприклад: RW-0001):",
            reply_markup=kb([], add_cancel=True))
        return CONFIRM_ORDER
    order_num = text.split("|")[0].strip() if "|" in text else text
    ctx.user_data["confirm_order_num"] = order_num
    await update.message.reply_text(
        f"Заказ: *{order_num}*\n\n💰 Введіть фінальну суму (тільки цифри):",
        parse_mode="Markdown",
        reply_markup=kb([], add_cancel=True))
    return CONFIRM_PRICE

async def confirm_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    try:
        price = int(text.replace(" ", "").replace("₴", ""))
    except ValueError:
        await update.message.reply_text("Введіть суму цифрами, наприклад: 2500")
        return CONFIRM_PRICE
    order_num = ctx.user_data.get("confirm_order_num", "—")
    now_str = datetime.now().strftime("%d.%m.%Y | %H:%M")
    card_text = (
        f"✅ *REWISE STUDIO — Замовлення підтверджено*\n\n"
        f"🔖 *{order_num}*\n"
        f"💰 *Разом: {fmt(price)} — ФІНАЛ*\n"
        f"📅 {now_str}\n\n"
        f"Rewise Studio"
    )
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
    update_order_price(order_num, fmt(price))
    await update.message.reply_text(
        f"✅ Замовлення {order_num} підтверджено — {fmt(price)}\nКартку відправлено до каналу.",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── /status — смена статуса изделия ─────────────────────────────────────────

async def status_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = get_active_orders()
    if orders:
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])]
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Оберіть замовлення:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
    else:
        await update.message.reply_text("Введіть номер замовлення:",
            reply_markup=kb([], add_cancel=True))
    return STATUS_ORDER

async def status_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("Введіть номер замовлення:",
            reply_markup=kb([], add_cancel=True))
        return STATUS_ORDER
    order_num = text.split("|")[0].strip() if "|" in text else text
    ctx.user_data["status_order_num"] = order_num
    items = get_active_items(order_num)
    if items:
        buttons = [f"{r[1]} — {r[2]} {r[3]} ({r[6]})" for r in items]
        await update.message.reply_text("Оберіть виріб:",
            reply_markup=kb(buttons, cols=1, add_back=True, add_cancel=True))
    else:
        await update.message.reply_text("Активних виробів не знайдено.",
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return STATUS_ITEM

async def status_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        orders = get_active_orders()
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])] if orders else []
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Оберіть замовлення:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
        return STATUS_ORDER
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    item_num = text.split("—")[0].strip() if "—" in text else text
    ctx.user_data["status_item_num"] = item_num
    await update.message.reply_text(f"Изделие: *{item_num}*\n\nНовий статус?",
        parse_mode="Markdown",
        reply_markup=kb(STATUSES, cols=2, add_back=True, add_cancel=True))
    return STATUS_CHOOSE

async def status_choose(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        order_num = ctx.user_data.get("status_order_num", "")
        items = get_active_items(order_num)
        buttons = [f"{r[1]} — {r[2]} {r[3]} ({r[6]})" for r in items] if items else []
        await update.message.reply_text("Оберіть виріб:",
            reply_markup=kb(buttons, cols=1, add_back=True, add_cancel=True))
        return STATUS_ITEM
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text not in STATUSES:
        await update.message.reply_text("Выберите статус из списка.",
            reply_markup=kb(STATUSES, cols=2, add_cancel=True))
        return STATUS_CHOOSE
    item_num = ctx.user_data.get("status_item_num", "—")
    order_num = ctx.user_data.get("status_order_num", "—")
    update_item_status(item_num, text)
    now_str = datetime.now().strftime("%d.%m.%Y | %H:%M")
    card_text = (
        f"🔄 *Статус виробу оновлено*\n\n"
        f"🔖 Заказ: {order_num}\n"
        f"📦 Виріб: {item_num}\n"
        f"📌 Статус: {text}\n"
        f"📅 {now_str}\n\n"
        f"Rewise Studio"
    )
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
    await update.message.reply_text(
        f"✅ Статус виробу {item_num} оновлено: {text}",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── /issued — выдача изделия ────────────────────────────────────────────────

async def issued_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = get_active_orders()
    if orders:
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])]
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Оберіть замовлення для видачі:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
    else:
        await update.message.reply_text("Введіть номер замовлення:",
            reply_markup=kb([], add_cancel=True))
    return ISSUED_ORDER

async def issued_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("Введіть номер замовлення:",
            reply_markup=kb([], add_cancel=True))
        return ISSUED_ORDER
    order_num = text.split("|")[0].strip() if "|" in text else text
    ctx.user_data["issued_order_num"] = order_num
    items = get_active_items(order_num)
    if items:
        buttons = [f"{r[1]} — {r[2]} {r[3]}" for r in items]
        buttons.append("📦 Видати всі")
        await update.message.reply_text("Який виріб видаємо?",
            reply_markup=kb(buttons, cols=1, add_back=True, add_cancel=True))
    else:
        await update.message.reply_text("Активних виробів не знайдено.",
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return ISSUED_ITEM

async def issued_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        orders = get_active_orders()
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])] if orders else []
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Оберіть замовлення для видачі:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
        return ISSUED_ORDER
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    order_num = ctx.user_data.get("issued_order_num", "—")
    now_str = datetime.now().strftime("%d.%m.%Y | %H:%M")

    if text == "📦 Видати всі":
        items = get_active_items(order_num)
        issued_nums = []
        for row in items:
            item_num = row[1]
            update_item_status(item_num, "📦 Виданий")
            issued_nums.append(item_num)
        card_text = (
            f"📦 *REWISE STUDIO — Замовлення видано*\n\n"
            f"🔖 Заказ: {order_num}\n"
            f"✅ Видано: {', '.join(issued_nums)}\n"
            f"📅 {now_str}\n\n"
            f"Rewise Studio"
        )
        await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
        await update.message.reply_text(
            f"✅ Замовлення {order_num} видано повністю.",
            reply_markup=ReplyKeyboardRemove())
    else:
        item_num = text.split("—")[0].strip() if "—" in text else text
        update_item_status(item_num, "📦 Виданий")
        remaining = get_active_items(order_num)
        remain_str = ""
        if remaining:
            remain_nums = [r[1] for r in remaining]
            remain_str = f"\n🔧 Залишок: {', '.join(remain_nums)}"
        card_text = (
            f"📦 *REWISE STUDIO — Часткова видача*\n\n"
            f"🔖 Заказ: {order_num}\n"
            f"✅ Видано: {item_num}"
            f"{remain_str}\n"
            f"📅 {now_str}\n\n"
            f"Rewise Studio"
        )
        await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
        await update.message.reply_text(
            f"✅ Виріб {item_num} видано.",
            reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── cancel ───────────────────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано. Для нового замовлення натисніть /start",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MANAGER:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_manager)],
            NAME:             [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE:            [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ITEM_TYPE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_type)],
            BRAND:            [MessageHandler(filters.TEXT & ~filters.COMMAND, get_brand)],
            DEPT:             [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dept)],
            SERVICE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            MANUAL_SVC_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_manual_svc_name)],
            MANUAL_SVC_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_manual_svc_price)],
            QTY:              [MessageHandler(filters.TEXT & ~filters.COMMAND, get_qty)],
            EXTRA200:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_extra200)],
            NEXT:             [MessageHandler(filters.TEXT & ~filters.COMMAND, get_next)],
            PAYMENT:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment)],
            PREPAY_AMOUNT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prepay_amount)],
            DEADLINE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    confirm_conv = ConversationHandler(
        entry_points=[CommandHandler("confirm", confirm_start)],
        states={
            CONFIRM_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
            CONFIRM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    status_conv = ConversationHandler(
        entry_points=[CommandHandler("status", status_start)],
        states={
            STATUS_ORDER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, status_order)],
            STATUS_ITEM:   [MessageHandler(filters.TEXT & ~filters.COMMAND, status_item)],
            STATUS_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_choose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    issued_conv = ConversationHandler(
        entry_points=[CommandHandler("issued", issued_start)],
        states={
            ISSUED_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, issued_order)],
            ISSUED_ITEM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, issued_item)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(order_conv)
    app.add_handler(confirm_conv)
    app.add_handler(status_conv)
    app.add_handler(issued_conv)
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
