import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import timedelta
from pyrogram.errors.exceptions.bad_request_400 import WebpageCurlFailed

api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6008466751:AAFjUsWB-wAvc04004E7f7STbNql5QphKEI'

app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ydl_opts = {
    'format': 'best',
    'quiet': True,
    'progress_hooks': [lambda d: on_download_progress(d)],
}

ydl = yt_dlp.YoutubeDL(ydl_opts)

user_settings = {}
user_thumbnails = {}
download_progress = {}

def format_duration(duration):
    duration = timedelta(seconds=duration)
    return str(duration)

def on_download_progress(data):
    user_id = data['status'].get('user_id')
    message_id = download_progress.get(user_id)

    if message_id:
        percent_str = data['_percent_str']
        eta_str = data['_eta_str']
        speed_str = data['_speed_str']

        message = f"Downloading: {percent_str} - ETA: {eta_str} - Speed: {speed_str}"
        app.edit_message_text(chat_id=user_id, message_id=message_id, text=message)

def get_auto_generated_thumbnail(url):
    try:
        info_dict = ydl.extract_info(url, download=False)

        if 'entries' in info_dict:
            video = info_dict['entries'][0]
        else:
            video = info_dict

        return video.get('thumbnail', '')
    except yt_dlp.DownloadError:
        return ''

def save_user_thumbnail(user_id, thumbnail_url):
    user_thumbnails[user_id] = thumbnail_url

@app.on_message(filters.command("start"))
async def start_command(client, message):
    start_message = (
        "📎 Welcome to the URL Uploader Bot!\n"
        "Send me any valid URL to get started."
    )

    start_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Help", callback_data="help"),
                InlineKeyboardButton("About", callback_data="about"),
            ],
            [InlineKeyboardButton("Close", callback_data="close")],
        ]
    )

    await message.reply_text(start_message, reply_markup=start_keyboard)

@app.on_message(filters.regex(r"https?://.+") | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    user_id = message.from_user.id
    upload_mode = user_settings.get(user_id, "video")

    url = message.text
    download_directory = "downloads"
    os.makedirs(download_directory, exist_ok=True)

    # If the user sent a photo, save it as the thumbnail
    if message.photo:
        photo = message.photo[-1]
        thumbnail_url = photo.file_id
        save_user_thumbnail(user_id, thumbnail_url)

    try:
        info_dict = ydl.extract_info(url, download=False)

        if 'entries' in info_dict:
            video = info_dict['entries'][0]
        else:
            video = info_dict

        download_url = video.get('url', url)
        file_name = video.get('title', url)
        duration = video.get('duration', 0)
        formats = video.get('formats', [])

        if not formats:
            # No formats found
            await message.reply("No available formats found for this video.")
            return

        format_buttons = []

        for i, fmt in enumerate(formats):
            format_label = f"{fmt.get('format_note', 'Format')} - {fmt.get('ext', 'ext')} ({fmt.get('filesize')}"
            format_buttons.append([InlineKeyboardButton(format_label, callback_data=f"format_{i}")])

        if format_buttons:
            format_buttons.append([InlineKeyboardButton("Cancel", callback_data="cancel_format")])

            format_markup = InlineKeyboardMarkup(format_buttons)

            if upload_mode == "video":
                await message.reply_video(
                    video=download_url,
                    caption=f"{file_name}\nDuration: {format_duration(duration)}",
                    thumb=thumbnail_url,
                    reply_markup=format_markup
                )
            elif upload_mode == "file":
                await message.reply_document(
                    document=download_url,
                    caption=f"{file_name}\nDuration: {format_duration(duration)}",
                    thumb=thumbnail_url,
                    reply_markup=format_markup
                )

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")
    except WebpageCurlFailed:
        await message.reply("Telegram server could not fetch the provided URL. Please check the URL and try again.")

# Define the rest of your code for settings, callbacks, and running the bot.
# Settings command handler
@app.on_message(filters.command("settings"))
async def settings_command(client, message):
    user_id = message.from_user.id
    current_mode = user_settings.get(user_id, "video")

    upload_mode_callback = f"upload_mode_{user_id}"
    show_thumbnail_callback = f"show_thumbnail_{user_id}"
    delete_thumbnail_callback = f"delete_thumbnail_{user_id}"
    cancel_callback = f"cancel_{user_id}"

    keyboard = [
        [InlineKeyboardButton("Upload Mode", callback_data=upload_mode_callback)],
        [InlineKeyboardButton("Show Thumbnail", callback_data=show_thumbnail_callback), InlineKeyboardButton("Delete Thumbnail", callback_data=delete_thumbnail_callback)],
        [InlineKeyboardButton("Back", callback_data=cancel_callback)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply("Settings Menu", reply_markup=reply_markup)

# Callback data handler
@app.on_callback_query(filters.regex(r"^(upload_mode|show_thumbnail|delete_thumbnail|cancel)_\d+$"))
async def callback_handler(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])

    if "upload_mode" in callback_query.data:
        user_id = callback_query.from_user.id
        user_settings[user_id] = "file" if user_settings.get(user_id, "video") == "video" else "video"
        await app.send_message(user_id, f"Upload mode set to: {user_settings[user_id]}")

    if "show_thumbnail" in callback_query.data:
        user_id = callback_query.from_user.id
        thumbnail_url = user_thumbnails.get(user_id, None)

        if thumbnail_url:
            await app.send_photo(user_id, photo=thumbnail_url, caption="Saved Thumbnail")
        else:
            await app.send_message(user_id, "No saved thumbnail found.")

    if "delete_thumbnail" in callback_query.data:
        user_id = callback_query.from_user.id

        if user_id in user_thumbnails:
            del user_thumbnails[user_id]
            await app.send_message(user_id, "Thumbnail deleted.")
        else:
            await app.send_message(user_id, "No saved thumbnail to delete.")

if __name__ == "__main__":
    app.run()



