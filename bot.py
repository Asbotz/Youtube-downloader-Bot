import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import timedelta


# Add your API ID, API Hash, and Bot Token here
api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6008466751:AAFjUsWB-wAvc04004E7f7STbNql5QphKEI'  

# Add your API ID, API Hash, and Bot Token here
#api_id = 'YOUR_API_ID'
#api_hash = 'YOUR_API_HASH'
#bot_token = 'YOUR_BOT_TOKEN'

# Initialize the Pyrogram client
app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Initialize yt-dlp
ydl_opts = {
    'format': 'best',
    'quiet': True,
    'progress_hooks': [lambda d: on_download_progress(d)],
}

ydl = yt_dlp.YoutubeDL(ydl_opts)

# User settings for upload mode (file or video)
user_settings = {}

# User thumbnails
user_thumbnails = {}

# Download progress messages
download_progress = {}

# Available formats dictionary
format_options = {}

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

# Start command handler
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

# Close command handler
@app.on_message(filters.command("close"))
async def close_command(client, message):
    await message.reply_text("Menu closed.")

# Help command handler
@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = (
        "ℹ️ Help\n\n"
        "This bot allows you to upload content from URLs.\n\n"
        "To get started, send a valid URL. You can use the /settings command to change upload mode (video or file).\n\n"
        "You can also access the settings menu via the 'Settings' button."
    )
    await message.reply_text(help_text)

# About command handler
@app.on_message(filters.command("about"))
async def about_command(client, message):
    about_text = (
        "🤖 About\n\n"
        "URL Uploader Bot allows you to upload content from URLs, supporting both video and file upload modes.\n\n"
        "Created with ❤️ by Your Name."
    )
    await message.reply_text(about_text)

# Handle incoming messages containing valid URLs
@app.on_message(filters.regex(r"https?://.+") | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    user_id = message.from_user.id
    upload_mode = user_settings.get(user_id, "video")

    url = message.text
    download_directory = "downloads"
    os.makedirs(download_directory, exist_ok=True)

    thumbnail = user_thumbnails.get(user_id, get_auto_generated_thumbnail(url))

    try:
        info_dict = ydl.extract_info(url, download=False)

        if 'entries' in info_dict:
            video = info_dict['entries'][0]
        else:
            video = info_dict

        download_url = video.get('url', url)
        file_name = video.get('title', url)
        duration = video.get('duration', 0)

        if upload_mode == "video":
            download_message = await message.reply_video(
                video=download_url,
                caption=f"{file_name}\nDuration: {format_duration(duration)}",
                thumb=thumbnail
            )
        elif upload_mode == "file":
            download_message = await message.reply_document(
                document=download_url,
                caption=f"{file_name}\nDuration: {format_duration(duration)}",
                thumb=thumbnail
            )

        user_thumbnails[user_id] = thumbnail
        download_progress[user_id] = download_message.message_id

        # Generate format buttons and add them to the format_options dictionary
        available_formats = video.get('formats', [])
        format_buttons = []

        for i, fmt in enumerate(available_formats):
            format_label = f"{fmt.get('format_note', 'Format')} - {fmt.get('ext', 'ext')}"
            format_buttons.append(InlineKeyboardButton(format_label, callback_data=f"format_{i}|{url}|{download_directory}"))
            format_options[user_id] = format_buttons

        if format_buttons:
            format_buttons.append(InlineKeyboardButton("Cancel", callback_data=f"cancel_format|{user_id}"))
            format_options[user_id] = format_buttons

            format_markup = InlineKeyboardMarkup(format_buttons)
            await message.reply("Choose a format to download or stream:", reply_markup=format_markup)

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

# Show thumbnail command handler
@app.on_message(filters.command("showthumbnail"))
async def show_thumbnail_command(client, message):
    user_id = message.from_user.id
    thumbnail_url = user_thumbnails.get(user_id, None)

    if thumbnail_url:
        await message.reply_photo(thumbnail_url, caption="Saved Thumbnail")
    else:
        await message.reply("No saved thumbnail found.")

# Delete thumbnail command handler
@app.on_message(filters.command("deletethumbnail"))
async def delete_thumbnail_command(client, message):
    user_id = message.from_user.id

    if user_id in user_thumbnails:
        del user_thumbnails[user_id]
        await message.reply("Thumbnail deleted.")
    else:
        await message.reply("No saved thumbnail to delete.")

# Settings command handler
@app.on_message(filters.command("settings"))
async def settings_command(client, message):
    user_id = message.from_user.id
    current_mode = user_settings.get(user_id, "video")

    show_thumbnail_callback = f"show_thumbnail_{user_id}"
    delete_thumbnail_callback = f"delete_thumbnail_{user_id}"
    upload_mode_callback = f"upload_mode_{user_id}"
    cancel_callback = f"cancel_{user_id}"

    keyboard = [
        [InlineKeyboardButton("Upload Mode", callback_data=upload_mode_callback)],
        [InlineKeyboardButton("Show Thumbnail", callback_data=show_thumbnail_callback)],
        [InlineKeyboardButton("Delete Thumbnail", callback_data=delete_thumbnail_callback)],
        [InlineKeyboardButton("Cancel", callback_data=cancel_callback)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply("Settings Menu", reply_markup=reply_markup)

# Callback data handler
@app.on_callback_query(filters.regex(r"(help|about|close|show_thumbnail|delete_thumbnail|upload_mode|cancel)"))
async def callback_handler(client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])

    if "help" in callback_query.data:
        help_text = (
            "ℹ️ Help\n\n"
            "This bot allows you to upload content from URLs.\n\n"
            "To get started, send a valid URL. You can use the /settings command to change upload mode (video or file).\n\n"
            "You can also access the settings menu via the 'Settings' button."
        )
        await app.send_message(user_id, help_text)

    if "about" in callback_query.data:
        about_text = (
            "🤖 About\n\n"
            "URL Uploader Bot allows you to upload content from URLs, supporting both video and file upload modes.\n\n"
            "Created with ❤️ by Your Name."
        )
        await app.send_message(user_id, about_text)

    if "close" in callback_query.data:
        await app.send_message(user_id, "Menu closed.")

    if "show_thumbnail" in callback_query.data:
        # Handle showing the saved thumbnail
        user_id = callback_query.from_user.id
        thumbnail_url = user_thumbnails.get(user_id, None)
        if thumbnail_url:
            await app.send_photo(user_id, photo=thumbnail_url, caption="Saved Thumbnail")
        else:
            await app.send_message(user_id, "No saved thumbnail found.")

    if "delete_thumbnail" in callback_query.data:
        # Handle deleting the saved thumbnail
        user_id = callback_query.from_user.id
        if user_id in user_thumbnails:
            del user_thumbnails[user_id]
            await app.send_message(user_id, text="Thumbnail deleted.")
        else:
            await app.send_message(user_id, text="No saved thumbnail to delete.")

    if "upload_mode" in callback_query.data:
        user_id = callback_query.from_user.id
        user_settings[user_id] = "file" if user_settings.get(user_id, "video") == "video" else "video"
        await app.send_message(user_id, f"Upload mode set to: {user_settings[user_id]}")

    if "cancel" in callback_query.data:
        await app.send_message(user_id, "Settings menu canceled.")

# Run the bot
if __name__ == "__main__":
    app.run()
