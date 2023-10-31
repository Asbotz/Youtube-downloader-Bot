import os
import yt_dlp
from pyrogram import Client, filters

api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6008466751:AAGALmg_0BnZx4pZm1b7sDxeUPc7Sms0M-E'  # Replace with your bot token

app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ydl_opts = {
    'format': 'best',
    'quiet': True,
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
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])

        if not formats:
            await message.reply("No available formats found for this video.")
            return

        # Select the best format (you can customize this logic)
        best_format = max(formats, key=lambda fmt: fmt.get('filesize', 0))

        file_name = info_dict.get('title', url)
        duration = info_dict.get('duration', 0)

        download_url = best_format['url']

        await message.reply_video(
            video=download_url,
            caption=f"{file_name}\nDuration: {format_duration(duration)}",
            thumb=info_dict.get('thumbnail', None)
        )
    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid URL.")

if __name__ == "__main__":
    app.run()
