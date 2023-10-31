import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from tqdm import tqdm
import os

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

url_pattern = r"https?://(www\.)?(sonyliv\.com|youtube\.com|youtu\.be)/.+"  # Support SonyLIV, YouTube, and other sites

def is_valid_url(url):
    return re.match(url_pattern, url) is not None

@app.on_message(filters.regex(url_pattern) | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    global selected_format

    url = message.text
    if not is_valid_url(url):
        await message.reply("Invalid URL. Please provide a valid URL.")
        return

    try:
        ydl_opts = {
            'quiet': True,
            'progress_hooks': [lambda d: app.send_message(chat_id=d['filename'], text=f"Downloading... {d['_percent_str']}")]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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

        await message.reply_text("Please select a resolution (format in MB):", reply_markup=reply_markup)

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

@app.on_callback_query(filters.regex(r'^format_\d+'))
async def callback_handler(client, query):
    global selected_format

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
                    file_id = video_message.video.file_id

                    # Add a progress bar for uploading
                    with tqdm(total=os.path.getsize(video_file_path), unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                        while True:
                            chunk = file.read(1024 * 1024)  # 1 MB chunks
                            if not chunk:
                                break
                            await client.send_video(chat_id=chat_id, file_id=file_id, caption="Video uploaded successfully!", progress=pbar.update(len(chunk)))

        else:
            await query.answer("Format not found or available.")

    except yt_dlp.DownloadError:
        await query.answer("Invalid URL or no content found. Please provide a valid URL.")

if __name__ == "__main__":
    app.run()
