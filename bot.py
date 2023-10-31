import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from tqdm import tqdm
import os
import re

download_dir = "downloads"
upload_dir = "uploads"

api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '5828088037:AAGu9hwWDURyPjcsj5uvOacm9I5RLKdKHEI'  # Replace with your bot token

app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

selected_format = None

ydl_opts = {
    'quiet': True,
    'progress_hooks': [lambda d: app.send_message(chat_id=d['filename'], text=f"Downloading... {d['_percent_str']}")]
}

ydl = yt_dlp.YoutubeDL(ydl_opts)

url_pattern = r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/v/|youtube\.com/embed/|youtube\.com/?\?vi?=)([a-zA-Z0-9_-]+)"
url_regex = re.compile(url_pattern)

def is_valid_url(url):
    return bool(url_regex.match(url))

# Command handler for the /start command
@app.on_command("start")
async def start_command_handler(client, message: Message):
    await message.reply("Welcome to the URL Uploader Bot! Send a valid YouTube URL to start uploading videos.")

# Command handler for the /help command
@app.on_command("help")
async def help_command_handler(client, message: Message):
    help_text = "To use this bot, follow these steps:\n\n"
    help_text += "1. Send a valid YouTube URL.\n"
    help_text += "2. Select a resolution for the video to upload.\n\n"
    help_text += "The bot will then download and upload the video for you."

    await message.reply(help_text)

@app.on_message(filters.regex(url_pattern))
async def handle_upload(client, message):
    global selected_format

    url = message.text
    if not is_valid_url(url):
        await message.reply("Invalid URL. Please provide a valid YouTube URL.")
        return

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

        if not formats:
            await message.reply("No available formats found for this video.")
            return

        valid_formats = [format for format in formats if format.get('filesize') is not None and format['height'] in (240, 360, 720, 1080)]

        if not valid_formats:
            await message.reply("No available formats (240p, 360p, 720p, 1080p) found for this video.")
            return

        format_buttons = []
        for format in valid_formats:
            format_id = format['format_id']
            filesize_in_mb = f"{format['filesize'] / (1024 * 1024):.2f} MB"
            button_text = f"{format['height']}p ({filesize_in_mb})"
            button_data = f"format_{format_id}"
            format_buttons.append([InlineKeyboardButton(text=button_text, callback_data=button_data)])

        reply_markup = InlineKeyboardMarkup(format_buttons)

        await message.reply_text("Please select a resolution (format in MB):", reply_markup=reply_markup, quote=True)

    except Exception as e:
        print(str(e))
        await message.reply("An error occurred while processing the URL. Please provide a valid YouTube URL.")

@app.on_callback_query(filters.regex(r'^format_\d+'))
async def callback_handler(client, query):
    global selected_format

    format_id = query.data.split("_")[1]

    try:
        with yt_dlp.YoutubeDL() as ydl:
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
                    file_id = video_message.video.file_id

                    with tqdm(total=os.path.getsize(video_file_path), unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                        while True:
                            chunk = file.read(1024 * 1024)  # 1 MB chunks
                            if not chunk:
                                break
                            await client.send_video(chat_id=chat_id, file_id=file_id, caption="Video uploaded successfully!", progress=pbar.update(len(chunk)))

        else:
            await query.answer("Format not found or available.")

    except Exception as e:
        print(str(e))
        await query.answer("An error occurred while processing the URL. Please provide a valid YouTube URL.")

if __name__ == "__main__":
    app.run()
