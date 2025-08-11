from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import uuid
import json
import math
from typing import List, Dict, Optional

# JSON serialization helper for datetime objects
def json_serializable(obj):
    """Convert datetime objects to ISO format strings for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [json_serializable(item) for item in obj]
    else:
        return obj
import google.generativeai as genai
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import openpyxl.comments
import openpyxl.styles

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyB6DG8yocaGBjwfp7TatlDDHlKELYm56BU")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGO_URL)
    db = client.stock_management
    collection = db.stock_data
    print("MongoDB connecté avec succès")
except Exception as e:
    print(f"Échec de la connexion MongoDB: {e}")

# Pydantic models
class CalculationRequest(BaseModel):
    days: int
    product_filter: Optional[List[str]] = None
    packaging_filter: Optional[List[str]] = None

class GeminiQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ExportRequest(BaseModel):
    selected_items: List[Dict]
    session_id: str

# Locally manufactured articles list
LOCALLY_MADE_ARTICLES = {
    '1011', '1016', '1021', '1022', '1033', '1040', '1051', '1059', '1069', '1071',
    '1515', '1533', '1540', '1559', '1569', '2011', '2014', '2022', '2033', '2040',
    '2069', '3040', '3043', '3056', '3140', '3149', '3156', '3249', '3256', '3948',
    '3953', '4843', '4942', '5030', '5059', '5130', '5159', '5516', '6010', '6011',
    '6016', '6020', '6030', '6040', '6059', '6069', '6120', '6140', '7435', '7436',
    '7521', '7532', '7620', '7630', '7640', '7659', '7949', '7953'
}

# Allowed depots constraint
def is_allowed_depot(depot_code):
    """Check if a depot code is allowed based on the specified constraints"""
    if not depot_code or not isinstance(depot_code, str):
        return False
    
    # Clean the depot code (remove whitespace, convert to uppercase)
    depot = depot_code.strip().upper()
    
    # Check specific allowed depots
    specific_depots = {'M115', 'M120', 'M130', 'M170', 'M171'}
    if depot in specific_depots:
        return True
    
    # Check range M212-M280
    if depot.startswith('M') and len(depot) >= 4:
        try:
            depot_num = int(depot[1:])  # Extract number after 'M'
            if 212 <= depot_num <= 280:
                return True
        except ValueError:
            # If depot code doesn't have a valid number, it's not allowed
            pass
    
    return False

# Store uploaded data temporarily
commandes_data = {}  # Fichier commandes
stock_data = {}      # Fichier stock M210
transit_data = {}    # Fichier transit

@app.get("/")
async def root():
    return {"message": "API de Gestion des Stocks Simplifié fonctionne"}

@app.post("/api/upload-commandes-excel")
async def upload_commandes_excel(file: UploadFile = File(...)):
    """Upload du fichier commandes avec colonnes spécifiques"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Veuillez télécharger un fichier Excel (.xlsx ou .xls)")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(contents)
        
        # Vérifier les colonnes requises selon les spécifications - AJOUT COLONNE K
        required_columns = ['B', 'D', 'F', 'G', 'I', 'K']  # Article, Point d'Expédition, Quantité Commandée, Stock Utilisation Libre, Type Emballage, Produits par Palette
        
        # Si les colonnes sont nommées différemment, essayer de les identifier
        if 'B' not in df.columns:
            # Essayer avec les noms potentiels des colonnes
            column_mapping = {}
            if len(df.columns) >= 11:  # Au moins 11 colonnes pour avoir A-K
                column_mapping['Article'] = df.columns[1]  # Colonne B (index 1)
                column_mapping['Point d\'Expédition'] = df.columns[3]  # Colonne D (index 3) 
                column_mapping['Quantité Commandée'] = df.columns[5]  # Colonne F (index 5)
                column_mapping['Stock Utilisation Libre'] = df.columns[6]  # Colonne G (index 6)
                column_mapping['Type Emballage'] = df.columns[8]  # Colonne I (index 8)
                column_mapping['Produits par Palette'] = df.columns[10]  # Colonne K (index 10)
                
                # Renommer les colonnes pour standardiser
                df = df.rename(columns={
                    df.columns[1]: 'Article',
                    df.columns[3]: 'Point d\'Expédition', 
                    df.columns[5]: 'Quantité Commandée',
                    df.columns[6]: 'Stock Utilisation Libre',
                    df.columns[8]: 'Type Emballage',
                    df.columns[10]: 'Produits par Palette'
                })
        
        # Vérifier que nous avons les colonnes nécessaires après mapping
        required_cols = ['Article', 'Point d\'Expédition', 'Quantité Commandée', 'Stock Utilisation Libre', 'Type Emballage', 'Produits par Palette']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes: {', '.join(missing_cols)}. Vérifiez que le fichier contient les colonnes B, D, F, G, I, K selon les spécifications."
            )
        
        # Nettoyer et valider les données
        df['Quantité Commandée'] = pd.to_numeric(df['Quantité Commandée'], errors='coerce')
        df['Stock Utilisation Libre'] = pd.to_numeric(df['Stock Utilisation Libre'], errors='coerce')
        df['Produits par Palette'] = pd.to_numeric(df['Produits par Palette'], errors='coerce')
        
        # Nettoyer et standardiser le type d'emballage
        df['Type Emballage'] = df['Type Emballage'].astype(str).str.strip().str.lower()
        # Normaliser les valeurs d'emballage
        packaging_mapping = {
            'verre': 'verre',
            'pet': 'pet', 
            'ciel': 'ciel',
            'bottle': 'verre',  # Mapping anglais
            'plastic': 'pet',   # Mapping anglais
            'can': 'ciel'       # Mapping anglais
        }
        df['Type Emballage'] = df['Type Emballage'].map(packaging_mapping).fillna(df['Type Emballage'])
        
        # Supprimer les lignes avec données manquantes essentielles
        df = df.dropna(subset=['Article', 'Point d\'Expédition', 'Quantité Commandée', 'Type Emballage', 'Produits par Palette'])
        
        # Remplir Stock Utilisation Libre manquant par 0
        df['Stock Utilisation Libre'] = df['Stock Utilisation Libre'].fillna(0)
        
        # Validation: Produits par Palette doit être > 0
        df = df[df['Produits par Palette'] > 0]
        
        # Filtrer pour exclure M210 des dépôts destinataires (M210 ne doit jamais être approvisionné)
        df = df[df['Point d\'Expédition'] != 'M210']
        
        # Apply depot constraint: only consider allowed depots
        df['is_allowed_depot'] = df['Point d\'Expédition'].apply(is_allowed_depot)
        original_count = len(df)
        df = df[df['is_allowed_depot']].drop(columns=['is_allowed_depot'])
        filtered_count = len(df)
        
        print(f"Depot filtering applied: {original_count} -> {filtered_count} records")
        allowed_depots = sorted(df['Point d\'Expédition'].unique())
        print(f"Allowed depots found: {allowed_depots}")
        
        if len(df) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Aucun dépôt autorisé trouvé. Les dépôts autorisés sont: M115, M120, M130, M170, M171, et M212-M280"
            )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get unique values for filters
        unique_articles = sorted(df['Article'].astype(str).unique().tolist())
        unique_depots = sorted(df['Point d\'Expédition'].unique().tolist())
        unique_packaging = sorted(df['Type Emballage'].unique().tolist())
        
        # Store data
        commandes_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'filters': {
                'articles': unique_articles,
                'depots': unique_depots,
                'packaging': unique_packaging
            }
        }
        
        return {
            "session_id": session_id,
            "message": "Fichier commandes uploadé avec succès",
            "summary": {
                "total_records": len(df),
                "unique_articles": len(unique_articles),
                "unique_depots": len(unique_depots),
                "unique_packaging": len(unique_packaging),
                "total_quantity": float(df['Quantité Commandée'].sum()),
                "total_stock": float(df['Stock Utilisation Libre'].sum())
            },
            "filters": {
                "articles": unique_articles,
                "depots": unique_depots,
                "packaging": unique_packaging
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@app.post("/api/upload-stock-excel") 
async def upload_stock_excel(file: UploadFile = File(...)):
    """Upload du fichier stock M210 avec colonnes spécifiques"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Veuillez télécharger un fichier Excel (.xlsx ou .xls)")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(contents)
        
        # Vérifier les colonnes selon les spécifications
        # Colonne A: Division, B: Article, D: STOCK A DATE
        if len(df.columns) >= 4:
            df = df.rename(columns={
                df.columns[0]: 'Division',
                df.columns[1]: 'Article', 
                df.columns[3]: 'STOCK A DATE'
            })
        
        required_cols = ['Division', 'Article', 'STOCK A DATE']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes: {', '.join(missing_cols)}. Vérifiez que le fichier contient les colonnes A, B, D selon les spécifications."
            )
        
        # Filtrer uniquement M210 (dépôt central)
        df = df[df['Division'] == 'M210']
        
        if df.empty:
            raise HTTPException(
                status_code=400, 
                detail="Aucune donnée trouvée pour le dépôt M210. Vérifiez que le fichier contient des données avec Division = M210."
            )
        
        # Nettoyer les données
        df['STOCK A DATE'] = pd.to_numeric(df['STOCK A DATE'], errors='coerce')
        df = df.dropna(subset=['Article', 'STOCK A DATE'])
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get unique articles
        unique_articles = sorted(df['Article'].astype(str).unique().tolist())
        
        # Store data
        stock_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'summary': {
                'total_articles': len(unique_articles),
                'total_stock_m210': float(df['STOCK A DATE'].sum())
            }
        }
        
        return {
            "session_id": session_id,
            "message": "Fichier stock M210 uploadé avec succès",
            "summary": {
                "total_records": len(df),
                "unique_articles": len(unique_articles),
                "total_stock_m210": float(df['STOCK A DATE'].sum())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@app.post("/api/upload-transit-excel")
async def upload_transit_excel(file: UploadFile = File(...)):
    """Upload du fichier transit avec colonnes spécifiques"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Veuillez télécharger un fichier Excel (.xlsx ou .xls)")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(contents)
        
        # Vérifier les colonnes selon les spécifications  
        # Colonne A: Article, C: Division, G: Division cédante, I: Quantité
        if len(df.columns) >= 9:
            df = df.rename(columns={
                df.columns[0]: 'Article',
                df.columns[2]: 'Division',
                df.columns[6]: 'Division cédante',
                df.columns[8]: 'Quantité'
            })
        
        required_cols = ['Article', 'Division', 'Division cédante', 'Quantité']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes: {', '.join(missing_cols)}. Vérifiez que le fichier contient les colonnes A, C, G, I selon les spécifications."
            )
        
        # Filtrer seulement les transits depuis M210 (dépôt central)
        df = df[df['Division cédante'] == 'M210']
        
        # Apply depot constraint: only consider allowed destination depots
        df['is_allowed_depot'] = df['Division'].apply(is_allowed_depot)
        original_count = len(df)
        df = df[df['is_allowed_depot']].drop(columns=['is_allowed_depot'])
        filtered_count = len(df)
        
        print(f"Transit depot filtering applied: {original_count} -> {filtered_count} records")
        allowed_depots = sorted(df['Division'].unique())
        print(f"Allowed transit destination depots: {allowed_depots}")
        
        # Nettoyer les données
        df['Quantité'] = pd.to_numeric(df['Quantité'], errors='coerce')
        df = df.dropna(subset=['Article', 'Division', 'Quantité'])
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store data
        transit_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now()
        }
        
        return {
            "session_id": session_id,
            "message": "Fichier transit uploadé avec succès",
            "summary": {
                "total_records": len(df),
                "total_transit_quantity": float(df['Quantité'].sum()),
                "unique_articles": len(df['Article'].astype(str).unique()),
                "unique_destinations": len(df['Division'].unique())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@app.post("/api/calculate")
async def calculate_requirements(request: CalculationRequest):
    """Calcul simplifié avec la nouvelle formule"""
    try:
        # Vérifier qu'on a au moins les données commandes
        if not commandes_data:
            raise HTTPException(status_code=400, detail="Aucune donnée de commandes uploadée")
        
        # Prendre la dernière session de commandes uploadée
        commandes_session_id = list(commandes_data.keys())[-1]
        commandes_df = pd.DataFrame(commandes_data[commandes_session_id]['data'])
        
        # Appliquer le filtre de type d'emballage si spécifié
        if request.packaging_filter and len(request.packaging_filter) > 0:
            commandes_df = commandes_df[commandes_df['Type Emballage'].isin(request.packaging_filter)]
            
        if commandes_df.empty:
            raise HTTPException(status_code=400, detail="Aucune donnée après application des filtres d'emballage")
        
        # Obtenir les données de stock M210 si disponibles
        stock_m210 = {}
        if stock_data:
            stock_session_id = list(stock_data.keys())[-1] 
            stock_df = pd.DataFrame(stock_data[stock_session_id]['data'])
            # Créer un dictionnaire article -> stock disponible M210
            for _, row in stock_df.iterrows():
                stock_m210[str(row['Article'])] = float(row['STOCK A DATE'])
        
        # Obtenir les données de transit si disponibles
        transit_stocks = {}
        if transit_data:
            transit_session_id = list(transit_data.keys())[-1]
            transit_df = pd.DataFrame(transit_data[transit_session_id]['data'])
            # Créer un dictionnaire (article, depot) -> quantité en transit
            for _, row in transit_df.iterrows():
                key = (str(row['Article']), str(row['Division']))
                transit_stocks[key] = transit_stocks.get(key, 0) + float(row['Quantité'])
        
        # Grouper les commandes par (Article, Point d'Expédition, Type Emballage)
        grouped = commandes_df.groupby(['Article', 'Point d\'Expédition', 'Type Emballage']).agg({
            'Quantité Commandée': 'sum',  # CQM (Consommation Quotidienne Moyenne)
            'Stock Utilisation Libre': 'first',  # Stock actuel dans le dépôt
            'Produits par Palette': 'first'  # Produits par palette pour cet article
        }).reset_index()
        
        # Calculer pour chaque ligne
        results = []
        for _, row in grouped.iterrows():
            article = str(row['Article'])
            depot = str(row['Point d\'Expédition'])
            packaging = str(row['Type Emballage'])
            cqm = float(row['Quantité Commandée'])
            stock_actuel = float(row['Stock Utilisation Libre'])
            produits_par_palette = float(row['Produits par Palette'])
            
            # Obtenir le stock en transit pour cet article vers ce dépôt
            transit_key = (article, depot)
            stock_transit = transit_stocks.get(transit_key, 0)
            
            # Appliquer la nouvelle formule
            # Quantité à Envoyer = max(0, (Quantité Commandée × Jours à Couvrir) - Stock Utilisation Libre - Quantité en Transit)
            quantite_requise = cqm * request.days
            quantite_a_envoyer = max(0, quantite_requise - stock_actuel - stock_transit)
            
            # Vérifier le stock disponible à M210
            stock_dispo_m210 = stock_m210.get(article, 0)
            
            # Check if article is locally made
            is_locally_made = str(article) in LOCALLY_MADE_ARTICLES
            sourcing_status = 'local' if is_locally_made else 'external'
            sourcing_text = 'Production Locale' if is_locally_made else 'Sourcing Externe'
            
            # Déterminer le statut
            if quantite_a_envoyer == 0:
                statut = "OK"
                statut_color = "green"
            elif quantite_a_envoyer <= stock_dispo_m210:
                statut = "À livrer"
                statut_color = "orange"
            else:
                statut = "Non couvert"
                statut_color = "red"
            
            # NOUVEAU CALCUL DES PALETTES: utiliser la valeur de colonne K pour cet article
            palettes_needed = quantite_a_envoyer / produits_par_palette if quantite_a_envoyer > 0 and produits_par_palette > 0 else 0
            
            results.append({
                'article': article,
                'depot': depot,
                'packaging': packaging,
                'cqm': cqm,
                'stock_actuel': stock_actuel,
                'stock_transit': stock_transit,
                'quantite_requise': quantite_requise,
                'quantite_a_envoyer': quantite_a_envoyer,
                'stock_dispo_m210': stock_dispo_m210,
                'produits_par_palette': produits_par_palette,  # Ajouter cette info dans les résultats
                'palettes_needed': palettes_needed,
                'statut': statut,
                'statut_color': statut_color,
                'sourcing_status': sourcing_status,
                'sourcing_text': sourcing_text,
                'is_locally_made': is_locally_made
            })
        
        # Calculer les statistiques de résumé
        total_items = len(results)
        items_ok = len([r for r in results if r['statut'] == 'OK'])
        items_a_livrer = len([r for r in results if r['statut'] == 'À livrer'])
        items_non_couverts = len([r for r in results if r['statut'] == 'Non couvert'])
        
        # Calculer les statistiques de sourcing
        local_items = len([r for r in results if r['is_locally_made']])
        external_items = len([r for r in results if not r['is_locally_made']])
        
        # Calculer les statistiques par dépôt (palettes et camions)
        depot_stats = {}
        for result in results:
            depot = result['depot']
            if depot not in depot_stats:
                depot_stats[depot] = {
                    'depot': depot,
                    'total_palettes': 0,
                    'total_items': 0,
                    'trucks_needed': 0,
                    'delivery_efficiency': 'Efficace'
                }
            
            depot_stats[depot]['total_palettes'] += result['palettes_needed']
            depot_stats[depot]['total_items'] += 1
        
        # Calculer le nombre de camions et l'efficacité pour chaque dépôt
        for depot in depot_stats:
            total_palettes = depot_stats[depot]['total_palettes']
            trucks_needed = math.ceil(total_palettes / 24) if total_palettes > 0 else 0
            depot_stats[depot]['trucks_needed'] = trucks_needed
            
            # Vérifier si on a des camions incomplets (pas un multiple parfait de 24)
            if total_palettes > 0 and total_palettes % 24 != 0:
                depot_stats[depot]['delivery_efficiency'] = 'Inefficace'
                # Calculer combien de palettes manquent pour compléter le dernier camion
                palettes_in_last_truck = total_palettes % 24
                depot_stats[depot]['missing_palettes'] = 24 - palettes_in_last_truck
            else:
                depot_stats[depot]['delivery_efficiency'] = 'Efficace'
                depot_stats[depot]['missing_palettes'] = 0
        
        # Convertir en liste et trier par nombre de palettes (décroissant)
        depot_summary = sorted(list(depot_stats.values()), key=lambda x: x['total_palettes'], reverse=True)
        
        # Trier les résultats par dépôt
        results_sorted = sorted(results, key=lambda x: x['depot'])
        
        return {
            "calculations": results_sorted,
            "summary": {
                "total_items": total_items,
                "items_ok": items_ok,
                "items_a_livrer": items_a_livrer,
                "items_non_couverts": items_non_couverts,
                "jours_couvrir": request.days
            },
            "sourcing_summary": {
                "local_items": local_items,
                "external_items": external_items,
                "local_percentage": round((local_items / total_items * 100) if total_items > 0 else 0, 1),
                "external_percentage": round((external_items / total_items * 100) if total_items > 0 else 0, 1)
            },
            "depot_summary": depot_summary,
            "has_stock_data": len(stock_m210) > 0,
            "has_transit_data": len(transit_stocks) > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du calcul: {str(e)}")

@app.get("/api/sessions")
async def get_sessions():
    """Obtenir les sessions actives"""
    return {
        "commandes_sessions": list(commandes_data.keys()),
        "stock_sessions": list(stock_data.keys()),
        "transit_sessions": list(transit_data.keys())
    }

@app.post("/api/export-excel")
async def export_excel(request: ExportRequest):
    """Export Excel intelligent organisé par dépôt"""
    try:
        if not request.selected_items:
            raise HTTPException(status_code=400, detail="Aucun élément sélectionné pour l'export")
        
        # Trier les données par dépôt puis par quantité à envoyer (décroissant)
        sorted_items = sorted(request.selected_items, 
                            key=lambda x: (x['depot'], -x['quantite_a_envoyer']))
        
        # Grouper par dépôt pour les statistiques
        depot_groups = {}
        for item in sorted_items:
            depot = item['depot']
            if depot not in depot_groups:
                depot_groups[depot] = {
                    'items': [],
                    'total_palettes': 0,
                    'total_articles': 0
                }
            depot_groups[depot]['items'].append(item)
            depot_groups[depot]['total_palettes'] += item.get('palettes_needed', 0)
            depot_groups[depot]['total_articles'] += 1
        
        # Créer un nouveau classeur Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Livraisons par Dépôt"
        
        # En-têtes essentiels (focus sur l'important)
        headers = ["Dépôt", "Code Article", "Quantité à Livrer", "Palettes", "Statut"]
        
        # Style simple et professionnel
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F4F4F", end_color="4F4F4F", fill_type="solid")
        
        # Ajouter les en-têtes
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        current_row = 2
        current_depot = None
        
        # Ajouter les données organisées par dépôt
        for item in sorted_items:
            depot = item['depot']
            
            # Ajouter une ligne de séparation entre les dépôts
            if current_depot and current_depot != depot:
                current_row += 1  # Ligne vide entre dépôts
                
                # Ligne de résumé du dépôt précédent
                depot_stats = depot_groups[current_depot]
                summary_row = current_row
                ws.cell(row=summary_row, column=1, value=f"TOTAL {current_depot}")
                ws.cell(row=summary_row, column=3, value="")
                ws.cell(row=summary_row, column=4, value=f"{depot_stats['total_palettes']} palettes")
                trucks_needed = math.ceil(depot_stats['total_palettes'] / 24)
                efficiency = "Efficace" if depot_stats['total_palettes'] >= 24 else "Inefficace"
                ws.cell(row=summary_row, column=5, value=f"{trucks_needed} camion(s) - {efficiency}")
                
                # Style pour la ligne de résumé
                for col in range(1, len(headers) + 1):
                    cell = ws.cell(row=summary_row, column=col)
                    cell.font = Font(bold=True, color="333333")
                    cell.fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
                
                current_row += 2  # Espace après le résumé
            
            current_depot = depot
            
            # Données essentielles seulement
            ws.cell(row=current_row, column=1, value=item['depot'])
            ws.cell(row=current_row, column=2, value=item['article'])
            ws.cell(row=current_row, column=3, value=item['quantite_a_envoyer'])
            ws.cell(row=current_row, column=4, value=item.get('palettes_needed', 0))
            ws.cell(row=current_row, column=5, value=item['statut'])
            
            # Style minimal - juste les priorités
            if item['statut'] == 'Non couvert':
                for col in range(1, len(headers) + 1):
                    ws.cell(row=current_row, column=col).fill = PatternFill(
                        start_color="FFEBEE", end_color="FFEBEE", fill_type="solid"
                    )
            
            current_row += 1
        
        # Résumé du dernier dépôt
        if current_depot:
            current_row += 1
            depot_stats = depot_groups[current_depot]
            summary_row = current_row
            ws.cell(row=summary_row, column=1, value=f"TOTAL {current_depot}")
            ws.cell(row=summary_row, column=3, value="")
            ws.cell(row=summary_row, column=4, value=f"{depot_stats['total_palettes']} palettes")
            trucks_needed = math.ceil(depot_stats['total_palettes'] / 24)
            efficiency = "Efficace" if depot_stats['total_palettes'] >= 24 else "Inefficace"
            ws.cell(row=summary_row, column=5, value=f"{trucks_needed} camion(s) - {efficiency}")
            
            # Style pour la ligne de résumé
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=summary_row, column=col)
                cell.font = Font(bold=True, color="333333")
                cell.fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
        
        # Ajuster les largeurs de colonne intelligemment
        column_widths = [12, 15, 18, 12, 15]  # Optimisé pour le contenu
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Figer les en-têtes
        ws.freeze_panes = 'A2'
        
        # Sauvegarder dans un buffer
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Nom de fichier intelligent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Livraisons_Depot_{timestamp}.xlsx"
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'export: {str(e)}")

@app.post("/api/depot-suggestions")
async def get_depot_suggestions(request: dict):
    """Génère des suggestions pour compléter 24 palettes par camion pour un dépôt"""
    try:
        depot_name = request.get('depot_name')
        current_days = request.get('days', 10)
        
        if not depot_name:
            raise HTTPException(status_code=400, detail="Nom de dépôt requis")
        
        # Check if depot is allowed
        if not is_allowed_depot(depot_name):
            raise HTTPException(
                status_code=400, 
                detail=f"Dépôt '{depot_name}' non autorisé. Les dépôts autorisés sont: M115, M120, M130, M170, M171, et M212-M280"
            )
        
        # Vérifier qu'on a des données de commandes
        if not commandes_data:
            raise HTTPException(status_code=400, detail="Aucune donnée de commandes uploadée")
        
        # Prendre la dernière session de commandes uploadée
        commandes_session_id = list(commandes_data.keys())[-1]
        commandes_df = pd.DataFrame(commandes_data[commandes_session_id]['data'])
        
        # Obtenir les données de stock et transit actuelles
        stock_m210 = {}
        if stock_data and len(stock_data) > 0:
            stock_session_id = list(stock_data.keys())[-1]
            stock_df = pd.DataFrame(stock_data[stock_session_id]['data'])
            stock_m210 = dict(zip(stock_df['Article'].astype(str), stock_df['STOCK A DATE']))
        
        transit_stocks = {}
        if transit_data and len(transit_data) > 0:
            transit_session_id = list(transit_data.keys())[-1]
            transit_df = pd.DataFrame(transit_data[transit_session_id]['data'])
            
            for _, row in transit_df.iterrows():
                article = str(row['Article'])
                if article not in transit_stocks:
                    transit_stocks[article] = {}
                depot = row['Division']
                if depot not in transit_stocks[article]:
                    transit_stocks[article][depot] = 0
                transit_stocks[article][depot] += row['Quantité']
        
        # Filtrer les commandes pour ce dépôt spécifique
        depot_commandes = commandes_df[commandes_df['Point d\'Expédition'] == depot_name]
        
        if depot_commandes.empty:
            return {
                "depot_name": depot_name,
                "current_palettes": 0,
                "target_palettes": 24,
                "suggestions": [],
                "message": f"Aucune commande trouvée pour le dépôt {depot_name}"
            }
        
        # Calculer les palettes actuelles pour ce dépôt
        current_palettes = 0
        depot_products = []
        
        for _, row in depot_commandes.iterrows():
            article = str(row['Article'])
            depot = row['Point d\'Expédition']
            packaging = row['Type Emballage']
            cqm = row['Quantité Commandée']
            stock_actuel = row['Stock Utilisation Libre']
            produits_par_palette = float(row['Produits par Palette'])
            stock_transit = transit_stocks.get(article, {}).get(depot, 0)
            
            # Calculer avec la formule actuelle
            quantite_requise = cqm * current_days
            quantite_a_envoyer = max(0, quantite_requise - stock_actuel - stock_transit)
            palettes_needed = quantite_a_envoyer / produits_par_palette if quantite_a_envoyer > 0 and produits_par_palette > 0 else 0
            
            current_palettes += palettes_needed
            
            depot_products.append({
                'article': article,
                'packaging': packaging,
                'cqm': cqm,
                'stock_actuel': stock_actuel,
                'stock_transit': stock_transit,
                'quantite_a_envoyer': quantite_a_envoyer,
                'palettes_needed': palettes_needed,
                'produits_par_palette': produits_par_palette,
                'stock_dispo_m210': stock_m210.get(article, 0)
            })
        
        # Calculer combien de palettes sont nécessaires pour atteindre des multiples de 24
        current_trucks = math.ceil(current_palettes / 24) if current_palettes > 0 else 1
        target_palettes = current_trucks * 24
        palettes_to_add = target_palettes - current_palettes
        
        suggestions = []
        if palettes_to_add > 0:
            # NOUVELLE LOGIQUE: Suggérer des produits basés sur les plus faibles quantités de stock
            # Obtenir tous les produits du stock M210 et les trier par quantité de stock (ascendant)
            if not stock_m210:
                suggestions.append({
                    'message': 'Aucune donnée de stock M210 disponible pour générer des suggestions'
                })
            else:
                # Créer une liste de tous les produits avec leurs stocks M210, triés par stock croissant
                all_stock_products = []
                for article, stock_quantity in stock_m210.items():
                    # Vérifier si ce produit n'est pas déjà dans les commandes actuelles du dépôt
                    article_already_ordered = any(p['article'] == article for p in depot_products)
                    
                    if not article_already_ordered and stock_quantity > 0:
                        all_stock_products.append({
                            'article': article,
                            'stock_m210': stock_quantity,
                            'packaging': 'verre',  # Valeur par défaut, pourrait être améliorée avec plus de données
                        })
                
                # Trier par stock M210 (ascendant) - les plus faibles quantités en premier
                all_stock_products.sort(key=lambda x: x['stock_m210'])
                
                remaining_palettes = palettes_to_add
                products_needed_per_palette = 30
                
                for product in all_stock_products:
                    if remaining_palettes <= 0:
                        break
                    
                    # Calculer combien de palettes on peut suggérer avec ce produit
                    # On va suggérer de 1 à 3 palettes selon les besoins restants
                    suggested_palettes = min(3, remaining_palettes)
                    suggested_quantity = suggested_palettes * products_needed_per_palette
                    
                    # Vérifier si on a assez de stock M210 pour cette suggestion
                    stock_available = product['stock_m210']
                    can_fulfill = suggested_quantity <= stock_available
                    
                    suggestions.append({
                        'article': product['article'],
                        'packaging': product['packaging'],
                        'stock_m210': stock_available,
                        'suggested_quantity': suggested_quantity,
                        'suggested_palettes': suggested_palettes,
                        'can_fulfill': can_fulfill,
                        'feasibility': 'Réalisable' if can_fulfill else 'Stock insuffisant',
                        'reason': f'Stock faible ({stock_available} unités) - Priorité pour reconstitution'
                    })
                    
                    remaining_palettes -= suggested_palettes
        
        return {
            "depot_name": depot_name,
            "current_palettes": current_palettes,
            "current_trucks": current_trucks,
            "target_palettes": target_palettes,
            "palettes_to_add": palettes_to_add,
            "suggestions": suggestions[:5],  # Limiter à 5 suggestions max
            "efficiency_status": "Efficace" if current_palettes > 0 and current_palettes % 24 == 0 else "Inefficace"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la génération des suggestions: {str(e)}")

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """Chat with AI about uploaded files and inventory data"""
    try:
        # Get available data context
        data_context = {}
        
        # Add commandes data if available
        if commandes_data:
            latest_commandes = list(commandes_data.keys())[-1]
            commandes_info = commandes_data[latest_commandes]
            data_context['commandes'] = {
                'total_records': len(commandes_info['data']),
                'summary': commandes_info.get('summary', {}),
                'sample_data': commandes_info['data'][:3] if len(commandes_info['data']) > 0 else []
            }
        
        # Add stock data if available
        if stock_data:
            latest_stock = list(stock_data.keys())[-1]
            stock_info = stock_data[latest_stock]
            data_context['stock'] = {
                'total_records': len(stock_info['data']),
                'summary': stock_info.get('summary', {}),
                'sample_data': stock_info['data'][:3] if len(stock_info['data']) > 0 else []
            }
        
        # Add transit data if available
        if transit_data:
            latest_transit = list(transit_data.keys())[-1]
            transit_info = transit_data[latest_transit]
            data_context['transit'] = {
                'total_records': len(transit_info['data']),
                'sample_data': transit_info['data'][:3] if len(transit_info['data']) > 0 else []
            }
        
        # Build context prompt
        system_prompt = """Tu es un assistant IA spécialisé dans l'analyse d'inventaire et la gestion des stocks. 
        Tu aides les utilisateurs à comprendre et analyser leurs données d'inventaire.

        CONTEXTE DU SYSTÈME:
        - Système de gestion des stocks pour distribution depuis dépôt central M210
        - Trois types de fichiers: Commandes, Stock M210, Transit
        - Formule de calcul: Quantité à Envoyer = max(0, (Quantité Commandée × Jours) - Stock Actuel - Transit)
        - Articles locaux vs sourcing externe
        - Logistique palettes (30 produits/palette) et camions (24 palettes/camion)

        DONNÉES DISPONIBLES:
        """
        
        if data_context:
            for data_type, info in data_context.items():
                system_prompt += f"\n{data_type.upper()}:"
                system_prompt += f"\n- Total enregistrements: {info['total_records']}"
                if 'summary' in info:
                    # Use safe JSON serialization for datetime objects
                    safe_summary = json_serializable(info['summary'])
                    system_prompt += f"\n- Résumé: {json.dumps(safe_summary, ensure_ascii=False)}"
                if info['sample_data']:
                    # Use safe JSON serialization for datetime objects
                    safe_sample_data = json_serializable(info['sample_data'][:2])
                    system_prompt += f"\n- Exemple données: {json.dumps(safe_sample_data, ensure_ascii=False)}"
        else:
            system_prompt += "\nAucune donnée uploadée actuellement."
        
        system_prompt += """

        INSTRUCTIONS:
        - Réponds en français
        - Sois précis et factuel basé sur les données disponibles
        - Si pas de données, explique ce que tu pourrais analyser avec des données
        - Propose des analyses pertinentes selon le contexte
        - Utilise les termes métier: dépôts, articles, palettes, camions, sourcing
        """
        
        # Create the chat
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare the full prompt
        full_prompt = f"{system_prompt}\n\nQUESTION UTILISATEUR: {request.message}"
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Aucune réponse générée par l'IA")
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        return {
            "response": response.text,
            "conversation_id": conversation_id,
            "has_data": len(data_context) > 0,
            "data_types": list(data_context.keys()),
            "message": request.message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de réponse: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)