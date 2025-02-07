import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import random
from urllib.parse import urlparse, parse_qs

# Configuration
base_url = "https://www.jumia.ma/ordinateurs-accessoires-informatique/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_total_pages(soup):
    """Extrait le nombre total de pages depuis la pagination"""
    pagination = soup.find('div', class_='pg-w -ptm -pbxl')
    if not pagination:
        return 1
    
    pages = pagination.find_all('a', href=True)
    page_numbers = []
    
    for page in pages:
        href = page['href']
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        page_num = params.get('page', [''])[0]
        if page_num.isdigit():
            page_numbers.append(int(page_num))
    
    return max(page_numbers) if page_numbers else 1

def scrape_page(url):
    """Scrape les produits d'une page donnée"""
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
        
    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('article', class_='prd')
    page_data = []
    
    for product in products:
        try:
            entry = {
                'Nom': product.find('h3', class_='name').text.strip(),
                'Prix': product.find('div', class_='prc').text.strip(),
                'Site web': 'Jumia.ma',
                'Catégorie': product.find('a', class_='core').get('data-ga4-item_category4', 'Non spécifiée').strip(),
                'Date de collecte': datetime.now().strftime("%Y-%m-%d"),
                'Promotions': (promo_tag.text.strip() if (promo_tag := product.find('div', class_='bdg _dsct')) else 'Aucune')
            }
            page_data.append(entry)
        except Exception as e:
            continue
    
    return page_data

# Initialisation
data = []
current_page = 1

# Récupération de la première page pour détecter la pagination
response = requests.get(base_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
total_pages = 7

print(f"Détection de {total_pages} pages à scraper...")

# Scraping de toutes les pages
while current_page <= total_pages:
    page_url = f"{base_url}?page={current_page}" if current_page > 1 else base_url
    print(f"Scraping page {current_page}/{total_pages}...")
    
    page_data = scrape_page(page_url)
    if not page_data:
        break  # Arrêt si page vide
    
    data.extend(page_data)
    
    # Délai aléatoire entre 1 et 3 secondes
    time.sleep(random.uniform(1, 3))
    current_page += 1

# Export CSV
filename = f"jumia_scrap_{datetime.now().strftime('%Y%m%d')}.csv"
with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Nom', 'Prix', 'Site web', 'Catégorie', 'Date de collecte', 'Promotions']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

print(f"Scraping terminé! {len(data)} produits exportés dans {filename}")