




import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re  # Import the re module for URL validation

# Define your download and upload directories
download_dir = "downloads"  # Directory for storing downloaded videos
upload_dir = "uploads"  # Directory for storing videos to be uploaded to Telegram

api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '5828088037:AAGu9hwWDURyPjcsj5uvOacm9I5RLKdKHEI'  # Replace with your bot token

app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

selected_format = None  # To keep track of the selected format

ydl_opts = {
    'format': 'best',
    'quiet': True,
    'progress_hooks': [lambda d: app.send_message(chat_id=d['filename'], text=f"Downloading... {d['_percent_str']}")]
}

ydl = yt_dlp.YoutubeDL(ydl_opts)

# Define a regular expression pattern for a valid URL
url_pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"

def is_valid_url(url):
    # Use the re module to match the URL against the pattern
    return re.match(url_pattern, url) is not None

@app.on_message(filters.command("start"))
async def start_command(client, message):
    start_message = (
        "📎 Welcome to the URL Uploader Bot!\n"
        "Send me any valid URL to get started."
    )

    await message.reply_text(start_message)

@app.on_message(filters.regex(r"https?://.+") | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    global selected_format  # Declare global variable

    url = message.text
    if not is_valid_url(url):
        await message.reply("Invalid URL. Please provide a valid URL.")
        return

    try:
        info_dict = ydl.extract_info(url, download=True)
        formats = info_dict.get('formats', [])

        valid_formats = [format for format in formats if format.get('filesize') is not None and format['height'] in (240, 360, 720, 1080)]

        if not valid_formats:
            await message.reply("No available formats with the specified resolutions found for this video.")
            return

        format_buttons = []
        for format in valid_formats:
            format_id = format['format_id']
            button_text = f"{format['height']}p ({format['filesize']}B)"
            button_data = f"format_{format_id}"  # Use the format_id as the button_data
            format_buttons.append([InlineKeyboardButton(text=button_text, callback_data=button_data)])

        # Create an InlineKeyboardMarkup with the format buttons displayed vertically
        reply_markup = InlineKeyboardMarkup(format_buttons)

        await message.reply_text("Please select a resolution:", reply_markup=reply_markup)

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

@app.on_callback_query()
async def callback_handler(client, query):
    global selected_format  # Declare global variable

    format_id = query.data.split("_")[1]

    if format_id == selected_format:  # Check if the format matches the selected format
        chat_id = query.message.chat.id
        url = query.message.text
        info_dict = ydl.extract_info(url, download=True)
        video_file_path = info_dict['_filename']

        with open(video_file_path, "rb") as file:
            # Send the video to Telegram
            video_message = await client.send_video(chat_id=chat_id, video=file, caption="Video upload in progress...")

        if video_message:
            await client.send_message(chat_id=chat_id, text="Video uploaded successfully!")

if __name__ == "__main__":
    app.run()



        
        

