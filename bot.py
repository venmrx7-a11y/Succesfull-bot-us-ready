import re
import json
import os
import sys
import random
import asyncio
import string
import time
from datetime import datetime, time as dtime, timedelta
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ============ FLASK FOR RENDER ============
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "KALYUG ESCROW BOT is running!", 200

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port)

# ============ CONFIG ============
BOT_TOKEN = "8885172416:AAFRtSo5uGlTSZBBQgU62Xal8XPgu571tjg"
OWNER_ID = 7977493987
ADMIN_IDS = [OWNER_ID]

# Group IDs
GROUP_ID = -1003920615096
JOIN_GROUP_ID = -1002353854365
JOIN_GROUP_LINK = "https://t.me/+5Z_XCSm-BzE4YTJl"

USERS_FILE = "users.json"
DEALS_FILE = "deals.json"
ADMINS_FILE = "admins.json"
CONFIG_FILE = "config.json"
GIFS_FILE = "gifs.json"

# ============ LOAD/SAVE ============
def load_json(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# ============ DATA ============
users = load_json(USERS_FILE)
deals = load_json(DEALS_FILE)
admins_data = load_json(ADMINS_FILE, {"approved": [str(OWNER_ID)]})
config = load_json(CONFIG_FILE, {
    "lock_enabled": False,
    "lock_time": None,
    "unlock_time": None,
    "morning_speech": "",
    "locked": False
})
gifs_data = load_json(GIFS_FILE, {"gifs": {}})

# Ensure owner is admin
if str(OWNER_ID) not in admins_data.get("approved", []):
    admins_data.setdefault("approved", []).append(str(OWNER_ID))
    save_json(ADMINS_FILE, admins_data)

# ============ PREMIUM EMOJIS ============
PREMIUM_EMOJIS = {
    "verified": {"id": "6246537187614005254", "fallback": "✅"},
    "verify": {"id": "6246782404476803545", "fallback": "✅"},
    "verify_blue": {"id": "6010060634803148161", "fallback": "✅"},
    "eye": {"id": "6035338338406242050", "fallback": "👁️"},
    "eyeball": {"id": "6035051267087143217", "fallback": "👁️"},
    "eyes": {"id": "6035225389356290238", "fallback": "👀"},
    "fire": {"id": "4956222745814762495", "fallback": "🔥"},
    "fire_red": {"id": "4956606007221421405", "fallback": "🔥"},
    "explosion": {"id": "6032673796530377389", "fallback": "💥"},
    "heart": {"id": "5783157259152397008", "fallback": "❤️"},
    "heart_red": {"id": "5801084710343938087", "fallback": "❤️"},
    "heart_pink": {"id": "6010280773351904888", "fallback": "❤️"},
    "heart_blue": {"id": "5780496071645991525", "fallback": "💙"},
    "heart_green": {"id": "5888789252493283486", "fallback": "💚"},
    "heart_yellow": {"id": "5840261097719148872", "fallback": "💛"},
    "heart_purple": {"id": "5840265018655703965", "fallback": "💜"},
    "heart_black": {"id": "5840266939932994956", "fallback": "🖤"},
    "star": {"id": "6244496562752331516", "fallback": "⭐"},
    "star_gold": {"id": "5904618938578243567", "fallback": "⭐"},
    "star_glow": {"id": "6010156854955480259", "fallback": "🌟"},
    "sparkle": {"id": "6010338729640596556", "fallback": "✨"},
    "sparkle_blue": {"id": "6010086134023985536", "fallback": "✨"},
    "vampire": {"id": "6034871295072539452", "fallback": "🧛"},
    "monster": {"id": "6034962795055812935", "fallback": "👹"},
    "ghost": {"id": "6035070298087231243", "fallback": "👻"},
    "devil": {"id": "6035242444671421879", "fallback": "👿"},
    "crown": {"id": "5794422335599546668", "fallback": "👑"},
    "crown_gold": {"id": "6089003761496232797", "fallback": "👑"},
    "crown_blue": {"id": "6247039939305808563", "fallback": "👑"},
    "money": {"id": "6089104607328342288", "fallback": "💰"},
    "money_bag": {"id": "6086730718774300509", "fallback": "💰"},
    "dollar": {"id": "6089140105233044310", "fallback": "💵"},
    "diamond": {"id": "6086778246882399112", "fallback": "💎"},
    "like": {"id": "6089313931149448495", "fallback": "👍"},
    "unlike": {"id": "6088789257285988672", "fallback": "👎"},
    "clap": {"id": "6093744967304352336", "fallback": "👏"},
    "smile": {"id": "6093864814071780526", "fallback": "😀"},
    "laugh": {"id": "5782741660936966676", "fallback": "😂"},
    "heart_eyes": {"id": "6010179687001625256", "fallback": "😍"},
    "cool": {"id": "6032853480782172520", "fallback": "😎"},
    "sad": {"id": "5780793884678296697", "fallback": "😢"},
    "angry": {"id": "6035355642829475999", "fallback": "😡"},
    "think": {"id": "5782756916660802905", "fallback": "🤔"},
    "lock_emoji": {"id": "5465443379917629504", "fallback": "🔓"},
    "sigma_emoji": {"id": "6235620067942341623", "fallback": "🥃"},
    "don_emoji": {"id": "6235717714023814969", "fallback": "🍂"},
    "skills_emoji": {"id": "6235593671073339928", "fallback": "💀"},
    "bolt": {"id": "5791970059597386804", "fallback": "⚡"},
}

ALL_PREMIUM_KEYS = list(PREMIUM_EMOJIS.keys())

def get_emoji_html(name):
    name = name.lower().strip()
    if name in PREMIUM_EMOJIS:
        data = PREMIUM_EMOJIS[name]
        return f'<tg-emoji emoji-id="{data["id"]}">{data["fallback"]}</tg-emoji>'
    return ""

def get_random_emoji():
    if not ALL_PREMIUM_KEYS:
        return ""
    return get_emoji_html(random.choice(ALL_PREMIUM_KEYS))

def wrap_with_emojis(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():
            le = get_random_emoji()
            re = get_random_emoji()
            result.append(f"{le} {line} {re}")
        else:
            result.append(line)
    return '\n'.join(result)

def to_fancy(text):
    fancy_map = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈',
        'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑',
        'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢',
        'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
        's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    }
    return ''.join(fancy_map.get(c, c) for c in text)

def generate_deal_id():
    chars = string.ascii_uppercase + string.digits
    return "KAL-" + ''.join(random.choices(chars, k=6))

def is_admin_user(user_id):
    return str(user_id) in admins_data.get("approved", [])

def is_owner_user(user_id):
    return user_id == OWNER_ID

def register_user(user_id, username, first_name):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "id": user_id,
            "username": username or "NoUsername",
            "name": first_name,
            "joined": str(datetime.now())
        }
        save_json(USERS_FILE, users)
        return True
    return False

# ============ COMMANDS ============

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    register_user(uid, user.username, user.first_name)
    
    if update.effective_chat.type == "private":
        fancy_name = to_fancy(user.first_name)
        buttons = [[InlineKeyboardButton("🔹 JOIN GROUP 🔹", url=JOIN_GROUP_LINK)]]
        msg = f"""
👋 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 {fancy_name}
━━━━━━━━━━━━━━━━━━
𝐉𝐨𝐢𝐧 𝐨𝐮𝐫 𝐠𝐫𝐨𝐮𝐩 𝐟𝐢𝐫𝐬𝐭 𝐭𝐨 𝐮𝐬𝐞 𝐭𝐡𝐞 𝐛𝐨𝐭:
👉 {JOIN_GROUP_LINK}
━━━━━━━━━━━━━━━━━━
𝐓𝐡𝐢𝐬 𝐛𝐨𝐭 𝐢𝐬 𝐟𝐨𝐫:
• 𝙆𝘼𝙇𝙔𝙐𝙂 𝙀𝙎𝘾𝙍𝙊𝙒 𝘿𝙀𝘼𝙇 𝙁𝙊𝙍𝙈
• 𝐃𝐞𝐚𝐥 𝐌𝐚𝐧𝐚𝐠𝐞𝐦𝐞𝐧𝐭
• 𝐆𝐫𝐨𝐮𝐩 𝐋𝐨𝐜𝐤/𝐔𝐧𝐥𝐨𝐜𝐤
• 𝐃𝐢𝐜𝐞 𝐆𝐚𝐦𝐞
━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    await update.message.reply_text(f"𝐁𝐨𝐭 𝐢𝐬 𝐚𝐜𝐭𝐢𝐯𝐞!", parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if update.effective_chat.type == "private" and not is_admin_user(uid) and not is_owner_user(uid):
        buttons = [[InlineKeyboardButton("🔹 JOIN GROUP 🔹", url=JOIN_GROUP_LINK)]]
        await update.message.reply_text(
            f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞 𝐠𝐫𝐨𝐮𝐩 𝐟𝐢𝐫𝐬𝐭:\n{JOIN_GROUP_LINK}",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
        return
    
    msg = f"""
𝐊𝐀𝐋𝐘𝐔𝐆 𝐄𝐒𝐂𝐑𝐎𝐖 𝐁𝐎𝐓 - 𝐇𝐄𝐋𝐏
━━━━━━━━━━━━━━━━━━
𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:
/start - 𝐒𝐭𝐚𝐫𝐭 𝐛𝐨𝐭
/help - 𝐓𝐡𝐢𝐬 𝐦𝐞𝐧𝐮
/time - 𝐒𝐡𝐨𝐰 𝐜𝐮𝐫𝐫𝐞𝐧𝐭 𝐛𝐨𝐭 𝐭𝐢𝐦𝐞
━━━━━━━━━━━━━━━━━━
𝐀𝐃𝐌𝐈𝐍 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:
/lock - 𝐋𝐨𝐜𝐤 𝐠𝐫𝐨𝐮𝐩
/unlock - 𝐔𝐧𝐥𝐨𝐜𝐤 𝐠𝐫𝐨𝐮𝐩
/setlock 𝐇𝐇:𝐌𝐌 - 𝐀𝐮𝐭𝐨 𝐥𝐨𝐜𝐤
/setunlock 𝐇𝐇:𝐌𝐌 - 𝐀𝐮𝐭𝐨 𝐮𝐧𝐥𝐨𝐜𝐤
/setspeech 𝐭𝐞𝐱𝐭 - 𝐒𝐞𝐭 𝐦𝐨𝐫𝐧𝐢𝐧𝐠 𝐬𝐩𝐞𝐞𝐜𝐡
/broadcast 𝐦𝐬𝐠 - 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭
/send - 𝐒𝐞𝐧𝐝 𝐩𝐡𝐨𝐭𝐨/𝐟𝐢𝐥𝐞
/check 𝐃𝐄𝐀𝐋_𝐈𝐃 - 𝐂𝐡𝐞𝐜𝐤 𝐝𝐞𝐚𝐥
/approve 𝐔𝐈𝐃 - 𝐀𝐩𝐩𝐫𝐨𝐯𝐞 𝐚𝐝𝐦𝐢𝐧
/removeadmin 𝐔𝐈𝐃 - 𝐑𝐞𝐦𝐨𝐯𝐞 𝐚𝐝𝐦𝐢𝐧
/admins - 𝐋𝐢𝐬𝐭 𝐚𝐝𝐦𝐢𝐧𝐬
/dice - 𝐃𝐢𝐜𝐞 𝐆𝐚𝐦𝐞
/owner - 𝐎𝐰𝐧𝐞𝐫 𝐩𝐚𝐧𝐞𝐥
━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")

async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    current_time = now.strftime("%I:%M:%S %p")
    current_date = now.strftime("%d %B %Y")
    msg = f"""
𝐁𝐎𝐓 𝐓𝐈𝐌𝐄
━━━━━━━━━━━━━━━━━━
𝐃𝐚𝐭𝐞: {to_fancy(current_date)}
𝐓𝐢𝐦𝐞: {to_fancy(current_time)}
𝐓𝐢𝐦𝐞𝐳𝐨𝐧𝐞: 𝐈𝐒𝐓 (𝐔𝐓𝐂+𝟓:𝟑𝟎)
━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin_user(uid) and not is_owner_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    
    chat_id = update.effective_chat.id
    try:
        permissions = {
            "can_send_messages": False,
            "can_send_media_messages": False,
            "can_send_polls": False,
            "can_send_other_messages": False,
            "can_add_web_page_previews": False,
            "can_change_info": False,
            "can_invite_users": False,
            "can_pin_messages": False
        }
        await context.bot.set_chat_permissions(chat_id, permissions)
        config["locked"] = True
        save_json(CONFIG_FILE, config)
        
        speech = config.get("morning_speech", "")
        msg = f"""
🔒 𝐆𝐑𝐎𝐔𝐏 𝐈𝐒 𝐋𝐎𝐂𝐊𝐄𝐃 🔒
━━━━━━━━━━━━━━━━━━
𝐆𝐫𝐨𝐮𝐩 𝐡𝐚𝐬 𝐛𝐞𝐞𝐧 𝐥𝐨𝐜𝐤𝐞𝐝 𝐛𝐲 𝐚𝐝𝐦𝐢𝐧!
𝐎𝐧𝐥𝐲 𝐚𝐝𝐦𝐢𝐧𝐬 𝐜𝐚𝐧 𝐬𝐞𝐧𝐝 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬 𝐧𝐨𝐰.
━━━━━━━━━━━━━━━━━━
"""
        if speech:
            msg += f"\n{speech}\n━━━━━━━━━━━━━━━━━━\n"
        
        await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"𝐄𝐫𝐫𝐨𝐫: {str(e)}", parse_mode="HTML")

async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin_user(uid) and not is_owner_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    
    chat_id = update.effective_chat.id
    try:
        permissions = {
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,
            "can_change_info": False,
            "can_invite_users": True,
            "can_pin_messages": False
        }
        await context.bot.set_chat_permissions(chat_id, permissions)
        config["locked"] = False
        save_json(CONFIG_FILE, config)
        
        msg = f"""
🔓 𝐆𝐑𝐎𝐔𝐏 𝐈𝐒 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃 🔓
━━━━━━━━━━━━━━━━━━
𝐆𝐫𝐨𝐮𝐩 𝐡𝐚𝐬 𝐛𝐞𝐞𝐧 𝐮𝐧𝐥𝐨𝐜𝐤𝐞𝐝!
𝐄𝐯𝐞𝐫𝐲𝐨𝐧𝐞 𝐜𝐚𝐧 𝐬𝐞𝐧𝐝 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬 𝐧𝐨𝐰.
━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"𝐄𝐫𝐫𝐨𝐫: {str(e)}", parse_mode="HTML")

async def setlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid) and not is_admin_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /setlock 𝐇𝐇:𝐌𝐌", parse_mode="HTML")
        return
    time_str = context.args[0]
    try:
        hour, minute = map(int, time_str.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError
        config["lock_time"] = f"{hour:02d}:{minute:02d}"
        save_json(CONFIG_FILE, config)
        await update.message.reply_text(f"𝐀𝐮𝐭𝐨-𝐥𝐨𝐜𝐤 𝐬𝐞𝐭 𝐟𝐨𝐫 {to_fancy(time_str)}", parse_mode="HTML")
    except:
        await update.message.reply_text(f"𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐭𝐢𝐦𝐞! 𝐔𝐬𝐞 𝐇𝐇:𝐌𝐌", parse_mode="HTML")

async def setunlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid) and not is_admin_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /setunlock 𝐇𝐇:𝐌𝐌", parse_mode="HTML")
        return
    time_str = context.args[0]
    try:
        hour, minute = map(int, time_str.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError
        config["unlock_time"] = f"{hour:02d}:{minute:02d}"
        save_json(CONFIG_FILE, config)
        await update.message.reply_text(f"𝐀𝐮𝐭𝐨-𝐮𝐧𝐥𝐨𝐜𝐤 𝐬𝐞𝐭 𝐟𝐨𝐫 {to_fancy(time_str)}", parse_mode="HTML")
    except:
        await update.message.reply_text(f"𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐭𝐢𝐦𝐞! 𝐔𝐬𝐞 𝐇𝐇:𝐌𝐌", parse_mode="HTML")

async def setspeech_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid) and not is_admin_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /setspeech 𝐲𝐨𝐮𝐫 𝐬𝐩𝐞𝐞𝐜𝐡", parse_mode="HTML")
        return
    speech = " ".join(context.args)
    config["morning_speech"] = speech
    save_json(CONFIG_FILE, config)
    await update.message.reply_text(f"𝐌𝐨𝐫𝐧𝐢𝐧𝐠 𝐬𝐩𝐞𝐞𝐜𝐡 𝐬𝐞𝐭!\n━━━━━━━━━━━━━━━━━━\n{speech}\n━━━━━━━━━━━━━━━━━━", parse_mode="HTML")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid) and not is_admin_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /broadcast 𝐦𝐞𝐬𝐬𝐚𝐠𝐞", parse_mode="HTML")
        return
    if update.message.reply_to_message:
        text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
    else:
        text = " ".join(context.args)
    if not text:
        await update.message.reply_text(f"𝐍𝐨 𝐦𝐞𝐬𝐬𝐚𝐠𝐞!", parse_mode="HTML")
        return
    broadcast_msg = f"""
📢 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓 📢
━━━━━━━━━━━━━━━━━━
{text}
━━━━━━━━━━━━━━━━━━
"""
    await context.bot.send_message(chat_id=GROUP_ID, text=wrap_with_emojis(broadcast_msg), parse_mode="HTML")
    await update.message.reply_text(f"𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐬𝐞𝐧𝐭! ✅", parse_mode="HTML")

async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid) and not is_admin_user(uid):
        await update.message.reply_text(f"𝐀𝐝𝐦𝐢𝐧 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        photo = update.message.reply_to_message.photo[-1].file_id
        caption = " ".join(context.args) if context.args else None
        await context.bot.send_photo(chat_id=GROUP_ID, photo=photo, caption=caption)
        await update.message.reply_text(f"𝐏𝐡𝐨𝐭𝐨 𝐬𝐞𝐧𝐭 𝐭𝐨 𝐠𝐫𝐨𝐮𝐩! ✅", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /send 𝐭𝐞𝐱𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐨𝐫 𝐫𝐞𝐩𝐥𝐲 𝐭𝐨 𝐩𝐡𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝", parse_mode="HTML")
        return
    text = " ".join(context.args)
    msg = f"""
📢 𝐅𝐑𝐎𝐌 𝐀𝐃𝐌𝐈𝐍 📢
━━━━━━━━━━━━━━━━━━
{text}
━━━━━━━━━━━━━━━━━━
"""
    await context.bot.send_message(chat_id=GROUP_ID, text=wrap_with_emojis(msg), parse_mode="HTML")
    await update.message.reply_text(f"𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐬𝐞𝐧𝐭! ✅", parse_mode="HTML")

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid):
        await update.message.reply_text(f"𝐎𝐰𝐧𝐞𝐫 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /approve 𝐔𝐒𝐄𝐑_𝐈𝐃", parse_mode="HTML")
        return
    target_id = context.args[0].strip()
    if target_id in admins_data.get("approved", []):
        await update.message.reply_text(f"𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧!", parse_mode="HTML")
        return
    admins_data.setdefault("approved", []).append(target_id)
    save_json(ADMINS_FILE, admins_data)
    await update.message.reply_text(
        f"✅ 𝐀𝐃𝐌𝐈𝐍 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 ✅\n━━━━━━━━━━━━━━━━━━\n𝐔𝐬𝐞𝐫 𝐈𝐃: {to_fancy(target_id)}\n𝐍𝐨𝐰 𝐭𝐡𝐢𝐬 𝐮𝐬𝐞𝐫 𝐢𝐬 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧!\n━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

async def removeadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid):
        await update.message.reply_text(f"𝐎𝐰𝐧𝐞𝐫 𝐨𝐧𝐥𝐲!", parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /removeadmin 𝐔𝐒𝐄𝐑_𝐈𝐃", parse_mode="HTML")
        return
    target_id = context.args[0].strip()
    if target_id == str(OWNER_ID):
        await update.message.reply_text(f"𝐂𝐚𝐧𝐧𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐫𝐞𝐦𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐞𝐫!", parse_mode="HTML")
        return
    if target_id not in admins_data.get("approved", []):
        await update.message.reply_text(f"𝐍𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧!", parse_mode="HTML")
        return
    admins_data["approved"].remove(target_id)
    save_json(ADMINS_FILE, admins_data)
    await update.message.reply_text(
        f"❌ 𝐀𝐃𝐌𝐈𝐍 𝐑𝐄𝐌𝐎𝐕𝐄𝐃 ❌\n━━━━━━━━━━━━━━━━━━\n𝐔𝐬𝐞𝐫 𝐈𝐃: {to_fancy(target_id)}\n━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"𝐔𝐬𝐚𝐠𝐞: /check 𝐃𝐄𝐀𝐋_𝐈𝐃", parse_mode="HTML")
        return
    deal_id = context.args[0].strip().upper()
    if deal_id in deals:
        deal = deals[deal_id]
        msg = f"""
📋 𝐃𝐄𝐀𝐋 𝐅𝐎𝐔𝐍𝐃 📋
━━━━━━━━━━━━━━━━━━
🆔 <code>{deal_id}</code>
💰 𝐀𝐦𝐨𝐮𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {deal.get('deal_amount', '𝐍/𝐀')}
👤 𝐁𝐮𝐲𝐞𝐫: {deal.get('buyers', '𝐍/𝐀')}
👤 𝐒𝐞𝐥𝐥𝐞𝐫: {deal.get('seller', '𝐍/𝐀')}
📝 𝐃𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐥: {deal.get('deal_detail', '𝐍/𝐀')}
⏰ 𝐄𝐬𝐜𝐫𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐓𝐢𝐥𝐥: {deal.get('escrow_till', '𝐍/𝐀')}
📅 𝐂𝐫𝐞𝐚𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐝: {deal.get('created_at', '𝐍/𝐀')}
━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")
    else:
        await update.message.reply_text(f"𝐃𝐞𝐚𝐥 '{deal_id}' 𝐧𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐟𝐨𝐮𝐧𝐝!", parse_mode="HTML")

async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎲 𝐒𝐄𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐆𝐈𝐅 🎲", callback_data="set_gif")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"𝐃𝐈𝐂𝐄 𝐆𝐀𝐌𝐄\n━━━━━━━━━━━━━━━━━━\n𝐂𝐥𝐢𝐜𝐤 𝐛𝐞𝐥𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐨 𝐬𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐚 𝐆𝐈𝐅!\n𝐒𝐞𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐦𝐞 𝐚 𝐆𝐈𝐅 𝐰𝐢𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐡 𝐤𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐨𝐫𝐝",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner_user(update.effective_user.id):
        await update.message.reply_text(f"𝐎𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐞𝐫 𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐥𝐲!", parse_mode="HTML")
        return
    total_users = len(users)
    total_deals = len(deals)
    total_admins = len(admins_data.get("approved", []))
    lock_status = "🔒 𝐋𝐨𝐜𝐤𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝" if config.get("locked") else "🔓 𝐔𝐧𝐥𝐨𝐜𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝"
    msg = f"""
👑 𝐎𝐖𝐍𝐄𝐑 𝐏𝐀𝐍𝐄𝐋 👑
━━━━━━━━━━━━━━━━━━
📊 𝐒𝐓𝐀𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃𝐒𝐓𝐈𝐂𝐒:
👥 𝐔𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐞𝐫𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {total_users}
📋 𝐃𝐞𝐚𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {total_deals}
🛡️ 𝐀𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐦𝐢𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {total_admins}
🔐 𝐆𝐫𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {lock_status}
━━━━━━━━━━━━━━━━━━
📌 𝐂𝐎𝐌𝐌𝐀𝐍𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃𝐒:
🔹 /lock
🔹 /unlock
🔹 /setlock 𝐇𝐇:𝐌𝐌
🔹 /setunlock 𝐇𝐇:𝐌𝐌
🔹 /setspeech
🔹 /broadcast
🔹 /approve 𝐈𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃
🔹 /removeadmin 𝐈𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃
🔹 /check 𝐃𝐄𝐀𝐋_𝐈𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃
🔹 /time
━━━━━━━━━━━━━━━━━━
⏰ 𝐋𝐨𝐜𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {config.get('lock_time', '𝐍𝐨𝐧𝐞')}
⏰ 𝐔𝐧𝐥𝐨𝐜𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {config.get('unlock_time', '𝐍𝐨𝐧𝐞')}
━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner_user(uid) and not is_admin_user(uid):
        await update.message.reply_text(f"𝐀𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐦𝐢𝐧 𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐥𝐲!", parse_mode="HTML")
        return
    admin_list = admins_data.get("approved", [])
    msg = f"𝐀𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃𝐌𝐈𝐍 𝐋𝐈𝐒𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃\n━━━━━━━━━━━━━━━━━━\n"
    for i, admin_id in enumerate(admin_list, 1):
        owner_tag = " 👑" if admin_id == str(OWNER_ID) else ""
        user_info = users.get(admin_id, {})
        uname = user_info.get('username', '𝐍𝐨𝐧𝐞')
        msg += f"{i}. 🆔 {admin_id}\n   @{uname}{owner_tag}\n\n"
    msg += "━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(wrap_with_emojis(msg), parse_mode="HTML")

# ============ CALLBACK ============
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "set_gif":
        uid = update.effective_user.id
        if not is_owner_user(uid) and not is_admin_user(uid):
            await query.edit_message_text(f"𝐀𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐦𝐢𝐧 𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐥𝐲!", parse_mode="HTML")
            return
        context.user_data["awaiting_gif_keyword"] = True
        await query.edit_message_text(
            f"𝐒𝐄𝐍𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃 𝐆𝐈𝐅 𝐊𝐄𝐘𝐖𝐎𝐑𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐃\n━━━━━━━━━━━━━━━━━━\n𝐒𝐞𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝 𝐦𝐞 𝐚 𝐤𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝\n𝐄𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐞: 𝐁𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞",
            parse_mode="HTML"
        )

# ============ DEAL FORM PARSER ============
def parse_deal_form(text):
    data = {}
    text_upper = text.upper()
    
    # Extract fields
    patterns = [
        ("deal_amount", r'(?:DEAL|𝘿𝙀𝘼𝙇)\s*(?:AMOUNT|𝘼𝙈𝙊𝙐𝙉𝙏)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
        ("buyers", r'(?:BUYERS|𝘽𝙐𝙔𝙀𝙍𝙎)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
        ("seller", r'(?:SELLER|𝙎𝙀𝙇𝙇𝙀𝙍)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
        ("deal_detail", r'(?:DEAL|𝘿𝙀𝘼𝙇)\s*(?:DETAIL|𝘿𝙀𝙏𝘼𝙄𝙇)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
        ("rls_upi", r'(?:RLS|𝙍𝙇𝙎)\s*(?:UPI|𝙐𝙋𝙄)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
        ("condition", r'(?:CONDITION|𝘾𝙊𝙉𝘿𝙄𝙏𝙄𝙊𝙉)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
        ("escrow_till", r'(?:ESCROW|𝙀𝙎𝘾𝙍𝙊𝙒)\s*(?:TILL|𝙏𝙄𝙇𝙇)\s*[:：\-]?\s*(.+?)(?:\n|$)', re.IGNORECASE),
    ]
    
    for key, pattern, flags in patterns:
        match = re.search(pattern, text, flags | re.DOTALL)
        if match:
            value = match.group(1).strip()
            # Clean fancy text to normal
            cleaned = ""
            for ch in value:
                if '\u1d400' <= ch <= '\u1d7ff':  # Mathematical bold range
                    # Approximate mapping back
                    if '𝐀' <= ch <= '𝐙':
                        cleaned += chr(ord('A') + (ord(ch) - 0x1D400))
                    elif '𝐚' <= ch <= '𝐳':
                        cleaned += chr(ord('a') + (ord(ch) - 0x1D41A))
                    elif '𝟎' <= ch <= '𝟗':
                        cleaned += chr(ord('0') + (ord(ch) - 0x1D7CE))
                    else:
                        cleaned += ch
                else:
                    cleaned += ch
            data[key] = cleaned.strip() if cleaned.strip() else value
    
    return data

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if chat_id != GROUP_ID:
        return
    
    # Check for deal form
    has_deal = '𝘿𝙀𝘼𝙇' in text or 'DEAL' in text.upper()
    has_any_field = any(f in text for f in ['𝘼𝙈𝙊𝙐𝙉𝙏', '𝘽𝙐𝙔𝙀𝙍𝙎', '𝙎𝙀𝙇𝙇𝙀𝙍', '𝘿𝙀𝘼𝙇 𝘿𝙀𝙏𝘼𝙄𝙇', '𝙍𝙇𝙎', '𝘾𝙊𝙉𝘿𝙄𝙏𝙄𝙊𝙉', '𝙀𝙎𝘾𝙍𝙊𝙒', 'AMOUNT', 'BUYERS', 'SELLER'])
    
    if not (has_deal and has_any_field):
        return
    
    data = parse_deal_form(text)
    
    buyers = data.get('buyers', '').strip()
    seller = data.get('seller', '').strip()
    
    if not buyers and not seller:
        return
    
    deal_id = generate_deal_id()
    
    deals[deal_id] = {
        "deal_amount": data.get('deal_amount', '𝐍/𝐀'),
        "buyers": buyers,
        "seller": seller,
        "deal_detail": data.get('deal_detail', '𝐍/𝐀'),
        "rls_upi": data.get('rls_upi', '𝐍/𝐀'),
        "condition": data.get('condition', '𝐍/𝐀'),
        "escrow_till": data.get('escrow_till', '𝐍/𝐀'),
        "created_at": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        "created_by": update.effective_user.id
    }
    save_json(DEALS_FILE, deals)
    
    group_msg = f"""
✅ 𝐃𝐄𝐀𝐋 𝐈𝐃 𝐂𝐑𝐄𝐀𝐓𝐄𝐃 ✅
━━━━━━━━━━━━━━━━━━
🆔 <code>{deal_id}</code> (𝐓𝐚𝐩 𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐨 𝐜𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝𝐲)
💰 𝐃𝐞𝐚𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐥 𝐀𝐦𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐝: {data.get('deal_amount', '𝐍/𝐀')}
👤 𝐁𝐮𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐫: {buyers}
👤 𝐒𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐫: {seller}
📝 𝐃𝐞𝐚𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐥: {data.get('deal_detail', '𝐍/𝐀')}
💳 𝐑𝐋𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐒 𝐔𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐈: {data.get('rls_upi', '𝐍/𝐀')}
📋 𝐂𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐢𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧: {data.get('condition', '𝐍/𝐀')}
⏰ 𝐄𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐜𝐫𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧: {data.get('escrow_till', '𝐍/𝐀')}
━━━━━━━━━━━━━━━━━━
𝙀𝙎𝘾𝙍𝙊𝙒 𝙁𝙀𝙀𝙎 𝙄𝙎 𝙉𝙊𝙉 - 𝙍𝙀𝙁𝙐𝙉𝘿𝘼𝘽𝙇𝙀
𝙍𝙂 : @𝙆𝘼𝙇𝙔𝙐𝙂𝙀𝙎𝘾𝙍𝙊𝙒𝙎𝙀𝙍𝙑𝙄𝘾𝙀
━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(wrap_with_emojis(group_msg), parse_mode="HTML")
    
    # Send to all admins
    for admin_id in admins_data.get("approved", []):
        try:
            admin_msg = f"""
📋 𝐍𝐄𝐖 𝐃𝐄𝐀𝐋 𝐅𝐎𝐑𝐌 📋
━━━━━━━━━━━━━━━━━━
🆔 <code>{deal_id}</code>
💰 𝐀𝐦𝐨𝐮𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧: {data.get('deal_amount', '𝐍/𝐀')}
👤 𝐁𝐮𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐫: {buyers}
👤 𝐒𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐫: {seller}
👤 𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐲: @{update.effective_user.username or '𝐍𝐨𝐧𝐞'}
━━━━━━━━━━━━━━━━━━
"""
            await context.bot.send_message(chat_id=int(admin_id), text=wrap_with_emojis(admin_msg), parse_mode="HTML")
        except:
            pass

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_chat.type != "private":
        return
    
    uid = update.effective_user.id
    text = update.message.text
    
    if not text:
        # Check for GIF
        if update.message.animation and context.user_data.get("awaiting_gif_file"):
            keyword = context.user_data.get("gif_keyword", "")
            if keyword:
                gif_id = update.message.animation.file_id
                gifs_data["gifs"][keyword] = gif_id
                save_json(GIFS_FILE, gifs_data)
                context.user_data["awaiting_gif_keyword"] = False
                context.user_data["awaiting_gif_file"] = False
                context.user_data["gif_keyword"] = ""
                await update.message.reply_text(
                    f"✅ 𝐆𝐈𝐅 𝐒𝐀𝐕𝐄𝐃!\n━━━━━━━━━━━━━━━━━━\n𝐊𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧: {keyword}\n𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐬𝐞/𝐝𝐢𝐜𝐞 {keyword}\n━━━━━━━━━━━━━━━━━━",
                    parse_mode="HTML"
                )
            return
        return
    
    # Check for GIF keyword trigger
    if text.lower() in gifs_data.get("gifs", {}):
        gif_id = gifs_data["gifs"][text.lower()]
        await context.bot.send_animation(chat_id=GROUP_ID, animation=gif_id)
        await update.message.reply_text(f"✅ 𝐆𝐈𝐅 𝐬𝐞𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧!", parse_mode="HTML")
        return
    
    if context.user_data.get("awaiting_gif_keyword"):
        keyword = text.strip().lower()
        context.user_data["gif_keyword"] = keyword
        context.user_data["awaiting_gif_keyword"] = False
        context.user_data["awaiting_gif_file"] = True
        await update.message.reply_text(
            f"✅ 𝐊𝐞𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧: {to_fancy(keyword)}\n𝐍𝐨𝐁𝐞𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧 𝐦𝐞 𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧 𝐆𝐈𝐅!",
            parse_mode="HTML"
        )
        return

# ============ AUTO LOCK/UNLOCK CHECKER ============
async def auto_lock_check(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    lock_time = config.get("lock_time")
    unlock_time = config.get("unlock_time")
    
    if lock_time and current_time == lock_time and not config.get("locked"):
        try:
            permissions = {
                "can_send_messages": False,
                "can_send_media_messages": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False
            }
            await context.bot.set_chat_permissions(GROUP_ID, permissions)
            config["locked"] = True
            save_json(CONFIG_FILE, config)
            
            speech = config.get("morning_speech", "")
            lock_msg = f"🔒 𝐀𝐔𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁 𝐋𝐎𝐂𝐊𝐄𝐁𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁🔒\n━━━━━━━━━━━━━━━━━━\n𝐆𝐫𝐨𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁 𝐡𝐚𝐁𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁 𝐛𝐞𝐞𝐧 𝐚𝐁𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁-𝐥𝐨𝐜𝐁𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁𝐁𝐟𝐨𝐫𝐞𝐁𝐞𝐁𝐟𝐨𝐫𝐞𝐡𝐚𝐧𝐁ed!\n━━━━━━━━━━━━━━━━━━"
            if speech:
                lock_msg += f"\n{speech}\n━━━━━━━━━━━━━━━━━━\n"
            await context.bot.send_message(chat_id=GROUP_ID, text=wrap_with_emojis(lock_msg), parse_mode="HTML")
        except:
            pass
    
    if unlock_time and current_time == unlock_time and config.get("locked"):
        try:
            permissions = {
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
                "can_change_info": False,
                "can_invite_users": True,
                "can_pin_messages": False
            }
            await context.bot.set_chat_permissions(GROUP_ID, permissions)
            config["locked"] = False
            save_json(CONFIG_FILE, config)
            
            unlock_msg = f"🔓 𝐀𝐔𝐓𝐎 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃 🔓\n━━━━━━━━━━━━━━━━━━\n━━━━━━━━━━━━━━━━━━"
            await context.bot.send_message(chat_id=GROUP_ID, text=wrap_with_emojis(unlock_msg), parse_mode="HTML")
        except:
            pass

# ============ MAIN ============
def main():
    Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("time", time_cmd))
    application.add_handler(CommandHandler("lock", lock_cmd))
    application.add_handler(CommandHandler("unlock", unlock_cmd))
    application.add_handler(CommandHandler("setlock", setlock_cmd))
    application.add_handler(CommandHandler("setunlock", setunlock_cmd))
    application.add_handler(CommandHandler("setspeech", setspeech_cmd))
    application.add_handler(CommandHandler("broadcast", broadcast_cmd))
    application.add_handler(CommandHandler("send", send_cmd))
    application.add_handler(CommandHandler("approve", approve_cmd))
    application.add_handler(CommandHandler("removeadmin", removeadmin_cmd))
    application.add_handler(CommandHandler("check", check_cmd))
    application.add_handler(CommandHandler("dice", dice_cmd))
    application.add_handler(CommandHandler("owner", owner_cmd))
    application.add_handler(CommandHandler("admins", admins_cmd))
    
    # Callback
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & filters.Chat(GROUP_ID), handle_group_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.PRIVATE, handle_private_message))
    application.add_handler(MessageHandler(filters.ANIMATION & filters.PRIVATE, handle_private_message))
    
    # Auto lock/unlock job - check every minute
    job_queue = application.job_queue
    job_queue.run_repeating(auto_lock_check, interval=60, first=10)
    
    print("=" * 50)
    print("✨ KALYUG ESCROW BOT STARTED!")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"📋 Group: {GROUP_ID}")
    print(f"📦 Total Emojis: {len(PREMIUM_EMOJIS)}")
    print(f"✅ Bot is ready!")
    print("=" * 50)
    
    application.run_polling()

if __name__ == "__main__":
    main()
