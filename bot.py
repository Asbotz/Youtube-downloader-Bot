import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
from humanize import naturalsize  # Import naturalsize function from humanize

# Your API credentials
api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6978191724:AAESbthSlnMiulbsBb9y4Bdi5vvCb0eNMTY'

# Create a Pyrogram Client instance
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

def has_video(url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict.get("formats") is not None
    except yt_dlp.DownloadError:
        return False

@app.on_message(filters.regex(url_pattern) | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    global selected_format

    url = message.text
    if not is_valid_url(url):
        await message.reply("Invalid URL. Please provide a valid URL.")
        return
    if not has_video(url):
        await message.reply("No video content found in the provided URL.")
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

        format_buttons = []
        format_buttons.append([InlineKeyboardButton(text="All formats", callback_data="format_all")])

        for format in formats:
            format_id = format['format_id']
            filesize_in_bytes = format.get('filesize', 0)
            filesize_humanized = naturalsize(filesize_in_bytes, binary=True)  # Format the file size
            format_type = format['ext']  # Get the format type (MP4, WebM, etc.)
            height = format.get('height', 'Unknown')  # Get the height or set to 'Unknown' if not available
            button_text = f"{height}p ({filesize_humanized}) - {format_type}"
            button_data = f"format_{format_id}"
            format_buttons.append([InlineKeyboardButton(text=button_text, callback_data=button_data)])

        reply_markup = InlineKeyboardMarkup(format_buttons, row_width=1)

        await message.reply_text("Please select a format:", reply_markup=reply_markup)

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

@app.on_callback_query(filters.regex(r'^format_\d+'))
async def callback_handler(client, query):
    global selected_format

    format_id = query.data.split("_")[1]

    try:
        info_dict = ydl.extract_info(query.message.text, download=True)
        formats = info_dict.get('formats', [])

        if format_id == 'all':
            # Download all available formats
            await query.answer("Downloading...")

            chat_id = query.message.chat.id
            video_file_path = info_dict['_filename']

            with open(video_file_path, "rb") as file:
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

# Start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply("Welcome to the URL Uploader Bot! Send a supported URL to get started.")

# Help command
#@app.on_message(filters.command("
# Help command
@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = "This bot can download and upload videos from supported URLs.\n\n" \
                "To use it, send a supported URL and choose the format to download.\n\n" \
                "Supported URLs: SonyLIV, YouTube, and others.\n" \
                "Use /start to begin and /help for more information about the bot."
    await message.reply(help_text)

if __name__ == "__main__":
    app.run()

