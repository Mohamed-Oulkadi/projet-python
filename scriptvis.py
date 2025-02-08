import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Paramétrer Seaborn pour des graphiques esthétiques
sns.set(style="whitegrid")

###########################################
# Chargement et nettoyage des données
###########################################

# Supposons que vos données nettoyées se trouvent dans un fichier CSV sans entête.
# Chaque ligne du fichier "products.csv" a le format suivant:
# Product,Price,Platform,Category,Date,Promotion
# Par exemple:
# Logitech K400 Plus Clavier sans Fil Touch TV avec Contrôle Média et Pavé Tactile- Noir,349.00 MAD,Jumia.ma,Keyboards,2024-12-08,-39.00MAD
df = pd.read_csv('all_products_cleaned.csv', header=None, 
                 names=["Product", "Price", "Platform", "Category", "Date", "Promotion"])

# Nettoyage de la colonne Price : suppression du "MAD" et conversion en float
df['Price'] = df['Price'].str.replace(' MAD', '', regex=False).str.replace('MAD', '', regex=False)
df['Price'] = df['Price'].str.replace(',', '.')  # au cas où des virgules sont utilisées pour les décimales
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

# Fonction pour convertir la colonne Promotion en valeur numérique
def convert_discount(val):
    if pd.isnull(val) or val.strip() in ['Aucune', '']:
         return 0.0
    # Supprimer les espaces et le texte "MAD"
    val = val.replace('MAD','').replace(' ', '')
    # Remplacer la virgule par un point (pour les décimales)
    val = val.replace(',', '.')
    try:
         return float(val)
    except:
         return 0.0

# Créer une nouvelle colonne 'Discount' à partir de 'Promotion'
df['Discount'] = df['Promotion'].apply(convert_discount)

# Conversion de la colonne Date en type datetime
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')

# Afficher quelques lignes pour vérifier le nettoyage
print("Aperçu des données nettoyées :")
print(df.head())

###########################################
# 1. Comparaison des prix entre plateformes
###########################################

# Pour comparer les prix pour un même produit vendu sur différentes plateformes,
# nous regroupons par produit et plateforme et calculons le prix moyen.
price_comparison = df.groupby(['Product', 'Platform'])['Price'].mean().reset_index()

# Création d'un tableau croisé : chaque ligne = produit, colonnes = plateformes
price_pivot = price_comparison.pivot(index='Product', columns='Platform', values='Price')

# Calcul de l'écart de prix pour chaque produit (différence entre le prix max et le prix min)
price_pivot['Price_Ecart'] = price_pivot.max(axis=1) - price_pivot.min(axis=1)

print("\nComparaison des prix (extrait du tableau pivot) :")
print(price_pivot.head())

# Visualisation : Histogramme des écarts de prix pour les produits disponibles sur plusieurs plateformes
# On sélectionne uniquement les produits apparaissant sur au moins 2 plateformes (valeurs non nulles)
price_pivot_valid = price_pivot[price_pivot.notnull().sum(axis=1) > 1]

plt.figure(figsize=(10,6))
sns.histplot(price_pivot_valid['Price_Ecart'], bins=10, kde=True, color='skyblue')
plt.title("Histogramme des écarts de prix entre plateformes")
plt.xlabel("Écart de prix (MAD)")
plt.ylabel("Nombre de produits")
plt.show()

###########################################
# 2. Identification des promotions
###########################################

# a) Déterminer les catégories avec le plus de promotions
# On considère qu'une promotion est présente si la valeur de Discount est différente de 0.
promo_counts = df[df['Discount'] != 0].groupby('Category').size().reset_index(name='Promo_Count')

print("\nNombre de promotions par catégorie :")
print(promo_counts)

# Visualisation : Diagramme en barres du nombre de promotions par catégorie
plt.figure(figsize=(8,6))
sns.barplot(data=promo_counts, x='Category', y='Promo_Count', palette="viridis")
plt.title("Nombre de promotions par catégorie")
plt.xlabel("Catégorie")
plt.ylabel("Nombre de promotions")
plt.xticks(rotation=45)
plt.show()

# b) Analyse de l’évolution des promotions et des prix dans le temps pour un produit spécifique
# Par exemple, nous analysons l'évolution pour "LENOVO V15"
produit_exemple = "LENOVO V15"
df_produit = df[df['Product'] == produit_exemple].sort_values('Date')

if df_produit.empty:
    print(f"\nAucune donnée trouvée pour le produit: {produit_exemple}")
else:
    plt.figure(figsize=(10,6))
    plt.plot(df_produit['Date'], df_produit['Price'], marker='o', label='Prix', color='blue')
    plt.plot(df_produit['Date'], df_produit['Discount'], marker='s', label='Promotion (Discount)', color='red')
    plt.title(f"Évolution du prix et des promotions pour\n{produit_exemple}")
    plt.xlabel("Date")
    plt.ylabel("Montant (MAD)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
