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
SUPER_ADMIN_USERNAME = "lytixx"
# ==================================================

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "bot_data.json"

# ===================== ЗАГРУЗКА / СОХРАНЕНИЕ =====================
data = {
    "stats": {},
    "homework": {},
    "next_hw_id": 1,
    "users_balance": {}
}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения] {e}")

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for key in data:
                    if key in loaded:
                        data[key] = loaded[key]
            print("[Данные загружены из файла]")
        except Exception as e:
            print(f"[Ошибка загрузки] {e}")

load_data()

# ===================== КОНСТАНТЫ =====================
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

PREMIUMS = {
    "👀": {"price": 1000, "name": "Глаза"},
    "⭐": {"price": 5000, "name": "Звезда"},
    "🔥": {"price": 10000, "name": "Огонь"},
    "👑": {"price": 25000, "name": "Корона"},
    "💎": {"price": 50000, "name": "Бриллиант"},
    "🌀": {"price": 100000, "name": "Плюмбучка"}
}

GIFTS = {
    "мишка": {"emoji": "🧸", "price": 100, "name": "Мишка"},
    "сердечко": {"emoji": "❤️", "price": 100, "name": "Сердечко"}
}

# ===================== УТИЛИТЫ =====================
def now_msk():
    return datetime.utcnow() + timedelta(hours=3)

def is_casino_time():
    current = now_msk()
    return 6 <= current.hour < 12

def get_user_name(user):
    return f"@{user.username}" if user.username else user.first_name

def is_admin(user):
    if not user.username:
        return False
    return user.username.strip().lower() == SUPER_ADMIN_USERNAME.strip().lower()

def get_user_stats(chat_id, user_id, user_name=None):
    if chat_id not in data["stats"]:
        data["stats"][chat_id] = {}
    uid = str(user_id)
    if uid not in data["stats"][chat_id]:
        data["stats"][chat_id][uid] = {
            "name": user_name or str(user_id),
            "count": 0,
            "late": 0,
            "premium": "",
            "gifts": []
        }
    if user_name:
        data["stats"][chat_id][uid]["name"] = user_name
    if "gifts" not in data["stats"][chat_id][uid]:
        data["stats"][chat_id][uid]["gifts"] = []
    return data["stats"][chat_id][uid]

def get_balance(chat_id, user_id):
    if chat_id not in data["users_balance"]:
        data["users_balance"][chat_id] = {}
    return data["users_balance"][chat_id].get(str(user_id), 0)

def add_balance(chat_id, user_id, amount):
    if chat_id not in data["users_balance"]:
        data["users_balance"][chat_id] = {}
    uid = str(user_id)
    current = data["users_balance"][chat_id].get(uid, 0)
    data["users_balance"][chat_id][uid] = current + amount

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
        "👋 Привет! Я бот для закрепа, расписания, учителей, ДЗ, статистики, казино и игр.\n\n"
        "📌 **Команды:**\n"
        "• `закреп` — закрепить (в ответ)\n"
        "• `учителя` — преподаватели\n"
        "• `расписание` — расписание\n"
        "• `+дз <текст>, <дата>` — добавить ДЗ\n"
        "• `-дз <номер>` — удалить ДЗ\n"
        "• `дз` — список ДЗ\n"
        "• `стата` — статистика и топ опозданий\n"
        "• `профиль` — профиль (свой или в ответ)\n"
        "• `казино` — помощь по казино\n"
        "• `казино куб [ставка]` — игра в куб\n"
        "• `казино рулетка [ставка]` — рулетка\n"
        "• `магазин` — премиумы за коины\n"
        "• `баланс` — мои коины\n"
        "• `подарить мишку` / `подарить сердечко` — подарить (в ответ, 100 коинов)\n"
        "• `обкашлять` (в ответ) — мини-игра\n"
        "• `команды` — список"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ===================== ОСНОВНОЙ ОБРАБОТЧИК =====================
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

    # ============ АДМИН-КОМАНДЫ (@lytixx) ============
    if text_lower.startswith("+коины") or text_lower.startswith("+прем") or text_lower.startswith("+подарок"):
        if not is_admin(message.from_user):
            bot.reply_to(message, "❌ У вас нет прав на эту команду.")
            return

        # ---- +КОИНЫ ----
        if text_lower.startswith("+коины"):
            parts = text.split()

            # +коины <сумма> всем
            if len(parts) == 3 and parts[2].lower() in ["всем", "все"]:
                try:
                    amount = int(parts[1])
                except ValueError:
                    bot.reply_to(message, "❌ Сумма должна быть числом.")
                    return
                if chat_id not in data["stats"] or not data["stats"][chat_id]:
                    bot.reply_to(message, "❌ В этом чате ещё нет участников в статистике.")
                    return
                count = 0
                for uid in data["stats"][chat_id]:
                    add_balance(chat_id, uid, amount)
                    count += 1
                save_data()
                bot.reply_to(message, f"✅ Выдано **{amount}** коинов **{count}** участникам чата!", parse_mode="Markdown")
                return

            # +коины <сумма> @username
            if len(parts) == 3 and parts[2].startswith("@"):
                try:
                    amount = int(parts[1])
                except ValueError:
                    bot.reply_to(message, "❌ Сумма должна быть числом.")
                    return
                target_username = parts[2].replace("@", "").lower()
                target_id = None
                target_name = None
                if chat_id in data["stats"]:
                    for uid, u in data["stats"][chat_id].items():
                        if u["name"].lower() == f"@{target_username}":
                            target_id = uid
                            target_name = u["name"]
                            break
                if not target_id:
                    bot.reply_to(message, "❌ Пользователь не найден в чате. Он должен хотя бы раз написать сообщение.")
                    return
                add_balance(chat_id, target_id, amount)
                save_data()
                bot.reply_to(message, f"✅ Выдано **{amount}** коинов пользователю {target_name}.", parse_mode="Markdown")
                return

            # +коины <сумма> (в ответ)
            if len(parts) == 2 and message.reply_to_message:
                try:
                    amount = int(parts[1])
                except ValueError:
                    bot.reply_to(message, "❌ Сумма должна быть числом.")
                    return
                target = message.reply_to_message.from_user
                if target.is_bot:
                    bot.reply_to(message, "❌ Нельзя выдать коины боту.")
                    return
                target_id = str(target.id)
                target_name = get_user_name(target)
                get_user_stats(chat_id, target_id, target_name)
                add_balance(chat_id, target_id, amount)
                save_data()
                bot.reply_to(message, f"✅ Выдано **{amount}** коинов пользователю {target_name}.", parse_mode="Markdown")
                return

            bot.reply_to(message, (
                "❌ Формат:\n"
                "• `+коины <сумма>` (в ответ на сообщение)\n"
                "• `+коины <сумма> @username`\n"
                "• `+коины <сумма> всем`"
            ), parse_mode="Markdown")
            return

        # ---- +ПРЕМ ----
        if text_lower.startswith("+прем"):
            if not message.reply_to_message:
                bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которому хотите выдать премиум.")
                return
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "❌ Формат: `+прем <эмодзи>` (в ответ на сообщение)")
                return
            emoji = parts[1].strip()
            if emoji not in PREMIUMS:
                bot.reply_to(message, f"❌ Доступные премиумы: {', '.join(PREMIUMS.keys())}")
                return
            target = message.reply_to_message.from_user
            if target.is_bot:
                bot.reply_to(message, "❌ Нельзя выдать премиум боту.")
                return
            target_id = str(target.id)
            target_name = get_user_name(target)
            target_stats = get_user_stats(chat_id, target_id, target_name)
            target_stats["premium"] = emoji
            save_data()
            bot.reply_to(message, f"✅ Пользователю {target_name} выдан премиум {emoji}!", parse_mode="Markdown")
            return

        # ---- +ПОДАРОК ----
        if text_lower.startswith("+подарок"):
            if not message.reply_to_message:
                bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которому хотите подарить подарок.")
                return
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "❌ Формат: `+подарок <мишка|сердечко>` (в ответ на сообщение)")
                return
            gift_name = parts[1].strip().lower()
            if gift_name not in GIFTS:
                bot.reply_to(message, f"❌ Доступные подарки: {', '.join(GIFTS.keys())}")
                return
            target = message.reply_to_message.from_user
            if target.is_bot:
                bot.reply_to(message, "❌ Нельзя подарить подарок боту.")
                return
            target_id = str(target.id)
            target_name = get_user_name(target)
            target_stats = get_user_stats(chat_id, target_id, target_name)
            gift_info = GIFTS[gift_name]
            gift_entry = {
                "from": user_name,
                "gift": gift_info["emoji"] + " " + gift_info["name"],
                "date": now_msk().strftime("%d.%m.%Y %H:%M")
            }
            target_stats["gifts"].append(gift_entry)
            save_data()
            bot.reply_to(message, f"✅ Вы подарили {gift_info['emoji']} **{gift_info['name']}** пользователю {target_name}!", parse_mode="Markdown")
            return

    # ============ КОМАНДЫ ============
    if text_lower == "команды":
        bot.send_message(chat_id, (
            "📋 **Команды:**\n\n"
            "📌 **Утилиты:**\n"
            "• `закреп`, `учителя`, `расписание`, `стата`\n\n"
            "📚 **ДЗ:** `+дз <текст>, <дата>`, `-дз <номер>`, `дз`\n\n"
            "👤 **Профиль:** `профиль`\n\n"
            "🎰 **Казино:**\n"
            "• `казино` — помощь\n"
            "• `казино куб [ставка]` — игра в куб\n"
            "• `казино рулетка [ставка]` — рулетка\n\n"
            "💰 **Экономика:** `баланс`, `магазин`\n\n"
            "🎁 **Подарки:** `подарить мишку`, `подарить сердечко` (в ответ, 100 коинов)\n\n"
            "🎮 **Игры:** `обкашлять` (в ответ на сообщение)\n\n"
            "👑 **Админ:** `+коины <сумма> [@user|всем]`, `+прем <эмодзи>`, `+подарок <мишка|сердечко>` (в ответ)"
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

    # ============ СТАТА (вместо топ) ============
    if text_lower == "стата":
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

        # Топ опозданий
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

    # ============ ПРОФИЛЬ ============
    if text_lower == "профиль":
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        target_id = str(target.id)
        target_name = get_user_name(target)
        target_stats = get_user_stats(chat_id, target_id, target_name)
        balance = get_balance(chat_id, target_id)

        premium = target_stats.get("premium", "")
        premium_str = f"{premium} " if premium else ""

        gifts = target_stats.get("gifts", [])
        gifts_lines = []
        if gifts:
            for g in gifts:
                gifts_lines.append(f"• {g['gift']} от {g['from']} ({g['date']})")
        else:
            gifts_lines.append("• Пока нет подарков")

        profile_text = (
            f"╔══════════════════════════╗\n"
            f"║   👤 **ПРОФИЛЬ** {premium_str}{target_name}\n"
            f"╚══════════════════════════╝\n"
            f"💬 **Сообщений:** {target_stats['count']}\n"
            f"⏰ **Опозданий:** {target_stats['late']}\n"
            f"💰 **Коинов:** {balance} 🪙\n"
            f"🎖 **Премиум:** {premium if premium else 'Нет'}\n\n"
            f"🎁 **Подарки:**\n" + "\n".join(gifts_lines)
        )
        bot.send_message(chat_id, profile_text, parse_mode="Markdown")
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
        bot.reply_to(message, f"✅ Ты купил {found_emoji} **{PREMIUMS[found_emoji]['name']}** за {price} 🪙!", parse_mode="Markdown")
        return

    # ============ ПОДАРИТЬ МИШКУ / СЕРДЕЧКО ============
    if text_lower == "подарить мишку" or text_lower == "подарить сердечко":
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которому хотите подарить подарок.")
            return
        gift_name = "мишка" if "мишку" in text_lower else "сердечко"
        gift_info = GIFTS[gift_name]
        price = gift_info["price"]
        if get_balance(chat_id, user_id) < price:
            bot.reply_to(message, f"❌ Недостаточно коинов. Нужно {price}, у тебя {get_balance(chat_id, user_id)}.")
            return
        target = message.reply_to_message.from_user
        if target.id == message.from_user.id:
            bot.reply_to(message, "❌ Нельзя подарить подарок самому себе.")
            return
        target_id = str(target.id)
        target_name = get_user_name(target)
        target_stats = get_user_stats(chat_id, target_id, target_name)
        add_balance(chat_id, user_id, -price)
        gift_entry = {
            "from": user_name,
            "gift": gift_info["emoji"] + " " + gift_info["name"],
            "date": now_msk().strftime("%d.%m.%Y %H:%M")
        }
        target_stats["gifts"].append(gift_entry)
        save_data()
        bot.reply_to(message, f"✅ Ты подарил {gift_info['emoji']} **{gift_info['name']}** пользователю {target_name}!", parse_mode="Markdown")
        return

    # ============ КАЗИНО ============
    if text_lower == "казино":
        bot.reply_to(message, (
            "🎰 **Доступные игры:**\n\n"
            "• `казино куб [ставка]` — куб (шанс выиграть 1 к 6, выплата x5)\n"
            "• `казино рулетка [ставка]` — рулетка (шанс выиграть 20%, выплата x4)\n\n"
            "Пример: `казино куб 100` или `казино рулетка 500`\n"
            "Если ставка не указана, используется 100 коинов."
        ), parse_mode="Markdown")
        return

    if text_lower.startswith("казино куб") or text_lower.startswith("казино рулетка"):
        if not is_casino_time():
            current = now_msk().strftime("%H:%M")
            bot.reply_to(message, f"🎰 Казино работает только с **06:00 до 12:00** по МСК.\nСейчас: {current} МСК.", parse_mode="Markdown")
            return

        parts = text.split()
        game_type = parts[1].lower()  # "куб" или "рулетка"
        bet = 100
        if len(parts) >= 3:
            try:
                bet = int(parts[2])
            except ValueError:
                bot.reply_to(message, "❌ Ставка должна быть числом.")
                return
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше нуля.")
                return

        if get_balance(chat_id, user_id) < bet:
            bot.reply_to(message, f"❌ Недостаточно коинов. Нужно {bet}, у тебя {get_balance(chat_id, user_id)}.")
            return

        # Списываем ставку
        add_balance(chat_id, user_id, -bet)
        save_data()

        msg = bot.reply_to(message, "🎰 Крутим...")
        frames = ["🎰 | ❓ | ❓ | ❓", "🎰 | 🔄 | ❓ | ❓", "🎰 | 🔄 | 🔄 | ❓", "🎰 | 🔄 | 🔄 | 🔄"]
        time.sleep(0.5)
        for frame in frames[:3]:
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=frame)
                time.sleep(0.4)
            except Exception:
                pass

        # Определяем результат
        if game_type == "куб":
            # Куб: выигрыш если выпадет 6 (шанс 1/6), выплата x5
            dice_result = random.randint(1, 6)
            dice_emoji = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}
            final_text = f"🎲 Выпало: {dice_emoji[dice_result]}\n"
            if dice_result == 6:
                win = bet * 5
                add_balance(chat_id, user_id, win)
                final_text += f"🎉 **ПОБЕДА!** Ты выиграл **{win}** 🪙!\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"
            else:
                final_text += f"😢 **Проигрыш.** Ты потерял {bet} 🪙.\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"
        else:  # рулетка
            # Рулетка: выигрыш с шансом 20%, выплата x4
            win_chance = random.random() < 0.20
            final_text = "🎡 Крутится рулетка...\n"
            if win_chance:
                win = bet * 4
                add_balance(chat_id, user_id, win)
                final_text += f"🎉 **ПОБЕДА!** Ты выиграл **{win}** 🪙!\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"
            else:
                final_text += f"😢 **Проигрыш.** Ты потерял {bet} 🪙.\n💰 Баланс: {get_balance(chat_id, user_id)} 🪙"

        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=final_text, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id, final_text, parse_mode="Markdown")
        save_data()
        return

    # ============ ОБКАШЛЯТЬ ============
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