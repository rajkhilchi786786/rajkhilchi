from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from XMUSIC import app

# 👇 Tumhara Flask session generator ka URL
SESSION_GENERATOR_URL = "http://194.62.248.97:8080"

@app.on_message(filters.command(["startsession", "session"]) & filters.private)
async def start_session(_, message):
    text = (
        "📲 **ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ᴘʏʀᴏɢʀᴀᴍ sᴛʀɪɴɢ sᴇssɪᴏɴ**\n\n"
        "✨ ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sᴀғᴇʟʏ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ sᴇssɪᴏɴ "
        "ɪɴ ᴛʜᴇ ᴍɪɴɪ ᴀᴘᴘ."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔘 PRESS TO GENERATE", url=SESSION_GENERATOR_URL),
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close_startsession")
            ],
        ]
    )

    await message.reply_text(
        text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex("^close_startsession$"))
async def close_callback(_, query):
    await query.answer("Closed", show_alert=True)
    await query.message.delete()

print("✅ session.py loaded successfully!")