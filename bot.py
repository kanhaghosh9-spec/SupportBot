import telebot
import os
from pathlib import Path
import time

API_KEY = os.getenv("BOT_TOKEN")

ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
bot = telebot.TeleBot(API_KEY)

FILES = {
    'bot_status.txt': 'on',
    'reply_mode.txt': '',
    'users.txt': '',
    'blocked_users.txt': ''
}

for file, default in FILES.items():
    Path(file).touch(exist_ok=True)
    if not Path(file).read_text().strip():
        Path(file).write_text(default)

def read_text(file):
    return Path(file).read_text().strip()

def write_text(file, content):
    Path(file).write_text(content)

def append_text(file, content):
    with Path(file).open('a') as f:
        f.write(f'{content}\n')

def get_lines(file):
    return set(Path(file).read_text().splitlines()) - {''}

@bot.message_handler(content_types=['text'])
def handle_message(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    text = message.text
    name = message.from_user.first_name or ''
    username = message.from_user.username or 'No Username'

    bot_status = read_text('bot_status.txt')
    reply_mode = read_text('reply_mode.txt')
    blocked = get_lines('blocked_users.txt')

    if user_id in blocked and message.from_user.id not in ADMIN_IDS:
        bot.send_message(chat_id, "⛔️ You are blocked by the admin and cannot use the bot. Made by @MasterShayan")
        return

    if message.from_user.id in ADMIN_IDS:
        if text == '/admin':
            kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row('📬 Broadcast Message', f'⚡️ Bot Status: {"On ✅" if bot_status == "on" else "Off ❌"}')
            kb.row('Bot Stats 📊', 'User Management 🗄️')
            bot.send_message(chat_id, f"🔰 Admin Panel\n\n📊 Current Status: {'On ✅' if bot_status == 'on' else 'Off ❌'} Made by @MasterShayan", reply_markup=kb)
            return

        if text == 'User Management 🗄️':
            users, blocked = get_lines('users.txt'), get_lines('blocked_users.txt')
            kb = telebot.types.InlineKeyboardMarkup()
            for uid in users:
                status = '🚫' if uid in blocked else '✅'
                kb.add(telebot.types.InlineKeyboardButton(f"{status} User: {uid}", callback_data=f"user_manage_{uid}"))
            bot.send_message(chat_id, "👥 Bot Users List:\n\n✅ = Active\n🚫 = Blocked\n\nClick on a user to manage them. Made by @MasterShayan" if users else "❌ No users found! Made by @MasterShayan", reply_markup=kb if users else None)
            return

        if text.startswith('⚡️ Bot Status:'):
            new_status = 'off' if bot_status == 'on' else 'on'
            write_text('bot_status.txt', new_status)
            kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row('📬 Broadcast Message', f'⚡️ Bot Status: {"On ✅" if new_status == "on" else "Off ❌"}')
            kb.row('Bot Stats 📊', 'User Management 🗄️')
            bot.send_message(chat_id, f"Bot status changed to {'On ✅' if new_status == 'on' else 'Off ❌'}. Made by @MasterShayan", reply_markup=kb)
            return

        if text == 'Bot Stats 📊':
            users, blocked = get_lines('users.txt'), get_lines('blocked_users.txt')
            bot.send_message(chat_id, f"📊 Bot Stats:\n\n👥 Total Users: {len(users)}\n🚫 Blocked Users: {len(blocked)} Made by @MasterShayan")
            return

        if text == '📬 Broadcast Message':
            write_text('reply_mode.txt', 'broadcast')
            bot.send_message(chat_id, '📝 Enter your message for broadcasting: Made by @MasterShayan')
            return

        if reply_mode == 'broadcast' and text != 'Broadcast Message':
            users, blocked = get_lines('users.txt'), get_lines('blocked_users.txt')
            success, fail = 0, 0
            for uid in users - blocked:
                try:
                    bot.send_message(uid, f"📢 Message from Admin:\n\n{text} Made by @MasterShayan")
                    success += 1
                except:
                    fail += 1
                time.sleep(0.05)
            write_text('reply_mode.txt', '')
            bot.send_message(chat_id, f"📬 Broadcast Result:\n\n✅ Success: {success}\n❌ Failed: {fail} Made by @MasterShayan")
            return

        if message.reply_to_message and message.reply_to_message.forward_from:
            uid = str(message.reply_to_message.forward_from.id)
            if uid not in blocked:
                bot.send_message(uid, f"📬 Reply from Support:\n\n{text} Made by @MasterShayan", reply_to_message_id=message.reply_to_message.message_id)
                bot.send_message(chat_id, "✅ Your reply was sent successfully. Made by @MasterShayan")
            else:
                bot.send_message(chat_id, "⚠️ This user is blocked, you cannot send them a message. Made by @MasterShayan")
            return

    if text == '/start':
        if bot_status == 'off' and message.from_user.id not in ADMIN_IDS:
            bot.send_message(chat_id, "⚠️ The bot is currently off. Please try again later. Made by @MasterShayan")
            return
        users = get_lines('users.txt')
        if user_id not in users:
            append_text('users.txt', user_id)
        bot.send_message(chat_id, f"👋 Hello {name}!\n\nWelcome to SupportBot.\n 💬 Send your message to reach support.\n/help Made by @MasterShayan")
        return

    if text == '/help':
        if bot_status == 'off' and message.from_user.id not in ADMIN_IDS:
            bot.send_message(chat_id, "⚠️ The bot is currently off. Please try again later. Made by @MasterShayan")
            return
        bot.send_message(chat_id, "💡 Bot Guide:\n\n📝 Just send a message to contact support.\n\n✅ Your message will be sent directly to admins and answered soon. Made by @MasterShayan")
        return

    if text and message.from_user.id not in ADMIN_IDS and bot_status == 'on' and text not in ['/start', '/help', '/admin']:
        for admin in ADMIN_IDS:
            forwarded = bot.forward_message(admin, chat_id, message.message_id)
            kb = telebot.types.InlineKeyboardMarkup()
            kb.add(
                telebot.types.InlineKeyboardButton('📝 Quick Reply', callback_data=f'reply_to_{user_id}'),
                telebot.types.InlineKeyboardButton('🚫 Block User', callback_data=f'block_{user_id}')
            )
            bot.send_message(admin, f"📨 User Info:\n\n👤 Name: {name}\n🆔 Username: @{username}\n📌 User ID: {user_id}\n\n💡 To reply:\n1️⃣ Reply to the message\n2️⃣ Use Quick Reply Made by @MasterShayan", reply_to_message_id=forwarded.message_id, reply_markup=kb)
        bot.send_message(chat_id, "✅ Your message was sent to support.\n\n⏳ Please wait for a response. Made by @MasterShayan", reply_to_message_id=message.message_id)
        return

    if reply_mode.isdigit() and text and text != 'Cancel Reply':
        uid = reply_mode
        if uid in blocked:
            bot.send_message(chat_id, "⚠️ This user is blocked, you cannot send them a message. Made by @MasterShayan")
        else:
            bot.send_message(uid, f"📬 Reply from Support:\n\n{text} Made by @MasterShayan")
            kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row('📬 Broadcast Message', f'⚡️ Bot Status: {"On ✅" if bot_status == "on" else "Off ❌"}')
            kb.row('Bot Stats 📊', 'User Management 🗄️')
            bot.send_message(chat_id, "✅ Your message was sent successfully. Made by @MasterShayan", reply_markup=kb)
        write_text('reply_mode.txt', '')
        return

    if text == 'Cancel Reply' and reply_mode:
        write_text('reply_mode.txt', '')
        kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row('📬 Broadcast Message', f'⚡️ Bot Status: {"On ✅" if bot_status == "on" else "Off ❌"}')
        kb.row('Bot Stats 📊', 'User Management 🗄️')
        bot.send_message(chat_id, "❌ Reply canceled. Made by @MasterShayan", reply_markup=kb)
        return

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    blocked = get_lines('blocked_users.txt')

    if data.startswith('user_manage_'):
        uid = data.replace('user_manage_', '')
        is_blocked = uid in blocked
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton('✅ Unblock User' if is_blocked else '🚫 Block User', callback_data=f"unblock_{uid}" if is_blocked else f"block_{uid}"))
        kb.add(telebot.types.InlineKeyboardButton('🔙 Back to List', callback_data='back_to_users_list'))
        bot.edit_message_text(f"👤 Manage User: {uid}\n\nCurrent Status: {'🚫 Blocked' if is_blocked else '✅ Active'} Made by @MasterShayan", chat_id, msg_id, reply_markup=kb)

    elif data.startswith('block_'):
        uid = data.replace('block_', '')
        if uid not in blocked:
            append_text('blocked_users.txt', uid)
            bot.send_message(uid, "⛔️ You are blocked by the admin and cannot use the bot. Made by @MasterShayan")
            kb = telebot.types.InlineKeyboardMarkup()
            kb.add(telebot.types.InlineKeyboardButton('✅ Unblock User', callback_data=f"unblock_{uid}"))
            kb.add(telebot.types.InlineKeyboardButton('🔙 Back to List', callback_data='back_to_users_list'))
            bot.edit_message_text(f"✅ User {uid} blocked successfully.\n\nCurrent Status: 🚫 Blocked Made by @MasterShayan", chat_id, msg_id, reply_markup=kb)

    elif data.startswith('unblock_'):
        uid = data.replace('unblock_', '')
        if uid in blocked:
            blocked.remove(uid)
            write_text('blocked_users.txt', '\n'.join(blocked))
            bot.send_message(uid, "✅ Your access restriction to the bot has been lifted. Made by @MasterShayan")
            kb = telebot.types.InlineKeyboardMarkup()
            kb.add(telebot.types.InlineKeyboardButton('🚫 Block User', callback_data=f"block_{uid}"))
            kb.add(telebot.types.InlineKeyboardButton('🔙 Back to List', callback_data='back_to_users_list'))
            bot.edit_message_text(f"✅ User {uid} unblocked successfully.\n\nCurrent Status: ✅ Active Made by @MasterShayan", chat_id, msg_id, reply_markup=kb)

    elif data == 'back_to_users_list':
        users, blocked = get_lines('users.txt'), get_lines('blocked_users.txt')
        kb = telebot.types.InlineKeyboardMarkup()
        for uid in users:
            status = '🚫' if uid in blocked else '✅'
            kb.add(telebot.types.InlineKeyboardButton(f"{status} User: {uid}", callback_data=f"user_manage_{uid}"))
        bot.edit_message_text("👥 Bot Users List:\n\n✅ = Active\n🚫 = Blocked\n\nClick on a user to manage them. Made by @MasterShayan", chat_id, msg_id, reply_markup=kb)

    elif data.startswith('reply_to_'):
        uid = data.replace('reply_to_', '')
        if uid in blocked:
            bot.answer_callback_query(call.id, "⚠️ This user is blocked, you cannot send them a message. Made by @MasterShayan", show_alert=True)
        else:
            write_text('reply_mode.txt', uid)
            kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(telebot.types.KeyboardButton('Cancel Reply'))
            bot.send_message(chat_id, "📝 Please enter your message to send to the user: Made by @MasterShayan", reply_markup=kb)

if __name__ == '__main__':
    bot.polling(none_stop=True)
