import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import random
import re
from urllib.parse import urlparse, parse_qs

#########################################
#   Définition du format commun         #
#########################################
# Les colonnes communes pour le CSV final
CSV_FIELDNAMES = [
    "Nom",          # Nom du produit
    "Prix",         # Prix affiché
    "Site web",     # Nom du site
    "Catégorie",    # Catégorie du produit
    "Date de collecte",  # Date et heure de récupération des données
    "Promotions",   # Informations sur les promotions (le cas échéant)
]

#########################################
#           Scraping Jumia.ma           #
#########################################

# Configuration pour Jumia
JUMIA_BASE_URL = "https://www.jumia.ma/ordinateurs-accessoires-informatique/"
JUMIA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_jumia_page(url):
    """
    Récupère les données des produits sur une page Jumia donnée.
    Normalise le résultat dans le format commun.
    """
    response = requests.get(url, headers=JUMIA_HEADERS)
    if response.status_code != 200:
        return []
        
    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('article', class_='prd')
    page_data = []
    
    for product in products:
        try:
            name_tag = product.find('h3', class_='name')
            category_tag = product.find('a', class_='core')
            promo_tag = product.find('div', class_='bdg _dsct')
            
            # Extraction des informations de base
            nom = name_tag.text.strip() if name_tag else 'Non disponible'
            prix = product.find('div', class_='prc').text.strip() if product.find('div', class_='prc') else 'Non disponible'
            categorie = category_tag.get('data-ga4-item_category4', 'Non spécifiée').strip() if category_tag else 'Non spécifiée'
            promotions = promo_tag.text.strip() if promo_tag else 'Aucune'
            
            # Normalisation dans le format commun
            entry = {
                "Nom": nom,
                "Prix": prix,
                "Site web": "Jumia.ma",
                "Catégorie": categorie,
                "Date de collecte": datetime.now().strftime("%Y-%m-%d"),
                "Promotions": promotions,
            }
            page_data.append(entry)
        except Exception as e:
            # En cas d'erreur sur un produit, on le passe
            continue
    
    return page_data

def scrape_jumia():
    """
    Scrape plusieurs pages de Jumia.ma.
    Pour cet exemple, on utilise 7 pages.
    """
    data = []
    current_page = 1
    total_pages = 7  # Vous pouvez mettre à jour cette valeur ou détecter dynamiquement
    
    print(f"Jumia : Détection de {total_pages} pages à scraper...")
    
    while current_page <= total_pages:
        page_url = f"{JUMIA_BASE_URL}?page={current_page}" if current_page > 1 else JUMIA_BASE_URL
        print(f"Jumia : Scraping page {current_page}/{total_pages}...")
        
        page_data = scrape_jumia_page(page_url)
        if not page_data:
            break
        
        data.extend(page_data)
        time.sleep(random.uniform(1, 3))  # Pause entre les requêtes
        current_page += 1

    return data

#########################################
#           Scraping UltraPC.ma         #
#########################################

def scrape_ultrapc():
    """
    Récupère les informations des produits depuis UltraPC.ma et les normalise.
    """
    url = "https://www.ultrapc.ma/19-pc-portables"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("UltraPC : Échec de la récupération de la page web")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.find_all("div", class_="product-block clearfix")
    results = []
    
    for product in products:
        try:
            name_tag = product.find("h3", class_="product-title")
            nom = name_tag.text.strip() if name_tag else "N/A"
            
            price_tag = product.find("span", class_="price")
            prix = price_tag.text.strip() if price_tag else "N/A"
            
            
            promo_tag = product.find("ul", class_="product-flags")
            promotions = promo_tag.text.strip() if promo_tag else "Aucune"
            
            entry = {
                "Nom": nom,  # Normalisation : Utilisation de "Nom" au lieu de "Nom du produit"
                "Prix": prix,
                "Site web": "UltraPC.ma",
                "Catégorie": "Laptops",
                "Date de collecte": datetime.now().strftime("%Y-%m-%d"),
                "Promotions": promotions,
            }
            results.append(entry)
        except Exception as e:
            continue
    
    return results

#########################################
#          Scraping SetupGame.ma        #
#########################################

# Configuration pour SetupGame
SETUPGAME_BASE_URL = "https://setupgame.ma/categorie-produit/pc-portable/"
SETUPGAME_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def parse_price(price_str):
    """
    Extrait la valeur numérique d'une chaîne de caractères représentant un prix.
    Par exemple : "8,999.00MAD" → 8999.00 (float)
    """
    if not price_str:
        return 0.0
    # Supprime espaces et insécables
    price_str = price_str.replace("\u202f", "").replace(" ", "")
    # Supprime les lettres (ex: "MAD")
    price_str = re.sub(r"[A-Za-z]", "", price_str)
    # Supprime les virgules servant de séparateur de milliers
    price_str = price_str.replace(",", "")
    try:
        return float(price_str)
    except ValueError:
        return 0.0

def scrape_setupgame_page(page_url):
    """
    Récupère les données des produits sur une page donnée de SetupGame.ma
    et les normalise dans le format commun.
    Pour chaque produit :
      - Si un prix de vente est disponible, le prix affiché est le prix de vente,
        et le champ Promotions contiendra le montant de la remise (prix régulier - prix de vente).
      - Sinon, le prix affiché est le prix régulier et Promotions vaut "Aucune".
    """
    response = requests.get(page_url, headers=SETUPGAME_HEADERS)
    if response.status_code != 200:
        return []
        
    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('div', class_='products__data-wrapper')
    page_data = []
    
    for product in products:
        try:
            name_tag_wrapper = product.find('h3', class_='products__name')
            name_tag = name_tag_wrapper.find('a') if name_tag_wrapper else None
            nom = name_tag.text.strip() if name_tag else 'Non disponible'
            
            regular_price_tag = product.find('h3', class_='products__regular-price')
            sale_price_tag = product.find('h3', class_='products__sale-price')
            
            if sale_price_tag:
                # En cas de promotion, on utilise le prix de vente et on calcule la remise.
                sale_price_text = sale_price_tag.text.strip()
                # Si le prix régulier n'est pas trouvé, on considère qu'il est identique au prix de vente.
                regular_price_text = regular_price_tag.text.strip() if regular_price_tag else sale_price_text
                
                sale_price_value = parse_price(sale_price_text)
                regular_price_value = parse_price(regular_price_text)
                discount_value = regular_price_value - sale_price_value
                
                prix = f"{sale_price_value:.2f} MAD"
                promotions = f"-{discount_value:.2f} MAD"
            else:
                # Pas de promotion : on utilise le prix régulier.
                if regular_price_tag:
                    regular_price_text = regular_price_tag.text.strip()
                    regular_price_value = parse_price(regular_price_text)
                    prix = f"{regular_price_value:.2f} MAD"
                else:
                    prix = "Non disponible"
                promotions = "Aucune"
            
            entry = {
                "Nom": nom,
                "Prix": prix,
                "Site web": "SetupGame.ma",
                "Catégorie": "Laptops",
                "Date de collecte": datetime.now().strftime("%Y-%m-%d"),
                "Promotions": promotions,
            }
            page_data.append(entry)
        except Exception as e:
            continue
    
    return page_data

def scrape_setupgame():
    """
    Scrape les produits sur plusieurs pages de SetupGame.ma et retourne les données normalisées.
    """
    data = []
    max_pages = 6  # Nombre de pages à scraper
    
    for page in range(1, max_pages + 1):
        page_url = SETUPGAME_BASE_URL if page == 1 else f"{SETUPGAME_BASE_URL}page/{page}/"
        print(f"Setup Game : Scraping page {page}...")
        page_data = scrape_setupgame_page(page_url)
        if not page_data:
            break
        data.extend(page_data)
        time.sleep(random.uniform(1, 3))
    
    return data

#########################################
#         Fonction d'export CSV         #
#########################################

def export_to_csv(all_data, filename=None):
    """
    Exporte l'ensemble des données dans un seul fichier CSV.
    Les données doivent être au format commun défini par CSV_FIELDNAMES.
    """
    if filename is None:
        filename = f"all_products.csv"
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"Export terminé! {len(all_data)} produits ont été enregistrés dans {filename}")

#########################################
#       Fonction principale (main)      #
#########################################

def main():
    all_products = []  # Liste pour stocker toutes les données

    # Scraping de Jumia.ma
    print("Démarrage du scraping pour Jumia.ma...")
    jumia_data = scrape_jumia()
    all_products.extend(jumia_data)
    
    # Scraping de UltraPC.ma
    print("\nDémarrage du scraping pour UltraPC.ma...")
    ultrapc_data = scrape_ultrapc()
    all_products.extend(ultrapc_data)
    
    # Scraping de SetupGame.ma
    print("\nDémarrage du scraping pour SetupGame.ma...")
    setupgame_data = scrape_setupgame()
    all_products.extend(setupgame_data)
    
    # Export des données de tous les sites dans un seul fichier CSV
    export_to_csv(all_products)

if __name__ == "__main__":
    main()
