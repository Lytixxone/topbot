import sqlite3
import telebot
from telebot import types

# ==================== НАСТРОЙКИ БОТА ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"

BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
SUPER_ADMIN_USERNAME = "lytixx"  # Ваш юзернейм без символа @
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# ==================== РАБОТА С БАЗОЙ ДАННЫХ ====================
def init_db():
    """Создает таблицы в БД, если они еще не созданы, и добавляет стандартные команды"""
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    # Таблица администраторов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY
        )
    """)
    
    # Таблица статистики сообщений
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            chat_id INTEGER,
            user_id INTEGER,
            user_name TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    """)
    
    # Таблица РП-команд
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rp_commands (
            cmd_name TEXT PRIMARY KEY,
            cmd_text TEXT
        )
    """)
    
    # Добавляем супер-админа по умолчанию
    cursor.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", (SUPER_ADMIN_USERNAME.lower(),))
    
    # Добавляем базовые РП-команды, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM rp_commands")
    if cursor.fetchone()[0] == 0:
        default_rp = [
            ("обкашлить", "{user1} обкашлил вопросы с {user2} 🤝"),
            ("трахнуть", "{user1} трахнул {user2} 🔞"),
            ("обнять", "{user1} крепко обнял {user2} 🤗"),
            ("поцеловать", "{user1} нежно поцеловал {user2} 😘"),
            ("кусь", "{user1} сделал кусь {user2} 😼")
        ]
        cursor.executemany("INSERT INTO rp_commands (cmd_name, cmd_text) VALUES (?, ?)", default_rp)
        
    conn.commit()
    conn.close()

def is_admin(username):
    if not username:
        return False
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE username = ?", (username.lower(),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_admin(username):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", (username.lower(),))
    conn.commit()
    conn.close()

def add_rp_command(name, text):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO rp_commands (cmd_name, cmd_text) VALUES (?, ?)", (name.lower(), text))
    conn.commit()
    conn.close()

def get_rp_commands():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT cmd_name, cmd_text FROM rp_commands")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def increment_stats(chat_id, user_id, user_name):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    # Обновляем количество сообщений и имя юзера (на случай, если сменил ник)
    cursor.execute("""
        INSERT INTO stats (chat_id, user_id, user_name, count) 
        VALUES (?, ?, ?, 1)
        ON CONFLICT(chat_id, user_id) 
        DO UPDATE SET count = count + 1, user_name = excluded.user_name
    """, (chat_id, user_id, user_name))
    conn.commit()
    conn.close()

def get_top_users(chat_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_name, count FROM stats 
        WHERE chat_id = ? 
        ORDER BY count DESC LIMIT 10
    """, (chat_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Инициализируем БД перед запуском бота
init_db()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_user_name(user):
    if user.username:
        return f"@{user.username}"
    name = user.first_name
    for char in ['_', '*', '`', '[']:
        name = name.replace(char, f'\\{char}')
    return name

# ==================== АДМИНКА В ЛС ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
        
    username = message.from_user.username
    if is_admin(username):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Назначить админа", "🎭 Добавить РП-команду")
        bot.send_message(message.chat.id, "Привет, Босс! Доступна админ-панель.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Привет! Добавь меня в группу, чтобы я администрировал её.")

@bot.message_handler(func=lambda msg: msg.chat.type == 'private' and is_admin(msg.from_user.username))
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
    if not message.text:
        return

    if state == "waiting_for_admin_username":
        new_admin = message.text.strip().replace("@", "").lower()
        add_admin(new_admin)
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
        add_rp_command(cmd_name, cmd_text)
        bot.send_message(message.chat.id, f"✅ РП-команда `!{cmd_name}` успешно сохранена в базу данных!")
        del user_states[message.chat.id]

# ==================== ФУНКЦИОНАЛ ДЛЯ ГРУППЫ ====================

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'], content_types=['text', 'photo', 'video', 'document', 'sticker'])
def group_messages_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = get_user_name(message.from_user)
    
    raw_text = message.text or message.caption or ""
    text = raw_text.strip()

    # Запись активности в БД
    increment_stats(chat_id, user_id, user_name)

    # Команда !закреп
    if text.lower() == "!закреп":
        if message.reply_to_message:
            try:
                bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
                bot.reply_to(message, "📌 Сообщение успешно закреплено!")
            except Exception:
                bot.reply_to(message, "❌ Не удалось закрепить. Убедитесь, что у меня есть права администратора.")
        else:
            bot.reply_to(message, "❌ Эта команда должна быть ответом на другое сообщение.")
        return

    # Команда просмотра статистики
    if text.lower() in ["стата", "топ"]:
        top_users = get_top_users(chat_id)
        if not top_users:
            bot.send_message(chat_id, "📊 В этом чате ещё нет статистики актива.")
            return
        
        reply_text = "📊 **Топ актива группы:**\n\n"
        for index, (name, count) in enumerate(top_users, 1):
            reply_text += f"{index}. {name} — {count} сообщ.\n"
        bot.send_message(chat_id, reply_text, parse_mode="Markdown")
        return

    # Динамические РП-команды
    if text.startswith("!"):
        possible_cmd = text[1:].lower()
        commands_dict = get_rp_commands()
        
        if possible_cmd in commands_dict:
            if not message.reply_to_message:
                bot.reply_to(message, f"❌ Команду `!{possible_cmd}` нужно использовать в ответ на сообщение!")
                return
            user1 = get_user_name(message.from_user)
            user2 = get_user_name(message.reply_to_message.from_user)
            response = commands_dict[possible_cmd].format(user1=user1, user2=user2)
            bot.send_message(chat_id, response)

if __name__ == "__main__":
    print("Бот запущен с постоянной базой данных...")
    bot.infinity_polling()
