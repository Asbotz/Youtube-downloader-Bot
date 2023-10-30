






import os
from pytube import YouTube
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# Add your API ID, API Hash, and Bot Token here
api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6008466751:AAFjUsWB-wAvc04004E7f7STbNql5QphKEI'  # Replace with your bot token
# Add your API ID, API Hash, and Bot Token here
#api_id = 'YOUR_API_ID'
#api_hash = 'YOUR_API_HASH'
#bot_token = 'YOUR_BOT_TOKEN'

# Initialize the Pyrogram client
app = Client("youtube_downloader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Start command handler
@app.on_message(filters.command("start"))
async def start_command(client, message):
    start_message = (
        "🎬 Welcome to the YouTube Video Downloader Bot!\n"
        "Send me a YouTube video URL to get started."
    )
    await message.reply_text(start_message)

# Handle incoming messages containing YouTube video URLs
@app.on_message(filters.regex(r"https://www\.youtube\.com/watch\?v=.+"))
async def handle_download(client, message):
    url = message.text
    yt = YouTube(url)
    download_directory = "downloads"
    os.makedirs(download_directory, exist_ok=True)

    available_formats = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()

    if not available_formats:
        await message.reply("No video formats available for this URL.")
        return

    format_buttons = []

    for stream in available_formats:
        format_buttons.append([InlineKeyboardButton(f"{stream.resolution} - {stream.mime_type}", callback_data=f"format_{available_formats.index(stream)}|{url}|{download_directory}")])

    reply_markup = InlineKeyboardMarkup(format_buttons)

    await message.reply("Processing the link and available formats:")
    await message.reply("Choose a format to download or stream:", reply_markup=reply_markup)

# Handle callback queries for format selection
@app.on_callback_query(filters.regex(r"^(format_\d+)\|.+\|.+"))
async def callback_handler(client, callback_query):
    callback_data = callback_query.data.split('|')
    format_choice, url, download_directory = callback_data

    format_choice = int(format_choice.replace("format_", ""))
    yt = YouTube(url)

    try:
        selected_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()[format_choice]
        video_title = re.sub(r'[\/:*?"<>|]', '-', yt.title)
        video_path = os.path.join(download_directory, video_title + ".mp4")
        selected_stream.download(output_path=download_directory, filename=video_title)

        # Send the video as a document
        await client.send_document(callback_query.from_user.id, document=video_path, caption=video_title)
        os.remove(video_path)

    except Exception as e:
        await callback_query.answer(text=f"Error: {str(e)}")

# Start the bot
if __name__ == "__main__":
    app.run()
