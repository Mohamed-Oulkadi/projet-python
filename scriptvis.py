import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Paramétrer Seaborn pour des graphiques esthétiques
sns.set(style="whitegrid")

###########################################
# 1. Chargement et nettoyage des données
###########################################

# Charger le fichier CSV (assurez-vous que le fichier "all_products_cleaned.csv" se trouve dans le même répertoire)
df = pd.read_csv('all_products_cleaned.csv')

# Vérifiez que le fichier possède bien ces colonnes : 
# Nom, Prix, Site web, Catégorie, Date de collecte, Promotions

# Nettoyage de la colonne 'Prix'
df['Prix'] = df['Prix'].str.replace(' MAD', '', regex=False).str.replace('MAD', '', regex=False)
df['Prix'] = df['Prix'].str.replace(',', '.', regex=False)
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

# Créer une nouvelle colonne 'Discount' à partir de 'Promotions'
df['Discount'] = df['Promotions'].apply(convert_discount)

# Conversion de la colonne 'Date de collecte' en type datetime
df['Date de collecte'] = pd.to_datetime(df['Date de collecte'], format='%Y-%m-%d', errors='coerce')


###########################################
# 2. Comparaison des prix entre plateformes
###########################################

# 2.1 Comparaison globale par produit et par site
price_comparison = df.groupby(['Nom', 'Site web'])['Prix'].mean().reset_index()
price_pivot = price_comparison.pivot(index='Nom', columns='Site web', values='Prix')
price_pivot['Price_Ecart'] = price_pivot.max(axis=1) - price_pivot.min(axis=1)


# 2.2 Comparaison par date de collecte (pour les produits présents sur plusieurs plateformes)
pivot = df.pivot_table(index=['Nom', 'Date de collecte'], columns='Site web', values='Prix', aggfunc='first')
# Garder uniquement les lignes où au moins 2 plateformes sont renseignées
pivot = pivot.dropna(thresh=2)
if pivot.empty:
    print("Données insuffisantes pour une comparaison entre plusieurs plateformes.")
else:
    pivot['Prix_min'] = pivot.min(axis=1)
    pivot['Prix_max'] = pivot.max(axis=1)
    pivot['Écart'] = pivot['Prix_max'] - pivot['Prix_min']
    
    # Sélectionner les 10 enregistrements avec le plus grand écart de prix
    top10 = pivot.sort_values(by='Écart', ascending=False).head(10)
    if top10.empty:
        print("Aucun enregistrement avec plusieurs plateformes pour comparaison.")
    else:
        # Réinitialiser l'index pour combiner Nom et Date de collecte dans un label
        top10 = top10.reset_index()
        top10["Produit_date"] = top10["Nom"] + " (" + top10["Date de collecte"].astype(str) + ")"
        top10 = top10.set_index("Produit_date")
        # On retire les colonnes de synthèse pour ne garder que les prix par site
        top10_prices = top10.drop(columns=['Nom', 'Date de collecte', 'Prix_min', 'Prix_max', 'Écart'])
        
        # Affichage du diagramme à barres
        top10_prices.plot(kind='bar', figsize=(12, 8))
        plt.title("Comparaison des prix sur différentes plateformes\npour les 10 enregistrements avec le plus grand écart")
        plt.xlabel("Produit (Date de collecte)")
        plt.ylabel("Prix (MAD)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

###########################################
# 3. Identification des promotions
###########################################

# 3.a) Compter les promotions par catégorie (Promotion présente si Discount != 0)
promo_counts = df[df['Discount'] != 0].groupby('Catégorie').size().reset_index(name='Promo_Count')


# Diagramme en barres pour le nombre de promotions par catégorie
plt.figure(figsize=(8,6))
sns.barplot(data=promo_counts, x='Catégorie', y='Promo_Count', hue='Catégorie', palette="viridis", legend=False)
plt.title("Nombre de promotions par catégorie")
plt.xlabel("Catégorie")
plt.ylabel("Nombre de promotions")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 3.b) Analyse de l'évolution des prix et des promotions dans le temps pour un produit spécifique
# Exemple : "LENOVO V15" (recherche non sensible à la casse)
produit_exemple = "LENOVO V15"
df_produit = df[df['Nom'].str.contains(produit_exemple, case=False, na=False)].sort_values('Date de collecte')

if df_produit.empty:
    print(f"\nAucune donnée trouvée pour le produit: {produit_exemple}")
else:
    plt.figure(figsize=(10,6))
    plt.plot(df_produit['Date de collecte'], df_produit['Prix'], marker='o', label='Prix', color='blue')
    plt.plot(df_produit['Date de collecte'], df_produit['Discount'], marker='s', label='Promotion (Discount)', color='red')
    plt.title(f"Évolution du prix et des promotions pour\n{produit_exemple}")
    plt.xlabel("Date")
    plt.ylabel("Montant (MAD)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
