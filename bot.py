from pyrogram import Client, filters
import os
import subprocess
from config import BOT_TOKEN, API_ID, API_HASH, DEFAULT_THUMB

app = Client(
    "torrent-bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# store user thumbnails in memory
user_thumb = {}

def get_thumb(user_id):
    """
    Returns the thumbnail path for the user.
    If user cleared it or no default exists, returns None.
    """
    # user removed thumbnail
    if user_id in user_thumb and user_thumb[user_id] is None:
        return None

    # user set a custom thumbnail
    if user_id in user_thumb:
        return user_thumb[user_id]

    # default thumbnail may be None
    if DEFAULT_THUMB and os.path.exists(DEFAULT_THUMB):
        return DEFAULT_THUMB

    # no thumbnail available
    return None


# -----------------------------
# THUMBNAIL COMMANDS
# -----------------------------

@app.on_message(filters.command("defaultthumb"))
async def reset_to_default(client, message):
    if DEFAULT_THUMB and os.path.exists(DEFAULT_THUMB):
        user_thumb[message.from_user.id] = DEFAULT_THUMB
        await message.reply("🔄 Thumbnail reset to the default one.")
    else:
        user_thumb[message.from_user.id] = None
        await message.reply("⚪ No default thumbnail is set. Files will be sent without a thumbnail.")


@app.on_message(filters.command("clearthumb"))
async def clear_thumb(client, message):
    user_thumb[message.from_user.id] = None
    await message.reply("🚫 Thumbnail removed. Files will upload with NO thumbnail.")


@app.on_message(filters.command("showthumb"))
async def show_thumb(client, message):
    path = get_thumb(message.from_user.id)
    if not path:
        await message.reply("❌ You currently have NO thumbnail set.")
        return
    await message.reply_photo(path, caption="📌 This is your current thumbnail.")


@app.on_message(filters.photo)
async def save_thumbnail(client, message):
    user_id = message.from_user.id
    path = f"thumb_{user_id}.jpg"
    await message.download(file_name=path)
    user_thumb[user_id] = path
    await message.reply("✅ Custom thumbnail saved!")


# -----------------------------
# HANDLE LINKS (direct/torrent/magnet)
# -----------------------------

@app.on_message(filters.text)
async def download_link(client, message):
    link = message.text
    user_id = message.from_user.id

    await message.reply("⏳ Downloading...")

    # run aria2
    cmd = ["aria2c", "-x", "16", "-s", "16", "-k", "1M", link, "-d", "downloads"]
    subprocess.run(cmd)

    # find downloaded file
    file_path = None
    for f in os.listdir("downloads"):
        file_path = "downloads/" + f

    if not file_path:
        await message.reply("❌ Download failed.")
        return

    await message.reply("⬆️ Uploading to Telegram...")

    await app.send_document(
        chat_id=message.chat.id,
        document=file_path,
        thumb=get_thumb(user_id)
    )

    os.remove(file_path)


app.run()
