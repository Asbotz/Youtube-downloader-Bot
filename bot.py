import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Define your download and upload directories
download_dir = "downloads"  # Directory for storing downloaded videos
upload_dir = "uploads"  # Directory for storing videos to be uploaded to Telegram

api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '5828088037:AAGu9hwWDURyPjcsj5uvOacm9I5RLKdKHEI'  # Replace with your bot token

app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ydl_opts = {
    'format': 'best',
    'quiet': True,
    'progress_hooks': [lambda d: app.send_message(chat_id=d['filename'], text=f"Downloading... {d['_percent_str']}")]
}

ydl = yt_dlp.YoutubeDL(ydl_opts)

def format_duration(duration):
    duration = yt_dlp.utils.formatSeconds(duration)
    return duration

@app.on_message(filters.command("start"))
async def start_command(client, message):
    start_message = (
        "📎 Welcome to the URL Uploader Bot!\n"
        "Send me any valid URL to get started."
    )

    await message.reply_text(start_message)

@app.on_message(filters.regex(r"https?://.+") | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    url = message.text
    try:
        info_dict = ydl.extract_info(url, download=True, outtmpl=os.path.join(download_dir, '%(title)s.%(ext)s'))
        formats = info_dict.get('formats', [])

        if not formats:
            await message.reply("No available formats found for this video.")
            return

        # Create a list of format buttons
        format_buttons = []
        for format in formats:
            file_size = format.get('filesize', None)
            format_id = format['format_id']

            # Customize the text for each button as per your requirements
            button_text = f"Format {format_id}{' (' + str(file_size) + 'B)' if file_size is not None else ''}"

            # Define the callback data for each button
            button_data = f"format_{format_id}"

            # Append the button to the list
            format_buttons.append(InlineKeyboardButton(text=button_text, callback_data=button_data))

        # Create an InlineKeyboardMarkup with the format buttons
        reply_markup = InlineKeyboardMarkup([format_buttons])

        await message.reply_text("Please select a format:", reply_markup=reply_markup)

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

@app.on_callback_query()
async def callback_handler(client, query):
    if query.data.startswith("format_"):
        format_id = query.data.split("_")[1]
        chat_id = query.message.chat.id
        info_dict = ydl.extract_info(url, download=True, outtmpl=os.path.join(upload_dir, '%(title)s.%(ext)s'))
        video_file_path = info_dict['_filename']

        with open(video_file_path, "rb") as file:
            # Send the video to Telegram
            video_message = await app.send_video(chat_id=chat_id, video=file, caption="Video upload in progress...")

        if video_message:
            await app.send_message(chat_id=chat_id, text="Video uploaded successfully!")

if __name__ == "__main__":
    app.run()
