from pyrogram import Client, filters
import fitz  # PyMuPDF
import os
from flask import Flask
import threading
import logging

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask
webapp = Flask(__name__)

@webapp.route('/')
def hello_world():
    return 'Hello, World!'

@webapp.route('/health')
def health_check():
    return 'Healthy', 200

def run_flask():
    webapp.run(host='0.0.0.0', port=8080)

# Configuration Variables
API_ID = "25731065"  # Replace with your API ID
API_HASH = "be534fb5a5afd8c3308c9ca92afde672"  # Replace with your API hash
BOT_TOKEN = "7309568989:AAF48YF2QK7lz-BGMgOh0vmZKduTmCVIxfY"  # Replace with your Bot Token

# Initialize Pyrogram Client
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Dictionary to store user data
user_files = {}

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Send me PDF files to merge! Type /merge to merge the files.")

@app.on_message(filters.document)
async def handle_document(client, message):
    if message.document.mime_type == "application/pdf":
        user_id = message.from_user.id
        file_id = message.document.file_id
        file_name = f"{file_id}.pdf"
        download_path = await message.download(file_name)
        
        if user_id not in user_files:
            user_files[user_id] = []

        user_files[user_id].append(file_name)
        await message.reply(f"File downloaded: {file_name}. Send more PDFs or type /merge to merge them.")
    else:
        await message.reply("Please send only PDF files.")

@app.on_message(filters.command("merge"))
async def merge_pdfs(client, message):
    user_id = message.from_user.id
    if user_id not in user_files or not user_files[user_id]:
        await message.reply("No PDFs to merge. Please send some PDFs first.")
        return

    pdf_files = user_files[user_id]
    
    if len(pdf_files) < 2:
        await message.reply("Please send at least two PDF files to merge.")
        return

    output_path = "merged_output.pdf"
    pdf_writer = fitz.open()

    try:
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                pdf_reader = fitz.open(pdf_file)
                if pdf_reader.page_count > 0:
                    pdf_writer.insert_pdf(pdf_reader)
                pdf_reader.close()
                logger.info(f"Merged file: {pdf_file}")
            else:
                logger.error(f"File does not exist: {pdf_file}")

        if pdf_writer.page_count > 0:
            pdf_writer.save(output_path)
            pdf_writer.close()
            await message.reply_document(output_path)
            await message.reply(f"File downloaded: {os.path.basename(output_path)}. Send more PDFs or type /merge to merge them.")
        else:
            await message.reply("No pages to merge.")
            pdf_writer.close()

    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}")
        await message.reply("An error occurred while merging PDFs. Please try again.")

    # Clean up files
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
    if os.path.exists(output_path):
        os.remove(output_path)
    del user_files[user_id]  # Clear the user's files

# Start the Flask server in a separate thread
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    
    # Start the Pyrogram Client
    app.run()
