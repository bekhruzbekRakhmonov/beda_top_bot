import os
from dotenv import load_dotenv
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import sqlite3
import asyncio

# Load environment variables
load_dotenv()

# Set up the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the sentence transformer model
encoder = SentenceTransformer("all-MiniLM-L6-v2")

# Set up Qdrant client
qdrant_storage_path = "./qdrant_storage"
client = QdrantClient(path=qdrant_storage_path)
collection_name = "uybozor_data"

# Set up user database
USER_DB_PATH = 'user_data.db'

# Set up chat history
CHAT_HISTORIES = {}


def setup_user_db():
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        credits INTEGER DEFAULT 200,
        referrer_id INTEGER
    )
    ''')
    conn.commit()
    conn.close()


def get_user_credits(user_id):
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT credits FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def update_user_credits(user_id, credits):
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO users (user_id, credits) VALUES (?, ?)', (user_id, credits))
    conn.commit()
    conn.close()


def add_referral(user_id, referrer_id):
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
    cursor.execute(
        'UPDATE users SET credits = credits + 25 WHERE user_id = ?', (referrer_id,))
    conn.commit()
    conn.close()


def read_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, GROUP_CONCAT(p.photo_url) as photos
        FROM listings l
        LEFT JOIN photos p ON l.id = p.listing_id
        GROUP BY l.id
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def setup_qdrant():
    collections = client.get_collections()
    collection_exists = any(
        collection.name == collection_name for collection in collections.collections)

    if not collection_exists:
        print(f"Yangi to'plam yaratilmoqda: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )

        # Read data from SQLite and upload to Qdrant
        db_path = 'uybor_listings.db'
        data = read_from_sqlite(db_path)

        client.upload_points(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=row[0],
                    vector=encoder.encode(str(row)).tolist(),
                    payload={
                        "id": row[0],
                        "user_id": row[1],
                        "operation_type": row[2],
                        "category_id": row[3],
                        "sub_category_id": row[4],
                        "description": row[5],
                        "price": row[6],
                        "price_currency": row[7],
                        "address": row[8],
                        "region_id": row[9],
                        "district_id": row[10],
                        "street_id": row[11],
                        "zone_id": row[12],
                        "room": row[13],
                        "lat": row[14],
                        "lng": row[15],
                        "square": row[16],
                        "floor": row[17],
                        "floor_total": row[18],
                        "is_new_building": row[19],
                        "repair": row[20],
                        "foundation": row[21],
                        "created_at": row[22],
                        "updated_at": row[23],
                        "media_count": row[24],
                        "views": row[25],
                        "clicks": row[26],
                        "favorites": row[27],
                        "photos": row[28].split(',') if row[28] else []
                    }
                )
                for row in data
            ],
        )
        print("Ma'lumotlar muvaffaqiyatli yuklandi.")
    else:
        print(
            f"{collection_name} to'plami allaqachon mavjud. Mavjud ma'lumotlardan foydalanilmoqda.")


def improve_query(query, chat_history):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Foydalanuvchi so'rovini yaxshilang va aniqlashtiring. Quyidagi suhbat tarixi va so'rovdan foydalaning:

Suhbat tarixi:
{chat_history}

Asl so'rov: {query}

Yaxshilangan so'rov:"""

    response = model.generate_content(prompt)
    return response.text


def retrieve_relevant_properties(query, top_k=5):
    hits = client.search(
        collection_name=collection_name,
        query_vector=encoder.encode(query).tolist(),
        limit=top_k,
    )
    return hits


def generate_property_description(property_data, query):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Quyidagi ma'lumotlardan foydalanib, uy-joy haqida qisqa va ma'lumotli tavsif yozing. YouTube, Instagram yoki Telegram havolalarini olib tashlang. Oddiy matn ishlatib, asosiy ma'lumotlarni ta'kidlang. Javob uy joyga aloqador bo'lishi shart.

Ma'lumotlar:
- Narx: {property_data['price']} {property_data['price_currency']}
- Manzil: {property_data['address']}
- Xonalar soni: {property_data['room']}
- Maydon: {property_data['square']} kv.m
- Qavat: {property_data['floor']}/{property_data['floor_total']}
- Yangi qurilish: {'Ha' if property_data['is_new_building'] else 'Yo\'q'}
- Ta'mirlash: {property_data['repair']}
- Poydevor: {property_data['foundation']}
- Tavsif: {property_data['description']}

So'rov: {query}
Tavsif:"""

    response = model.generate_content(prompt)
    return response.text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    credits = get_user_credits(user_id)
    if credits is None:
        update_user_credits(user_id, 200)
        credits = 200

    # Initialize an empty chat history for the user
    CHAT_HISTORIES[user_id] = []

    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        f'Xush kelibsiz! Sizda {credits} ta kredit bor. O\'zbekistondagi kvartiralar haqida so\'rovingizni yuboring.\n\n'
        f'Ko\'proq kredit olish uchun ushbu havolani ulashing: {referral_link}'
    )


def is_real_estate_query(query):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Determine if the following query is related to real estate or property searching. Respond with only 'Yes' or 'No'.

Query: {query}

Is this query related to real estate?"""

    response = model.generate_content(prompt)
    return response.text.strip().lower() == 'yes'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    credits = get_user_credits(user_id)

    if credits <= 0:
        await update.message.reply_text("Sizda kreditlar tugadi. Ko'proq kredit olish uchun do'stingizni taklif qiling!")
        return

    query = update.message.text

    # Check if the query is related to real estate
    if not is_real_estate_query(query):
        await update.message.reply_text("Kechirasiz, men faqat ko'chmas mulk va uy-joy haqidagi so'rovlarga javob bera olaman. Iltimos, ko'chmas mulk bilan bog'liq savol bering.")
        return

    # Start typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # Get the user's chat history
    user_history = CHAT_HISTORIES.get(user_id, [])
    chat_history = "\n".join(user_history)

    # Improve the query
    improved_query = improve_query(query, chat_history)

    # Retrieve relevant properties
    relevant_properties = retrieve_relevant_properties(improved_query)

    if not relevant_properties:
        await update.message.reply_text("Kechirasiz, so'rovingizga mos uy-joylar topilmadi.")
        return

    # Send each property as a separate message
    for hit in relevant_properties:
        property_data = hit.payload
        photos = property_data.get('photos', [])

        # Generate description for the property
        description = generate_property_description(property_data, query)

        # Send photos if available
        if photos:
            media_group = [InputMediaPhoto(photo.strip())
                           for photo in photos[:10]]  # Limit to 10 photos
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)

        # Send property description
        await update.message.reply_text(description)

    # Update chat history
    user_history = user_history[-4:] + \
        [f"User: {query}", f"Bot: Natijalar yuborildi"]
    CHAT_HISTORIES[user_id] = user_history

    # Update user credits
    new_credits = credits - 1
    update_user_credits(user_id, new_credits)
    await update.message.reply_text(f"Sizda {new_credits} ta kredit qoldi.")

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if args and args[0].isdigit():
        referrer_id = int(args[0])
        user_id = update.effective_user.id
        if referrer_id != user_id:
            add_referral(user_id, referrer_id)
            await update.message.reply_text("Taklif havolasidan foydalanganingiz uchun rahmat! Siz va do'stingiz 25 ta kredit oldingiz.")
        else:
            await update.message.reply_text("O'zingizni taklif qila olmaysiz!")
    await start(update, context)


def main() -> None:
    # Set up databases
    setup_qdrant()
    setup_user_db()

    # Set up the Telegram bot
    application = Application.builder().token(
        os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", handle_referral))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
