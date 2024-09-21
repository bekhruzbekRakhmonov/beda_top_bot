import requests
import json
import sqlite3
from datetime import datetime


def create_database():
    conn = sqlite3.connect('uybor_listings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS listings
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  operation_type TEXT,
                  category_id INTEGER,
                  sub_category_id INTEGER,
                  description TEXT,
                  price REAL,
                  price_currency TEXT,
                  address TEXT,
                  region_id INTEGER,
                  district_id INTEGER,
                  street_id INTEGER,
                  zone_id INTEGER,
                  room TEXT,
                  lat REAL,
                  lng REAL,
                  square REAL,
                  floor INTEGER,
                  floor_total INTEGER,
                  is_new_building BOOLEAN,
                  repair TEXT,
                  foundation TEXT,
                  created_at TEXT,
                  updated_at TEXT,
                  media_count INTEGER,
                  views INTEGER,
                  clicks INTEGER,
                  favorites INTEGER)''')

    # Create a new table for storing photo URLs
    c.execute('''CREATE TABLE IF NOT EXISTS photos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  listing_id INTEGER,
                  photo_url TEXT,
                  FOREIGN KEY (listing_id) REFERENCES listings (id))''')

    conn.commit()
    return conn


def scrape_and_save_uybor_api():
    url = "https://api.uybor.uz/api/v1/listings"
    params = {
        "mode": "search",
        "includeFeatured": "true",
        "limit": 100,
        "embed": "category,subCategory,residentialComplex,region,city,district,zone,street,metro,media,user,user.avatar,user.organization,user.organization.logo",
        "order": "upAt",
        "operationType__eq": "sale",
        "priceCurrency__eq": "usd",
        "offset": 0
    }

    conn = create_database()
    c = conn.cursor()

    total_saved = 0

    try:
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data['results']:
                break

            for listing in data['results']:
                c.execute('''INSERT OR REPLACE INTO listings
                             (id, user_id, operation_type, category_id, sub_category_id,
                              description, price, price_currency, address, region_id,
                              district_id, street_id, zone_id, room, lat, lng, square,
                              floor, floor_total, is_new_building, repair, foundation,
                              created_at, updated_at, media_count, views, clicks, favorites)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (listing['id'],
                           listing['userId'],
                           listing['operationType'],
                           listing['categoryId'],
                           listing.get('subCategoryId'),
                           listing['description'],
                           listing['price'],
                           listing['priceCurrency'],
                           listing['address'],
                           listing.get('regionId'),
                           listing.get('districtId'),
                           listing.get('streetId'),
                           listing.get('zoneId'),
                           listing.get('room'),
                           listing['lat'],
                           listing['lng'],
                           listing.get('square'),
                           listing.get('floor'),
                           listing.get('floorTotal'),
                           listing.get('isNewBuilding'),
                           listing.get('repair'),
                           listing.get('foundation'),
                           listing['createdAt'],
                           listing['updatedAt'],
                           len(listing.get('media', [])),
                           listing['views'],
                           listing['clicks'],
                           listing['favorites']))

                # Save photo URLs
                for media in listing.get('media', []):
                    c.execute('''INSERT INTO photos (listing_id, photo_url)
                                 VALUES (?, ?)''', (listing['id'], media['url']))

            conn.commit()
            total_saved += len(data['results'])
            print(f"Saved {total_saved} listings so far...")

            params['offset'] += params['limit']

            if total_saved >= data['total']:
                break

        print(
            f"Successfully saved all {total_saved} listings to the database.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
    except json.JSONDecodeError:
        print("Failed to parse the JSON response")
    except KeyError as e:
        print(f"Expected key not found in the response: {e}")
    except sqlite3.Error as e:
        print(f"An error occurred while working with the database: {e}")
    finally:
        if conn:
            conn.close()


def display_data_summary():
    try:
        conn = sqlite3.connect('uybor_listings.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM listings")
        count = c.fetchone()[0]
        print(f"\nTotal listings in database: {count}")

        c.execute("SELECT MIN(price), MAX(price) FROM listings")
        min_price, max_price = c.fetchone()
        print(f"Price range: ${min_price} - ${max_price}")

        c.execute(
            "SELECT MIN(square), MAX(square) FROM listings WHERE square IS NOT NULL")
        min_square, max_square = c.fetchone()
        print(f"Square range: {min_square} - {max_square} sq.m")

        c.execute(
            "SELECT DISTINCT foundation FROM listings WHERE foundation IS NOT NULL")
        foundations = [row[0] for row in c.fetchall()]
        print(f"Building materials: {', '.join(foundations)}")

        c.execute("SELECT COUNT(*) FROM photos")
        photo_count = c.fetchone()[0]
        print(f"Total photo URLs saved: {photo_count}")

    except sqlite3.Error as e:
        print(f"An error occurred while querying the database: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    scrape_and_save_uybor_api()
    display_data_summary()
