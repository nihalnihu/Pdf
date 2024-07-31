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

# Initialize Pyrogram Client
app = Client(
    "my_bot",
    api_id=os.getenv("25731065"),         # Fetch from environment variable
    api_hash=os.getenv("be534fb5a5afd8c3308c9ca92afde672"),     # Fetch from environment variable
    bot_token=os.getenv("7309568989:AAF48YF2QK7lz-BGMgOh0vmZKduTmCVIxfY")    # Fetch from environment variable
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

    for pdf_file in pdf_files:
        try:
            pdf_reader = fitz.open(pdf_file)
            pdf_writer.insert_pdf(pdf_reader)
            pdf_reader.close()
            logger.info(f"Merged file: {pdf_file}")
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")

    pdf_writer.save(output_path)
    pdf_writer.close()

    await message.reply_document(output_path)

    # Clean up files
    for pdf_file in pdf_files:
        os.remove(pdf_file)
    os.remove(output_path)
    del user_files[user_id]  # Clear the user's files

# Start the Flask server in a separate thread
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    
    # Start the Pyrogram Client
    app.run()
