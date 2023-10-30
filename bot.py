from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytube import YouTube
import re
import os

# Add your API ID, API Hash, and Bot Token here
api_id = '21915156'
api_hash = '4bc31ee81291b145ba12ab74cf21f4c3'
bot_token = '6867385596:AAGgVjOFGTMWjVG5UzmwzXnMRUyhM-8vKGU'

# Initialize the Pyrogram client
app = Client("youtube_downloader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Start message with an inline keyboard
start_message = (
    "🎬 Welcome to the YouTube Video Downloader Bot!\n"
    "Send me a YouTube video URL to get started."
)

keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("📖 How to Use", url="https://yourwebsite.com/how-to-use")],
        [InlineKeyboardButton("💌 Feedback", url="https://yourwebsite.com/feedback")],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about")],
    ]
)

# Start command handler
@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(start_message, reply_markup=keyboard)

# About command handler
@app.on_callback_query(filters.regex("about"))
async def about_command(client, callback_query):
    about_text = (
        "🤖 This bot allows you to download and stream YouTube videos.\n"
        "Created with ❤️ by Your Name.\n"
        "For more information, visit our website: [Website Link](https://yourwebsite.com/about)"
    )
    await callback_query.message.edit_text(about_text, parse_mode="markdown")

# Handle incoming messages containing YouTube video URLs
@app.on_message(filters.regex(r"https://www\.youtube\.com/watch\?v=.+"))
async def handle_download(client, message):
    chat_id = message.chat.id
    url = message.text

    yt = YouTube(url)
    download_directory = "downloads"
    os.makedirs(download_directory, exist_ok=True)

    format_buttons = []
    available_formats = []

    for stream in yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc():
        if stream.includes_video_track:
            available_formats.append(stream)

    if not available_formats:
        await client.send_message(chat_id, "No video formats available for this URL.")
        return

    for resolution in ["240p", "360p", "720p", "1080p"]:
        format_found = False
        for stream in available_formats:
            if resolution in stream.resolution:
                format_buttons.append([InlineKeyboardButton(resolution, callback_data=f"format_{available_formats.index(stream)}|{url}|{download_directory}")])
                format_found = True
                break
        if not format_found:
            format_buttons.append([InlineKeyboardButton(f"No {resolution}", callback_data=f"no_format|{url}|{download_directory}")])

    reply_markup = InlineKeyboardMarkup(format_buttons)

    await message.reply("Processing the link and available formats:")
    await message.reply("Choose a format to download or stream:", reply_markup=reply_markup)

# Handle callback queries for format selection
@app.on_callback_query(filters.regex(r"^(format_\d+|no_format)\|.+\|.+"))
async def callback_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    callback_data = callback_query.data.split('|')
    format_choice, url, download_directory = callback_data

    if format_choice == "no_format":
        await client.send_message(chat_id, "No video format available for streaming.")
        return

    format_choice = int(format_choice.replace("format_", ""))
    yt = YouTube(url)

    try:
        selected_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()[format_choice]
        video_title = re.sub(r'[\/:*?"<>|]', '-', yt.title)
        video_path = os.path.join(download_directory, video_title + ".mp4")
        selected_stream.download(output_path=download_directory, filename=video_title)

        # Send the video as a document
        video_file = open(video_path, "rb")
        await client.send_document(chat_id, document=video_file, file_name=f"{video_title}.mp4")
        os.remove(video_path)
        video_file.close()

    except Exception as e:
        await callback_query.answer(text=f"Error: {str(e)}")

# Start the bot
if __name__ == "__main__":
    app.run()
