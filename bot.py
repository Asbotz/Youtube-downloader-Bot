import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import os
from humanize import naturalsize

# Your API credentials
api_id = 'your_api_id'
api_hash = 'your_api_hash'
bot_token = 'your_bot_token'

# Create a Pyrogram Client instance
app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ydl_opts = {
    'quiet': True,
    'progress_hooks': [lambda d: app.send_message(chat_id=d['filename'], text=f"Downloading... {d['_percent_str']}")]
}

ydl = YoutubeDL(ydl_opts)

url_pattern = r"https?://(www\.)?(sonyliv\.com|youtube\.com|youtu\.be)/.+"  # Support SonyLIV, YouTube, and other sites

def is_valid_url(url):
    return re.match(url_pattern, url) is not None

@app.on_message(filters.command(["start"]))
async def start_command(client, message):
    await message.reply("Welcome to the URL Uploader Bot! Send a video URL to get started.")

@app.on_message(filters.command(["help"]))
async def help_command(client, message):
    help_text = (
        "This bot can download and upload videos. Here's how to use it:\n\n"
        "1. Send a video URL from supported platforms.\n"
        "2. Select the format you want to download/upload.\n\n"
        "Supported platforms: SonyLIV, YouTube, and more."
    )
    await message.reply(help_text)

@app.on_message(filters.regex(url_pattern) | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    url = message.text
    if not is_valid_url(url):
        await message.reply("Invalid URL. Please provide a valid URL.")
        return

    try:
        ydl_opts = {
            'quiet': True,
            'progress_hooks': [lambda d: app.send_message(chat_id=d['filename'], text=f"Downloading... {d['_percent_str']}")]
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

        if not formats:
            await message.reply("No available formats found for this video.")
            return

        format_buttons = []
        for format in formats:
            format_id = format['format_id']
            button_text = f"{format.get('format_note', f'Format {format_id')} - {naturalsize(format.get('filesize', 0))}"
            button_data = f"format_{format_id}"
            format_buttons.append([InlineKeyboardButton(text=button_text, callback_data=button_data)])

        reply_markup = InlineKeyboardMarkup(format_buttons)

        await message.reply_text("Please select a format:", reply_markup=reply_markup)

    except Exception as e:
        print(e)
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

@app.on_callback_query(filters.regex(r'^format_\d+'))
async def callback_handler(client, query):
    format_id = query.data.split("_")[1]

    try:
        info_dict = ydl.extract_info(query.message.text, download=True)
        formats = info_dict.get('formats', [])

        selected_format = next((format for format in formats if format['format_id'] == format_id), None)

        if selected_format:
            await query.answer("Downloading...")

            video_file_path = info_dict['_filename']

            with open(video_file_path, "rb") as file:
                chat_id = query.message.chat.id
                video_message = await client.send_video(chat_id=chat_id, video=file, caption="Video upload in progress...")

                if video_message:
                    await query.message.reply_text("Uploading...")

        else:
            await query.answer("Format not found or available.")

    except Exception as e:
        print(e)
        await query.answer("Invalid URL or no content found. Please provide a valid URL.")

if __name__ == "__main__":
    app.run()
