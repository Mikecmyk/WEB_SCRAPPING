import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
import json
import csv

# --- Configuration ---
BASE_CURRENCY = 'GBP'
TARGET_CURRENCY = 'KES'
# ExchangeRate-API Open Access Endpoint for Base currency GBP
API_URL = f"https://open.er-api.com/v6/latest/{BASE_CURRENCY}"

# ==============================================================================
# 1. SCRAPING AND CLEANING (Steps 1 & 2)
# ==============================================================================

def scrape_products(url="http://books.toscrape.com/"):
    """Scrapes product name and price from the target website."""
    product_data = []

    print(f"Attempting to scrape from: {url}")
    
    try:
        # Step 7: Error handling for connection issues
        response = requests.get(url, timeout=10)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f" Connection Error or Request Failed: {e}")
        return product_data

    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('article', class_='product_pod')

    # Scrape prices of at least 10 products
    for product in products[:10]:
        name_tag = product.find('h3').find('a')
        product_name = name_tag['title'].strip() if name_tag else "N/A"
        
        price_tag = product.find('p', class_='price_color')
        original_price_str = price_tag.text.strip() if price_tag else "£0.00"

        # Step 2: Clean the price (remove '£' and convert to float)
        cleaned_price_str = re.sub(r'[^\d.]', '', original_price_str)
        
        try:
            original_price_float = float(cleaned_price_str)
        except ValueError:
            original_price_float = 0.0
            print(f" Warning: Could not convert price for {product_name}. Using 0.0.")

        product_data.append({
            'name': product_name,
            'original_currency': 'GBP',
            'original_price': original_price_float
        })

    print(f" Successfully scraped {len(product_data)} products.")
    return product_data

# ==============================================================================
# 2. CURRENCY CONVERSION (Steps 3 & 4)
# ==============================================================================

def get_exchange_rate(base_currency, target_currency):
    """Fetches the latest exchange rate from the API, with error handling."""
    
    MOCK_RATE = 175.00 # Fallback rate
    conversion_rate = MOCK_RATE
    last_updated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\nStep 3: Attempting to fetch live rate from {API_URL}...")

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['result'] == 'success':
            rates = data.get('rates', {})
            if target_currency in rates:
                conversion_rate = rates[target_currency]
                # Add timestamp for when conversion was done
                last_updated_time = datetime.fromtimestamp(data['time_last_update_unix']).strftime("%Y-%m-%d %H:%M:%S")
                print(f" Success! Live 1 {BASE_CURRENCY} = {conversion_rate:.4f} {TARGET_CURRENCY}")
            else:
                print(f" Warning: Target currency {target_currency} not found. Using mock rate: {MOCK_RATE}")
        else:
            print(f" Warning: API request failed. Using mock rate: {MOCK_RATE}. Message: {data.get('error', 'Unknown Error')}")
            
    except requests.exceptions.RequestException as e:
        print(f" Connection/API Error: {e}. Using mock rate: {MOCK_RATE}")

    return conversion_rate, last_updated_time

def convert_prices(products_list):
    """Converts the prices for all products in the list."""
    
    rate, timestamp = get_exchange_rate(BASE_CURRENCY, TARGET_CURRENCY)
    
    # Step 4: Convert prices and save the data
    for product in products_list:
        converted_price = product['original_price'] * rate
        
        product['converted_currency'] = TARGET_CURRENCY
        product['converted_price'] = round(converted_price, 2)
        product['conversion_rate'] = round(rate, 4)
        product['conversion_timestamp'] = timestamp
        
    return products_list, timestamp

# ==============================================================================
# 3. DISPLAY AND SAVE (Steps 5 & 6)
# ==============================================================================

def display_data_table(data, timestamp):
    """Displays the product data in a readable table format using pandas."""
    
    print("\n" + "="*80)
    print("       Product Prices Scraped & Currency Converted (GBP to KES) 🇰🇪")
    print(f"      Last Conversion Time: {timestamp}")
    print("="*80)

    if not data:
        print("No data to display.")
        return

    df = pd.DataFrame(data)
    
    # Select, rename, and format columns for display
    df_display = df[['name', 'original_price', 'converted_price', 'conversion_rate']].copy()
    df_display.columns = ['Product Name', 'Price (GBP)', 'Price (KES)', 'Rate (1 GBP)']
    df_display.set_index('Product Name', inplace=True)
    
    df_display['Price (GBP)'] = df_display['Price (GBP)'].apply(lambda x: f"£{x:.2f}")
    df_display['Price (KES)'] = df_display['Price (KES)'].apply(lambda x: f"KES {x:,.2f}")
    
    print(df_display.to_markdown(numalign="left", stralign="left"))
    print("="*80 + "\n")

def save_to_csv(data, filename='product_prices_converted.csv'):
    """Saves the list of dictionaries to a CSV file."""
    if not data:
        print(f"Cannot save to {filename}: Data list is empty.")
        return
        
    fieldnames = data[0].keys()
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f" Data successfully saved to {filename}")
    except IOError as e:
        print(f" I/O Error when writing to CSV: {e}")

def save_to_json(data, filename='product_prices_converted.json'):
    """Saves the list of dictionaries to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=4)
        print(f" Data successfully saved to {filename}")
    except IOError as e:
        print(f" I/O Error when writing to JSON: {e}")

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================

if __name__ == "__main__":
    # 1. Execute the scraping
    scraped_products = scrape_products()
    
    if scraped_products:
        # 2. Convert Prices
        final_product_data, final_timestamp = convert_prices(scraped_products)
        
        # 3. Display Data
        display_data_table(final_product_data, final_timestamp)

        # 4. Save Data
        save_to_csv(final_product_data)
        save_to_json(final_product_data)
    else:
        print("\nScript terminated because no product data was scraped.")