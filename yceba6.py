import telebot
from datetime import datetime, timedelta
import json
import os
import random
import time

# ==================== НАСТРОЙКИ ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"
BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
# ==================================================

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "bot_data.json"

# ===================== ЗАГРУЗКА / СОХРАНЕНИЕ =====================
data = {
    "stats": {},          # {chat_id: {user_id: {"name": str, "count": int, "late": int, "premium": str}}}
    "homework": {},       # {chat_id: [{"id": int, "text": str, "date": str, "author": str}]}
    "next_hw_id": 1,
    "users_balance": {}   # {chat_id: {user_id: int}} — коины для магазина
}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for key in data:
                    if key in loaded:
                        data[key] = loaded[key]
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

load_data()

# ===================== СЛОВА ОПОЗДАНИЙ =====================
LATE_WORDS = [
    "опаздываю", "опаздываешь", "опаздывает", "опаздываем", "опаздываете", "опаздывают",
    "опоздал", "опоздала", "опоздало", "опоздали",
    "опоздаю", "опоздаешь", "опоздает", "опоздаем", "опоздаете", "опоздают",
    "опоздание", "опоздания", "опозданий",
    "проспал", "проспала", "проспали", "просплю", "проспишь", "проспит",
    "просыпаю", "просыпал", "проспавший",
    "задержался", "задержалась", "задержались", "задержусь", "задержишься",
    "задерживаюсь", "задерживаемся", "задержка",
    "поздно", "поздновато",
    "не успеваю", "не успел", "не успела", "не успели",
    "буду позже", "буду поздно", "приду позже", "приду поздно",
    "опазд", "опозн", "задерж"
]

# ===================== ПРЕМИУМЫ =====================
PREMIUMS = {
    "👀": {"price": 1000, "name": "Глаза"},
    "⭐": {"price": 5000, "name": "Звезда"},
    "🔥": {"price": 10000, "name": "Огонь"},
    "👑": {"price": 25000, "name": "Корона"},
    "💎": {"price": 50000, "name": "Бриллиант"}
}

# ===================== УТИЛИТЫ =====================
def now_msk():
    """Возвращает текущее время по МСК (UTC+3)."""
    return datetime.utcnow() + timedelta(hours=3)

def is_casino_time():
    """Казино доступно с 06:00 до 12:00 по МСК."""
    current = now_msk()
    return 6 <= current.hour < 12

def get_user_name(user):
    return f"@{user.username}" if user.username else user.first_name

def get_user_stats(chat_id, user_id, user_name=None):
    if chat_id not in data["stats"]:
        data["stats"][chat_id] = {}
    if str(user_id) not in data["stats"][chat_id]:
        data["stats"][chat_id][str(user_id)] = {
            "name": user_name or str(user_id),
            "count": 0,
            "late": 0,
            "premium": ""
        }
    if user_name:
        data["stats"][chat_id][str(user_id)]["name"] = user_name
    return data["stats"][chat_id][str(user_id)]

def get_balance(chat_id, user_id):
    if chat_id not in data["users_balance"]:
        data["users_balance"][chat_id] = {}
    return data["users_balance"][chat_id].get(str(user_id), 0)

def add_balance(chat_id, user_id, amount):
    if chat_id not in data["users_balance"]:
        data["users_balance"][chat_id] = {}
    current = data["users_balance"][chat_id].get(str(user_id), 0)
    data["users_balance"][chat_id][str(user_id)] = current + amount

def parse_date(date_str):
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def cleanup_homework(chat_id):
    if chat_id not in data["homework"]:
        return
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    data["homework"][chat_id] = [
        hw for hw in data["homework"][chat_id]
        if parse_date(hw["date"]) and parse_date(hw["date"]) >= today
    ]

def animate_message(chat_id, message_id, frames, final_text, delay=0.4):
    """Простая анимация через редактирование сообщения."""
    for frame in frames:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=frame)
            time.sleep(delay)
        except Exception:
            pass
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=final_text, parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, final_text, parse_mode="Markdown")

# ===================== СТАРТ =====================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 Привет! Я бот для закрепа, расписания, учителей, ДЗ, топа, казино и игр.\n\n"
        "📌 **Команды:**\n"
        "• `закреп` — закрепить (в ответ)\n"
        "• `учителя` — преподаватели\n"
        "• `расписание` — расписание\n"
        "• `+дз <текст>, <дата>` — добавить ДЗ\n"
        "• `-дз <номер>` — удалить ДЗ\n"
        "• `дз` — список ДЗ\n"
        "• `топ` — топ активности и опозданий\n"
        "• `казино` — игра (с 06:00 до 12:00 МСК)\n"
        "• `магазин` — премиумы за коины\n"
        "• `баланс` — мои коины\n"
        "• `обкашлять` (в ответ) — мини-игра\n"
        "• `команды` — список"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ===================== ОСНОВНОЙ ОБРАБОТЧИК ГРУПП =====================
@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'] and msg.text)
def handle_group(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    user_name = get_user_name(message.from_user)
    text = message.text.strip()
    text_lower = text.lower()

    # Учёт статистики
    user_stats = get_user_stats(chat_id, user_id, user_name)
    user_stats["count"] += 1
    if any(word in text_lower for word in LATE_WORDS):
        user_stats["late"] += 1

    # Начисляем 1 коин за сообщение
    add_balance(chat_id, user_id, 1)
    save_data()

    # ============ КОМАНДЫ ============
    if text_lower == "команды":
        bot.send_message(chat_id, (
            "📋 **Команды:**\n\n"
            "📌 **Утилиты:**\n"
            "• `закреп`, `учителя`, `расписание`, `топ`\n\n"
            "📚 **ДЗ:** `+дз <текст>, <дата>`, `-дз <номер>`, `дз`\n\n"
            "🎰 **Казино:** `казино` (с 06:00 до 12:00 МСК)\n\n"
            "💰 **Экономика:** `баланс`, `магазин`\n\n"
            "🎮 **Игры:** `обкашлять` (в ответ на сообщение)"
        ), parse_mode="Markdown")
        return

    if text_lower == "закреп":
        if message.reply_to_message:
            try:
                bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
                bot.reply_to(message, "📌 Сообщение успешно закреплено!")
            except Exception:
                bot.reply_to(message, "❌ Не удалось закрепить. Проверьте права админа.")
        else:
            bot.reply_to(message, "❌ Эта команда должна быть ответом на сообщение.")
        return

    if text_lower == "учителя":
        bot.send_message(chat_id, (
            "🎓 **Список преподавателей:**\n\n"
            "• Ибрагимов Максуд Умарович — физическая культура\n"
            "• Сулько Мария Григорьевна — математика\n"
            "• Корбова Марина Александровна — русский язык\n"
            "• Чумак Вера Анатольевна — иностранный язык\n"
            "• Шляхов Алексей Борисович — введение в проф. деятельность\n"
            "• Колеватова Вероника Константиновна — информатика\n"
            "• Мавлютова Гузалия Мавлеткуловна — физика\n"
            "• Золтан Варвара Николаевна — физкультура (плавание)\n"
            "• Гончаров Алексей Анатольевич — история; ОБЗР"
        ), parse_mode="Markdown")
        return

    if text_lower == "расписание":
        bot.send_message(chat_id, (
            "▎**Расписание занятий**\n\n"
            "👥 **Группа ЭМ-1-26(а)**\n"
            "🏫 БУ «Нижневартовский политехнический колледж»\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 **Понедельник**\n"
            "08:00–08:30 — Разговоры о важном, ауд. А22\n"
            "08:35–09:35 — Основы бережливого производства, ауд. А22\n"
            "09:50–10:50 — Математика, Хиндогина, ауд. А25\n"
            "11:05–11:35 — Математика, Хиндогина, ауд. А25\n"
            "11:35–12:05 — Русский язык, Корбова, ауд. А7\n"
            "12:20–13:20 — Русский язык, Корбова, дистанционно\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 **Вторник**\n"
            "08:00–09:35 — Физическая культура, Ибрагимов, спортзал\n"
            "09:50–11:25 — Иностранный язык, Чумак А., ауд. Б59\n"
            "11:40–13:25 — Введение в проф. деятельность, Шляхов, ауд. Б63\n"
            "13:35–14:20 — Математика, Хиндогина, дистанционно\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 **Среда**\n"
            "08:00–09:35 — Информатика, Колеватова, ауд. А26\n"
            "09:50–11:25 — Физика, Мавлютова, ауд. А22\n"
            "11:40–13:25 — История, Гончаров, ауд. Б41\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 **Четверг**\n"
            "08:00–09:35 — Иностранный язык, Чумак А., ауд. А24\n"
            "09:50–11:25 — ОБЖ, Гончаров, ауд. Б41\n"
            "11:40–12:25 — Физика, Мавлютова, ауд. А22\n"
            "12:40–14:20 — Физическая культура, Ибрагимов, дистанционно\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📅 **Пятница**\n"
            "08:00–09:35 — История, Гончаров, ауд. Б41\n"
            "09:50–11:25 — Физика, Мавлютова, ауд. А22\n"
            "11:40–13:25 — Информатика, Колеватова, ауд. Б50\n"
            "13:35–15:10 — Русский язык, Корбова, дистанционно"
        ), parse_mode="Markdown")
        return

    # ============ ДОБАВИТЬ ДЗ ============
    if text_lower.startswith("+дз"):
        body = text[3:].strip()
        if not body:
            bot.reply_to(message, "❌ Формат: `+дз <текст>, <дата>`\nПример: `+дз написать стих, 14.11.26`", parse_mode="Markdown")
            return
        if "," in body:
            parts = body.rsplit(",", 1)
            hw_text = parts[0].strip()
            date_str = parts[1].strip()
        else:
            words = body.split()
            date_str = words[-1]
            hw_text = " ".join(words[:-1]).strip()
        parsed = parse_date(date_str)
        if not parsed:
            bot.reply_to(message, "❌ Не вижу дату сдачи в конце. Пример: `+дз написать стих, 14.11.26`")
            return
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if parsed < today:
            bot.reply_to(message, "❌ Дата уже прошла.")
            return
        if not hw_text:
            bot.reply_to(message, "❌ Не вижу текст задания.")
            return
        if chat_id not in data["homework"]:
            data["homework"][chat_id] = []
        hw_id = data["next_hw_id"]
        data["next_hw_id"] += 1
        data["homework"][chat_id].append({
            "id": hw_id, "text": hw_text, "date": date_str, "author": user_name
        })
        save_data()
        bot.reply_to(message, (
            f"✅ **Задание добавлено!**\n\n"
            f"📚 {hw_text}\n"
            f"⏳ Сдать до: **{date_str}**\n"
            f"🔢 Номер: **№{hw_id}**"
        ), parse_mode="Markdown")
        return

    # ============ УДАЛИТЬ ДЗ ============
    if text_lower.startswith("-дз"):
        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: `-дз <номер>`")
            return
        try:
            hw_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Номер должен быть числом.")
            return
        if chat_id not in data["homework"]:
            bot.reply_to(message, "❌ Список пуст.")
            return
        before = len(data["homework"][chat_id])
        data["homework"][chat_id] = [hw for hw in data["homework"][chat_id] if hw["id"] != hw_id]
        if len(data["homework"][chat_id]) < before:
            save_data()
            bot.reply_to(message, f"✅ Задание №{hw_id} удалено.")
        else:
            bot.reply_to(message, f"❌ Задание №{hw_id} не найдено.")
        return

    # ============ СПИСОК ДЗ ============
    if text_lower == "дз":
        cleanup_homework(chat_id)
        save_data()
        if chat_id not in data["homework"] or not data["homework"][chat_id]:
            bot.reply_to(message, "📭 Список домашних заданий пуст.")
            return
        lines = ["📚 **Домашние задания:**\n"]
        for hw in data["homework"][chat_id]:
            lines.append(
                f"**№{hw['id']}** — {hw['text']}\n"
                f"   ⏳ Сдать до: **{hw['date']}**\n"
                f"   ✍️ Добавил: {hw['author']}\n"
            )
        bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown")
        return

    # ============ ТОП ============
    if text_lower == "топ":
        if chat_id not in data["stats"] or not data["stats"][chat_id]:
            bot.reply_to(message, "📊 Статистика пуста.")
            return

        all_users = list(data["stats"][chat_id].values())

        # Топ активности
        sorted_active = sorted(all_users, key=lambda x: x["count"], reverse=True)[:10]
        active_lines = ["📊 **Топ по активности:**\n"]
        for i, u in enumerate(sorted_active, 1):
            premium = u.get("premium", "")
            prefix = f"{premium} " if premium else ""
            active_lines.append(f"{i}. {prefix}{u['name']} — {u['count']} сообщ.")
        active_text = "\n".join(active_lines)

        # Топ опозданий (только у кого > 0)
        late_users = [u for u in all_users if u["late"] > 0]
        late_users.sort(key=lambda x: x["late"], reverse=True)
        late_lines = ["\n⏰ **Топ опозданий:**\n"]
        if late_users:
            for i, u in enumerate(late_users[:10], 1):
                premium = u.get("premium", "")
                prefix = f"{premium} " if premium else ""
                late_lines.append(f"{i}. {prefix}{u['name']} — {u['late']} раз(а)")
        else:
            late_lines.append("😇 Пока никто не опаздывал")
        late_text = "\n".join(late_lines)

        bot.send_message(chat_id, active_text + late_text, parse_mode="Markdown")
        return

    # ============ БАЛАНС ============
    if text_lower == "баланс":
        bal = get_balance(chat_id, user_id)
        bot.reply_to(message, f"💰 У {user_name} **{bal}** коинов.", parse_mode="Markdown")
        return

    # ============ МАГАЗИН ============
    if text_lower == "магазин":
        lines = ["🛒 **Магазин премиумов:**\n"]
        for emoji, info in PREMIUMS.items():
            lines.append(f"{emoji} **{info['name']}** — {info['price']} 🪙")
        lines.append("\nКупить: `купить <название>`")
        lines.append(f"💰 Твой баланс: {get_balance(chat_id, user_id)} 🪙")
        bot.reply_to(message, "\n".join(lines), parse_mode="Markdown")
        return

    # ============ КУПИТЬ ПРЕМИУМ ============
    if text_lower.startswith("купить "):
        item_name = text[7:].strip().lower()
        found_emoji = None
        for emoji, info in PREMIUMS.items():
            if info["name"].lower() == item_name:
                found_emoji = emoji
                break
        if not found_emoji:
            bot.reply_to(message, "❌ Такого премиума нет. Смотри `магазин`.")
            return
        price = PREMIUMS[found_emoji]["price"]
        if get_balance(chat_id, user_id) < price:
            bot.reply_to(message, f"❌ Недостаточно коинов. Нужно {price}, у тебя {get_balance(chat_id, user_id)}.")
            return
        add_balance(chat_id, user_id, -price)
        user_stats["premium"] = found_emoji
        save_data()
        bot.reply_to(message, f"✅ Ты купил {found_emoji} **{PREMIUMS[found_emoji]['name']}** за {price} 🪙!\nТеперь значок отображается в топе.", parse_mode="Markdown")
        return

    # ============ КАЗИНО ============
    if text_lower == "казино":
        if not is_casino_time():
            current = now_msk().strftime("%H:%M")
            bot.reply_to(message, f"🎰 Казино работает только с **06:00 до 12:00** по МСК.\nСейчас: {current} МСК.", parse_mode="Markdown")
            return
        if get_balance(chat_id, user_id) < 100:
            bot.reply_to(message, "❌ Нужно минимум 100 коинов для игры.")
            return
        bet = 100
        add_balance(chat_id, user_id, -bet)
        msg = bot.reply_to(message, "🎰 Крутим барабаны...")
        frames = ["🎰 | ❓ | ❓ | ❓", "🎰 | 🍒 | ❓ | ❓", "🎰 | 🍒 | 🍋 | ❓", "🎰 | 🍒 | 🍋 | 💎"]
        roll = random.random()
        if roll < 0.4:
            win = bet * 2
            add_balance(chat_id, user_id, win)
            final = f"🎉 **Выигрыш x2!** Ты получил **{win}** 🪙!\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"
        elif roll < 0.5:
            win = bet * 5
            add_balance(chat_id, user_id, win)
            final = f"💎 **ДЖЕКПОТ x5!** Ты получил **{win}** 🪙!\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"
        else:
            final = f"😢 **Проигрыш.** Ты потерял {bet} 🪙.\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"
        save_data()
        animate_message(chat_id, msg.message_id, frames, final, delay=0.5)
        return

    # ============ ОБКАШЛЯТЬ (мини-игра) ============
    if text_lower == "обкашлять":
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение игрока, с которым хотите обкашлять вопросы.")
            return
        target_user = message.reply_to_message.from_user
        target_name = get_user_name(target_user)
        if target_user.id == message.from_user.id:
            bot.reply_to(message, "❌ Нельзя обкашлять самого себя 🤔")
            return

        msg = bot.reply_to(message, f"🤝 {user_name} начинает обкашливать вопросы с {target_name}...")
        frames = [
            "🤝 | Обкашливаем...",
            "🤝 | Обкашливаем вопросы... 🤔",
            "🤝 | Активно обкашливаем... 💬",
            "🤝 | Почти закончили... ⏳"
        ]
        # Вероятность успеха 60%
        if random.random() < 0.6:
            final = f"✅ **Успешно обкашляно!** {user_name} и {target_name} отлично пообщались 🤝"
        else:
            final = f"❌ **Не удалось обкашлять.** {user_name} и {target_name} не нашли общий язык 😬"
        animate_message(chat_id, msg.message_id, frames, final, delay=0.4)
        return

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()