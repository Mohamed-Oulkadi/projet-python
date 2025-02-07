import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv

def scrape_ultrapc():
    url = "https://www.ultrapc.ma/19-pc-portables"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to retrieve the webpage")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.find_all("div", class_="product-block clearfix")
    
    results = []
    for product in products:
        name_tag = product.find("h3", class_="product-title")
        name = name_tag.text.strip() if name_tag else "N/A"
        
        price_tag = product.find("span", class_="price")
        price = price_tag.text.strip() if price_tag else "N/A"
        
        link_tag = name_tag.find("a") if name_tag else None
        link = link_tag["href"] if link_tag else "N/A"
        
        promo_tag = product.find("ul", class_="product-flags")
        promotion = promo_tag.text.strip() if promo_tag else "No Promotion"
        
        results.append({
            "Nom du produit": name,
            "Prix": price,
            "Site web": "UltraPC.ma",
            "Catégorie": "PC Portables",
            "Date de collecte": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Promotions": promotion,
            "Lien": link
        })
    
    return results

def save_to_csv(data, filename="ultrapc_products.csv"):
    keys = data[0].keys() if data else []
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")

# Test the scraper
data = scrape_ultrapc()
save_to_csv(data)
