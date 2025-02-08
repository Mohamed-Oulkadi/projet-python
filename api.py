from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

###########################################
# Chargement et nettoyage des données
###########################################

# Lecture du fichier CSV (assurez-vous que le fichier 'all_products_cleaned.csv' se trouve dans le même répertoire)
# Le CSV doit contenir les colonnes suivantes en entête : 
# Nom,Prix,Site web,Catégorie,Date de collecte,Promotions
df = pd.read_csv('all_products_cleaned.csv')

# Nettoyage de la colonne 'Prix'
# - Suppression du texte " MAD"
# - Remplacement de la virgule par un point (si nécessaire)
df['Prix'] = (df['Prix']
              .str.replace(' MAD', '', regex=False)
              .str.replace('MAD', '', regex=False)
              .str.replace(',', '.', regex=False))
df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')

# Fonction de conversion pour la colonne 'Promotions'
def convert_discount(val):
    if pd.isnull(val) or val.strip().lower() == 'aucune' or val.strip() == '':
        return 0.0
    # Supprimer "MAD", les espaces et convertir la virgule en point
    val = val.replace('MAD', '').replace(' ', '').replace(',', '.')
    try:
        return float(val)
    except Exception:
        return 0.0

# Création d'une colonne numérique 'Discount' pour faciliter le filtrage
df['Discount'] = df['Promotions'].apply(convert_discount)

# Conversion de la colonne 'Date de collecte' en type datetime
df['Date de collecte'] = pd.to_datetime(df['Date de collecte'], format='%Y-%m-%d', errors='coerce')

###########################################
# Endpoints de l'API
###########################################

@app.route('/lowest_price', methods=['GET'])
def get_lowest_price():
    """
    Récupère le prix le plus bas d’un produit.
    Paramètre GET attendu : product (ex. "LENOVO V15")
    Renvoie en JSON le nom du produit, le site web et le prix le plus bas.
    """
    product_name = request.args.get('product', default='', type=str)
    if not product_name:
        return jsonify({'error': 'Le paramètre "product" est requis.'}), 400

    # Filtrer les produits dont le nom contient la chaîne recherchée (insensible à la casse)
    df_product = df[df['Nom'].str.contains(product_name, case=False, na=False)]
    if df_product.empty:
        return jsonify({'error': f'Produit "{product_name}" non trouvé.'}), 404

    # Sélectionner la ligne ayant le prix minimum
    lowest = df_product.loc[df_product['Prix'].idxmin()]
    response = {
        'Nom': lowest['Nom'],
        'Site web': lowest['Site web'],
        'Prix': lowest['Prix']
    }
    return jsonify(response)


@app.route('/promotions', methods=['GET'])
def get_promotions_by_category():
    """
    Liste les promotions actuelles par catégorie.
    Une promotion est considérée présente lorsque la valeur 'Discount' est différente de 0.
    Renvoie un dictionnaire où chaque clé est une catégorie et la valeur est une liste de produits en promotion.
    """
    # Filtrer les produits en promotion
    df_promo = df[df['Discount'] != 0]

    promo_dict = {}
    for category, group in df_promo.groupby('Catégorie'):
        promo_list = []
        for _, row in group.iterrows():
            promo_list.append({
                'Nom': row['Nom'],
                'Site web': row['Site web'],
                'Prix': row['Prix'],
                'Promotions': row['Promotions'],
                'Date de collecte': row['Date de collecte'].strftime('%Y-%m-%d') if pd.notnull(row['Date de collecte']) else None
            })
        promo_dict[category] = promo_list

    return jsonify(promo_dict)


###########################################
# Lancement de l'API
###########################################
if __name__ == '__main__':
    app.run(debug=True)

#pour tester avec un produit: http://127.0.0.1:5000/lowest_price?product=LENOVO%20V15
#pour tester les promos : http://127.0.0.1:5000/promotions 

