from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
from tqdm import tqdm
import os
import re

# Your API credentials
api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6759465412:AAFAxePYnXgIOT2ZdD4T71KyLxXigr7iWXc'



# Create a Pyrogram Client instance
app = Client("url_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

url_pattern = r"https?://(www\.)?(sonyliv\.com|youtube\.com|youtu\.be|hotstar\.com)/.+"  # Support SonyLIV, YouTube, Hotstar, and other sites

def is_valid_url(url):
    return re.match(url_pattern, url) is not None

@app.on_message(filters.regex(url_pattern) | filters.regex(r"www\..+\..+"))
async def handle_upload(client, message):
    try:
        url = message.text
        if not is_valid_url(url):
            await message.reply("Invalid URL. Please provide a valid URL.")
            return

        ydl_opts = {}
        ydl = YoutubeDL(ydl_opts)

        with ydl:
            info_dict = ydl.extract_info(url, download=False)
            if not info_dict:
                await message.reply("No content found for this URL.")
                return

            formats = info_dict.get('formats', [])
            if not formats:
                await message.reply("No available formats found for this video.")
                return

            format_buttons = []

            for format in formats:
                format_id = format['format_id']
                format_description = format['format_note']
                button_text = f"{format_description}"
                button_data = f"format_{format_id}"
                format_buttons.append([InlineKeyboardButton(text=button_text, callback_data=button_data)])

            reply_markup = InlineKeyboardMarkup(format_buttons, row_width=2)

            await message.reply_text("Please select a format:", reply_markup=reply_markup)

    except Exception as e:
        print(e)
        await message.reply("An error occurred. Please try again later.")

@app.on_callback_query(filters.regex(r'^format_\d+'))
async def callback_handler(client, query):
    try:
        format_id = query.data.split("_")[1]

        ydl_opts = {}
        ydl = YoutubeDL(ydl_opts)

        info_dict = ydl.extract_info(query.message.text, download=True)
        if not info_dict:
            await query.answer("No content found.")
            return

        formats = info_dict.get('formats', [])

        selected_format = next((format for format in formats if format['format_id'] == format_id), None)

        if selected_format:
            await query.answer("Downloading...")

            video_file_path = info_dict['_filename']
            video_file_size = os.path.getsize(video_file_path)

            with open(video_file_path, "rb") as file:
                chat_id = query.message.chat.id
                video_message = await client.send_video(chat_id=chat_id, video=file, caption="Video upload in progress...")

                if video_message:
                    await query.message.delete()
                    await query.message.reply_text("Uploading...")

                    file_id = video_message.video.file_id

                    with tqdm(total=video_file_size, unit='B', unit_scale=True, unit_divisor=1024, position=0, leave=True) as pbar:
                        while True:
                            chunk = file.read(1024 * 1024)  # 1 MB chunks
                            if not chunk:
                                break
                            await client.send_video(chat_id=chat_id, file_id=file_id, caption="Video uploaded successfully!", progress=pbar.update(len(chunk)))

        else:
            await query.answer("Format not found or available.")

    except Exception as e:
        print(e)
        await query.answer("An error occurred. Please try again later.")

if __name__ == "__main__":
    app.run()






