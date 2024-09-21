import requests
import sqlite3
import json

# URL to scrape
URL = "https://uysot.uz/_next/data/QpI4SLaIUKEw0kmripZaZ/uz/gorod-tashkent/kvartiri/musaffo-3-komnatnaya-kvartira-2.json"


def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: HTTP {response.status_code}")


def create_database():
    conn = sqlite3.connect('uysot_properties.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY,
        complex_id INTEGER,
        block_id INTEGER,
        apartment_id INTEGER,
        rooms_count INTEGER,
        block_floors_count INTEGER,
        area REAL,
        floor INTEGER,
        price REAL,
        total_price REAL,
        price_permission INTEGER,
        total_price_permission INTEGER,
        builder_id INTEGER,
        lat REAL,
        lng REAL,
        address TEXT,
        city TEXT,
        district TEXT,
        builder_name TEXT,
        complex_name TEXT
    )
    ''')
    conn.commit()
    return conn


def insert_data(conn, property_data):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO properties (
        id, complex_id, block_id, apartment_id, rooms_count, block_floors_count,
        area, floor, price, total_price, price_permission, total_price_permission,
        builder_id, lat, lng, address, city, district, builder_name, complex_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        property_data.get('id'),
        property_data.get('complex_id'),
        property_data.get('block_id'),
        property_data.get('apartment_id'),
        property_data.get('rooms_count'),
        property_data.get('block_floors_count'),
        property_data.get('area'),
        property_data.get('floor'),
        property_data.get('price'),
        property_data.get('total_price'),
        property_data.get('price_permission'),
        property_data.get('total_price_permission'),
        property_data.get('builder_id'),
        property_data.get('lat'),
        property_data.get('lng'),
        property_data.get('complex', {}).get('address'),
        property_data.get('complex', {}).get('city', {}).get('name'),
        property_data.get('complex', {}).get('district', {}).get('name'),
        property_data.get('builder', {}).get('name'),
        property_data.get('complex', {}).get('name')
    ))
    conn.commit()


def main():
    try:
        data = fetch_data(URL)
        conn = create_database()

        # Extract the list of properties from the JSON response
        properties = data['pageProps']['dehydratedState']['queries'][1]['state']['data']

        for property_data in properties:
            insert_data(conn, property_data)

        print(
            f"Successfully scraped and saved {len(properties)} properties to the database.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
