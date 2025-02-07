import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import random

# Configuration
base_url = "https://setupgame.ma/categorie-produit/pc-portable/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_page(page_url):
    """Scrape une page individuelle"""
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        return []
        
    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('div', class_='products__data-wrapper')
    page_data = []
    
    for product in products:
        try:
            name_tag = product.find('h3', class_='products__name').find('a')
            regular_price = product.find('h3', class_='products__regular-price')
            sale_price = product.find('h3', class_='products__sale-price')
            
            entry = {
                'Nom': name_tag.text.strip() if name_tag else 'Non disponible',
                'Prix': sale_price.text.strip() if sale_price else regular_price.text.strip(),
                'Prix réduit': regular_price.text.strip() if sale_price else 'N/A',
                'Lien': name_tag['href'] if name_tag else 'N/A',
                'Site web': 'Setup Game',
                'Catégorie': 'PC Portable',
                'Date de collecte': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            page_data.append(entry)
            
        except Exception as e:
            continue
    
    return page_data

# Initialisation
data = []
max_pages = 6

for page in range(1, max_pages + 1):
    if page == 1:
        page_url = base_url
    else:
        page_url = f"{base_url}page/{page}/"
    
    print(f"Scraping page {page}...")
    page_data = scrape_page(page_url)
    
    if not page_data:
        break
    
    data.extend(page_data)
    
    # Délai aléatoire entre 1-3 secondes
    time.sleep(random.uniform(1, 3))

# Export CSV
filename = f"setupgame_scrap_{datetime.now().strftime('%Y%m%d')}.csv"
with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Nom', 'Prix', 'Prix réduit', 'Lien', 'Site web', 'Catégorie', 'Date de collecte']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

print(f"Scraping terminé! {len(data)} produits trouvés sur {max_pages} pages.")