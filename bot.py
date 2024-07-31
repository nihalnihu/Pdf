from pyrogram import Client, filters
import fitz  # PyMuPDF
import os

app = Client("my_bot", bot_token="7309568989:AAF48YF2QK7lz-BGMgOh0vmZKduTmCVIxfY")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Send me PDF files to merge!")

@app.on_message(filters.document.mime_type("application/pdf"))
async def handle_document(client, message):
    file_id = message.document.file_id
    file_name = f"{file_id}.pdf"
    await message.download(file_name)
    await message.reply(f"File downloaded: {file_name}")

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

app.run()
