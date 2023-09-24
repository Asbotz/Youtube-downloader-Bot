from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from pytube import YouTube
from pytube.exceptions import VideoUnavailable, PytubeError
import os
import re

# Add your API ID, API Hash, and Bot Token here

api_id = '23163825' 
api_hash = '668422a97c2fcf2ed125ffd8a783223d'
bot_token = '6698671287:AAEVU1O02ZBZqDmYulk2OdOtKJtOu7d4_48'
# Initialize the Pyrogram client
app = Client("youtube_downloader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Define the start message with advanced inline keyboard buttons
start_message = (
    "🎬 Welcome to the YouTube Video Downloader Bot!\n"
    "Send me a YouTube video URL or playlist URL to get started."
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
def start_command(client, message):
    message.reply_text(start_message, reply_markup=keyboard)

# About command handler
@app.on_callback_query(filters.regex("about"))
def about_command(client, callback_query):
    about_text = (
        "🤖 This bot allows you to download YouTube videos and playlists.\n"
        "Created with ❤️ by Your Name.\n"
        "For more information, visit our website: [Website Link](https://yourwebsite.com/about)"
    )
    callback_query.message.edit_text(about_text, parse_mode="markdown")

# Help command handler
@app.on_command("help")
def help_command(client, message):
    help_text = (
        "📚 Here are some commands you can use:\n\n"
        "/start - Start the bot and get instructions.\n"
        "/help - Get help and a list of available commands.\n"
        "/about - Learn more about this bot.\n"
        "Simply send a YouTube video or playlist URL to download."
    )
    message.reply_text(help_text)

# Handle incoming messages containing YouTube video or playlist URLs
@app.on_message(filters.regex(r"(https://www\.youtube\.com/playlist\?list=|https://www\.youtube\.com/watch\?v=).+"))
def handle_download(client, message):
    try:
        chat_id = message.chat.id
        url = message.text

        if "playlist" in url:
            # Handle YouTube playlist
            playlist = YouTube(url)
            playlist_title = re.sub(r'[\/:*?"<>|]', '-', playlist.title)[:64]  # Clean title for folder creation

            download_directory = f"downloads/{playlist_title}"
            os.makedirs(download_directory, exist_ok=True)

            for video in playlist.streams.filter(progressive=True, file_extension="mp4").all():
                try:
                    video.download(output_path=download_directory)
                except (VideoUnavailable, PytubeError):
                    pass

            client.send_message(chat_id, f"Downloaded videos from the playlist: {playlist.title}")
        else:
            # Handle single YouTube video
            yt = YouTube(url)
            download_directory = "downloads"

            os.makedirs(download_directory, exist_ok=True)

            # Get available video formats for the YouTube video
            formats = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().all()

            if formats:
                # Create a message to display available formats
                format_message = "Available Formats:\n\n"
                format_buttons = []

                for i, format in enumerate(formats):
                    format_message += f"{i + 1}. {format.resolution}p\n"
                    format_buttons.append([InlineKeyboardButton(f"{format.resolution}p", callback_data=f"format_{i}|{url}|{download_directory}")])

                # Create inline keyboard with format selection buttons
                reply_markup = InlineKeyboardMarkup(format_buttons)

                client.send_message(chat_id, format_message + "Choose a format:", reply_markup=reply_markup)
            else:
                client.send_message(chat_id, "No video formats available for this URL.")

    except Exception as e:
        message.reply_text(f"Error: {str(e)}")

# Handle callback queries for format selection
@app.on_callback_query()
def callback_handler(client, callback_query):
    try:
        chat_id = callback_query.message.chat.id
        callback_data = callback_query.data.split('|')
        format_choice, url, download_directory = callback_data
        format_choice = int(format_choice.replace("format_", ""))

        yt = YouTube(url)
        selected_format = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()[format_choice]

        selected_format.download(output_path=download_directory)

        # Upload the video to Telegram
        client.send_video(chat_id, video=InputFile(os.path.join(download_directory, yt.title + ".mp4")))
        os.remove(os.path.join(download_directory, yt.title + ".mp4"))  # Remove the local file after uploading

    except Exception as e:
        callback_query.answer(text=f"Error: {str(e)}")

# Start the bot
if __name__ == "__main__":
    app.run()
