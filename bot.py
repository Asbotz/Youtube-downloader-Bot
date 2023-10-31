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

# Define a handler for incoming photos in JPEG format
@app.on_message(filters.photo & (filters.mime("image/jpeg") | filters.mime("image/jpg")))
async def handle_thumbnail_photo(client, message):
    user_id = message.from_user.id
    photo = message.photo[-1]
    thumbnail_file_id = photo.file_id
    save_user_thumbnail(user_id, thumbnail_file_id)
    await app.send_message(user_id, "Thumbnail saved!")

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
                InlineKeyboardButton("Show Thumbnail", callback_data="show_thumbnail"),
                InlineKeyboardButton("Delete Thumbnail", callback_data="delete_thumbnail"),
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
        thumbnail_url = get_auto_generated_thumbnail(url)  # Get the thumbnail URL here

        if not formats:
            # No formats found
            await message.reply("No available formats found for this video.")
            return

        format_buttons = []

        for i, fmt in enumerate(formats):
            format_label = f"{fmt.get('format_note', 'Format')} - {fmt.get('ext', 'ext')} ({fmt.get('filesize')})"
            format_buttons.append([InlineKeyboardButton(format_label, callback_data=f"format_{i}_{fmt['ext']}")])

        if format_buttons:
            format_buttons.append([InlineKeyboardButton("Cancel", callback_data="cancel_format")])

            format_markup = InlineKeyboardMarkup(format_buttons)

            format_message = f"{file_name}\nDuration: {format_duration(duration)}\nAvailable formats:"
            format_data = []

            for i, fmt in enumerate(formats):
                format_label = f"{fmt.get('format_note', 'Format')} - {fmt.get('ext', 'ext')} ({fmt.get('filesize')})"
                format_data.append(f"format_{i}_{fmt['ext']}")  # Include the file extension in the callback data
                format_message += f"\n{format_label}"

            if upload_mode == "video":
                await message.reply_video(
                    video=download_url,
                    caption=format_message,
                    thumb=thumbnail_url,
                    reply_markup=format_markup
                )
            elif upload_mode == "file":
                await message.reply_document(
                    document=download_url,
                    caption=format_message,
                    thumb=thumbnail_url,
                    reply_markup=format_markup
                )

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")
    except WebpageCurlFailed:
        await message.reply("Telegram server could not fetch the provided URL. Please check the URL and try again.")

# Define the "Show Thumbnail" command
@app.on_message(filters.command("showthumbnail"))
async def show_thumbnail_command(client, message):
    user_id = message.from_user.id
    thumbnail_url = user_thumbnails.get(user_id, None)

    if thumbnail_url:
        await app.send_photo(user_id, photo=thumbnail_url, caption="Saved Thumbnail")
    else:
        await app.send_message(user_id, "No saved thumbnail found.")

# Define the "Delete Thumbnail" command
@app.on_message(filters.command("deletethumbnail"))
async def delete_thumbnail_command(client, message):
    user_id = message.from_user.id

    if user_id in user_thumbnails:
        del user_thumbnails[user_id]
        await app.send_message(user_id, "Thumbnail deleted.")
    else:
        await app.send_message(user_id, "No saved thumbnail to delete.")

# Settings command handler
@app.on_message(filters.command("settings"))
async def settings_command(client, message):
    user_id = message.from_user.id
    current_mode = user_settings.get(user_id, "video")

    upload_mode_callback = f"upload_mode_{user_id}"
    show_thumbnail_callback = f"show_thumbnail_{user_id}"
    delete_thumbnail_callback = f"delete_thumbnail_{user_id}"
    settings_back_callback = f"settings_back_{user_id}"  # Define the back button callback data

    keyboard = [
        [InlineKeyboardButton("Upload Mode", callback_data=upload_mode_callback)],
        [InlineKeyboardButton("Show Thumbnail", callback_data=show_thumbnail_callback)],
        [InlineKeyboardButton("Delete Thumbnail", callback_data=delete_thumbnail_callback)],
        [InlineKeyboardButton("Back", callback_data=settings_back_callback)]  # Use the back button callback data
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply("Settings Menu", reply_markup=reply_markup)

# Callback data handler
@app.on_callback_query(filters.regex(r"^(upload_mode|show_thumbnail|delete_thumbnail|settings|settings_back)_\d+$"))
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

    if "settings" in callback_query.data:
        # Navigate to the "Settings" menu
        user_id = callback_query.from_user.id
        current_mode = user_settings.get(user_id, "video")

        upload_mode_callback = f"upload_mode_{user_id}"
        show_thumbnail_callback = f"show_thumbnail_{user_id}"
        delete_thumbnail_callback = f"delete_thumbnail_{user_id}"
        settings_back_callback = f"settings_back_{user_id}"  # Define the back button callback data

        keyboard = [
            [InlineKeyboardButton("Upload Mode", callback_data=upload_mode_callback)],
            [InlineKeyboardButton("Show Thumbnail", callback_data=show_thumbnail_callback)],
            [InlineKeyboardButton("Delete Thumbnail", callback_data=delete_thumbnail_callback)],
            [InlineKeyboardButton("Back", callback_data=settings_back_callback)]  # Use the back button callback data
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await app.send_message(user_id, "Settings Menu", reply_markup=reply_markup)

    if "settings_back" in callback_query.data:
        # Navigate back to the main menu
        user_id = callback_query.from_user.id
        start_message = (
            "📎 Welcome to the URL Uploader Bot!\n"
            "Send me any valid URL to get started."
        )

        start_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Help", callback_data="help"),
                    InlineKeyboardButton("About", callback_data="about"),
                    InlineKeyboardButton("Show Thumbnail", callback_data="show_thumbnail"),
                    InlineKeyboardButton("Delete Thumbnail", callback_data="delete_thumbnail"),
                ],
                [InlineKeyboardButton("Close", callback_data="close")],
            ]
        )

        await app.send_message(user_id, start_message, reply_markup=start_keyboard)

if __name__ == "__main__":
    app.run()
