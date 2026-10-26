import telebot
from telebot import types
from datetime import datetime, timedelta

# ==================== НАСТРОЙКИ БОТА ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"
BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище ДЗ: {chat_id: [ {"id": int, "text": str, "date": "ДД.ММ.ГГГГ", "author": str} ]}
homework_db = {}
user_states = {}  # {chat_id: {"state": "...", "data": {}}}
next_hw_id = 1

def get_user_name(user):
    return f"@{user.username}" if user.username else user.first_name

def parse_date(date_str):
    """Парсит дату вида ДД.ММ.ГГГГ и возвращает datetime или None."""
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y")
    except ValueError:
        return None

def cleanup_homework(chat_id):
    """Удаляет задания, у которых дата сдачи уже прошла (раньше сегодняшнего дня)."""
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
            "• `+дз` — добавить домашнее задание\n"
            "• `-дз` — удалить домашнее задание по номеру\n"
            "• `дз` — показать список домашних заданий\n"
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
            "• `+дз`, `-дз`, `дз`\n"
            "• `команды`"
        )

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def handle_group_commands(message):
    if not message.text:
        return
    chat_id = message.chat.id
    text = message.text.strip()
    text_lower = text.lower()
    user_name = get_user_name(message.from_user)

    # === Список команд ===
    if text_lower == "команды":
        commands_list = (
            "📋 **Список команд:**\n\n"
            "📌 **Утилиты:**\n"
            "• `закреп` — закрепить сообщение (в ответ на сообщение)\n"
            "• `учителя` — список преподавателей\n"
            "• `расписание` — расписание занятий\n"
            "• `команды` — этот список\n\n"
            "📚 **Домашние задания:**\n"
            "• `+дз` — добавить задание\n"
            "• `-дз` — удалить задание по номеру\n"
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

    # === ДОБАВИТЬ ДЗ (+дз) ===
    if text_lower == "+дз":
        user_states[chat_id] = {"state": "hw_awaiting_task", "data": {"author": user_name}}
        bot.reply_to(message, "📚 **Напишите, что задано** (например: «Упражнения 53, 54»):")
        return

    # === УДАЛИТЬ ДЗ (-дз) ===
    if text_lower.startswith("-дз"):
        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: `-дз <номер>` (номер смотрите в `дз`)")
            return
        try:
            hw_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Номер должен быть числом.")
            return
        if chat_id not in homework_db:
            bot.reply_to(message, "❌ Список домашних заданий пуст.")
            return
        before = len(homework_db[chat_id])
        homework_db[chat_id] = [hw for hw in homework_db[chat_id] if hw["id"] != hw_id]
        if len(homework_db[chat_id]) < before:
            bot.reply_to(message, f"✅ Задание №{hw_id} удалено.")
        else:
            bot.reply_to(message, f"❌ Задание с номером {hw_id} не найдено.")
        return

    # === ПОКАЗАТЬ СПИСОК ДЗ (дз) ===
    if text_lower == "дз":
        cleanup_homework(chat_id)  # удаляем просроченные
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

# ================= ОБРАБОТЧИК ОТВЕТОВ (+дз) =================

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'] and msg.chat.id in user_states)
def process_hw_steps(message):
    global next_hw_id
    chat_id = message.chat.id
    state_data = user_states.get(chat_id)
    if not state_data:
        return

    state = state_data.get("state")
    data = state_data.get("data", {})

    if state == "hw_awaiting_task":
        data["text"] = message.text.strip()
        state_data["state"] = "hw_awaiting_date"
        state_data["data"] = data
        user_states[chat_id] = state_data
        bot.reply_to(message, "📅 **До какого числа сдать?** Напишите дату в формате `ДД.ММ.ГГГГ` (например: 01.11.2026):")
        return

    if state == "hw_awaiting_date":
        date_str = message.text.strip()
        parsed = parse_date(date_str)
        if not parsed:
            bot.reply_to(message, "❌ Неверный формат даты. Напишите в формате `ДД.ММ.ГГГГ` (например: 01.11.2026):")
            return
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if parsed < today:
            bot.reply_to(message, "❌ Дата уже прошла. Укажите будущую дату в формате `ДД.ММ.ГГГГ`:")
            return

        data["date"] = date_str
        if chat_id not in homework_db:
            homework_db[chat_id] = []
        hw_id = next_hw_id
        next_hw_id += 1
        homework_db[chat_id].append({
            "id": hw_id,
            "text": data["text"],
            "date": data["date"],
            "author": data.get("author", get_user_name(message.from_user))
        })
        del user_states[chat_id]
        bot.reply_to(
            message,
            f"✅ **Задание добавлено!**\n\n"
            f"📚 {data['text']}\n"
            f"⏳ Сдать до: **{data['date']}**\n"
            f"🔢 Номер задания: **№{hw_id}**\n\n"
            f"Посмотреть все задания: `дз`",
            parse_mode="Markdown"
        )
        return

# ================= ЗАПУСК =================
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()