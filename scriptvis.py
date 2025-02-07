#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'analyse et de visualisation des données nettoyées.

Les analyses réalisées sont :
1. Comparaison des prix entre différentes plateformes pour un même produit.
2. Identification des promotions par catégorie.
3. Visualisation de l'évolution des prix dans le temps pour un produit spécifique (si données temporelles disponibles).
"""

import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- Fonction d'extraction du prix numérique ---
def extract_price(price_str):
    """
    Extrait la valeur numérique d'une chaîne représentant un prix.
    Par exemple : "1,549.00 Dhs" → 1549.00 (float)
    """
    if pd.isna(price_str) or not price_str:
        return None
    # Remplacer les espaces insécables et espaces normaux
    price_str = price_str.replace("\u202f", "").replace(" ", "")
    match = re.search(r"([\d.,]+)", price_str)
    if match:
        num_str = match.group(1)
        # On supprime les virgules servant de séparateur de milliers
        num_str = num_str.replace(",", "")
        try:
            return float(num_str)
        except ValueError:
            return None
    return None

# --- Lecture des données nettoyées ---
# Remplacez le nom de fichier par celui de vos données nettoyées
input_filename = "all_products_cleaned.csv"
df = pd.read_csv(input_filename)

# Création d'une colonne numérique pour le prix (en MAD)
df["Prix_num"] = df["Prix"].apply(extract_price)

# Conversion de la colonne "Date de collecte" en type datetime, si nécessaire
if "Date de collecte" in df.columns:
    df["Date de collecte"] = pd.to_datetime(df["Date de collecte"], format="%Y-%m-%d %H:%M:%S", errors='coerce')

# Affichage des premières lignes pour vérification
print(df.head())

# ============================================================================
# 1. Comparaison des prix entre différentes plateformes pour un même produit
# ============================================================================

# On suppose que plusieurs plateformes peuvent proposer le même produit.
# Pour comparer, on crée un pivot table dont l'index est le nom du produit et
# les colonnes représentent les différents sites web.
pivot_prices = df.pivot_table(index="Nom", columns="Site web", values="Prix_num")
print("Tableau croisé des prix par produit et plateforme:")
print(pivot_prices.head())

# Pour illustrer, nous sélectionnons quelques produits ayant des données sur plusieurs plateformes.
# (Adaptez cette sélection selon vos données réelles.)
sample_products = pivot_prices.dropna(thresh=2).head(5)  # Produits présents sur au moins 2 plateformes
sample_products.plot(kind="bar", figsize=(12, 6))
plt.title("Comparaison des prix par plateforme pour quelques produits")
plt.ylabel("Prix en MAD")
plt.xlabel("Nom du produit")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# ============================================================================
# 2. Identification des promotions
# ============================================================================

# Pour identifier les promotions, on considère qu'un produit est en promotion
# si la colonne "Promotions" n'est pas vide et n'est pas "Aucune".
df["En_promotion"] = df["Promotions"].apply(lambda x: False if pd.isna(x) or x.strip().lower() in ["", "aucune"] else True)

# Comptage des promotions par catégorie
promo_by_cat = df.groupby("Catégorie")["En_promotion"].sum().sort_values(ascending=False)
print("Nombre de promotions par catégorie:")
print(promo_by_cat)

# Diagramme en barres des promotions par catégorie
promo_by_cat.plot(kind="bar", figsize=(10, 6), color="skyblue")
plt.title("Nombre de promotions par catégorie")
plt.ylabel("Nombre de promotions")
plt.xlabel("Catégorie")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# ============================================================================
# 3. Analyse de l'évolution des prix dans le temps pour un produit spécifique
# ============================================================================

# Si vos données couvrent plusieurs dates de collecte, vous pouvez suivre l'évolution
# du prix d'un produit particulier. Par exemple, pour le produit "HP EliteBook 830 G5".
# (Adaptez le nom du produit selon vos données.)
produit_cible = "HP EliteBook 830 G5"
df_produit = df[df["Nom"] == produit_cible].copy()

# S'assurer que l'on a plusieurs points temporels pour ce produit
if not df_produit.empty and df_produit["Date de collecte"].nunique() > 1:
    df_produit = df_produit.sort_values("Date de collecte")
    plt.figure(figsize=(10, 6))
    plt.plot(df_produit["Date de collecte"], df_produit["Prix_num"], marker="o", linestyle="-")
    plt.title(f"Evolution du prix de '{produit_cible}' dans le temps")
    plt.xlabel("Date de collecte")
    plt.ylabel("Prix en MAD")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print(f"Pas assez de données temporelles pour analyser l'évolution du prix de '{produit_cible}'.")

