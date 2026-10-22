import telebot

# ==================== НАСТРОЙКИ БОТА ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"
BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.send_message(
            message.chat.id,
            "👋 Привет! Я бот для закрепа и списка учителей.\n\n"
            "📌 **Команды:**\n"
            "• `закреп` — закрепить сообщение (в ответ на сообщение)\n"
            "• `учителя` — список преподавателей\n"
            "• `команды` — этот список",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            message.chat.id,
            "👋 Я в чате! Используйте:\n"
            "• `закреп` (в ответ на сообщение)\n"
            "• `учителя`\n"
            "• `команды`"
        )

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def handle_group_commands(message):
    if not message.text:
        return
    text_lower = message.text.strip().lower()

    if text_lower == "команды":
        commands_list = (
            "📋 **Список команд:**\n\n"
            "📌 **Утилиты:**\n"
            "• `закреп` — закрепить сообщение (в ответ на сообщение)\n"
            "• `учителя` — список преподавателей\n"
            "• `команды` — этот список"
        )
        bot.send_message(message.chat.id, commands_list, parse_mode="Markdown")
        return

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
        bot.send_message(message.chat.id, teachers, parse_mode="Markdown")
        return

    if text_lower == "закреп":
        if message.reply_to_message:
            try:
                bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
                bot.reply_to(message, "📌 Сообщение успешно закреплено!")
            except Exception:
                bot.reply_to(message, "❌ Не удалось закрепить. Проверьте, что я администратор с правом закрепления сообщений.")
        else:
            bot.reply_to(message, "❌ Эта команда должна быть ответом на сообщение.")
        return

if __name__ == "__main__":
    print("Бот для закрепа и учителей запущен...")
    bot.infinity_polling()