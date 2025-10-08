import requests
from bs4 import BeautifulSoup

# --- 1. The Stable URL ---
URL = 'https://www.bbc.com/sport/football' 

# -------------------------------------------------------------
# --- 2. Fetch the HTML Content ---
# -------------------------------------------------------------
print(f"Fetching data from: {URL}")
try:
    # Set a User-Agent header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    
    # Check for HTTP errors
    response.raise_for_status() 
    
    html_content = response.text
    print("Successfully downloaded HTML content.")

except requests.exceptions.RequestException as e:
    print(f"Error fetching URL: {e}")
    exit()

# -------------------------------------------------------------
# --- 3. Parse the HTML and Extract the Headline ---
# -------------------------------------------------------------
soup = BeautifulSoup(html_content, 'html.parser')

try:
    # --- FINAL STRATEGY: Try finding the first <h2> tag on the page. ---
    # Since H3 failed, H2 is the next most likely generic tag for a primary headline.
    headline_element = soup.find('h2')
    
    if headline_element:
        # Get all the text inside the element and clean up whitespace
        title = headline_element.text.strip()
        
        print("\n===================================")
        print(" EXTRACTED HEADLINE:")
        print(title)
        print("===================================")
    else:
        print("\n Extraction failed. Could not find any <h2> element on the page.")
        print("   The headline may now be in an <h1> or a <span>.")

except Exception as e:
    print(f"\nAn error occurred during parsing: {e}")