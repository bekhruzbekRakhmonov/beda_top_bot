import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatAction
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import sqlite3
import asyncio
import json
from docx import Document
from docx2pdf import convert
from PyPDF2 import PdfReader, PdfWriter
import requests

# Load environment variables
load_dotenv()

# Set up the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the sentence transformer model
encoder = SentenceTransformer("all-MiniLM-L6-v2")

# Set up Qdrant client
qdrant_storage_path = "./qdrant_storage"
client = QdrantClient(path=qdrant_storage_path)
collection_name = "real_estate_data"

# Set up chat history and user states
CHAT_HISTORIES = {}
USER_STATES = {}

# API endpoint
# Update with your actual API endpoint
API_ENDPOINT = "http://localhost:5000/api"


def api_request(method, endpoint, data=None):
    url = f"{API_ENDPOINT}/{endpoint}"
    headers = {'Content-Type': 'application/json'}

    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method == 'PUT':
        response = requests.put(url, headers=headers, json=data)
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers)

    return response.json()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    api_request('POST', 'agents', {
        'agent_id': user.id,
        'name': user.full_name,
        'agency': "Unknown Agency"
    })

    CHAT_HISTORIES[user.id] = []
    USER_STATES[user.id] = {'state': 'idle'}

    keyboard = [
        [InlineKeyboardButton("Add Property", callback_data='add_property')],
        [InlineKeyboardButton("Add Client", callback_data='add_client')],
        [InlineKeyboardButton("Prepare Document",
                              callback_data='prepare_document')],
        [InlineKeyboardButton("View My Properties",
                              callback_data='view_properties')],
        [InlineKeyboardButton("View My Clients", callback_data='view_clients')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f'Welcome, {user.full_name}! How can I assist you today?',
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    api_request('POST', 'agents', {
        'agent_id': user.id,
        'name': user.full_name,
        'agency': "Unknown Agency"
    })

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    query = update.message.text
    state = USER_STATES[user.id]['state']

    if state == 'add_property':
        property_data = json.loads(query)
        property_data['agent_id'] = user.id
        response = api_request('POST', 'properties', property_data)
        USER_STATES[user.id]['state'] = 'idle'
        await update.message.reply_text(f"Property added successfully! Property ID: {response['id']}")
    elif state == 'add_client':
        client_data = json.loads(query)
        client_data['agent_id'] = user.id
        response = api_request('POST', 'clients', client_data)
        USER_STATES[user.id]['state'] = 'idle'
        await update.message.reply_text(f"Client added successfully! Client ID: {response['id']}")
    elif state == 'prepare_document':
        doc_data = json.loads(query)
        doc_data['agent_id'] = user.id
        response = api_request('POST', 'documents', doc_data)
        USER_STATES[user.id]['state'] = 'idle'
        # Here you would typically generate and send the document
        await update.message.reply_text(f"Document prepared successfully! Document ID: {response['id']}")
    else:
        # General query handling
        agent_history = CHAT_HISTORIES.get(user.id, [])
        chat_history = "\n".join(agent_history)

        # Here you would typically use your NLP model to generate a response
        response = "I understood your query. How else can I assist you?"

        agent_history = agent_history[-4:] + \
            [f"Agent: {query}", f"Bot: {response}"]
        CHAT_HISTORIES[user.id] = agent_history

        await update.message.reply_text(response, disable_web_page_preview=True)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'add_property':
        USER_STATES[query.from_user.id]['state'] = 'add_property'
        await query.edit_message_text("Please provide the property details in JSON format:")
    elif query.data == 'add_client':
        USER_STATES[query.from_user.id]['state'] = 'add_client'
        await query.edit_message_text("Please provide the client details in JSON format:")
    elif query.data == 'prepare_document':
        USER_STATES[query.from_user.id]['state'] = 'prepare_document'
        await query.edit_message_text("Please provide the document details in JSON format:")
    elif query.data == 'view_properties':
        properties = api_request(
            'GET', f'properties?agent_id={query.from_user.id}')
        property_list = "\n".join(
            [f"{p['address']} - ${p['price']}" for p in properties])
        await query.edit_message_text(f"Your properties:\n{property_list}")
    elif query.data == 'view_clients':
        clients = api_request('GET', f'clients?agent_id={query.from_user.id}')
        client_list = "\n".join(
            [f"{c['name']} - {c['email']}" for c in clients])
        await query.edit_message_text(f"Your clients:\n{client_list}")


def main() -> None:
    application = Application.builder().token(
        os.getenv("TELEGRAM_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
