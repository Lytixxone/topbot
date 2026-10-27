import telebot
from datetime import datetime

# ==================== НАСТРОЙКИ БОТА ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"
BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище ДЗ: {chat_id: [ {"id": int, "text": str, "date": "ДД.ММ.ГГГГ", "author": str} ]}
homework_db = {}
next_hw_id = 1

# Статистика пользователей: {chat_id: {user_id: {"name": str, "count": int, "late": int}}}
stats = {}

# Слова, означающие опоздание
LATE_WORDS = ["опаздываю", "опоздал", "опоздала", "опоздание", "проспал", "проспала", "задержался", "задержалась"]

def get_user_name(user):
    return f"@{user.username}" if user.username else user.first_name

def parse_date(date_str):
    """Парсит дату вида ДД.ММ.ГГГГ или ДД.ММ.ГГ и возвращает datetime или None."""
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def cleanup_homework(chat_id):
    """Удаляет задания, у которых дата сдачи уже прошла."""
    if chat_id not in homework_db:
        return
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    homework_db[chat_id] = [
        hw for hw in homework_db[chat_id]
        if parse_date(hw["date"]) and parse_date(hw["date"]) >= today
    ]

# ================= КОМАНДЫ =================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.send_message(
            message.chat.id,
            "👋 Привет! Я бот для закрепа, расписания, учителей и домашних заданий.\n\n"
            "📌 **Команды:**\n"
            "• `закреп` — закрепить сообщение (в ответ на сообщение)\n"
            "• `учителя` — список преподавателей\n"
            "• `расписание` — расписание занятий\n"
            "• `+дз <текст>, <дата>` — добавить домашнее задание\n"
            "• `-дз <номер>` — удалить домашнее задание\n"
            "• `дз` — список домашних заданий\n"
            "• `топ` — топ по активности и опозданиям\n"
            "• `команды` — этот список",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            message.chat.id,
            "👋 Я в чате! Используйте:\n"
            "• `закреп` (в ответ на сообщение)\n"
            "• `учителя`\n"
            "• `расписание`\n"
            "• `+дз <текст>, <дата>`\n"
            "• `-дз`, `дз`\n"
            "• `топ`\n"
            "• `команды`"
        )

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def handle_group_commands(message):
    global next_hw_id
    if not message.text:
        return
    chat_id = message.chat.id
    text = message.text.strip()
    text_lower = text.lower()
    user_name = get_user_name(message.from_user)
    user_id = message.from_user.id

    # === УЧЁТ СТАТИСТИКИ (сообщения и опоздания) ===
    if chat_id not in stats:
        stats[chat_id] = {}
    if user_id not in stats[chat_id]:
        stats[chat_id][user_id] = {"name": user_name, "count": 0, "late": 0}
    stats[chat_id][user_id]["count"] += 1

    # Проверяем наличие слов опоздания в тексте (в любом месте)
    if any(word in text_lower for word in LATE_WORDS):
        stats[chat_id][user_id]["late"] += 1

    # === Список команд ===
    if text_lower == "команды":
        commands_list = (
            "📋 **Список команд:**\n\n"
            "📌 **Утилиты:**\n"
            "• `закреп` — закрепить сообщение (в ответ на сообщение)\n"
            "• `учителя` — список преподавателей\n"
            "• `расписание` — расписание занятий\n"
            "• `топ` — топ активности и опозданий\n"
            "• `команды` — этот список\n\n"
            "📚 **Домашние задания:**\n"
            "• `+дз <текст>, <дата>` — добавить (например: `+дз написать стих, 14.11.26`)\n"
            "• `-дз <номер>` — удалить задание по номеру\n"
            "• `дз` — показать список заданий"
        )
        bot.send_message(chat_id, commands_list, parse_mode="Markdown")
        return

    # === Учителя ===
    if text_lower == "учителя":
        teachers = (
            "🎓 **Список преподавателей:**\n\n"
            "• Ибрагимов Максуд Умарович — физическая культура (лекция, практическое занятие)\n"
            "• Сулько Мария Григорьевна — математика\n"
            "• Корбова Марина Александровна — русский язык\n"
            "• Чумак Вера Анатольевна — иностранный язык\n"
            "• Шляхов Алексей Борисович — введение в профессиональную деятельность\n"
            "• Колеватова Вероника Константиновна — информатика\n"
            "• Мавлютова Гузалия Мавлеткуловна — физика\n"
            "• Золтан Варвара Николаевна — физическая культура (плавание)\n"
            "• Гончаров Алексей Анатольевич — история; основы безопасности и защиты Родины"
        )
        bot.send_message(chat_id, teachers, parse_mode="Markdown")
        return

    # === Расписание ===
    if text_lower == "расписание":
        schedule = (
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
            "08:00–09:35 — Физическая культура, Ибрагимов, спортивный зал\n"
            "09:50–11:25 — Иностранный язык, Чумак А., ауд. Б59\n"
            "11:40–13:25 — Введение в профессиональную деятельность, Шляхов, ауд. Б63\n"
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
        )
        bot.send_message(chat_id, schedule, parse_mode="Markdown")
        return

    # === Закреп ===
    if text_lower == "закреп":
        if message.reply_to_message:
            try:
                bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
                bot.reply_to(message, "📌 Сообщение успешно закреплено!")
            except Exception:
                bot.reply_to(message, "❌ Не удалось закрепить. Проверьте, что я администратор с правом закрепления сообщений.")
        else:
            bot.reply_to(message, "❌ Эта команда должна быть ответом на сообщение.")
        return

    # === ТОП (АКТИВНОСТЬ + ОПОЗДАНИЯ) ===
    if text_lower == "топ":
        if chat_id not in stats or not stats[chat_id]:
            bot.reply_to(message, "📊 Статистика пока пуста.")
            return

        # Топ по активности
        sorted_active = sorted(stats[chat_id].values(), key=lambda x: x["count"], reverse=True)[:10]
        top_active_text = "📊 **Топ по активности:**\n\n"
        for i, user in enumerate(sorted_active, 1):
            top_active_text += f"{i}. {user['name']} — {user['count']} сообщ.\n"

        # Топ по опозданиям
        sorted_late = sorted(stats[chat_id].values(), key=lambda x: x["late"], reverse=True)[:10]
        top_late_text = "\n⏰ **Топ по опозданиям:**\n\n"
        for i, user in enumerate(sorted_late, 1):
            if user['late'] > 0:
                top_late_text += f"{i}. {user['name']} — {user['late']} раз(а)\n"
        if all(u["late"] == 0 for u in sorted_late):
            top_late_text += "Пока никто не опаздывал 😇\n"

        bot.send_message(chat_id, top_active_text + top_late_text, parse_mode="Markdown")
        return

    # === ДОБАВИТЬ ДЗ (+дз) ===
    if text_lower.startswith("+дз"):
        body = text[3:].strip()
        if not body:
            bot.reply_to(
                message,
                "❌ Формат: `+дз <текст задания>, <дата>`\n"
                "Пример: `+дз написать стихотворение об России 20века, 14.11.26`",
                parse_mode="Markdown"
            )
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
            bot.reply_to(
                message,
                "❌ Не вижу дату сдачи. Укажите её в конце: `ДД.ММ.ГГГГ` или `ДД.ММ.ГГ`.\n"
                "Пример: `+дз написать стих, 14.11.26`",
                parse_mode="Markdown"
            )
            return

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if parsed < today:
            bot.reply_to(message, "❌ Дата уже прошла. Укажите будущую дату.")
            return

        if not hw_text:
            bot.reply_to(message, "❌ Не вижу текст задания. Пример: `+дз написать стих, 14.11.26`")
            return

        if chat_id not in homework_db:
            homework_db[chat_id] = []
        hw_id = next_hw_id
        next_hw_id += 1
        homework_db[chat_id].append({
            "id": hw_id,
            "text": hw_text,
            "date": date_str,
            "author": user_name
        })

        bot.reply_to(
            message,
            f"✅ **Задание добавлено!**\n\n"
            f"📚 {hw_text}\n"
            f"⏳ Сдать до: **{date_str}**\n"
            f"🔢 Номер: **№{hw_id}**\n"
            f"Посмотреть все: `дз`",
            parse_mode="Markdown"
        )
        return

    # === УДАЛИТЬ ДЗ (-дз) ===
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
        if chat_id not in homework_db:
            bot.reply_to(message, "❌ Список пуст.")
            return
        before = len(homework_db[chat_id])
        homework_db[chat_id] = [hw for hw in homework_db[chat_id] if hw["id"] != hw_id]
        if len(homework_db[chat_id]) < before:
            bot.reply_to(message, f"✅ Задание №{hw_id} удалено.")
        else:
            bot.reply_to(message, f"❌ Задание №{hw_id} не найдено.")
        return

    # === ПОКАЗАТЬ СПИСОК ДЗ ===
    if text_lower == "дз":
        cleanup_homework(chat_id)
        if chat_id not in homework_db or not homework_db[chat_id]:
            bot.reply_to(message, "📭 Список домашних заданий пуст.")
            return
        lines = ["📚 **Домашние задания:**\n"]
        for hw in homework_db[chat_id]:
            lines.append(
                f"**№{hw['id']}** — {hw['text']}\n"
                f"   ⏳ Сдать до: **{hw['date']}**\n"
                f"   ✍️ Добавил: {hw['author']}\n"
            )
        bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown")
        return

# ================= ЗАПУСК =================
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()