import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
CHANNEL_ID = -5226279696

# Шаги диалога
(NAME, PHONE, ITEM_TYPE, BRAND, DEPT, SERVICE, QTY, EXTRA200, NEXT) = range(9)

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
    "shoes": {
        "cleaning": [
            ("Открытая летняя обувь (босоножки, сандалии, шлёпанцы)", "пара", 1200, False),
            ("Туфли, балетки, кеды, кроссовки, слипоны", "пара", 1400, False),
            ("Ботинки, ботильоны", "пара", 1600, False),
            ("Сапоги, ботфорты, берцы", "пара", 1800, False),
            ("UGG и меховая обувь", "пара", 1400, False),
            ("Базовый уход — туфли, балетки, кеды", "пара", 1400, False),
            ("Базовый уход — ботинки, ботильоны", "пара", 1600, False),
            ("Базовый уход — сапоги, ботфорты", "пара", 1800, False),
            ("Базовый уход — UGG и меховая обувь", "пара", 1400, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "painting": [
            ("Покраска — открытая летняя обувь", "пара", 1400, False),
            ("Покраска — туфли, балетки, кеды, кроссовки", "пара", 1800, False),
            ("Покраска — ботинки, ботильоны", "пара", 2000, False),
            ("Покраска — сапоги, ботфорты, берцы", "пара", 2800, False),
            ("Покраска — UGG и меховая обувь", "пара", 1800, False),
            ("Покраска / отбеливание Midsole", "пара", 1100, False),
            ("Отбеливание подошвы Loro Piana", "пара", 1100, False),
            ("Покраска каблуков", "пара", 900, False),
            ("Покраска ранта обуви", "пара", 700, False),
            ("Покраска танкетки", "пара", 1200, False),
            ("Глассаж — полировка гладкой кожи до блеска", "пара", 600, False),
            ("Комплексная реставрация — открытая летняя", "пара", 1600, True),
            ("Комплексная реставрация — туфли, балетки, кроссовки", "пара", 2000, True),
            ("Комплексная реставрация — ботинки, ботильоны", "пара", 2200, True),
            ("Комплексная реставрация — сапоги, берцы", "пара", 3200, True),
            ("Комплексная реставрация — UGG", "пара", 2400, True),
            ("Реставрация носочной части", "пара", 1200, True),
            ("Реставрация каблуков (гладкая кожа)", "пара", 900, True),
            ("Реставрация каблуков (лаковая кожа)", "пара", 1200, True),
            ("Устранение повреждений", "1 место", 1000, True),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "heels": [
            ("Набойки листовые", "пара", 700, False),
            ("Набойки формованные", "пара", 850, False),
            ("Набойки штифтовые полиуретановые — шпилька", "пара", 550, False),
            ("Набойки металлические — шпилька", "пара", 700, False),
            ("Наращивание каблуков", "пара", 400, False),
            ("Выравнивание каблука под набойку", "пара", 250, False),
            ("Демонтаж металлического штифта", "пара", 250, False),
            ("Замена каблуков без обтяжки", "пара", 1800, False),
            ("Замена каблуков с обтяжкой кожей", "пара", 2500, False),
            ("Замена обтяжки каблуков + новая набойка", "пара", 2400, False),
            ("Замена обтяжки танкетки", "пара", 2600, False),
            ("Укрепление каблука", "1 шт.", 400, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "sole": [
            ("Профилактика женская", "пара", 1200, False),
            ("Профилактика мужская", "пара", 1200, False),
            ("Профилактика женская комбинированная", "пара", 1500, False),
            ("Профилактика на всю площадь подошвы", "пара", 1400, False),
            ("Профилактика полный след спортивной обуви", "пара", 1800, False),
            ("Наращивание носочной части подошвы", "пара", 400, False),
            ("Локальная подклейка подошвы", "1 место", 300, False),
            ("Подклейка подошвы по периметру", "пара", 600, False),
            ("Переклейка подошвы / следа", "пара", 900, False),
            ("Переклейка + прошивка подошвы", "пара", 1400, False),
            ("Прошивка подошвы", "пара", 800, False),
            ("Замена резиновой подошвы", "пара", 2400, False),
            ("Замена подошвы кожволон", "пара", 3000, False),
            ("Замена кожаной подошвы — клеевой метод", "пара", 4000, False),
            ("Замена кожаной подошвы — прошивной метод", "пара", 6000, False),
            ("Замена подошвы Loro Piana", "пара", 4000, False),
            ("Замена подошвы Golden Goose", "пара", 4000, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "zippers": [
            ("Замена молнии до 20 см (без стоимости материала)", "1 шт.", 700, False),
            ("Замена молнии от 21 см (без стоимости материала)", "1 шт.", 900, False),
            ("Замена бегунка молнии", "1 шт.", 300, False),
            ("Врезание молнии в голенище (без стоимости материала)", "пара", 2200, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "hardware": [
            ("Замена крючков + резинка", "пара", 500, False),
            ("Замена пряжки (без стоимости материала)", "пара", 450, False),
            ("Блочок / люверс / хольнитен", "1 шт.", 200, False),
            ("Замена кнопки (без разбора изделия)", "1 шт.", 200, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "sewing": [
            ("Восстановление машинной строчки (1 место)", "1 место", 300, False),
            ("Восстановление ручной строчки (1 место)", "1 место", 500, False),
            ("Изготовление и замена кожаных стелек — закрытая обувь", "пара", 900, False),
            ("Изготовление и замена кожаных стелек — открытая обувь", "пара", 900, False),
            ("Замена подкладки задника из сетки", "пара", 1600, False),
            ("Замена кармана задника из кожи", "пара", 1300, False),
            ("Замена кармана задника Balenciaga", "пара", 1800, False),
            ("Замена подкладки задника из кожи", "пара", 2000, False),
            ("Внутренняя латка", "1 шт.", 450, False),
            ("Декоративная латка", "1 шт.", 600, False),
            ("Замена союзки в кроссовках", "пара", 1600, False),
            ("Замена деталей верха в босоножках", "пара", 2800, False),
            ("Замена липучек", "пара", 550, False),
            ("Изготовление и замена ремешков обуви", "пара", 1600, False),
            ("Уменьшение высоты голенища", "пара", 1600, False),
            ("Уменьшение ширины голенища", "пара", 2000, False),
            ("Замена резинок с обтяжкой кожей", "пара", 900, False),
            ("Вшивание резинок в голенище", "пара", 1400, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "stretch": [
            ("Растяжка обуви в подъёме / ширина", "пара", 600, False),
            ("Растяжка голенища сапог / ботинок", "пара", 1000, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
    },
    "bags": {
        "cleaning": [
            ("Кожаная сумка / клатч / кошелёк, S (до 25 см)", "1 шт.", 1400, False),
            ("Кожаная сумка / портфель / рюкзак, M (25–40 см)", "1 шт.", 1600, False),
            ("Кожаная сумка / портфель / рюкзак, L (от 40 см)", "1 шт.", 1800, False),
            ("Текстильная сумка S", "1 шт.", 1400, False),
            ("Текстильная сумка M", "1 шт.", 1600, False),
            ("Текстильная сумка L", "1 шт.", 1800, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "painting": [
            ("Покраска кожаная сумка, S", "1 шт.", 1800, False),
            ("Покраска кожаная сумка, M", "1 шт.", 2200, False),
            ("Покраска кожаная сумка, L", "1 шт.", 2600, False),
            ("Покраска кожаного поясного ремня", "1 шт.", 1400, False),
            ("Комплексная реставрация, S", "1 шт.", 2200, True),
            ("Комплексная реставрация, M", "1 шт.", 2700, True),
            ("Комплексная реставрация, L", "1 шт.", 3200, True),
            ("Локальная реставрация кожи (1 место)", "1 место", 1000, True),
            ("Реставрация уголков (1 место)", "1 место", 450, True),
            ("Реставрация кожи ручек (переклейка, перестрочка)", "пара", 1600, True),
            ("Реставрация плечевого ремня", "1 шт.", 1600, True),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "handles": [
            ("Укорачивание плечевого ремня", "1 шт.", 450, False),
            ("Замена плечевого ремня с подбором кожи", "1 шт.", 2000, False),
            ("Замена ручек шопер", "пара", 1600, False),
            ("Замена ручек с подбором кожи", "пара", 2800, False),
            ("Замена ручек рюкзака с наполнителем", "пара", 3200, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "zippers": [
            ("Замена молнии до 25 см (без стоимости материала)", "1 шт.", 1400, False),
            ("Замена молнии от 25 см (без стоимости материала)", "1 шт.", 1600, False),
            ("Замена молнии в кошельке / органайзере (без стоимости материала)", "1 шт.", 1800, False),
            ("Замена молнии рюкзака / большой сумки (без стоимости материала)", "1 шт.", 1600, False),
            ("Замена бегунка молнии", "1 шт.", 300, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "hardware": [
            ("Замена карабина (без стоимости материала)", "1 шт.", 250, False),
            ("Замена пряжки ремня (без стоимости материала)", "1 шт.", 250, False),
            ("Замена кнопки / заклёпки / люверса", "1 шт.", 200, False),
            ("Замена магнита (без стоимости материала)", "1 шт.", 500, False),
            ("Установка декоративной латки", "1 шт.", 900, False),
            ("Установка внутренней латки", "1 шт.", 450, False),
            ("Установка кольца / полукольца (без стоимости материала)", "1 шт.", 250, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "sewing": [
            ("Восстановление машинного шва (1 место)", "1 место", 300, False),
            ("Подклейка кожи / детали (1 место)", "1 место", 300, False),
            ("Ремонт крепления ручек (без замены деталей)", "1 шт.", 450, False),
            ("Изготовление кожаного пуллера", "1 шт.", 500, False),
            ("Изготовление и замена тренчика", "1 шт.", 500, False),
            ("Изготовление и перешивка деталей", "1 шт.", 900, False),
            ("Замена канта в кошельке / клатче", "1 шт.", 1200, False),
            ("Замена окантовки — кедер", "1 шт.", 1200, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "lining": [
            ("Замена подкладки сумки, S", "1 шт.", 1800, False),
            ("Замена подкладки сумки, M", "1 шт.", 2200, False),
            ("Замена подкладки сумки, L", "1 шт.", 2600, False),
            ("Замена подкладки в кошельке / органайзере", "1 шт.", 2600, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "edges": [
            ("Торцевание уреза кожи", "1 см", 12, False),
            ("Торцевание ручек сумки (2 стороны)", "пара", 1200, False),
            ("Торцевание ручек сумки (4 стороны)", "пара", 1400, False),
            ("Торцевание плечевого ремня", "1 шт.", 1400, False),
            ("Торцевание тренчика / пулера / держателя ручек", "1 шт.", 400, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
        "belt": [
            ("Пробивание отверстий в ремне", "1 шт.", 200, False),
            ("Укорачивание кожаного ремня", "1 шт.", 450, False),
            ("Укорачивание ремня с перешиванием пряжки", "1 шт.", 600, False),
            ("Замена подклада ремня", "1 шт.", 2000, False),
            ("Реставрация ремня (проклейка, прошивка)", "1 шт.", 800, False),
            ("Мелкий ремонт", "услуга", 400, False),
        ],
    },
}

def fmt(n):
    return f"{n:,}".replace(",", " ") + " ₴"

def kb(buttons, cols=2):
    rows = []
    for i in range(0, len(buttons), cols):
        rows.append(buttons[i:i+cols])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

def get_data(ctx):
    if "order" not in ctx.user_data:
        ctx.user_data["order"] = {
            "client": "", "phone": "",
            "items": [],
            "cur": {"type": None, "type_label": "", "brand": "", "svcs": []},
            "total_fixed": 0, "total_approx": 0, "has_approx": False,
        }
    return ctx.user_data["order"]

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    get_data(ctx)
    await update.message.reply_text(
        "👋 Добро пожаловать в Rewise Studio\n\nОформляем новый заказ.\n\n*Имя клиента?*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    d["client"] = update.message.text.strip()
    await update.message.reply_text("📞 *Номер телефона?*", parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    d["phone"] = update.message.text.strip()
    d["cur"] = {"type": None, "type_label": "", "brand": "", "svcs": []}
    is_first = len(d["items"]) == 0
    text = "Какое изделие принёс клиент?" if is_first else "Ещё одна вещь — какое изделие?"
    await update.message.reply_text(
        text,
        reply_markup=kb(["👟 Обувь", "👜 Сумка / Аксессуар"], cols=2)
    )
    return ITEM_TYPE

async def get_item_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    text = update.message.text
    if "Обувь" in text:
        d["cur"]["type"] = "shoes"
        d["cur"]["type_label"] = "Обувь"
    else:
        d["cur"]["type"] = "bags"
        d["cur"]["type_label"] = "Сумка"
    await update.message.reply_text(
        "🏷 Бренд и модель?\n_(или напишите «без бренда»)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return BRAND

async def get_brand(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    d["cur"]["brand"] = update.message.text.strip()
    item_type = d["cur"]["type"]
    depts = DEPTS[item_type]
    dept_buttons = [label for _, label in depts]
    await update.message.reply_text(
        f"*{d['cur']['type_label']} — {d['cur']['brand']}*\n\nКакой отдел?",
        parse_mode="Markdown",
        reply_markup=kb(dept_buttons, cols=2)
    )
    return DEPT

async def get_dept(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    text = update.message.text.strip()
    item_type = d["cur"]["type"]
    depts = DEPTS[item_type]
    dept_id = None
    for did, dlabel in depts:
        if dlabel == text:
            dept_id = did
            break
    if not dept_id:
        await update.message.reply_text("Выберите отдел из списка.")
        return DEPT
    ctx.user_data["dept_id"] = dept_id
    ctx.user_data["dept_label"] = text
    svcs = SERVICES[item_type][dept_id]
    svc_buttons = [f"{name} — {'от ' if approx else ''}{fmt(price)}" for name, unit, price, approx in svcs]
    await update.message.reply_text(
        f"*{text}*\n\nВыберите услугу:",
        parse_mode="Markdown",
        reply_markup=kb(svc_buttons, cols=1)
    )
    return SERVICE

async def get_service(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    text = update.message.text.strip()
    item_type = d["cur"]["type"]
    dept_id = ctx.user_data["dept_id"]
    svcs = SERVICES[item_type][dept_id]
    chosen = None
    for name, unit, price, approx in svcs:
        label = f"{name} — {'от ' if approx else ''}{fmt(price)}"
        if label == text:
            chosen = (name, unit, price, approx)
            break
    if not chosen:
        await update.message.reply_text("Выберите услугу из списка.")
        return SERVICE
    ctx.user_data["chosen_svc"] = chosen
    await update.message.reply_text(
        f"Количество ({chosen[1]}):",
        reply_markup=kb(["1", "2", "3", "Больше"], cols=4)
    )
    return QTY

async def get_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
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
            reply_markup=kb(["✅ Да — +200 ₴", "❌ Нет"], cols=2)
        )
        return EXTRA200
    else:
        return await save_service(update, ctx, extra200=False)

async def get_extra200(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    extra200 = "Да" in text
    return await save_service(update, ctx, extra200=extra200)

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
        reply_markup=kb([
            "➕ Ещё одна услуга",
            "➕ Ещё одна вещь",
            "✅ Завершить заказ"
        ], cols=1)
    )
    return NEXT

async def get_next(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    text = update.message.text
    if "услуга" in text.lower():
        item_type = d["cur"]["type"]
        depts = DEPTS[item_type]
        dept_buttons = [label for _, label in depts]
        await update.message.reply_text(
            "Какой отдел?",
            reply_markup=kb(dept_buttons, cols=2)
        )
        return DEPT
    elif "вещь" in text.lower():
        commit_item(d)
        await update.message.reply_text(
            "Какое изделие?",
            reply_markup=kb(["👟 Обувь", "👜 Сумка / Аксессуар"], cols=2)
        )
        return ITEM_TYPE
    elif "Завершить" in text or "завершить" in text.lower():
        commit_item(d)
        await finish_order(update, ctx)
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=kb(["➕ Ещё одна услуга", "➕ Ещё одна вещь", "✅ Завершить заказ"], cols=1)
        )
        return NEXT

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

async def finish_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = get_data(ctx)
    total = d["total_fixed"] + d["total_approx"]
    now = datetime.now().strftime("%d.%m.%Y | %H:%M")
    lines = [
        "📋 *REWISE STUDIO — Новый заказ*",
        "",
        f"👤 {d['client']}",
        f"📞 {d['phone']}",
        f"📅 {now}",
        "",
    ]
    for i, item in enumerate(d["items"], 1):
        icon = "👟" if "Обув" in item["type_label"] else "👜"
        lines.append(f"{icon} *{item['type_label']} {i} — {item['brand']}*")
        for svc in item["svcs"]:
            price_str = f"{'от ' if svc['approx'] else ''}{fmt(svc['total'])}"
            extra = " + 200 ₴" if svc.get("extra200") else ""
            warn = " ⚠️ уточнить" if svc["approx"] else ""
            lines.append(f"  • {svc['name']} — {price_str}{extra}{warn}")
        lines.append("")
    prefix = "от " if d["has_approx"] else ""
    lines.append(f"💰 *Итого: {prefix}{fmt(total)}*")
    if d["has_approx"]:
        lines.append("⚠️ _Есть позиции для уточнения после осмотра_")
    lines.append("")
    lines.append("🔧 Rewise Studio")
    card_text = "\n".join(lines)
    await update.message.reply_text(
        f"✅ Заказ сформирован!\n\n💰 {prefix}{fmt(total)}",
        reply_markup=ReplyKeyboardRemove()
    )
    await ctx.bot.send_message(
        chat_id=CHANNEL_ID,
        text=card_text,
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "Карточка отправлена в канал ✓\n\nДля нового заказа нажми /start",
        reply_markup=ReplyKeyboardRemove()
    )

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Заказ отменён. Для нового нажми /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ITEM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_type)],
            BRAND:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_brand)],
            DEPT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dept)],
            SERVICE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            QTY:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_qty)],
            EXTRA200:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_extra200)],
            NEXT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_next)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
