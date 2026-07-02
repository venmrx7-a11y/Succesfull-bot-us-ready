import os
import sys
import random
import asyncio
import json
import threading
import re
from datetime import datetime
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

print("=" * 60)
print("🔥 KALYUG ESCROW DEAL BOT STARTING...")
print("=" * 60)

# ============ CONFIG ============
BOT_TOKEN = "8998803283:AAE4ugFUIoRYm1CSMu7f1OaqB0yrPDik548"
OWNER_ID = 7977493987
GROUP_ID = -1003920615096
JOIN_GROUP_LINK = "https://t.me/+5Z_XCSm-BzE4YTJl"

# ============ FILES ============
ADMINS_FILE = "admins.json"
DEALS_FILE = "deals.json"
SETTINGS_FILE = "settings.json"
SPEECH_FILE = "speech.json"

# ============ FLASK ============
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

# ============ EMOJIS ============
def get_random_emoji():
    emojis = ["🔥", "✅", "💰", "👑", "⭐", "✨", "🎲", "🏆", "🎁", "🔒", "🔓", "📱", "ℹ️", "📋"]
    return random.choice(emojis)

def format_with_emojis(text):
    lines = text.split('\n')
    formatted = []
    for line in lines:
        if line.strip():
            formatted.append(f"{get_random_emoji()} {line} {get_random_emoji()}")
        else:
            formatted.append(line)
    return '\n'.join(formatted)

# ============ DATABASE ============
def load_json(filename, default=None):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default or {}
    return default or {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# ============ ADMINS ============
def load_admins():
    admins = load_json(ADMINS_FILE, [])
    if OWNER_ID not in admins:
        admins.append(OWNER_ID)
        save_json(ADMINS_FILE, admins)
    return admins

def is_admin(user_id):
    return user_id in load_admins()

def is_owner(user_id):
    return user_id == OWNER_ID

def add_admin(user_id):
    admins = load_admins()
    if user_id not in admins:
        admins.append(user_id)
        save_json(ADMINS_FILE, admins)
        return True
    return False

# ============ DEALS ============
def load_deals():
    return load_json(DEALS_FILE, {})

def save_deals(deals):
    save_json(DEALS_FILE, deals)

def create_deal(deal_data):
    deals = load_deals()
    deal_id = f"DEAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    deals[deal_id] = {
        **deal_data,
        "date": str(datetime.now()),
        "status": "ACTIVE"
    }
    save_deals(deals)
    return deal_id

def get_deal(deal_id):
    deals = load_deals()
    return deals.get(deal_id, None)

# ============ SETTINGS ============
def load_settings():
    return load_json(SETTINGS_FILE, {
        "lock_time": "19:30",
        "unlock_time": "07:00",
        "group_locked": False
    })

def save_settings(settings):
    save_json(SETTINGS_FILE, settings)

# ============ SPEECH ============
def load_speeches():
    return load_json(SPEECH_FILE, {
        "morning": "🌅 Good Morning! New day, new deals!",
        "night": "🌙 Good Night! Group is locked."
    })

def save_speeches(speeches):
    save_json(SPEECH_FILE, speeches)

# ============ DEAL FORM ============
def parse_deal_form(text):
    patterns = {
        'amount': r'𝘿𝙀𝘼𝙇 𝘼𝙈𝙊𝙐𝙉𝙏\s*[:=]\s*([^\n]+)',
        'buyer': r'𝘽𝙐𝙔𝙀𝙍𝙎?\s*[:=]\s*@([^\s\n]+)',
        'seller': r'𝙎𝙀𝙇𝙇𝙀𝙍\s*[:=]\s*@([^\s\n]+)',
        'deal_detail': r'𝘿𝙀𝘼𝙇 𝘿𝙀𝙏𝘼𝙄𝙇\s*[:=]\s*([^\n]+)',
        'rls_upi': r'𝙍𝙇𝙎 𝙐𝙋𝙄\s*[:=]\s*([^\n]+)',
        'condition': r'𝘾𝙊𝙉𝘿𝙄𝙏𝙄𝙊𝙉\s*[:=]\s*([^\n]+)',
        'escrow_till': r'𝙀𝙎𝘾𝙍𝙊𝙒 𝙏𝙄𝙇𝙇\s*[:=]\s*([^\n]+)'
    }
    
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        result[key] = match.group(1).strip() if match else "N/A"
    return result

def is_valid_deal_form(text):
    has_buyer = re.search(r'𝘽𝙐𝙔𝙀𝙍𝙎?\s*[:=]\s*@', text, re.IGNORECASE)
    has_seller = re.search(r'𝙎𝙀𝙇𝙇𝙀𝙍\s*[:=]\s*@', text, re.IGNORECASE)
    has_amount = re.search(r'𝘿𝙀𝘼𝙇 𝘼𝙈𝙊𝙐𝙉𝙏\s*[:=]', text, re.IGNORECASE)
    return (has_buyer or has_seller) and has_amount

# ============ COMMANDS ============

async def start_command(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    try:
        await context.bot.get_chat_member(GROUP_ID, user_id)
    except:
        await update.message.reply_text(
            format_with_emojis(f"⚠️ JOIN GROUP FIRST!\n{JOIN_GROUP_LINK}")
        )
        return
    
    msg = f"""
🔥 KALYUG ESCROW DEAL BOT
━━━━━━━━━━━━━━━━━━
👋 Hey @{username}!

🔹 Commands:
/start - Start bot
/help - Help menu
/time - Bot time
/lock - Lock group
/unlock - Unlock group
/admins - List admins
/broadcast - Send broadcast
/send - Send to group
/dice - Play dice
/check DEAL_ID - Check deal

👑 Owner Commands:
/approve USER_ID - Add admin
/removeadmin USER_ID - Remove admin
/setlock HH:MM - Set lock time
/setunlock HH:MM - Set unlock time
/setmorning SPEECH - Set morning speech
/setnight SPEECH - Set night speech

━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg))

async def help_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    msg = """
❓ HELP MENU
━━━━━━━━━━━━━━━━━━

User Commands:
/start - Start bot
/help - This menu
/time - Bot time

Admin Commands:
/lock - Lock group
/unlock - Unlock group
/admins - List admins
/broadcast - Send broadcast
/send - Send to group
/dice - Play dice
/check DEAL_ID - Check deal
/setlock HH:MM - Set lock time
/setunlock HH:MM - Set unlock time
/setmorning SPEECH - Set morning speech
/setnight SPEECH - Set night speech

Owner Commands:
/approve USER_ID - Add admin
/removeadmin USER_ID - Remove admin

━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg))

async def time_command(update, context):
    now = datetime.now()
    settings = load_settings()
    
    msg = f"""
🕐 BOT TIME
━━━━━━━━━━━━━━━━━━
📅 Date: {now.strftime('%Y-%m-%d')}
🕐 Time: {now.strftime('%H:%M:%S')}
📌 Day: {now.strftime('%A')}

⏰ SCHEDULE
🔒 Lock Time: {settings.get('lock_time', '19:30')}
🔓 Unlock Time: {settings.get('unlock_time', '07:00')}
🔐 Status: {'🔒 LOCKED' if settings.get('group_locked', False) else '🔓 UNLOCKED'}
━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg))

async def lock_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    settings = load_settings()
    settings['group_locked'] = True
    save_settings(settings)
    
    speech = load_speeches().get('night', '🌙 Good Night! Group is locked.')
    await update.message.reply_text("🔒 Group locked!")
    await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(speech))

async def unlock_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    settings = load_settings()
    settings['group_locked'] = False
    save_settings(settings)
    
    speech = load_speeches().get('morning', '🌅 Good Morning! New day, new deals!')
    await update.message.reply_text("🔓 Group unlocked!")
    await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(speech))

async def set_lock_time(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /setlock HH:MM")
        return
    
    try:
        datetime.strptime(context.args[0], '%H:%M')
        settings = load_settings()
        settings['lock_time'] = context.args[0]
        save_settings(settings)
        await update.message.reply_text(f"✅ Lock time set to {context.args[0]}")
    except:
        await update.message.reply_text("❌ Invalid format! Use HH:MM")

async def set_unlock_time(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /setunlock HH:MM")
        return
    
    try:
        datetime.strptime(context.args[0], '%H:%M')
        settings = load_settings()
        settings['unlock_time'] = context.args[0]
        save_settings(settings)
        await update.message.reply_text(f"✅ Unlock time set to {context.args[0]}")
    except:
        await update.message.reply_text("❌ Invalid format! Use HH:MM")

async def set_morning_speech(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /setmorning your speech here")
        return
    
    speech = " ".join(context.args)
    speeches = load_speeches()
    speeches['morning'] = speech
    save_speeches(speeches)
    await update.message.reply_text("✅ Morning speech updated!")

async def set_night_speech(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /setnight your speech here")
        return
    
    speech = " ".join(context.args)
    speeches = load_speeches()
    speeches['night'] = speech
    save_speeches(speeches)
    await update.message.reply_text("✅ Night speech updated!")

async def broadcast_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /broadcast your message here")
        return
    
    msg = " ".join(context.args)
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=format_with_emojis(f"📢 BROADCAST\n━━━━━━━━━━━━━━━━━━\n{msg}\n━━━━━━━━━━━━━━━━━━")
    )
    await update.message.reply_text("✅ Broadcast sent!")

async def send_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        if msg.text:
            await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(msg.text))
        elif msg.photo:
            await context.bot.send_photo(chat_id=GROUP_ID, photo=msg.photo[-1].file_id)
        elif msg.animation:
            await context.bot.send_animation(chat_id=GROUP_ID, animation=msg.animation.file_id)
        else:
            await update.message.reply_text("❌ Unsupported media!")
            return
        await update.message.reply_text("✅ Sent to group!")
        return
    
    if context.args:
        await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(" ".join(context.args)))
        await update.message.reply_text("✅ Sent to group!")
        return
    
    await update.message.reply_text("📝 Reply to a message with /send")

async def dice_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    result = random.randint(1, 6)
    win = result >= 4
    
    msg = f"""
🎲 DICE GAME
━━━━━━━━━━━━━━━━━━
🎯 Result: {result}
{'🎉 YOU WIN!' if win else '😢 YOU LOSE!'}
━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg))

async def check_deal(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /check DEAL_ID")
        return
    
    deal = get_deal(context.args[0])
    if not deal:
        await update.message.reply_text(f"❌ Deal '{context.args[0]}' not found!")
        return
    
    msg = f"""
📋 DEAL DETAILS
━━━━━━━━━━━━━━━━━━
📋 Deal ID: {context.args[0]}
━━━━━━━━━━━━━━━━━━
💰 Amount: {deal.get('amount', 'N/A')}
👤 Buyer: @{deal.get('buyer', 'N/A')}
👤 Seller: @{deal.get('seller', 'N/A')}
📝 Detail: {deal.get('deal_detail', 'N/A')}
💳 UPI: {deal.get('rls_upi', 'N/A')}
📌 Condition: {deal.get('condition', 'N/A')}
⏰ Escrow Till: {deal.get('escrow_till', 'N/A')}
━━━━━━━━━━━━━━━━━━
📌 Status: {deal.get('status', 'UNKNOWN')}
📅 Created: {deal.get('date', 'N/A')}
━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg))

async def approve_admin(update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /approve USER_ID")
        return
    
    try:
        user_id = int(context.args[0])
        if add_admin(user_id):
            await update.message.reply_text(f"✅ User {user_id} is now an admin!")
        else:
            await update.message.reply_text(f"⚠️ User {user_id} is already an admin!")
    except:
        await update.message.reply_text("❌ Invalid user ID!")

async def remove_admin(update, context):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: /removeadmin USER_ID")
        return
    
    try:
        user_id = int(context.args[0])
        admins = load_admins()
        if user_id in admins and user_id != OWNER_ID:
            admins.remove(user_id)
            save_json(ADMINS_FILE, admins)
            await update.message.reply_text(f"✅ User {user_id} removed from admins!")
        else:
            await update.message.reply_text(f"⚠️ User {user_id} is not an admin or is owner!")
    except:
        await update.message.reply_text("❌ Invalid user ID!")

async def list_admins(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    admins = load_admins()
    msg = "👑 ADMINS LIST\n━━━━━━━━━━━━━━━━━━\n\n"
    for admin_id in admins:
        msg += f"👑 {admin_id} (Owner)\n" if admin_id == OWNER_ID else f"⚡ {admin_id}\n"
    msg += "━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(format_with_emojis(msg))

async def handle_deal_form(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    
    if not is_valid_deal_form(text):
        return
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to create deals!")
        return
    
    deal_data = parse_deal_form(text)
    
    if deal_data['buyer'] == "N/A" and deal_data['seller'] == "N/A":
        await update.message.reply_text("❌ Please mention buyer or seller with @username!")
        return
    
    deal_id = create_deal(deal_data)
    
    msg = f"""
🔥 NEW DEAL CREATED!
━━━━━━━━━━━━━━━━━━
📋 Deal ID: {deal_id}
━━━━━━━━━━━━━━━━━━
💰 Amount: {deal_data['amount']}
👤 Buyer: @{deal_data['buyer']}
👤 Seller: @{deal_data['seller']}
📝 Detail: {deal_data['deal_detail']}
💳 UPI: {deal_data['rls_upi']}
📌 Condition: {deal_data['condition']}
⏰ Escrow Till: {deal_data['escrow_till']}
━━━━━━━━━━━━━━━━━━
📌 Status: ✅ ACTIVE
━━━━━━━━━━━━━━━━━━
    """
    
    await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(msg))
    
    for admin_id in load_admins():
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📨 New Deal: {deal_id}\nBuyer: @{deal_data['buyer']}\nSeller: @{deal_data['seller']}"
            )
        except:
            pass
    
    await update.message.reply_text(f"✅ Deal created! ID: {deal_id}")

# ============ AUTO LOCK ============
async def auto_lock_unlock(context):
    settings = load_settings()
    now = datetime.now().strftime('%H:%M')
    
    if now == settings.get('lock_time', '19:30') and not settings.get('group_locked', False):
        settings['group_locked'] = True
        save_settings(settings)
        speech = load_speeches().get('night', '🌙 Good Night! Group is locked.')
        await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(speech))
    
    elif now == settings.get('unlock_time', '07:00') and settings.get('group_locked', False):
        settings['group_locked'] = False
        save_settings(settings)
        speech = load_speeches().get('morning', '🌅 Good Morning! New day, new deals!')
        await context.bot.send_message(chat_id=GROUP_ID, text=format_with_emojis(speech))

# ============ MAIN ============
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("lock", lock_command))
    application.add_handler(CommandHandler("unlock", unlock_command))
    application.add_handler(CommandHandler("setlock", set_lock_time))
    application.add_handler(CommandHandler("setunlock", set_unlock_time))
    application.add_handler(CommandHandler("setmorning", set_morning_speech))
    application.add_handler(CommandHandler("setnight", set_night_speech))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("send", send_command))
    application.add_handler(CommandHandler("dice", dice_command))
    application.add_handler(CommandHandler("check", check_deal))
    application.add_handler(CommandHandler("approve", approve_admin))
    application.add_handler(CommandHandler("removeadmin", remove_admin))
    application.add_handler(CommandHandler("admins", list_admins))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deal_form))
    
    job_queue = application.job_queue
    job_queue.run_repeating(auto_lock_unlock, interval=60, first=10)
    
    print("=" * 60)
    print("🔥 BOT STARTED SUCCESSFULLY!")
    print(f"👑 Owner: {OWNER_ID}")
    print("=" * 60)
    
    application.run_polling()

if __name__ == "__main__":
    main()
