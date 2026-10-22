import telebot
from telebot import types
import random
import time

# ==================== НАСТРОЙКИ БОТА ====================
TOKEN_PART1 = "8839559401:"
TOKEN_PART2 = "AAEAt4mP_UBPOPSj7VAk6e6P28r8bjWXkik"
BOT_TOKEN = TOKEN_PART1 + TOKEN_PART2
SUPER_ADMIN_USERNAME = "lytixx"
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

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
LATE_WORDS = ["опоздал", "опоздала", "опоздание", "проспал", "проспала", "задержался", "задержалась"]

SYSTEM_COMMANDS = {"команды", "учителя", "стата", "топ", "профиль", "закреп", "баланс", "перевести", "магазин", "купить", "рулетка", "инвентарь", "+монеты", "баланс-админ"}

# ================= ЭКОНОМИКА =================
balances = {}
inventory = {}

SHOP_ITEMS = {
    "котик": {"price": 50, "emoji": "🐱", "desc": "Милый котик", "type": "pet"},
    "пёсик": {"price": 50, "emoji": "🐶", "desc": "Верный пёсик", "type": "pet"},
    "дракон": {"price": 150, "emoji": "🐉", "desc": "Огнедышащий дракон", "type": "pet"},
    "единорог": {"price": 200, "emoji": "🦄", "desc": "Волшебный единорог", "type": "pet"},
    "феникс": {"price": 300, "emoji": "🔥", "desc": "Птица-феникс", "type": "pet"},
    "пингвин": {"price": 70, "emoji": "🐧", "desc": "Деловой пингвин", "type": "pet"},
    "робот": {"price": 250, "emoji": "🤖", "desc": "Робот-помощник", "type": "pet"},
    "призрак": {"price": 120, "emoji": "👻", "desc": "Дружелюбный призрак", "type": "pet"},
    "лада": {"price": 1000, "emoji": "🚗", "desc": "Лада Веста", "type": "car"},
    "мерседес": {"price": 5000, "emoji": "🚘", "desc": "Mercedes-Benz", "type": "car"},
    "ламборгини": {"price": 15000, "emoji": "🏎️", "desc": "Lamborghini", "type": "car"},
    "бугатти": {"price": 30000, "emoji": "🚀", "desc": "Bugatti Chiron", "type": "car"},
    "квартира": {"price": 2000, "emoji": "🏢", "desc": "Уютная квартира", "type": "house"},
    "коттедж": {"price": 10000, "emoji": "🏡", "desc": "Загородный коттедж", "type": "house"},
    "особняк": {"price": 50000, "emoji": "🏰", "desc": "Роскошный особняк", "type": "house"},
}

def get_user_name(user):
    return f"@{user.username}" if user.username else user.first_name

def get_user_rank(count):
    if count >= 1000: return "👑 Легенда чата"
    elif count >= 500: return "🔥 Мега-активист"
    elif count >= 100: return "⭐ Активист"
    elif count >= 50: return "💬 Болтун"
    elif count >= 10: return "👋 Новичок"
    else: return "🌱 Гость"

def get_balance(chat_id, user_id):
    if chat_id not in balances: balances[chat_id] = {}
    if user_id not in balances[chat_id]: balances[chat_id][user_id] = 0
    return balances[chat_id][user_id]

def add_coins(chat_id, user_id, amount):
    if chat_id not in balances: balances[chat_id] = {}
    if user_id not in balances[chat_id]: balances[chat_id][user_id] = 0
    balances[chat_id][user_id] += amount

def format_shop_items(item_type):
    text = ""
    for name, item in SHOP_ITEMS.items():
        if item["type"] == item_type:
            text += f"{item['emoji']} **{name.capitalize()}** — {item['price']} 🪙 ({item['desc']})\n"
    return text

# ================= АДМИНКА В ЛС =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private': return
    username = message.from_user.username
    if username and username.lower() in admins:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Назначить админа", "🎭 Добавить РП-команду")
        markup.row("💰 Выдать монеты")
        bot.send_message(message.chat.id, "Привет, Босс! Доступна админ-панель.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Привет! Добавь меня в группу.")

@bot.message_handler(func=lambda msg: msg.chat.type == 'private' and msg.from_user.username and msg.from_user.username.lower() in admins)
def handle_admin_buttons(message):
    if message.text == "➕ Назначить админа":
        bot.send_message(message.chat.id, "Введите username нового админа (без @):")
        user_states[message.chat.id] = "waiting_for_admin_username"
    elif message.text == "🎭 Добавить РП-команду":
        bot.send_message(message.chat.id, "Введите имя команды (например: `ударить`):")
        user_states[message.chat.id] = "waiting_for_rp_name"
    elif message.text == "💰 Выдать монеты":
        bot.send_message(message.chat.id, "Введите в формате: `<ID чата> <ID пользователя> <сумма>`\n\nПример: `-1001234567890 123456789 1000`")
        user_states[message.chat.id] = "waiting_for_coins_admin"

@bot.message_handler(func=lambda msg: msg.chat.type == 'private' and msg.chat.id in user_states)
def process_admin_input(message):
    state = user_states.get(message.chat.id)
    if state == "waiting_for_admin_username":
        new_admin = message.text.strip().replace("@", "").lower()
        admins.add(new_admin)
        bot.send_message(message.chat.id, f"✅ @{new_admin} назначен администратором!")
        del user_states[message.chat.id]
    elif state == "waiting_for_rp_name":
        cmd_name = message.text.strip().lower()
        if cmd_name in SYSTEM_COMMANDS:
            bot.send_message(message.chat.id, "❌ Это имя занято системной командой. Введите другое.")
            return
        user_states[message.chat.id] = f"waiting_for_rp_text:{cmd_name}"
        bot.send_message(message.chat.id, f"Введите текст ответа для `{cmd_name}`.\nТеги: `{{user1}}` и `{{user2}}`")
    elif state.startswith("waiting_for_rp_text:"):
        _, cmd_name = state.split(":", 1)
        rp_commands[cmd_name] = message.text.strip()
        bot.send_message(message.chat.id, f"✅ РП-команда `{cmd_name}` добавлена!")
        del user_states[message.chat.id]
    elif state == "waiting_for_coins_admin":
        parts = message.text.strip().split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ Формат: `<ID чата> <ID пользователя> <сумма>`")
            return
        try:
            chat_id = int(parts[0])
            target_user_id = int(parts[1])
            amount = int(parts[2])
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID и сумма должны быть числами.")
            return
        add_coins(chat_id, target_user_id, amount)
        bot.send_message(message.chat.id, f"✅ Пользователю `{target_user_id}` в чате `{chat_id}` выдано {amount} 🪙.")
        del user_states[message.chat.id]

# ================= ГЛАВНЫЙ ОБРАБОТЧИК ГРУППЫ =================
@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def group_messages_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = get_user_name(message.from_user)
    text = message.text.strip() if message.text else ""
    text_lower = text.lower()

    if chat_id not in stats: stats[chat_id] = {}
    if user_id not in stats[chat_id]:
        stats[chat_id][user_id] = {"name": user_name, "count": 0, "late": 0}
    stats[chat_id][user_id]["count"] += 1
    if any(w in text_lower for w in LATE_WORDS):
        stats[chat_id][user_id]["late"] += 1

    add_coins(chat_id, user_id, 1)

    # === АДМИНСКИЕ КОМАНДЫ ===
    if text_lower.startswith("+монеты "):
        if message.from_user.username and message.from_user.username.lower() == SUPER_ADMIN_USERNAME.lower():
            parts = text.split()
            if len(parts) < 3:
                bot.reply_to(message, "❌ Формат: `+монеты <сумма> <@username>`")
                return
            try:
                amount = int(parts[1])
            except ValueError:
                bot.reply_to(message, "❌ Сумма должна быть числом.")
                return
            target_username = parts[2].replace("@", "").lower()
            target_id = None
            target_name = None
            for uid, data in stats[chat_id].items():
                if data["name"].lower() == f"@{target_username}":
                    target_id = uid
                    target_name = data["name"]
                    break
            if target_id is None:
                bot.reply_to(message, "❌ Пользователь не найден в чате.")
                return
            add_coins(chat_id, target_id, amount)
            bot.reply_to(message, f"💰 {user_name} выдал **{amount}** 🪙 пользователю {target_name}!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ У вас нет прав на эту команду.")
        return

    # === АДМИНСКАЯ КОМАНДА БАЛАНСА (без минуса) ===
    if text_lower.startswith("баланс-админ"):
        if message.from_user.username and message.from_user.username.lower() == SUPER_ADMIN_USERNAME.lower():
            parts = text.split()
            if len(parts) == 1:
                target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
                target_id = target.id
                target_name = get_user_name(target)
                coins = get_balance(chat_id, target_id)
                bot.reply_to(message, f"💰 Баланс {target_name}: **{coins}** 🪙", parse_mode="Markdown")
                return
            elif parts[1].lower() == "все":
                if chat_id not in balances or not balances[chat_id]:
                    bot.reply_to(message, "❌ В чате пока нет данных о балансе.")
                    return
                sorted_balances = sorted(balances[chat_id].items(), key=lambda x: x[1], reverse=True)
                reply = "💰 **Балансы всех участников:**\n\n"
                for uid, coins in sorted_balances:
                    uname = stats[chat_id][uid]["name"] if uid in stats[chat_id] else f"ID {uid}"
                    reply += f"• {uname} — {coins} 🪙\n"
                bot.send_message(chat_id, reply, parse_mode="Markdown")
                return
            else:
                target_username = parts[1].replace("@", "").lower()
                target_id = None
                target_name = None
                for uid, data in stats[chat_id].items():
                    if data["name"].lower() == f"@{target_username}":
                        target_id = uid
                        target_name = data["name"]
                        break
                if target_id is None:
                    bot.reply_to(message, "❌ Пользователь не найден в чате.")
                    return
                coins = get_balance(chat_id, target_id)
                bot.reply_to(message, f"💰 Баланс {target_name}: **{coins}** 🪙", parse_mode="Markdown")
                return
        else:
            bot.reply_to(message, "❌ У вас нет прав на эту команду.")
        return

    # === ОБЩИЕ КОМАНДЫ ===
    if text_lower == "команды":
        commands_list = (
            "📋 **Команды:**\n\n"
            "💰 **Экономика:**\n"
            "• `баланс` — показать монеты\n"
            "• `перевести <сумма> <@username>` — перевести монеты\n"
            "• `магазин` — список товаров\n"
            "• `купить <название>` — купить товар\n"
            "• `инвентарь` — купленные товары\n"
            "• `рулетка` — казино с кнопками 🎰\n\n"
            "📊 **Статистика:**\n"
            "• `стата` / `топ` — топ активных\n"
            "• `профиль` — профиль (или в ответ)\n\n"
            "📌 **Утилиты:**\n"
            "• `закреп` — закрепить (в ответ)\n"
            "• `учителя` — список преподавателей\n"
            "• `команды` — этот список\n\n"
            "👑 **Для админа:**\n"
            "• `+монеты <сумма> <@username>` — выдать монеты\n"
            "• `баланс-админ [@username|все]` — посмотреть баланс\n\n"
            "🎭 **РП:**\n" + "\n".join([f"• `{cmd}`" for cmd in rp_commands])
        )
        bot.send_message(chat_id, commands_list, parse_mode="Markdown")
        return

    if text_lower == "учителя":
        teachers = (
            "🎓 **Преподаватели:**\n\n"
            "• Ибрагимов М.У. — физкультура\n"
            "• Сулько М.Г. — математика\n"
            "• Корбова М.А. — русский язык\n"
            "• Чумак В.А. — иностранный язык\n"
            "• Шляхов А.Б. — введение в проф. деятельность\n"
            "• Колеватова В.К. — информатика\n"
            "• Мавлютова Г.М. — физика\n"
            "• Золтан В.Н. — физкультура (плавание)\n"
            "• Гончаров А.А. — история; ОБЗР"
        )
        bot.send_message(chat_id, teachers, parse_mode="Markdown")
        return

    if text_lower == "закреп":
        if message.reply_to_message:
            try:
                bot.pin_chat_message(chat_id, message.reply_to_message.message_id)
                bot.reply_to(message, "📌 Закреплено!")
            except Exception:
                bot.reply_to(message, "❌ Нет прав.")
        else:
            bot.reply_to(message, "❌ Ответьте на сообщение.")
        return

    # === ЭКОНОМИКА ===
    if text_lower == "баланс":
        coins = get_balance(chat_id, user_id)
        bot.reply_to(message, f"💰 У {user_name} **{coins}** монет.", parse_mode="Markdown")
        return

    if text_lower == "магазин":
        shop_text = (
            "🛒 **Магазин:**\n\n"
            "🐾 **Персонажи:**\n" + format_shop_items("pet") +
            "\n🚗 **Машины:**\n" + format_shop_items("car") +
            "\n🏠 **Дома:**\n" + format_shop_items("house") +
            "\nКупить: `купить <название>`"
        )
        bot.send_message(chat_id, shop_text, parse_mode="Markdown")
        return

    if text_lower == "инвентарь":
        if chat_id in inventory and user_id in inventory[chat_id] and inventory[chat_id][user_id]:
            items = inventory[chat_id][user_id]
            text_inv = "🎒 **Твои покупки:**\n\n"
            for item_name in items:
                item = SHOP_ITEMS.get(item_name)
                if item:
                    text_inv += f"{item['emoji']} **{item_name.capitalize()}** — {item['desc']}\n"
            bot.reply_to(message, text_inv, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ У тебя пока ничего нет. Загляни в `магазин`!")
        return

    if text_lower.startswith("перевести "):
        parts = text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Формат: `перевести <сумма> <@username>`")
            return
        try:
            amount = int(parts[1])
        except ValueError:
            bot.reply_to(message, "❌ Сумма должна быть числом.")
            return
        target_username = parts[2].replace("@", "").lower()
        target_id = None
        target_name = None
        for uid, data in stats[chat_id].items():
            if data["name"].lower() == f"@{target_username}":
                target_id = uid
                target_name = data["name"]
                break
        if target_id is None:
            bot.reply_to(message, "❌ Пользователь не найден в чате.")
            return
        if target_id == user_id:
            bot.reply_to(message, "❌ Нельзя перевести самому себе.")
            return
        if get_balance(chat_id, user_id) < amount:
            bot.reply_to(message, f"❌ Недостаточно монет. У тебя {get_balance(chat_id, user_id)} 🪙.")
            return
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
            return
        add_coins(chat_id, user_id, -amount)
        add_coins(chat_id, target_id, amount)
        bot.reply_to(message, f"💸 {user_name} перевёл **{amount}** 🪙 пользователю {target_name}!", parse_mode="Markdown")
        return

    if text_lower.startswith("купить "):
        item_name = text_lower[7:].strip()
        if item_name not in SHOP_ITEMS:
            bot.reply_to(message, "❌ Такого товара нет в магазине. Смотри `магазин`.")
            return
        price = SHOP_ITEMS[item_name]["price"]
        if get_balance(chat_id, user_id) < price:
            bot.reply_to(message, f"❌ Недостаточно монет. Нужно {price} 🪙, у тебя {get_balance(chat_id, user_id)} 🪙.")
            return
        if chat_id not in inventory: inventory[chat_id] = {}
        if user_id not in inventory[chat_id]: inventory[chat_id][user_id] = []
        if item_name in inventory[chat_id][user_id]:
            bot.reply_to(message, "❌ У тебя уже есть этот предмет.")
            return
        add_coins(chat_id, user_id, -price)
        inventory[chat_id][user_id].append(item_name)
        bot.reply_to(message, f"✅ {user_name} купил {SHOP_ITEMS[item_name]['emoji']} **{item_name.capitalize()}** за {price} 🪙!", parse_mode="Markdown")
        return

    # ===== КАЗИНО С КНОПКАМИ =====
    if text_lower == "рулетка":
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn_x2 = types.InlineKeyboardButton("x2 (шанс 45%)", callback_data=f"bet|x2|{user_id}|100")
        btn_x3 = types.InlineKeyboardButton("x3 (шанс 15%)", callback_data=f"bet|x3|{user_id}|100")
        btn_x5 = types.InlineKeyboardButton("x5 (шанс 8%)", callback_data=f"bet|x5|{user_id}|100")
        markup.add(btn_x2, btn_x3, btn_x5)
        bot.reply_to(message, "🎰 **Выберите множитель и ставку (по умолчанию 100 🪙):**", reply_markup=markup, parse_mode="Markdown")
        return

    # === ПРОФИЛЬ / СТАТИСТИКА ===
    if text_lower in ["стата", "топ", "профиль"]:
        if chat_id not in stats or not stats[chat_id]:
            bot.send_message(chat_id, "📊 Нет статистики.")
            return
        if text_lower == "профиль" or message.reply_to_message:
            target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
            target_id = target.id
            target_name = get_user_name(target)
            if target_id in stats[chat_id]:
                c = stats[chat_id][target_id]["count"]
                l = stats[chat_id][target_id]["late"]
                r = get_user_rank(c)
                coins = get_balance(chat_id, target_id)
                inv_items = inventory.get(chat_id, {}).get(target_id, [])
                txt = (
                    f"👤 **Профиль:** {target_name}\n"
                    f"💬 **Сообщений:** {c}\n"
                    f"⏰ **Опозданий:** {l}\n"
                    f"🏅 **Ранг:** {r}\n"
                    f"💰 **Монет:** {coins} 🪙\n"
                )
                if inv_items:
                    txt += "🎒 **Покупки:**\n"
                    for item_name in inv_items:
                        item = SHOP_ITEMS.get(item_name)
                        if item:
                            txt += f"  {item['emoji']} {item_name.capitalize()}\n"
                txt += "🎖 **Награды:**\n"
                if c >= 10: txt += "• 🥉 Первые шаги\n"
                if c >= 100: txt += "• 🥈 Завсегдатай\n"
                if c >= 500: txt += "• 🥇 Ветеран чата\n"
                if c < 10: txt += "• Пока нет\n"
                bot.send_message(chat_id, txt, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Нет статистики.")
            return
        sorted_users = sorted(stats[chat_id].values(), key=lambda x: x['count'], reverse=True)[:10]
        reply = "📊 **Топ актива:**\n\n"
        for i, u in enumerate(sorted_users, 1):
            reply += f"{i}. {u['name']} — {u['count']} сообщ. {get_user_rank(u['count'])}\n"
        bot.send_message(chat_id, reply, parse_mode="Markdown")
        return

    # === РП-КОМАНДЫ ===
    if text_lower in rp_commands:
        if not message.reply_to_message:
            bot.reply_to(message, f"❌ `{text_lower}` — ответьте на сообщение.")
            return
        u1 = get_user_name(message.from_user)
        u2 = get_user_name(message.reply_to_message.from_user)
        bot.send_message(chat_id, rp_commands[text_lower].format(user1=u1, user2=u2))
        return

# ================= ОБРАБОТЧИК КНОПОК КАЗИНО =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("bet|"))
def handle_bet(call):
    data = call.data.split("|")
    multiplier_str = data[1]
    user_id = int(data[2])
    bet = int(data[3])
    
    chat_id = call.message.chat.id
    user_name = get_user_name(call.from_user)
    
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не ваша кнопка!")
        return
    
    if get_balance(chat_id, user_id) < bet:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет! У тебя {get_balance(chat_id, user_id)} 🪙.")
        return
    
    bot.answer_callback_query(call.id, f"🎰 Крутим {multiplier_str}...")
    
    multiplier = 2
    win_chance = 0.45
    jackpot_chance = 0.05
    if multiplier_str == "x3":
        multiplier = 3
        win_chance = 0.15
        jackpot_chance = 0.02
    elif multiplier_str == "x5":
        multiplier = 5
        win_chance = 0.08
        jackpot_chance = 0.01
    
    add_coins(chat_id, user_id, -bet)
    roll = random.random()
    balance_after = get_balance(chat_id, user_id)
    
    if roll < win_chance:
        win = bet * multiplier
        add_coins(chat_id, user_id, win)
        balance_after = get_balance(chat_id, user_id)
        new_text = (
            f"🎰 **Выигрыш!** {user_name} ставил {bet} на **{multiplier_str}** "
            f"и получил **{win}** 🪙!\n"
            f"💰 Баланс: {balance_after} 🪙"
        )
    elif roll < win_chance + jackpot_chance:
        win = bet * multiplier * 2
        add_coins(chat_id, user_id, win)
        balance_after = get_balance(chat_id, user_id)
        new_text = (
            f"💎 **ДЖЕКПОТ!** {user_name} ставил {bet} на **{multiplier_str}** "
            f"и сорвал **{win}** 🪙!\n"
            f"💰 Баланс: {balance_after} 🪙"
        )
    else:
        new_text = (
            f"😢 **Проигрыш.** {user_name} ставил {bet} на **{multiplier_str}** "
            f"и потерял монеты.\n"
            f"💰 Баланс: {balance_after} 🪙"
        )
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=new_text, parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, new_text, parse_mode="Markdown")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()