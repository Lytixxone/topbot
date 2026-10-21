import telebot
from telebot import types

# ==================== НАСТРОЙКИ БОТА ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"

BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
SUPER_ADMIN_USERNAME = "lytixx"  # Ваш юзернейм без символа @
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

# База данных в оперативной памяти (сбрасывается при перезапуске)
admins = {SUPER_ADMIN_USERNAME.lower()}
stats = {}
rp_commands = {
    "обкашлить": "{user1} обкашлил вопросы с {user2} 🤝",
    "трахнуть": "{user1} трахнул {user2} 🔞",
    "обнять": "{user1} крепко обнял {user2} 🤗",
    "поцеловать": "{user1} нежно поцеловал {user2} 😘",
    "кусь": "{user1} сделал кусь {user2} 😼"
}
user_states = {}

def get_user_name(user):
    if user.username:
        return f"@{user.username}"
    return user.first_name

# ================= АДМИНКА В ЛС =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
        
    username = message.from_user.username
    if username and username.lower() in admins:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Назначить админа", "🎭 Добавить РП-команду")
        bot.send_message(message.chat.id, "Привет, Босс! Доступна админ-панель.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Привет! Добавь меня в группу, чтобы я администрировал её.")

@bot.message_handler(func=lambda msg: msg.chat.type == 'private' and msg.from_user.username and msg.from_user.username.lower() in admins)
def handle_admin_buttons(message):
    if message.text == "➕ Назначить админа":
        bot.send_message(message.chat.id, "Введите username нового админа (без @):")
        user_states[message.chat.id] = "waiting_for_admin_username"
    elif message.text == "🎭 Добавить РП-команду":
        bot.send_message(message.chat.id, "Введите имя команды (например: `ударить`):")
        user_states[message.chat.id] = "waiting_for_rp_name"

@bot.message_handler(func=lambda msg: msg.chat.type == 'private' and msg.chat.id in user_states)
def process_admin_input(message):
    state = user_states.get(message.chat.id)
    
    if state == "waiting_for_admin_username":
        new_admin = message.text.strip().replace("@", "").lower()
        admins.add(new_admin)
        bot.send_message(message.chat.id, f"✅ Пользователь @{new_admin} назначен администратором бота!")
        del user_states[message.chat.id]
        
    elif state == "waiting_for_rp_name":
        cmd_name = message.text.strip().lower().replace("!", "")
        user_states[message.chat.id] = f"waiting_for_rp_text:{cmd_name}"
        bot.send_message(message.chat.id, 
                         f"Теперь введите текст ответа для команды `!{cmd_name}`.\n\n"
                         "Используйте теги `{user1}` (кто делает) и `{user2}` (кого выбрали).\n"
                         "Пример: `{user1} дал леща {user2}`")
                         
    elif state.startswith("waiting_for_rp_text:"):
        _, cmd_name = state.split(":", 1)
        cmd_text = message.text.strip()
        rp_commands[cmd_name] = cmd_text
        bot.send_message(message.chat.id, f"✅ РП-команда `!{cmd_name}` успешно добавлена!")
        del user_states[message.chat.id]

# ================= ФУНКЦИОНАЛ ДЛЯ ГРУППЫ =================

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'], content_types=['text', 'photo', 'video', 'document', 'sticker'])
def group_messages_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = get_user_name(message.from_user)
    text = message.text.strip() if message.text else ""

    if chat_id not in stats:
        stats[chat_id] = {}
    if user_id not in stats[chat_id]:
        stats[chat_id][user_id] = {"name": user_name, "count": 0}
    stats[chat_id][user_id]["count"] += 1

    # Команда вывода списка преподавателей
    if text.lower() == "!учителя":
        teachers_list = (
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
        bot.send_message(chat_id, teachers_list, parse_mode="Markdown")
        return

    if text.lower() == "!закреп":
        if message.reply_to_message:
            try:
                bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
                bot.reply_to(message, "📌 Сообщение успешно закреплено!")
            except Exception:
                bot.reply_to(message, "❌ Не удалось закрепить. Проверьте мои права администратора.")
        else:
            bot.reply_to(message, "❌ Эта команда должна быть ответом на сообщение.")
        return

    if text.lower() in ["стата", "топ"]:
        if chat_id not in stats or not stats[chat_id]:
            bot.send_message(chat_id, "📊 В этом чате ещё нет статистики актива.")
            return
        sorted_users = sorted(stats[chat_id].values(), key=lambda x: x['count'], reverse=True)[:10]
        reply_text = "📊 **Топ актива группы:**\n\n"
        for index, user_data in enumerate(sorted_users, 1):
            reply_text += f"{index}. {user_data['name']} — {user_data['count']} сообщ.\n"
        bot.send_message(chat_id, reply_text, parse_mode="Markdown")
        return

    if text.startswith("!"):
        possible_cmd = text[1:].lower()
        if possible_cmd in rp_commands:
            if not message.reply_to_message:
                bot.reply_to(message, f"❌ Команду `!{possible_cmd}` нужно использовать в ответ на сообщение!")
                return
            user1 = get_user_name(message.from_user)
            user2 = get_user_name(message.reply_to_message.from_user)
            response = rp_commands[possible_cmd].format(user1=user1, user2=user2)
            bot.send_message(chat_id, response)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()