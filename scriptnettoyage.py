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
    
    # Suppression des détails techniques commençant par " i" suivi d'un chiffre
    normalized = re.sub(r"\s+i\d[-\w/]*.*$", "", normalized)
    
    # Suppression des suffixes du type " -noir" en fin de chaîne
    normalized = re.sub(r"\s*-\S+$", "", normalized)
    
    # Découpage par délimiteurs courants pour ne garder que la partie principale
    delimiters = [" – ", " - ", ",", "/", "+"]
    for delim in delimiters:
        if delim in normalized:
            normalized = normalized.split(delim)[0].strip()
    
    return normalized

# --- Partie 2 : Extraction et conversion du prix (toujours en MAD) ---

def extract_price(price_str):
    """
    Extrait la valeur numérique d'une chaîne représentant un prix et renvoie un tuple :
      (valeur numérique, chaîne formatée en MAD)
    Par exemple : "1,549.00 Dhs" ou "13,299.00MAD" → (1549.00, "1549.00 MAD")
    """
    if not price_str:
        return None

    # Remplacer les espaces insécables et normaux
    price_str = price_str.replace("\u202f", "").replace(" ", "")
    
    # Recherche d'un motif numérique suivi éventuellement de "Dhs" ou "MAD"
    match = re.search(r"([\d.,]+)\s*(Dhs|MAD)?", price_str, re.IGNORECASE)
    
    if match:
        num_str = match.group(1)
        # Supprimer les virgules servant de séparateur de milliers
        num_str = num_str.replace(",", "")
        
        try:
            price_value = float(num_str)
            formatted_price = f"{price_value:.2f} MAD"  # Conversion en MAD
            return price_value, formatted_price
        except ValueError:
            return None
    return None

# --- Partie 3 : Nettoyage et préparation des données ---

def clean_data(products):
    """
    Parcourt la liste de produits (dictionnaires) et réalise le nettoyage suivant :
      - Suppression des produits dont le nom est vide ou indique "Non disponible".
      - Uniformisation du nom à l'aide de custom_normalize_product_name.
      - Formatage de la date de collecte au format ISO (YYYY-MM-DD).
      - Extraction du prix et conversion en MAD.
      - Application du nettoyage sur le champ Promotions.
      - Stockage d'une clé interne pour la comparaison du prix lors de la suppression des doublons.
    Retourne la liste nettoyée.
    """
    cleaned = []
    for prod in products:
        # Récupération et nettoyage du nom
        name = prod.get("Nom", "").strip()
        if not name or name.lower() == "non disponible":
            continue  # Ignorer les enregistrements sans nom pertinent
        
        # Uniformiser le nom du produit
        norm_name = custom_normalize_product_name(name)
        
        # Formatage de la date de collecte
        raw_date = prod.get("Date de collecte", "").strip()
        formatted_date = raw_date  # Valeur par défaut
        try:
            # Tenter d'interpréter la date au format mois/jour/année (ex: "12/8/2024")
            dt = datetime.strptime(raw_date, "%m/%d/%Y")
            formatted_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                # Sinon, tenter le format ISO (ex: "2024-12-08")
                dt = datetime.strptime(raw_date, "%Y-%m-%d")
                formatted_date = dt.strftime("%Y-%m-%d")
            except Exception:
                formatted_date = raw_date
        
        prod["Date de collecte"] = formatted_date

        # Extraction et conversion du prix
        raw_price = prod.get("Prix", "")
        extraction = extract_price(raw_price)
        if extraction is None:
            price_numeric = None
            price_formatted = raw_price  # Conserver la valeur d'origine si extraction impossible
        else:
            price_numeric, price_formatted = extraction
        
        # Nettoyage du champ Promotions (suppression des espaces insécables et normaux)
        raw_promotions = prod.get("Promotions", "")
        promotions_clean = raw_promotions.replace("\u202f", "").replace(" ", "")
        
        # Mise à jour de l'enregistrement avec les valeurs nettoyées
        prod["Nom"] = norm_name
        prod["Prix"] = price_formatted  # Exemple : "349.00 MAD"
        prod["Promotions"] = promotions_clean
        prod["_price_numeric"] = price_numeric  # Clé interne pour comparaison
        
        cleaned.append(prod)
    return cleaned

def remove_duplicates(products):
    """
    Supprime les doublons en gardant pour chaque produit (identifié par le nom normalisé,
    la date de collecte ET le site web) l'enregistrement ayant le prix le plus bas.
    
    Ainsi, deux enregistrements du même produit avec des dates ou des sites web différents
    ne seront pas considérés comme doublons.
    """
    unique_products = {}
    for prod in products:
        # Utiliser comme clé le tuple (Nom, Date de collecte, Site web)
        key = (prod["Nom"], prod["Date de collecte"], prod["Site web"])
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
        filename = "all_products_cleaned.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(products)
    print(f"Export terminé : {len(products)} produits enregistrés dans {filename}")

# --- Partie 5 : Pipeline principal ---

def main():
    input_filename = "all_products_20250208.csv"  # Nom du fichier CSV source
    print(f"Lecture des données depuis {input_filename}...")
    all_products = read_csv_data(input_filename)
    
    print("Nettoyage des données...")
    cleaned_data = clean_data(all_products)
    
    print("Suppression des doublons (en tenant compte du nom, de la date de collecte et du site web)...")
    unique_data = remove_duplicates(cleaned_data)
    
    print("Export des données nettoyées...")
    export_cleaned_data(unique_data)

if __name__ == "__main__":
    main()
