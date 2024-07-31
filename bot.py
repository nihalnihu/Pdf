from pyrogram import Client, filters
from pyrogram.types import Message
import zipfile
import io
import os
from flask import Flask
import threading, logging


# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize Flask
bot = Flask(__name__)

@bot.route('/')
def hello_world():
    return 'Hello, World!'

@bot.route('/health')
def health_check():
    return 'Healthy', 200


API_ID = '25731065'
API_HASH = 'be534fb5a5afd8c3308c9ca92afde672'
BOT_TOKEN = '7242003111:AAHHAd-poxmx3ADkUbK-6z0-dYbgaVKF2PA'

app = Client("zip_unzip_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def format_progress_bar(current, total, bar_length=10):
    filled_length = int(bar_length * current // total)
    bar = '●' * filled_length + '○' * (bar_length - filled_length)
    progress = (current / total) * 100
    return f'[{bar}] {progress:.2f}% Complete'

@app.on_message(filters.command('start'))
async def start(client: Client, message: Message):
    await message.reply("Send me a ZIP file and I'll unzip it for you!")

@app.on_message(filters.document)
async def unzip_file(client: Client, message: Message):
    if message.document.mime_type == 'application/zip':
        # Send initial message and get the message ID
        progress_message = await message.reply("Downloading file...")
        download_path = 'temp.zip'
        
        # Download the ZIP file with progress bar
        file_id = message.document.file_id
        file_size = message.document.file_size
        downloaded_size = 0

        def download_progress(current, total):
            nonlocal downloaded_size
            downloaded_size = current
            progress_text = format_progress_bar(downloaded_size, file_size)
            client.edit_message_text(message.chat.id, progress_message.id, f"Downloading file...\n{progress_text}")

        try:
            await client.download_media(file_id, file_name=download_path, progress=download_progress)
        except Exception as e:
            await client.edit_message_text(message.chat.id, progress_message.id, "Failed to download the file.")
            print(f"Download error: {e}")
            return

        # Check if file was downloaded
        if not os.path.exists(download_path):
            await client.edit_message_text(message.chat.id, progress_message.id, "Downloaded file not found.")
            return
        
        # Unzip the file
        extracted_files = []
        try:
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                total_files = len(zip_ref.infolist())
                processed_files = 0
                progress_message = await client.send_message(message.chat.id, "Extracting files...")
                for file_info in zip_ref.infolist():
                    extracted_file = zip_ref.read(file_info.filename)
                    extracted_files.append((file_info.filename, io.BytesIO(extracted_file)))
                    processed_files += 1
                    progress_text = f"Extracting files...\n{processed_files}/{total_files} files processed"
                    client.edit_message_text(message.chat.id, progress_message.id, progress_text)
        except Exception as e:
            await client.edit_message_text(message.chat.id, progress_message.id, "Failed to unzip the file.")
            print(f"Unzip error: {e}")
            return

        # Send the files back to the user
        for filename, file_bytes in extracted_files:
            file_size = len(file_bytes.getvalue())
            uploaded_size = 0

            def upload_progress(current, total):
                nonlocal uploaded_size
                uploaded_size = current
                progress_text = format_progress_bar(uploaded_size, file_size)
                client.edit_message_text(message.chat.id, progress_message.id, f"Uploading {filename}...\n{progress_text}")

            try:
                await client.send_document(
                    message.chat.id, 
                    file_bytes, 
                    caption=filename,
                    progress=upload_progress
                )
                # Clean up message for next file
                progress_message = await client.send_message(message.chat.id, f"Uploaded {filename}")
            except Exception as e:
                await client.edit_message_text(message.chat.id, progress_message.id, f"Failed to upload {filename}.")
                print(f"Upload error: {e}")

        # Clean up the temporary file
        if os.path.exists(download_path):
            os.remove(download_path)
        
        await client.send_message(message.chat.id, "All files processed successfully!")





# Start the Flask server in a separate thread
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    
    # Start the Pyrogram Client
    app.run()
