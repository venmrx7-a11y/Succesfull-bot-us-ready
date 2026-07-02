import os
import sys
import random
import asyncio
import json
import threading
import re
from datetime import datetime
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

print("=" * 60)
print("🔥 KALYUG ESCROW DEAL BOT STARTING...")
print(f"🐍 Python: {sys.version}")
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
GIFS_FILE = "gifs.json"
SPEECH_FILE = "speech.json"

# ============ FLASK ============
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return jsonify({"status": "running", "time": str(datetime.now())}), 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

# ============ PREMIUM EMOJIS ============
PREMIUM_EMOJIS = {
    "verified": {"id": "6246537187614005254", "fallback": "✅"},
    "fire": {"id": "4956222745814762495", "fallback": "🔥"},
    "heart": {"id": "5783157259152397008", "fallback": "❤️"},
    "crown": {"id": "5794422335599546668", "fallback": "👑"},
    "money": {"id": "6089104607328342288", "fallback": "💰"},
    "star": {"id": "6244496562752331516", "fallback": "⭐"},
    "sparkle": {"id": "6010338729640596556", "fallback": "✨"},
    "cool": {"id": "6032853480782172520", "fallback": "😎"},
    "dice": {"id": "5791970059597386804", "fallback": "🎲"},
    "trophy": {"id": "6010156854955480259", "fallback": "🏆"},
    "gift": {"id": "6010338729640596556", "fallback": "🎁"},
    "lock": {"id": "5465443379917629504", "fallback": "🔒"},
    "unlock": {"id": "5465443379917629504", "fallback": "🔓"},
    "warning": {"id": "6035355642829475999", "fallback": "⚠️"},
    "info": {"id": "6246537187614005254", "fallback": "ℹ️"},
    "copy": {"id": "6246537187614005254", "fallback": "📋"},
}

def get_random_emoji():
    names = list(PREMIUM_EMOJIS.keys())
    if names:
        name = random.choice(names)
        data = PREMIUM_EMOJIS[name]
        return f'<tg-emoji emoji-id="{data["id"]}">{data["fallback"]}</tg-emoji>'
    return ""

def format_with_emojis(text):
    lines = text.split('\n')
    formatted = []
    for line in lines:
        if line.strip():
            left = get_random_emoji()
            right = get_random_emoji()
            formatted.append(f"{left} {line} {right}")
        else:
            formatted.append(line)
    return '\n'.join(formatted)

def to_fancy(text):
    """Convert text to stylish fancy text"""
    fancy_map = {
        'A': '𝘼', 'B': '𝘽', 'C': '𝘾', 'D': '𝘿', 'E': '𝙀',
        'F': '𝙁', 'G': '𝙂', 'H': '𝙃', 'I': '𝙄', 'J': '𝙅',
        'K': '𝙆', 'L': '𝙇', 'M': '𝙈', 'N': '𝙉', 'O': '𝙊',
        'P': '𝙋', 'Q': '𝙌', 'R': '𝙍', 'S': '𝙎', 'T': '𝙏',
        'U': '𝙐', 'V': '𝙑', 'W': '𝙒', 'X': '𝙓', 'Y': '𝙔',
        'Z': '𝙕', 'a': '𝙖', 'b': '𝙗', 'c': '𝙘', 'd': '𝙙',
        'e': '𝙚', 'f': '𝙛', 'g': '𝙜', 'h': '𝙝', 'i': '𝙞',
        'j': '𝙟', 'k': '𝙠', 'l': '𝙡', 'm': '𝙢', 'n': '𝙣',
        'o': '𝙤', 'p': '𝙥', 'q': '𝙦', 'r': '𝙧', 's': '𝙨',
        't': '𝙩', 'u': '𝙪', 'v': '𝙫', 'w': '𝙬', 'x': '𝙭',
        'y': '𝙮', 'z': '𝙯', '0': '𝟎', '1': '𝟏', '2': '𝟐',
        '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕',
        '8': '𝟖', '9': '𝟗'
    }
    return ''.join(fancy_map.get(c, c) for c in text)

# ============ DATABASE FUNCTIONS ============
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

def save_admins(admins):
    save_json(ADMINS_FILE, admins)

def is_admin(user_id):
    admins = load_admins()
    return user_id in admins

def is_owner(user_id):
    return user_id == OWNER_ID

def add_admin(user_id):
    admins = load_admins()
    if user_id not in admins:
        admins.append(user_id)
        save_admins(admins)
        return True
    return False

def remove_admin(user_id):
    admins = load_admins()
    if user_id in admins and user_id != OWNER_ID:
        admins.remove(user_id)
        save_admins(admins)
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
        "group_locked": False,
        "morning_speech": "🌅 Good Morning! New day, new deals!",
        "night_speech": "🌙 Good Night! Group is locked. See you tomorrow!"
    })

def save_settings(settings):
    save_json(SETTINGS_FILE, settings)

# ============ GIFS ============
def load_gifs():
    return load_json(GIFS_FILE, {})

def save_gifs(gifs):
    save_json(GIFS_FILE, gifs)

def add_gif(name, file_id):
    gifs = load_gifs()
    gifs[name.lower()] = file_id
    save_gifs(gifs)
    return True

def get_gif(name):
    gifs = load_gifs()
    return gifs.get(name.lower(), None)

# ============ SPEECH ============
def load_speeches():
    return load_json(SPEECH_FILE, {
        "morning": "🌅 Good Morning! New day, new deals!",
        "night": "🌙 Good Night! Group is locked. See you tomorrow!"
    })

def save_speeches(speeches):
    save_json(SPEECH_FILE, speeches)

# ============ DEAL FORM DETECTION ============
def parse_deal_form(text):
    """Parse deal form from group message"""
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
        if match:
            result[key] = match.group(1).strip()
        else:
            result[key] = "N/A"
    
    return result

def is_valid_deal_form(text):
    """Check if text contains deal form with username"""
    # Must have buyer or seller with @username
    has_buyer = re.search(r'𝘽𝙐𝙔𝙀𝙍𝙎?\s*[:=]\s*@', text, re.IGNORECASE)
    has_seller = re.search(r'𝙎𝙀𝙇𝙇𝙀𝙍\s*[:=]\s*@', text, re.IGNORECASE)
    
    # Must have deal amount
    has_amount = re.search(r'𝘿𝙀𝘼𝙇 𝘼𝙈𝙊𝙐𝙉𝙏\s*[:=]', text, re.IGNORECASE)
    
    return (has_buyer or has_seller) and has_amount

# ============ DEAL FORM COMMAND ============
async def handle_deal_form(update, context):
    """Handle deal form submissions"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    text = update.message.text
    
    # Check if it's a deal form
    if not is_valid_deal_form(text):
        return
    
    # Check if user is admin
    if not is_admin(user_id):
        await update.message.reply_text(
            format_with_emojis("❌ You are not authorized to create deals!\nContact owner for admin access.")
        )
        return
    
    # Parse deal form
    deal_data = parse_deal_form(text)
    
    # Check if buyer or seller has username
    if deal_data['buyer'] == "N/A" and deal_data['seller'] == "N/A":
        await update.message.reply_text(
            format_with_emojis("❌ Please mention buyer or seller with @username!")
        )
        return
    
    # Create deal
    deal_id = create_deal(deal_data)
    
    # Format deal message with fancy text
    deal_msg = f"""
🔥 <b>𝙉𝙀𝙒 𝘿𝙀𝘼𝙇 𝘾𝙍𝙀𝘼𝙏𝙀𝘿!</b>
━━━━━━━━━━━━━━━━━━
📋 <b>𝙳𝙴𝙰𝙻 𝙸𝙳:</b> <code>{deal_id}</code> (Click to copy)
━━━━━━━━━━━━━━━━━━
💰 <b>𝘿𝙀𝘼𝙇 𝘼𝙈𝙊𝙐𝙉𝙏:</b> {to_fancy(deal_data['amount'])}
👤 <b>𝘽𝙐𝙔𝙀𝙍:</b> @{to_fancy(deal_data['buyer']) if deal_data['buyer'] != 'N/A' else 'N/A'}
👤 <b>𝙎𝙀𝙇𝙇𝙀𝙍:</b> @{to_fancy(deal_data['seller']) if deal_data['seller'] != 'N/A' else 'N/A'}
📝 <b>𝘿𝙀𝘼𝙇 𝘿𝙀𝙏𝘼𝙄𝙇:</b> {to_fancy(deal_data['deal_detail'])}
💳 <b>𝙍𝙇𝙎 𝙐𝙋𝙄:</b> {to_fancy(deal_data['rls_upi'])}
📌 <b>𝘾𝙊𝙉𝘿𝙄𝙏𝙄𝙊𝙉:</b> {to_fancy(deal_data['condition'])}
⏰ <b>𝙀𝙎𝘾𝙍𝙊𝙒 𝙏𝙄𝙇𝙇:</b> {to_fancy(deal_data['escrow_till'])}
━━━━━━━━━━━━━━━━━━
📌 <b>𝙎𝙏𝘼𝙏𝙐𝙎:</b> {to_fancy('✅ ACTIVE')}
━━━━━━━━━━━━━━━━━━
𝙀𝙎𝘾𝙍𝙊𝙒 𝙁𝙀𝙀𝙎 𝙄𝙎 𝙉𝙊𝙉 - 𝙍𝙀𝙁𝙐𝙉𝘿𝘼𝘽𝙇𝙀
𝙉𝙊 𝙈𝘼𝙏𝙏𝙀𝙍 𝙄𝙁 𝙏𝙃𝙀 𝘿𝙀𝘼𝙇 𝙂𝙀𝙏𝙎 𝘾𝘼𝙉𝘾𝙀𝙇𝙇𝙀𝘿.

𝙍𝙂 : @𝙆𝘼𝙇𝙔𝙐𝙂𝙀𝙎𝘾𝙍𝙊𝙒𝙎𝙀𝙍𝙑𝙄𝘾𝙀
━━━━━━━━━━━━━━━━━━
    """
    
    # Send to group
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=format_with_emojis(deal_msg),
        parse_mode="HTML"
    )
    
    # Send to all admins
    admins = load_admins()
    for admin_id in admins:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=format_with_emojis(f"""
📨 <b>𝙉𝙀𝙒 𝘿𝙀𝘼𝙇 𝘾𝙍𝙀𝘼𝙏𝙀𝘿!</b>
━━━━━━━━━━━━━━━━━━
📋 Deal ID: <code>{deal_id}</code>
👤 Buyer: @{deal_data['buyer']}
👤 Seller: @{deal_data['seller']}
💰 Amount: {deal_data['amount']}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━
Use /check {deal_id} to view deal
                """),
                parse_mode="HTML"
            )
        except:
            pass
    
    # Confirm to user
    await update.message.reply_text(
        format_with_emojis(f"✅ Deal created successfully!\n📋 Deal ID: <code>{deal_id}</code>"),
        parse_mode="HTML"
    )

# ============ CHECK DEAL COMMAND ============
async def check_deal(update, context):
    """Check deal details - /check DEAL_ID"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/check DEAL_ID`", parse_mode="Markdown")
        return
    
    deal_id = context.args[0]
    deal = get_deal(deal_id)
    
    if not deal:
        await update.message.reply_text(f"❌ Deal '{deal_id}' not found!")
        return
    
    msg = f"""
📋 <b>𝘿𝙀𝘼𝙇 𝘿𝙀𝙏𝘼𝙄𝙻𝙎</b>
━━━━━━━━━━━━━━━━━━
📋 <b>𝙳𝙴𝙰𝙻 𝙸𝙳:</b> <code>{deal_id}</code>
━━━━━━━━━━━━━━━━━━
💰 <b>𝘿𝙀𝘼𝙇 𝘼𝙈𝙊𝙐𝙉𝙏:</b> {to_fancy(deal.get('amount', 'N/A'))}
👤 <b>𝘽𝙐𝙔𝙀𝙍:</b> @{to_fancy(deal.get('buyer', 'N/A'))}
👤 <b>𝙎𝙀𝙇𝙇𝙀𝙍:</b> @{to_fancy(deal.get('seller', 'N/A'))}
📝 <b>𝘿𝙀𝘼𝙇 𝘿𝙀𝙏𝘼𝙄𝙇:</b> {to_fancy(deal.get('deal_detail', 'N/A'))}
💳 <b>𝙍𝙇𝙎 𝙐𝙋𝙄:</b> {to_fancy(deal.get('rls_upi', 'N/A'))}
📌 <b>𝘾𝙊𝙉𝘿𝙄𝙏𝙄𝙊𝙉:</b> {to_fancy(deal.get('condition', 'N/A'))}
⏰ <b>𝙀𝙎𝘾𝙍𝙊𝙒 𝙏𝙄𝙇𝙇:</b> {to_fancy(deal.get('escrow_till', 'N/A'))}
━━━━━━━━━━━━━━━━━━
📌 <b>𝙎𝙏𝘼𝙏𝙐𝙎:</b> {to_fancy(deal.get('status', 'UNKNOWN'))}
📅 <b>𝘾𝙍𝙀𝘼𝙏𝙀𝘿:</b> {deal.get('date', 'N/A')}
━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============ ADMIN COMMANDS ============
async def approve_admin(update, context):
    """Approve new admin - /approve USER_ID"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/approve USER_ID`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        if add_admin(user_id):
            await update.message.reply_text(f"✅ User {user_id} is now an admin!")
        else:
            await update.message.reply_text(f"⚠️ User {user_id} is already an admin!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def remove_admin(update, context):
    """Remove admin - /removeadmin USER_ID"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/removeadmin USER_ID`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        if remove_admin(user_id):
            await update.message.reply_text(f"✅ User {user_id} removed from admins!")
        else:
            await update.message.reply_text(f"⚠️ User {user_id} is not an admin or is owner!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def list_admins(update, context):
    """List all admins - /admins"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    admins = load_admins()
    msg = "👑 <b>ADMINS LIST</b>\n━━━━━━━━━━━━━━━━━━\n\n"
    for admin_id in admins:
        if admin_id == OWNER_ID:
            msg += f"👑 {admin_id} (Owner)\n"
        else:
            msg += f"⚡ {admin_id}\n"
    msg += "━━━━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============ LOCK/UNLOCK COMMANDS ============
async def lock_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    settings = load_settings()
    settings['group_locked'] = True
    save_settings(settings)
    
    speech = load_speeches().get('night', '🌙 Good Night! Group is locked.')
    
    await update.message.reply_text("🔒 Group locked!")
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=format_with_emojis(speech),
        parse_mode="HTML"
    )

async def unlock_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    settings = load_settings()
    settings['group_locked'] = False
    save_settings(settings)
    
    speech = load_speeches().get('morning', '🌅 Good Morning! New day, new deals!')
    
    await update.message.reply_text("🔓 Group unlocked!")
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=format_with_emojis(speech),
        parse_mode="HTML"
    )

async def set_lock_time(update, context):
    """Set lock time - /setlock HH:MM"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/setlock HH:MM`", parse_mode="Markdown")
        return
    
    time_str = context.args[0]
    try:
        datetime.strptime(time_str, '%H:%M')
        settings = load_settings()
        settings['lock_time'] = time_str
        save_settings(settings)
        await update.message.reply_text(f"✅ Lock time set to {time_str}")
    except ValueError:
        await update.message.reply_text("❌ Invalid format! Use HH:MM")

async def set_unlock_time(update, context):
    """Set unlock time - /setunlock HH:MM"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/setunlock HH:MM`", parse_mode="Markdown")
        return
    
    time_str = context.args[0]
    try:
        datetime.strptime(time_str, '%H:%M')
        settings = load_settings()
        settings['unlock_time'] = time_str
        save_settings(settings)
        await update.message.reply_text(f"✅ Unlock time set to {time_str}")
    except ValueError:
        await update.message.reply_text("❌ Invalid format! Use HH:MM")

# ============ SPEECH COMMANDS ============
async def set_morning_speech(update, context):
    """Set morning speech - /setmorning SPEECH"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/setmorning your speech here`", parse_mode="Markdown")
        return
    
    speech = " ".join(context.args)
    speeches = load_speeches()
    speeches['morning'] = speech
    save_speeches(speeches)
    await update.message.reply_text("✅ Morning speech updated!")

async def set_night_speech(update, context):
    """Set night speech - /setnight SPEECH"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/setnight your speech here`", parse_mode="Markdown")
        return
    
    speech = " ".join(context.args)
    speeches = load_speeches()
    speeches['night'] = speech
    save_speeches(speeches)
    await update.message.reply_text("✅ Night speech updated!")

# ============ BROADCAST COMMAND ============
async def broadcast_command(update, context):
    """Broadcast message - /broadcast TEXT"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("📝 Usage: `/broadcast your message here`", parse_mode="Markdown")
        return
    
    msg = " ".join(context.args)
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=format_with_emojis(f"""
📢 <b>𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏</b>
━━━━━━━━━━━━━━━━━━
{msg}
━━━━━━━━━━━━━━━━━━
        """),
        parse_mode="HTML"
    )
    await update.message.reply_text("✅ Broadcast sent!")

# ============ SEND COMMAND ============
async def send_command(update, context):
    """Send anything to group - /send"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    # If replying to a message
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        
        if msg.text:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=format_with_emojis(msg.text),
                parse_mode="HTML"
            )
        elif msg.photo:
            await context.bot.send_photo(
                chat_id=GROUP_ID,
                photo=msg.photo[-1].file_id,
                caption=format_with_emojis(msg.caption) if msg.caption else ""
            )
        elif msg.video:
            await context.bot.send_video(
                chat_id=GROUP_ID,
                video=msg.video.file_id,
                caption=format_with_emojis(msg.caption) if msg.caption else ""
            )
        elif msg.animation:
            await context.bot.send_animation(
                chat_id=GROUP_ID,
                animation=msg.animation.file_id,
                caption=format_with_emojis(msg.caption) if msg.caption else ""
            )
        elif msg.document:
            await context.bot.send_document(
                chat_id=GROUP_ID,
                document=msg.document.file_id,
                caption=format_with_emojis(msg.caption) if msg.caption else ""
            )
        else:
            await update.message.reply_text("❌ Unsupported media type!")
            return
        
        await update.message.reply_text("✅ Sent to group!")
        return
    
    # If text with /send command
    if context.args:
        text = " ".join(context.args)
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=format_with_emojis(text),
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ Sent to group!")
        return
    
    await update.message.reply_text("📝 Reply to a message with /send to forward it.")

# ============ DICE GAME ============
async def dice_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    result = random.randint(1, 6)
    win = result >= 4
    
    msg = f"""
🎲 <b>𝘿𝙄𝘾𝙀 𝙂𝘼𝙈𝙀</b>
━━━━━━━━━━━━━━━━━━
🎯 Result: <b>{result}</b>
{'🎉 YOU WIN!' if win else '😢 YOU LOSE!'}
━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============ DICE SETUP ============
async def dice_setup(update, context):
    """Setup dice - /dicesetup"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🎲 Send GIF", callback_data="dice_gif")],
        [InlineKeyboardButton("🎲 Send Emoji", callback_data="dice_emoji")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎲 <b>DICE SETUP</b>\n━━━━━━━━━━━━━━━━━━\n"
        "Click below to set dice GIF or Emoji",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ============ BUTTON CALLBACK ============
async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "dice_gif":
        await query.edit_message_text("📤 Send me a GIF to set as dice animation!")
        context.user_data['dice_setup'] = 'gif'
    
    elif data == "dice_emoji":
        await query.edit_message_text("📤 Send me an emoji to set as dice!")

# ============ GIF HANDLER ============
async def handle_gif_upload(update, context):
    """Handle GIF uploads for dice"""
    if not is_admin(update.effective_user.id):
        return
    
    if context.user_data.get('dice_setup') == 'gif':
        if update.message.animation:
            gif = update.message.animation
            add_gif('dice', gif.file_id)
            await update.message.reply_text("✅ Dice GIF set successfully!")
            context.user_data['dice_setup'] = None
        else:
            await update.message.reply_text("❌ Please send a GIF file!")

# ============ START COMMAND ============
async def start_command(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check if user is in group
    try:
        member = await context.bot.get_chat_member(GROUP_ID, user_id)
    except:
        msg = f"""
⚠️ <b>JOIN GROUP FIRST!</b>
━━━━━━━━━━━━━━━━━━
Please join our group to use this bot:
{JOIN_GROUP_LINK}
━━━━━━━━━━━━━━━━━━
        """
        await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")
        return
    
    msg = f"""
🔥 <b>𝙆𝘼𝙇𝙔𝙐𝙂 𝙀𝙎𝘾𝙍𝙊𝙒 𝘿𝙀𝘼𝙇 𝘽𝙊𝙏</b>
━━━━━━━━━━━━━━━━━━
👋 Hey @{username}!

🔹 <b>Features:</b>
📝 Create Deal Forms
👑 Admin Management
🔒 Lock/Unlock Group
📢 Broadcast Messages
🎲 Dice Game
🎨 Premium Emojis
⏰ Auto Lock/Unlock

━━━━━━━━━━━━━━━━━━
🔹 <b>Commands:</b>
/start - This menu
/help - Help menu
/time - Bot time
/lock - Lock group
/unlock - Unlock group
/admins - List admins
/broadcast - Send broadcast
/send - Send to group
/dice - Play dice
/dicesetup - Setup dice
/check DEAL_ID - Check deal

👑 <b>Owner Commands:</b>
/approve USER_ID - Add admin
/removeadmin USER_ID - Remove admin
/setlock HH:MM - Set lock time
/setunlock HH:MM - Set unlock time
/setmorning SPEECH - Set morning speech
/setnight SPEECH - Set night speech

━━━━━━━━━━━━━━━━━━
🔥 @𝙆𝘼𝙇𝙔𝙐𝙂𝙀𝙎𝘾𝙍𝙊𝙒𝙎𝙀𝙍𝙑𝙄𝘾𝙀
━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============ HELP COMMAND ============
async def help_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only!")
        return
    
    msg = f"""
❓ <b>𝙃𝙀𝙇𝙋 𝙈𝙀𝙉𝙐</b>
━━━━━━━━━━━━━━━━━━

🔹 <b>User Commands:</b>
/start - Start bot
/help - This menu
/time - Bot time

🔹 <b>Admin Commands:</b>
/lock - Lock group
/unlock - Unlock group
/admins - List admins
/broadcast - Send broadcast
/send - Send to group
/dice - Play dice
/dicesetup - Setup dice
/check DEAL_ID - Check deal
/setlock HH:MM - Set lock time
/setunlock HH:MM - Set unlock time
/setmorning SPEECH - Set morning speech
/setnight SPEECH - Set night speech

👑 <b>Owner Commands:</b>
/approve USER_ID - Add admin
/removeadmin USER_ID - Remove admin

━━━━━━━━━━━━━━━━━━
🔥 @𝙆𝘼𝙇𝙔𝙐𝙂𝙀𝙎𝘾𝙍𝙊𝙒𝙎𝙀𝙍𝙑𝙄𝘾𝙀
━━━━━━━━━━━━━━━━━━    """
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============ TIME COMMAND ============
async def time_command(update, context):
    now = datetime.now()
    settings = load_settings()
    
    msg = f"""
🕐 <b>𝘽𝙊𝙏 𝙏𝙄𝙈𝙀</b>
━━━━━━━━━━━━━━━━━━
📅 Date: {now.strftime('%Y-%m-%d')}
🕐 Time: {now.strftime('%H:%M:%S')}
📌 Day: {now.strftime('%A')}

⏰ <b>𝙎𝘾𝙃𝙀𝘿𝙐𝙇𝙀</b>
🔒 Lock Time: {settings.get('lock_time', '19:30')}
🔓 Unlock Time: {settings.get('unlock_time', '07:00')}
🔐 Status: {'🔒 LOCKED' if settings.get('group_locked', False) else '🔓 UNLOCKED'}

━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============ AUTO LOCK/UNLOCK ============
async def auto_lock_unlock(context):
    """Check and apply lock/unlock based on time"""
    settings = load_settings()
    now = datetime.now().strftime('%H:%M')
    
    lock_time = settings.get('lock_time', '19:30')
    unlock_time = settings.get('unlock_time', '07:00')
    
    # Lock at lock_time
    if now == lock_time and not settings.get('group_locked', False):
        settings['group_locked'] = True
        save_settings(settings)
        speech = load_speeches().get('night', '🌙 Good Night! Group is locked.')
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=format_with_emojis(speech),
            parse_mode="HTML"
        )
    
    # Unlock at unlock_time
    elif now == unlock_time and settings.get('group_locked', False):
        settings['group_locked'] = False
        save_settings(settings)
        speech = load_speeches().get('morning', '🌅 Good Morning! New day, new deals!')
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=format_with_emojis(speech),
            parse_mode="HTML"
        )

# ============ MAIN ============
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ============ COMMANDS ============
    # User commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("time", time_command))
    
    # Admin commands
    application.add_handler(CommandHandler("lock", lock_command))
    application.add_handler(CommandHandler("unlock", unlock_command))
    application.add_handler(CommandHandler("admins", list_admins))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("send", send_command))
    application.add_handler(CommandHandler("dice", dice_command))
    application.add_handler(CommandHandler("dicesetup", dice_setup))
    application.add_handler(CommandHandler("setlock", set_lock_time))
    application.add_handler(CommandHandler("setunlock", set_unlock_time))
    application.add_handler(CommandHandler("setmorning", set_morning_speech))
    application.add_handler(CommandHandler("setnight", set_night_speech))
    application.add_handler(CommandHandler("check", check_deal))
    
    # Owner commands
    application.add_handler(CommandHandler("approve", approve_admin))
    application.add_handler(CommandHandler("removeadmin", remove_admin))
    
    # Callback
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # ============ HANDLERS ============
    # Deal form handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deal_form))
    
    # GIF upload handler
    application.add_handler(MessageHandler(filters.ANIMATION, handle_gif_upload))
    
    # ============ JOB QUEUE ============
    job_queue = application.job_queue
    job_queue.run_repeating(auto_lock_unlock, interval=60, first=10)
    
    print("=" * 60)
    print("🔥 KALYUG ESCROW DEAL BOT STARTED!")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"📋 Group ID: {GROUP_ID}")
    print(f"👥 Admins: {len(load_admins())}")
    print("=" * 60)
    
    application.run_polling()

if __name__ == "__main__":
    main()