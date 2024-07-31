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
bot = Flask(__name__)

@bot.route('/')
def hello_world():
    return 'Hello, World!'

@bot.route('/health')
def health_check():
    return 'Healthy', 200

def run_flask():
    bot.run(host='0.0.0.0', port=8080)

# Initialize Pyrogram Client
app = Client(
    "my_bot",
    api_id="25731065",         # Replace with your API ID
    api_hash="be534fb5a5afd8c3308c9ca92afde672",     # Replace with your API hash
    bot_token="7309568989:AAF48YF2QK7lz-BGMgOh0vmZKduTmCVIxfY"    # Replace with your Bot Token
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Send me PDF files to merge!")

@app.on_message(filters.document)
async def handle_document(client, message):
    if message.document.mime_type == "application/pdf":
        file_id = message.document.file_id
        file_name = f"{file_id}.pdf"
        await message.download(file_name)
        await message.reply(f"File downloaded: {file_name}")
    else:
        await message.reply("Please send only PDF files.")

@app.on_message(filters.command("merge"))
async def merge_pdfs(client, message):
    pdf_files = [file for file in os.listdir() if file.endswith(".pdf")]
    
    if len(pdf_files) < 2:
        await message.reply("Please send at least two PDF files to merge.")
        return

    output_path = "merged_output.pdf"
    pdf_writer = fitz.open()

    for pdf_file in pdf_files:
        pdf_reader = fitz.open(pdf_file)
        pdf_writer.insert_pdf(pdf_reader)
        pdf_reader.close()

    pdf_writer.save(output_path)
    pdf_writer.close()

    await message.reply_document(output_path)
    
    # Clean up files
    for pdf_file in pdf_files:
        os.remove(pdf_file)
    os.remove(output_path)

# Start the Flask server in a separate thread
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    
    # Start the Pyrogram Client
    app.run()
