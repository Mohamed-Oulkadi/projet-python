

import re
import csv
from datetime import datetime

# Définition des colonnes finales du CSV
CSV_FIELDNAMES = [
    "Nom",
    "Prix",
    "Site web",
    "Catégorie",
    "Date de collecte",
    "Promotions",
]

# --- Partie 1 : Normalisation du nom du produit ---

def custom_normalize_product_name(name):
    
    # Suppression des espaces superflus et des guillemets éventuels
    normalized = name.strip().strip('"')
    
    # Suppression des détails techniques commençant par " i" suivi d'un chiffre (ex. " i5-8265U/8GB/256GB SSD,")
    normalized = re.sub(r"\s+i\d[-\w/]*.*$", "", normalized)
    
    # Suppression des suffixes du type " -noir" en fin de chaîne
    normalized = re.sub(r"\s*-\S+$", "", normalized)
    
    # Découpage par délimiteurs courants pour ne garder que la partie principale
    delimiters = [" – ", " - ", ",", "/", "+"]
    for delim in delimiters:
        if delim in normalized:
            normalized = normalized.split(delim)[0].strip()
    
    return normalized

# --- Partie 2 : Extraction du prix (sans conversion, conservation en MAD) ---

def extract_price(price_str):
    """
    Extrait la valeur numérique d'une chaîne de caractères représentant un prix.
    Par exemple : "1,549.00 Dhs" ou "13,299.00MAD" → 1549.00 ou 13299.00 (float)
    """
    if not price_str:
        return None
    # Remplacer les espaces insécables et normaux
    price_str = price_str.replace("\u202f", "").replace(" ", "")
    # Recherche d'un motif numérique
    match = re.search(r"([\d.,]+)", price_str)
    if match:
        num_str = match.group(1)
        # Supprimer les virgules servant de séparateur de milliers
        num_str = num_str.replace(",", "")
        try:
            return float(num_str)
        except ValueError:
            return None
    return None

# --- Partie 3 : Nettoyage et préparation des données ---

def clean_data(products):
    """
    Parcourt la liste de produits (dictionnaires) et réalise le nettoyage suivant :
      - Suppression des produits dont le nom est vide ou indique "Non disponible".
      - Uniformisation du nom à l'aide de custom_normalize_product_name.
      - Extraction du prix (en MAD) et stockage dans une clé interne pour la comparaison.
    Retourne la liste nettoyée.
    """
    cleaned = []
    for prod in products:
        # Récupérer et nettoyer le nom
        name = prod.get("Nom", "").strip()
        if not name or name.lower() == "non disponible":
            continue  # Ignorer les enregistrements sans nom pertinent
        
        # Uniformiser le nom du produit
        norm_name = custom_normalize_product_name(name)
        
        # Extraction du prix numérique
        raw_price = prod.get("Prix", "")
        price_value = extract_price(raw_price)
        
        # Mise à jour de l'enregistrement avec le nom normalisé et stockage du prix numérique dans une clé interne
        prod["Nom"] = norm_name
        prod["Prix"] = raw_price  # On conserve la valeur textuelle d'origine (ex: "1,549.00 Dhs")
        prod["_price_numeric"] = price_value  # Clé interne pour comparaison lors de la suppression des doublons
        
        cleaned.append(prod)
    return cleaned

def remove_duplicates(products):
    
    unique_products = {}
    for prod in products:
        key = prod["Nom"]
        current_price = prod.get("_price_numeric")
        if key in unique_products:
            existing = unique_products[key]
            existing_price = existing.get("_price_numeric")
            if current_price is not None and (existing_price is None or current_price < existing_price):
                unique_products[key] = prod
        else:
            unique_products[key] = prod
    # Suppression de la clé interne avant export
    for prod in unique_products.values():
        if "_price_numeric" in prod:
            del prod["_price_numeric"]
    return list(unique_products.values())

# --- Partie 4 : Lecture et export des données CSV ---

def read_csv_data(filename):
    """
    Lit les données d'un fichier CSV et retourne une liste de dictionnaires.
    """
    products = []
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products.append(row)
    return products

def export_cleaned_data(products, filename=None):
    """
    Exporte les données nettoyées dans un fichier CSV.
    """
    if filename is None:
        filename = f"all_products_cleaned_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(products)
    print(f"Export terminé : {len(products)} produits enregistrés dans {filename}")

# --- Partie 5 : Pipeline principal ---

def main():
    input_filename = "all_products.csv"  # Nom du fichier CSV source (à adapter)
    print(f"Lecture des données depuis {input_filename}...")
    all_products = read_csv_data(input_filename)
    
    print("Nettoyage des données...")
    cleaned_data = clean_data(all_products)
    
    print("Suppression des doublons...")
    unique_data = remove_duplicates(cleaned_data)
    
    print("Export des données nettoyées...")
    export_cleaned_data(unique_data)

if __name__ == "__main__":
    main()
