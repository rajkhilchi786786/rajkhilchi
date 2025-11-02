import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters, enums
from pyrogram.enums import MessageEntityType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, CallbackQuery, Message
from XMUSIC import app
from XMUSIC.plugins.Manager.nightmodedb import nightdb, nightmode_on, nightmode_off, get_nightchats
from datetime import datetime
import pytz
from pytz import timezone  # used for scheduler startup below

IST = pytz.timezone("Asia/Kolkata")

# ---------------------------
# ⚙️ Chat permission presets
CLOSE_CHAT = ChatPermissions(
    can_send_messages=True,  # users can still send text messages
    can_send_media_messages=False,
    can_send_polls=False,
    can_change_info=False,
    can_add_web_page_previews=False,
    can_pin_messages=False,
    can_invite_users=False,
)

OPEN_CHAT = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_change_info=True,
    can_add_web_page_previews=True,
    can_pin_messages=True,
    can_invite_users=True,
)

# ---------------------------
# 🌙 Inline Buttons
buttons = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("🌙 ᴇɴᴀʙʟᴇ ɴɪɢʜᴛᴍᴏᴅᴇ 🌙", callback_data="add_night"),
        InlineKeyboardButton("☀️ ᴅɪsᴀʙʟᴇ ɴɪɢʜᴛᴍᴏᴅᴇ ☀️", callback_data="rm_night")
    ]]
)

# ---------------------------
# 🌃 /nightmode command
@app.on_message(filters.command("nightmode") & filters.group)
async def _nightmode(_, message: Message):
    try:
        await message.reply_photo(
            photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
            caption=(
                "✨ **Nɪɢʜᴛᴍᴏᴅᴇ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ** ✨\n\n"
                "🌙 ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ **ᴇɴᴀʙʟᴇ** ᴏʀ **ᴅɪsᴀʙʟᴇ** ɴɪɢʜᴛᴍᴏᴅᴇ ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ.\n"
                "🕙 ᴅᴇғᴀᴜʟᴛ ᴛɪᴍᴇ: **10:00 ᴘᴍ → 7:00 ᴀᴍ (ɪsᴛ)**\n"
                "🚫 ᴍᴇᴅɪᴀ, sᴛɪᴄᴋᴇʀs & ʟɪɴᴋs ᴡɪʟʟ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ ᴅᴜʀɪɴɢ ɴɪɢʜᴛᴍᴏᴅᴇ.\n"
                "✅ ᴛᴇxᴛ & ᴍᴜsɪᴄ ᴄᴏᴍᴍᴀɴᴅs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ."
            ),
            reply_markup=buttons
        )
    except Exception as e:
        print(f"[nightmode_cmd_error] {e}")

# ---------------------------
# 🔘 Callback query handler
@app.on_callback_query(filters.regex("^(add_night|rm_night)$"))
async def nightcb(_, query: CallbackQuery):
    data = query.data
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    admins = [m.user.id async for m in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if user_id not in admins:
        return await query.answer("❌ Only group admins can use this feature.", show_alert=True)

    check_night = await nightdb.find_one({"chat_id": chat_id})
    try:
        if data == "add_night":
            if check_night:
                await query.message.edit_caption("🌙 **NɪɢʜᴛMᴏᴅᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴇɴᴀʙʟᴇᴅ!**")
            else:
                await nightmode_on(chat_id)
                await query.message.edit_caption(
                    "🌌 **NɪɢʜᴛMᴏᴅᴇ Aᴄᴛɪᴠᴀᴛᴇᴅ!** 🌌\n\n"
                    "🕙 Fʀᴏᴍ: 10 PM → 7 AM (ɪsᴛ)\n"
                    "🚫 Mᴇᴅɪᴀ, sᴛɪᴄᴋᴇʀs & ʟɪɴᴋs ᴀʀᴇ ʀᴇsᴛʀɪᴄᴛᴇᴅ."
                )
        elif data == "rm_night":
            if check_night:
                await nightmode_off(chat_id)
                await query.message.edit_caption("☀️ **DᴀʏMᴏᴅᴇ Aᴄᴛɪᴠᴇ!** Aʟʟ ᴍᴇssᴀɢᴇs ᴀʟʟᴏᴡᴇᴅ.")
            else:
                await query.message.edit_caption("☀️ **NɪɢʜᴛMᴏᴅᴇ ɪs ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ!**")
    except Exception as e:
        print(f"[nightmode_toggle_error] {e}")

# ---------------------------
# 🕓 Delete media/stickers/links during night (text & /play allowed)
@app.on_message(filters.group & (filters.media | filters.sticker | filters.text), group=99)
async def delete_night_messages(_, message: Message):
    try:
        chat_id = message.chat.id
        check_night = await nightdb.find_one({"chat_id": chat_id})
        if not check_night:
            return

        now = datetime.now(IST)
        hour = now.hour
        start_hour, end_hour = 22, 7
        is_night = hour >= start_hour or hour < end_hour

        if not is_night:
            return

        # ✅ Allow bot commands (so /play, /pause etc. stay)
        is_command = False
        if message.entities:
            for ent in message.entities:
                ent_type = getattr(ent, "type", None)
                if isinstance(ent_type, str):
                    if ent_type == "bot_command" and getattr(ent, "offset", 0) == 0:
                        is_command = True
                        break
                else:
                    if ent_type == MessageEntityType.BOT_COMMAND and getattr(ent, "offset", 0) == 0:
                        is_command = True
                        break
        if message.text and message.text.startswith("/"):
            is_command = True

        if is_command:
            return

        # 🚫 Delete restricted content
        if (
            message.sticker
            or message.photo
            or message.video
            or message.animation
            or message.audio
            or message.voice
            or message.video_note
            or (message.text and ("http://" in message.text or "https://" in message.text))
        ):
            try:
                await message.delete()
                warn = await message.reply_text(
                    "⚠️ **NɪɢʜᴛMᴏᴅᴇ Aᴄᴛɪᴠᴇ (10PM – 7AM IST)**\n"
                    "🚫 Mᴇᴅɪᴀ, Sᴛɪᴄᴋᴇʀs & Lɪɴᴋs ᴀʀᴇ ʀᴇsᴛʀɪᴄᴛᴇᴅ ɴᴏᴡ."
                )
                await asyncio.sleep(4)
                await warn.delete()
            except Exception as e:
                print(f"[nightmode_delete_error] {e}")
    except Exception as e:
        print(f"[nightmode_delete_outer_error] {e}")

# ---------------------------
# 🌌 Scheduler jobs (notifications)
async def start_nightmode():
    try:
        schats = await get_nightchats()
        chats = [int(chat["chat_id"]) for chat in schats] if schats else []
        for add_chat in chats:
            try:
                await app.send_photo(
                    add_chat,
                    photo="https://telegra.ph//file/06649d4d0bbf4285238ee.jpg",
                    caption="🌙 **NɪɢʜᴛMᴏᴅᴇ Aᴄᴛɪᴠᴇ:**\n🚫 Mᴇᴅɪᴀ, Sᴛɪᴄᴋᴇʀs & Lɪɴᴋs ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ.\n✅ Tᴇxᴛ & Cᴏᴍᴍᴀɴᴅs ᴀʟʟᴏᴡᴇᴅ."
                )
                await app.set_chat_permissions(add_chat, CLOSE_CHAT)
            except Exception as e:
                print(f"[nightmode_notify_error] {add_chat} - {e}")
    except Exception as e:
        print(f"[start_nightmode_error] {e}")

async def close_nightmode():
    try:
        schats = await get_nightchats()
        chats = [int(chat["chat_id"]) for chat in schats] if schats else []
        for rm_chat in chats:
            try:
                await app.send_photo(
                    rm_chat,
                    photo="https://telegra.ph//file/14ec9c3ff42b59867040a.jpg",
                    caption="🌞 **DᴀʏMᴏᴅᴇ:** NɪɢʜᴛMᴏᴅᴇ ᴇɴᴅᴇᴅ.\n🎉 Yᴏᴜ ᴄᴀɴ ɴᴏᴡ sᴇɴᴅ ᴀʟʟ ᴍᴇssᴀɢᴇ ᴛʏᴘᴇs ғʀᴇᴇʟʏ!"
                )
                await app.set_chat_permissions(rm_chat, OPEN_CHAT)
            except Exception as e:
                print(f"[nightmode_notify_error] {rm_chat} - {e}")
    except Exception as e:
        print(f"[close_nightmode_error] {e}")

# ---------------------------
# 🧠 Safe Scheduler
async def _start_scheduler_task():
    scheduler = AsyncIOScheduler(timezone=timezone("Asia/Kolkata"))
    scheduler.add_job(start_nightmode, trigger="cron", hour=22, minute=0)  # 10 PM
    scheduler.add_job(close_nightmode, trigger="cron", hour=7, minute=0)   # 7 AM
    scheduler.start()
    print("🌙 NightMode plugin loaded — Scheduler started (Asia/Kolkata)")

# Prevent scheduler duplication 🛡️
if not hasattr(app, "nightmode_scheduler_started"):
    asyncio.create_task(_start_scheduler_task())
    app.nightmode_scheduler_started = True