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
            "🆕 Новый"
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
                "🆕 Новый",
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
        active = [r for r in all_rows[1:] if len(r) > 7 and r[7] not in ["📦 Выдан"]]
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
        items = [r for r in all_rows[1:] if len(r) > 6 and r[6] not in ["📦 Выдан"]]
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
                if status == "🔧 В работе":
                    ws.update_cell(i + 1, 9, now_str)
                elif status == "✅ Готов":
                    ws.update_cell(i + 1, 10, now_str)
                elif status == "📦 Выдан":
                    ws.update_cell(i + 1, 11, now_str)
                elif status == "⏳ Отложен":
                    pass
                break
        # Проверяем все ли изделия заказа выданы
        order_num = item_num.rsplit("-", 1)[0]
        all_items = [r for r in all_rows[1:] if len(r) > 1 and r[0] == order_num]
        if all_items and all(r[6] == "📦 Выдан" for r in all_items):
            ws_orders = sh.worksheet("Замовлення")
            orders = ws_orders.get_all_values()
            for i, row in enumerate(orders):
                if len(row) > 0 and row[0] == order_num:
                    ws_orders.update_cell(i + 1, 8, "📦 Выдан")
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
                ws.update_cell(i + 1, 8, "✅ Подтверждён")
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
BTN_CANCEL = "❌ Отменить"
BTN_MANUAL = "✏️ Ввести вручную"

STATUSES = ["🔧 В работе", "✅ Готов", "⏳ Отложен", "📦 Выдан"]

DEPTS = {
    "shoes": [
        ("cleaning", "Чистка / Базовый уход"),
        ("painting", "Покраска / Реставрация"),
        ("heels",    "Каблуки и набойки"),
        ("sole",     "Подошва"),
        ("zippers",  "Молнии"),
        ("hardware", "Фурнитура"),
        ("sewing",   "Швейные работы и детали"),
        ("stretch",  "Растяжка"),
    ],
    "bags": [
        ("cleaning", "Чистка / Базовый уход"),
        ("painting", "Покраска / Реставрация"),
        ("handles",  "Ручки и ремень"),
        ("zippers",  "Молнии"),
        ("hardware", "Фурнитура"),
        ("sewing",   "Швейные работы и детали"),
        ("lining",   "Подкладка"),
        ("edges",    "Реставрация урезов"),
        ("belt",     "Поясной ремень"),
    ],
}

SERVICES = {
    'shoes': {
        'cleaning': [
            ('Чистка — летняя обувь', 'пара', 1200, False),
            ('Чистка — низкая обувь', 'пара', 1400, False),
            ('Чистка — средняя обувь', 'пара', 1600, False),
            ('Чистка — высокие сапоги', 'пара', 1800, False),
            ('Чистка — UGG и меховая', 'пара', 1400, False),
            ('Базовый уход — низкая обувь', 'пара', 1400, False),
            ('Базовый уход — средняя обувь', 'пара', 1600, False),
            ('Базовый уход — высокие сапоги', 'пара', 1800, False),
            ('Базовый уход — UGG и меховая', 'пара', 1400, False),
        ],
        'painting': [
            ('Покраска — летняя обувь', 'пара', 1400, False),
            ('Покраска — низкая обувь', 'пара', 1800, False),
            ('Покраска — средняя обувь', 'пара', 2000, False),
            ('Покраска — высокие сапоги', 'пара', 2800, False),
            ('Покраска — UGG и меховая', 'пара', 1800, False),
            ('Покраска / отбеливание Midsole', 'пара', 1100, False),
            ('Отбеливание подошвы Loro Piana', 'пара', 1100, False),
            ('Покраска каблуков', 'пара', 900, False),
            ('Покраска ранта обуви', 'пара', 700, False),
            ('Покраска танкетки', 'пара', 1200, False),
            ('Глассаж — полировка гладкой кожи до блеска', 'пара', 600, False),
            ('Реставрация — летняя обувь', 'пара', 1600, True),
            ('Реставрация — низкая обувь', 'пара', 2000, True),
            ('Реставрация — средняя обувь', 'пара', 2200, True),
            ('Реставрация — высокие сапоги', 'пара', 3200, True),
            ('Реставрация — UGG и меховая', 'пара', 2400, True),
            ('Реставрация носочной части обуви', 'пара', 1200, True),
            ('Реставрация каблуков (гладкая кожа)', 'пара', 900, True),
            ('Реставрация каблуков (лаковая кожа)', 'пара', 1200, True),
            ('Реставрация стелек — открытая летняя обувь', 'пара', 1200, True),
            ('Устранение повреждений верха обуви', '1 место', 1000, True),
        ],
        'heels': [
            ('Набойки листовые', 'пара', 700, False),
            ('Набойки формованные', 'пара', 850, False),
            ('Набойки штифтовые полиуретановые — шпилька', 'пара', 550, False),
            ('Набойки металлические — шпилька', 'пара', 700, False),
            ('Наращивание каблуков', 'пара', 400, False),
            ('Выравнивание каблука под набойку', 'пара', 250, False),
            ('Демонтаж металлического штифта', 'пара', 250, False),
            ('Замена каблуков без обтяжки', 'пара', 1800, False),
            ('Замена каблуков с обтяжкой кожей', 'пара', 2500, False),
            ('Замена обтяжки каблуков — новая набойка включена', 'пара', 2400, False),
            ('Замена обтяжки танкетки', 'пара', 2600, False),
            ('Укрепление каблука', '1 шт.', 400, False),
        ],
        'sole': [
            ('Профилактика женская', 'пара', 1200, False),
            ('Профилактика мужская', 'пара', 1200, False),
            ('Профилактика женская комбинированная', 'пара', 1500, False),
            ('Профилактика на всю площадь подошвы', 'пара', 1400, False),
            ('Профилактика полный след спортивной обуви', 'пара', 1800, False),
            ('Наращивание носочной части подошвы', 'пара', 400, False),
            ('Полировка ранта обуви', 'пара', 400, False),
            ('Локальная подклейка', '1 место', 300, False),
            ('Подклейка подошвы по периметру', 'пара', 600, False),
            ('Переклейка подошвы / следа', 'пара', 900, False),
            ('Переклейка + прошивка подошвы', 'пара', 1400, False),
            ('Подклейка / переклейка стелек', 'пара', 400, False),
            ('Прошивка подошвы', 'пара', 800, False),
            ('Прошивка подошвы сегментами', 'пара', 600, False),
            ('Замена задников обуви', 'пара', 900, False),
            ('Замена задников с разбором подошвы', 'пара', 1300, False),
            ('Замена резиновой подошвы', 'пара', 2400, False),
            ('Замена подошвы кожволон', 'пара', 3000, False),
            ('Замена кожаной подошвы — клеевой метод', 'пара', 4000, False),
            ('Замена кожаной подошвы — прошивной метод', 'пара', 6000, False),
            ('Замена подошвы Loro Piana', 'пара', 4000, False),
            ('Замена подошвы Golden Goose', 'пара', 4000, False),
            ('Замена супинатора', '1 шт.', 600, False),
        ],
        'zippers': [
            ('Замена молнии до 20 см (без стоимости материала)', '1 шт.', 700, False),
            ('Замена молнии от 21 см (без стоимости материала)', '1 шт.', 900, False),
            ('Замена бегунка молнии', '1 шт.', 300, False),
            ('Врезание молнии в голенище (без стоимости материала)', 'пара', 2200, False),
        ],
        'hardware': [
            ('Замена крючков + резинка', 'пара', 500, False),
            ('Замена пряжки (без стоимости материала)', 'пара', 450, False),
            ('Замена блочка и люверса', '1 шт.', 200, False),
            ('Замена кнопки (без разбора изделия)', '1 шт.', 200, False),
        ],
        'sewing': [
            ('Восстановление машинной строчки', '1 место', 300, False),
            ('Восстановление ручной строчки', '1 место', 500, False),
            ('Изготовление и замена кожаных стелек — закрытая обувь', 'пара', 900, False),
            ('Изготовление и замена кожаных стелек — открытая обувь', 'пара', 900, False),
            ('Замена подкладки задника из сетки', 'пара', 1600, False),
            ('Замена кармана задника из кожи', 'пара', 1300, False),
            ('Замена кармана задника Balenciaga', 'пара', 1800, False),
            ('Замена подкладки задника из кожи', 'пара', 2000, False),
            ('Внутренняя латка', '1 шт.', 450, False),
            ('Декоративная латка', '1 шт.', 600, False),
            ('Изготовление и замена новой детали обуви', '1 шт.', 700, False),
            ('Замена союзки в кроссовках', 'пара', 1600, False),
            ('Замена деталей верха в босоножках', 'пара', 2800, False),
            ('Ушивка голенища — по высоте', 'пара', 1600, False),
            ('Ушивка голенища — по ширине', 'пара', 2000, False),
            ('Замена резинок с обтяжкой кожей', 'пара', 900, False),
            ('Замена резинок на пряжках обуви', 'пара', 500, False),
            ('Замена резинок в голенище', '1 шт.', 500, False),
            ('Врезание резинок в голенище', 'пара', 1600, False),
            ('Замена липучек', 'пара', 550, False),
            ('Изготовление и замена ремешков обуви', 'пара', 1600, False),
        ],
        'stretch': [
            ('Растяжка обуви в подъёме / ширина', 'пара', 600, False),
            ('Растяжка голенища сапог / ботинок', 'пара', 1000, False),
        ],
    },
    'bags': {
        'cleaning': [
            ('Чистка — кожаная сумка S', '1 шт.', 1400, False),
            ('Чистка — кожаная сумка M', '1 шт.', 1600, False),
            ('Чистка — кожаная сумка L', '1 шт.', 1800, False),
            ('Чистка — текстильная сумка S', '1 шт.', 1400, False),
            ('Чистка — текстильная сумка M', '1 шт.', 1600, False),
            ('Чистка — текстильная сумка L', '1 шт.', 1800, False),
        ],
        'painting': [
            ('Покраска — кожаная сумка S', '1 шт.', 1800, False),
            ('Покраска — кожаная сумка M', '1 шт.', 2200, False),
            ('Покраска — кожаная сумка L', '1 шт.', 2600, False),
            ('Покраска — поясной ремень', '1 шт.', 1400, False),
            ('Реставрация — кожаная сумка S', '1 шт.', 2200, True),
            ('Реставрация — кожаная сумка M', '1 шт.', 2700, True),
            ('Реставрация — кожаная сумка L', '1 шт.', 3200, True),
            ('Локальная реставрация кожи сумки', '1 место', 1000, True),
            ('Реставрация уголков сумки', '1 место', 450, True),
            ('Реставрация ручек сумки', 'пара', 1600, True),
            ('Реставрация плечевого ремня сумки', '1 шт.', 1600, True),
        ],
        'handles': [
            ('Укорачивание плечевого ремня сумки', '1 шт.', 450, False),
            ('Замена плечевого ремня сумки с подбором кожи', '1 шт.', 2000, False),
            ('Замена ручек сумки типа шопер', 'пара', 1600, False),
            ('Замена ручек кожаной сумки с подбором кожи', 'пара', 2800, False),
            ('Замена ручек рюкзака с наполнителем', 'пара', 3200, False),
        ],
        'zippers': [
            ('Замена молнии сумки до 25 см (без стоимости материала)', '1 шт.', 1400, False),
            ('Замена молнии сумки от 25 см (без стоимости материала)', '1 шт.', 1600, False),
            ('Замена молнии в кошельке / органайзере (без стоимости материала)', '1 шт.', 1800, False),
            ('Замена молнии рюкзака / большой сумки (без стоимости материала)', '1 шт.', 1600, False),
            ('Замена бегунка молнии сумки', '1 шт.', 300, False),
        ],
        'hardware': [
            ('Замена карабина сумки (без стоимости материала)', '1 шт.', 250, False),
            ('Замена пряжки ремня сумки (без стоимости материала)', '1 шт.', 250, False),
            ('Замена кнопки / заклёпки / люверса сумки', '1 шт.', 200, False),
            ('Замена магнита сумки (без стоимости материала)', '1 шт.', 500, False),
            ('Установка декоративной латки', '1 шт.', 900, False),
            ('Установка внутренней латки', '1 шт.', 450, False),
            ('Установка кольца / полукольца (без стоимости материала)', '1 шт.', 250, False),
        ],
        'sewing': [
            ('Восстановление машинного шва сумки', '1 место', 300, False),
            ('Подклейка кожи / детали сумки', '1 место', 300, False),
            ('Ремонт крепления ручек сумки (без замены деталей)', '1 шт.', 450, False),
            ('Изготовление кожаного пуллера на бегунок', '1 шт.', 500, False),
            ('Изготовление и замена тренчика сумки', '1 шт.', 500, False),
            ('Изготовление и перешивка деталей сумки', '1 шт.', 900, False),
            ('Изготовление и замена настрочных креплений ручек', '1 шт.', 600, False),
            ('Изготовление и замена втачных креплений ручек', '1 шт.', 400, False),
            ('Замена канта в кошельке / клатче', '1 шт.', 1200, False),
            ('Замена окантовки сумки — кедер', '1 шт.', 1200, False),
        ],
        'lining': [
            ('Замена подкладки — сумка S', '1 шт.', 1800, False),
            ('Замена подкладки — сумка M', '1 шт.', 2200, False),
            ('Замена подкладки — сумка L', '1 шт.', 2600, False),
            ('Замена подкладки — кошелёк / органайзер', '1 шт.', 2600, False),
        ],
        'edges': [
            ('Торцевание уреза кожи', '1 см', 12, False),
            ('Торцевание ручек сумки (2 стороны)', 'пара', 1200, False),
            ('Торцевание ручек сумки (4 стороны)', 'пара', 1400, False),
            ('Торцевание плечевого ремня сумки', '1 шт.', 1400, False),
            ('Торцевание тренчика / пулера / держателя ручек', '1 шт.', 400, False),
        ],
        'belt': [
            ('Пробивание отверстий', '1 шт.', 200, False),
            ('Укорачивание кожаного поясного ремня', '1 шт.', 450, False),
            ('Укорачивание поясного ремня с перешиванием пряжки', '1 шт.', 600, False),
            ('Замена подклада поясного ремня', '1 шт.', 2000, False),
            ('Реставрация поясного ремня (проклейка, прошивка)', '1 шт.', 800, False),
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
        "👋 Rewise Studio\n\nКто принимает заказ?",
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
        await update.message.reply_text("Кто принимает заказ?",
            reply_markup=kb(partners, cols=2, add_cancel=True))
        return MANAGER
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    get_data(ctx)["client"] = text
    await update.message.reply_text("📞 *Номер телефона?*", parse_mode="Markdown",
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
    msg = "Какое изделие принёс клиент?" if is_first else "+ Ещё одна вещь — какое изделие?"
    await update.message.reply_text(msg,
        reply_markup=kb(["👟 Обувь", "👜 Сумка / Аксессуар"], cols=2, add_back=True, add_cancel=True))
    return ITEM_TYPE

async def get_item_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("📞 *Номер телефона?*", parse_mode="Markdown",
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
        msg = "Какое изделие принёс клиент?" if is_first else "+ Ещё одна вещь — какое изделие?"
        await update.message.reply_text(msg,
            reply_markup=kb(["👟 Обувь", "👜 Сумка / Аксессуар"], cols=2, add_back=True, add_cancel=True))
        return ITEM_TYPE
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    d = get_data(ctx)
    d["cur"]["brand"] = text
    depts = DEPTS[d["cur"]["type"]]
    dept_buttons = [label for _, label in depts]
    await update.message.reply_text(
        f"*{d['cur']['type_label']} — {d['cur']['brand']}*\n\nКакой отдел?",
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
        await update.message.reply_text("Выберите отдел из списка.",
            reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
        return DEPT
    ctx.user_data["dept_id"] = dept_id
    ctx.user_data["dept_label"] = text
    svcs = SERVICES[d["cur"]["type"]][dept_id]
    svc_buttons = [f"{name} — {'от ' if a else ''}{fmt(p)}" for name, u, p, a in svcs]
    svc_buttons.append(BTN_MANUAL)
    await update.message.reply_text(f"*{text}*\n\nВыберите услугу:", parse_mode="Markdown",
        reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
    return SERVICE

async def get_service(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        d = get_data(ctx)
        depts = DEPTS[d["cur"]["type"]]
        dept_buttons = [label for _, label in depts]
        await update.message.reply_text(
            f"*{d['cur']['type_label']} — {d['cur']['brand']}*\n\nКакой отдел?",
            parse_mode="Markdown",
            reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
        return DEPT
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("✏️ Введите название услуги:",
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
        await update.message.reply_text("Выберите услугу из списка.",
            reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
        return SERVICE
    ctx.user_data["chosen_svc"] = chosen
    await update.message.reply_text(f"Количество ({chosen[1]}):",
        reply_markup=kb(["1", "2", "3", "Больше"], cols=4, add_back=True, add_cancel=True))
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
        await update.message.reply_text(f"*{dept_label}*\n\nВыберите услугу:", parse_mode="Markdown",
            reply_markup=kb(svc_buttons, cols=1, add_back=True, add_cancel=True))
        return SERVICE
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    ctx.user_data["manual_svc_name"] = text
    await update.message.reply_text("💰 Введите цену (только цифры):",
        reply_markup=kb([], add_back=True, add_cancel=True))
    return MANUAL_SVC_PRICE

async def get_manual_svc_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("✏️ Введите название услуги:",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return MANUAL_SVC_NAME
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    try:
        price = int(text.replace(" ", "").replace("₴", ""))
    except ValueError:
        await update.message.reply_text("Введите цену цифрами, например: 500")
        return MANUAL_SVC_PRICE
    ctx.user_data["chosen_svc"] = (f"📝 {ctx.user_data['manual_svc_name']}", "шт.", price, False)
    await update.message.reply_text("Количество:",
        reply_markup=kb(["1", "2", "3", "Больше"], cols=4, add_back=True, add_cancel=True))
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
        await update.message.reply_text(f"*{dept_label}*\n\nВыберите услугу:", parse_mode="Markdown",
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
            reply_markup=kb(["✅ Да — +200 ₴", "❌ Нет"], cols=2, add_back=True, add_cancel=True))
        return EXTRA200
    return await save_service(update, ctx, extra200=False)

async def get_extra200(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        chosen = ctx.user_data["chosen_svc"]
        await update.message.reply_text(f"Количество ({chosen[1]}):",
            reply_markup=kb(["1", "2", "3", "Больше"], cols=4, add_back=True, add_cancel=True))
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
    extra_str = " + 200 ₴ (доп. материал)" if extra200 else ""
    await update.message.reply_text(
        f"✓ Добавлено: {svc['name']}\n{price_str}{extra_str}",
        reply_markup=kb(["➕ Ещё одна услуга", "➕ Ещё одна вещь", "✅ Завершить заказ"], cols=1, add_cancel=True))
    return NEXT

async def get_next(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if "услуга" in text.lower():
        depts = DEPTS[d["cur"]["type"]]
        dept_buttons = [label for _, label in depts]
        await update.message.reply_text("Какой отдел?",
            reply_markup=kb(dept_buttons, cols=2, add_back=True, add_cancel=True))
        return DEPT
    elif "вещь" in text.lower():
        commit_item(d)
        await update.message.reply_text("Какое изделие?",
            reply_markup=kb(["👟 Обувь", "👜 Сумка / Аксессуар"], cols=2, add_back=True, add_cancel=True))
        return ITEM_TYPE
    elif "завершить" in text.lower():
        commit_item(d)
        await update.message.reply_text("💳 Тип оплаты?",
            reply_markup=kb(["💳 Предоплата", "📦 Послеоплата"], cols=2, add_cancel=True))
        return PAYMENT
    else:
        await update.message.reply_text("Выберите действие:",
            reply_markup=kb(["➕ Ещё одна услуга", "➕ Ещё одна вещь", "✅ Завершить заказ"], cols=1, add_cancel=True))
        return NEXT

async def get_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    ctx.user_data["payment_type"] = text
    if "Предоплата" in text:
        await update.message.reply_text("💰 Введите сумму предоплаты (только цифры):",
            reply_markup=kb([], add_back=True, add_cancel=True))
        return PREPAY_AMOUNT
    ctx.user_data["payment"] = text
    await update.message.reply_text("📅 Срок выполнения?",
        reply_markup=kb(["⚡ Срочно", "🕐 Без срока", "📅 Указать дату"], cols=2, add_back=True, add_cancel=True))
    return DEADLINE

async def get_prepay_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("💳 Тип оплаты?",
            reply_markup=kb(["💳 Предоплата", "📦 Послеоплата"], cols=2, add_cancel=True))
        return PAYMENT
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    try:
        amount = int(text.replace(" ", "").replace("₴", ""))
        ctx.user_data["payment"] = f"Предоплата: {fmt(amount)}"
    except ValueError:
        await update.message.reply_text("Введите сумму цифрами, например: 500")
        return PREPAY_AMOUNT
    await update.message.reply_text("📅 Срок выполнения?",
        reply_markup=kb(["⚡ Срочно", "🕐 Без срока", "📅 Указать дату"], cols=2, add_back=True, add_cancel=True))
    return DEADLINE

async def get_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        await update.message.reply_text("💳 Тип оплаты?",
            reply_markup=kb(["💳 Предоплата", "📦 Послеоплата"], cols=2, add_cancel=True))
        return PAYMENT
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if "Указать дату" in text:
        await update.message.reply_text("Введите дату (например: 10.06 или пятница):",
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
        "📋 *REWISE STUDIO — Новый заказ*", "",
        f"🔖 *{order_num}*",
        f"👤 {d['client']}",
        f"📞 {d['phone']}",
        f"👨‍💼 Принял: {d['manager']}",
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

    lines.append(f"💰 *Итого: {prefix}{fmt(total)}*")
    if d["has_approx"]:
        lines.append("⚠️ _Есть позиции для уточнения после осмотра_")
    lines.append(f"💳 Оплата: {payment}")
    if "Срочно" in deadline:
        lines.append("⚡ *СРОЧНО*")
    elif deadline not in ("Без срока", "🕐 Без срока"):
        lines.append(f"📅 Срок: {deadline}")
    lines.append("")
    lines.append("_Окончательная стоимость согласовывается после осмотра изделия_")
    lines.append("\nRewise Studio")

    await update.message.reply_text(
        f"✅ Заказ *{order_num}* сформирован!\n\n💰 {prefix}{fmt(total)}",
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
        await update.message.reply_text("Выберите заказ:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
    else:
        await update.message.reply_text("Введите номер заказа:",
            reply_markup=kb([], add_cancel=True))
    return CONFIRM_ORDER

async def confirm_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("Введите номер заказа (например: RW-0001):",
            reply_markup=kb([], add_cancel=True))
        return CONFIRM_ORDER
    order_num = text.split("|")[0].strip() if "|" in text else text
    ctx.user_data["confirm_order_num"] = order_num
    await update.message.reply_text(
        f"Заказ: *{order_num}*\n\n💰 Введите финальную сумму (только цифры):",
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
        await update.message.reply_text("Введите сумму цифрами, например: 2500")
        return CONFIRM_PRICE
    order_num = ctx.user_data.get("confirm_order_num", "—")
    now_str = datetime.now().strftime("%d.%m.%Y | %H:%M")
    card_text = (
        f"✅ *REWISE STUDIO — Заказ подтверждён*\n\n"
        f"🔖 *{order_num}*\n"
        f"💰 *Итого: {fmt(price)} — ФИНАЛ*\n"
        f"📅 {now_str}\n\n"
        f"Rewise Studio"
    )
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
    update_order_price(order_num, fmt(price))
    await update.message.reply_text(
        f"✅ Заказ {order_num} подтверждён — {fmt(price)}\nКарточка отправлена в канал.",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── /status — смена статуса изделия ─────────────────────────────────────────

async def status_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = get_active_orders()
    if orders:
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])]
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Выберите заказ:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
    else:
        await update.message.reply_text("Введите номер заказа:",
            reply_markup=kb([], add_cancel=True))
    return STATUS_ORDER

async def status_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("Введите номер заказа:",
            reply_markup=kb([], add_cancel=True))
        return STATUS_ORDER
    order_num = text.split("|")[0].strip() if "|" in text else text
    ctx.user_data["status_order_num"] = order_num
    items = get_active_items(order_num)
    if items:
        buttons = [f"{r[1]} — {r[2]} {r[3]} ({r[6]})" for r in items]
        await update.message.reply_text("Выберите изделие:",
            reply_markup=kb(buttons, cols=1, add_back=True, add_cancel=True))
    else:
        await update.message.reply_text("Активных изделий не найдено.",
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return STATUS_ITEM

async def status_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        orders = get_active_orders()
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])] if orders else []
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Выберите заказ:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
        return STATUS_ORDER
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    item_num = text.split("—")[0].strip() if "—" in text else text
    ctx.user_data["status_item_num"] = item_num
    await update.message.reply_text(f"Изделие: *{item_num}*\n\nНовый статус?",
        parse_mode="Markdown",
        reply_markup=kb(STATUSES, cols=2, add_back=True, add_cancel=True))
    return STATUS_CHOOSE

async def status_choose(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        order_num = ctx.user_data.get("status_order_num", "")
        items = get_active_items(order_num)
        buttons = [f"{r[1]} — {r[2]} {r[3]} ({r[6]})" for r in items] if items else []
        await update.message.reply_text("Выберите изделие:",
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
        f"🔄 *Статус изделия обновлён*\n\n"
        f"🔖 Заказ: {order_num}\n"
        f"📦 Изделие: {item_num}\n"
        f"📌 Статус: {text}\n"
        f"📅 {now_str}\n\n"
        f"Rewise Studio"
    )
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
    await update.message.reply_text(
        f"✅ Статус изделия {item_num} обновлён: {text}",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── /issued — выдача изделия ────────────────────────────────────────────────

async def issued_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = get_active_orders()
    if orders:
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])]
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Выберите заказ для выдачи:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
    else:
        await update.message.reply_text("Введите номер заказа:",
            reply_markup=kb([], add_cancel=True))
    return ISSUED_ORDER

async def issued_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    if text == BTN_MANUAL:
        await update.message.reply_text("Введите номер заказа:",
            reply_markup=kb([], add_cancel=True))
        return ISSUED_ORDER
    order_num = text.split("|")[0].strip() if "|" in text else text
    ctx.user_data["issued_order_num"] = order_num
    items = get_active_items(order_num)
    if items:
        buttons = [f"{r[1]} — {r[2]} {r[3]}" for r in items]
        buttons.append("📦 Выдать все")
        await update.message.reply_text("Какое изделие выдаём?",
            reply_markup=kb(buttons, cols=1, add_back=True, add_cancel=True))
    else:
        await update.message.reply_text("Активных изделий не найдено.",
            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return ISSUED_ITEM

async def issued_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        orders = get_active_orders()
        buttons = [f"{r[0]} | {r[3]}" for r in reversed(orders[-10:])] if orders else []
        buttons.append(BTN_MANUAL)
        await update.message.reply_text("Выберите заказ для выдачи:",
            reply_markup=kb(buttons, cols=1, add_cancel=True))
        return ISSUED_ORDER
    if text == BTN_CANCEL:
        return await cancel(update, ctx)
    order_num = ctx.user_data.get("issued_order_num", "—")
    now_str = datetime.now().strftime("%d.%m.%Y | %H:%M")

    if text == "📦 Выдать все":
        items = get_active_items(order_num)
        issued_nums = []
        for row in items:
            item_num = row[1]
            update_item_status(item_num, "📦 Выдан")
            issued_nums.append(item_num)
        card_text = (
            f"📦 *REWISE STUDIO — Заказ выдан*\n\n"
            f"🔖 Заказ: {order_num}\n"
            f"✅ Выдано: {', '.join(issued_nums)}\n"
            f"📅 {now_str}\n\n"
            f"Rewise Studio"
        )
        await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
        await update.message.reply_text(
            f"✅ Заказ {order_num} выдан полностью.",
            reply_markup=ReplyKeyboardRemove())
    else:
        item_num = text.split("—")[0].strip() if "—" in text else text
        update_item_status(item_num, "📦 Выдан")
        remaining = get_active_items(order_num)
        remain_str = ""
        if remaining:
            remain_nums = [r[1] for r in remaining]
            remain_str = f"\n🔧 Остаток: {', '.join(remain_nums)}"
        card_text = (
            f"📦 *REWISE STUDIO — Частичная выдача*\n\n"
            f"🔖 Заказ: {order_num}\n"
            f"✅ Выдано: {item_num}"
            f"{remain_str}\n"
            f"📅 {now_str}\n\n"
            f"Rewise Studio"
        )
        await ctx.bot.send_message(chat_id=CHANNEL_ID, text=card_text, parse_mode="Markdown")
        await update.message.reply_text(
            f"✅ Изделие {item_num} выдано.",
            reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─── cancel ───────────────────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. Для нового заказа нажми /start",
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
