import sqlite3
from translator import transliterate

# Connect to the original SQLite database
conn_original = sqlite3.connect('uybozor.db')
cursor_original = conn_original.cursor()

# Create a new SQLite database for translated data
conn_new = sqlite3.connect('uybozor_translated.db')
cursor_new = conn_new.cursor()

# Create the scraped_data table in the new database
cursor_new.execute('''
CREATE TABLE IF NOT EXISTS scraped_data (
    image_url TEXT,
    link TEXT,
    date_time TEXT,
    message_text TEXT,
    views INTEGER
)
''')

# Fetch all rows from the original scraped_data table
cursor_original.execute(
    "SELECT image_url, link, date_time, message_text, views FROM scraped_data")
rows = cursor_original.fetchall()

# Translate each message_text and insert into the new database
for row in rows:
    image_url, link, date_time, message_text, views = row

    # Translate the message_text
    translated_text = transliterate(text=message_text, to_variant="latin")

    # Insert the row with translated text into the new database
    cursor_new.execute('''
    INSERT INTO scraped_data (image_url, link, date_time, message_text, views)
    VALUES (?, ?, ?, ?, ?)
    ''', (image_url, link, date_time, translated_text, views))

# Commit the changes and close both connections
conn_new.commit()
conn_original.close()
conn_new.close()

print("Translation completed and saved to new database: uybozor_translated.db")
