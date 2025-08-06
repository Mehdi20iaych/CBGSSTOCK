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
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyDaUyWzYQEDBqFwuniG8KiqKHgtk-l5Dco")
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
    session_id: str

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
        
        # Vérifier les colonnes requises selon les spécifications
        required_columns = ['B', 'D', 'F', 'G']  # Article, Point d'Expédition, Quantité Commandée, Stock Utilisation Libre
        
        # Si les colonnes sont nommées différemment, essayer de les identifier
        if 'B' not in df.columns:
            # Essayer avec les noms potentiels des colonnes
            column_mapping = {}
            if len(df.columns) >= 7:  # Au moins 7 colonnes pour avoir A-G
                column_mapping['Article'] = df.columns[1]  # Colonne B (index 1)
                column_mapping['Point d\'Expédition'] = df.columns[3]  # Colonne D (index 3) 
                column_mapping['Quantité Commandée'] = df.columns[5]  # Colonne F (index 5)
                column_mapping['Stock Utilisation Libre'] = df.columns[6]  # Colonne G (index 6)
                
                # Renommer les colonnes pour standardiser
                df = df.rename(columns={
                    df.columns[1]: 'Article',
                    df.columns[3]: 'Point d\'Expédition', 
                    df.columns[5]: 'Quantité Commandée',
                    df.columns[6]: 'Stock Utilisation Libre'
                })
        
        # Vérifier que nous avons les colonnes nécessaires après mapping
        required_cols = ['Article', 'Point d\'Expédition', 'Quantité Commandée', 'Stock Utilisation Libre']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes: {', '.join(missing_cols)}. Vérifiez que le fichier contient les colonnes B, D, F, G selon les spécifications."
            )
        
        # Nettoyer et valider les données
        df['Quantité Commandée'] = pd.to_numeric(df['Quantité Commandée'], errors='coerce')
        df['Stock Utilisation Libre'] = pd.to_numeric(df['Stock Utilisation Libre'], errors='coerce')
        
        # Supprimer les lignes avec données manquantes essentielles
        df = df.dropna(subset=['Article', 'Point d\'Expédition', 'Quantité Commandée'])
        
        # Remplir Stock Utilisation Libre manquant par 0
        df['Stock Utilisation Libre'] = df['Stock Utilisation Libre'].fillna(0)
        
        # Filtrer pour exclure M210 des dépôts destinataires (M210 ne doit jamais être approvisionné)
        df = df[df['Point d\'Expédition'] != 'M210']
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get unique values for filters
        unique_articles = sorted(df['Article'].astype(str).unique().tolist())
        unique_depots = sorted(df['Point d\'Expédition'].unique().tolist())
        
        # Store data
        commandes_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'filters': {
                'articles': unique_articles,
                'depots': unique_depots
            }
        }
        
        return {
            "session_id": session_id,
            "message": "Fichier commandes uploadé avec succès",
            "summary": {
                "total_records": len(df),
                "unique_articles": len(unique_articles),
                "unique_depots": len(unique_depots),
                "total_quantity": float(df['Quantité Commandée'].sum()),
                "total_stock": float(df['Stock Utilisation Libre'].sum())
            },
            "filters": {
                "articles": unique_articles,
                "depots": unique_depots
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
        
        # Grouper les commandes par (Article, Point d'Expédition)
        grouped = commandes_df.groupby(['Article', 'Point d\'Expédition']).agg({
            'Quantité Commandée': 'sum',  # CQM (Consommation Quotidienne Moyenne)
            'Stock Utilisation Libre': 'first'  # Stock actuel dans le dépôt
        }).reset_index()
        
        # Calculer pour chaque ligne
        results = []
        for _, row in grouped.iterrows():
            article = str(row['Article'])
            depot = str(row['Point d\'Expédition'])
            cqm = float(row['Quantité Commandée'])
            stock_actuel = float(row['Stock Utilisation Libre'])
            
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
            
            results.append({
                'article': article,
                'depot': depot, 
                'cqm': cqm,
                'stock_actuel': stock_actuel,
                'stock_transit': stock_transit,
                'quantite_requise': quantite_requise,
                'quantite_a_envoyer': quantite_a_envoyer,
                'stock_dispo_m210': stock_dispo_m210,
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
        
        return {
            "calculations": results,
            "summary": {
                "total_items": total_items,
                "items_ok": items_ok,
                "items_a_livrer": items_a_livrer,
                "items_non_couverts": items_non_couverts,
                "jours_couvrir": request.days
            },
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
    """Export Excel simplifié"""
    try:
        if not request.selected_items:
            raise HTTPException(status_code=400, detail="Aucun élément sélectionné pour l'export")
        
        # Créer un nouveau classeur Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Résultats Calcul Stock"
        
        # En-têtes
        headers = [
            "Code Article", "Code Dépôt", "Quantité Commandée", "Stock Actuel", 
            "Quantité en Transit", "Quantité à Envoyer", "Stock Dispo M210", "Statut"
        ]
        
        # Ajouter les en-têtes
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        
        # Ajouter les données
        for row_idx, item in enumerate(request.selected_items, 2):
            ws.cell(row=row_idx, column=1, value=item['article'])
            ws.cell(row=row_idx, column=2, value=item['depot'])
            ws.cell(row=row_idx, column=3, value=item['cqm'])
            ws.cell(row=row_idx, column=4, value=item['stock_actuel'])
            ws.cell(row=row_idx, column=5, value=item['stock_transit'])
            ws.cell(row=row_idx, column=6, value=item['quantite_a_envoyer'])
            ws.cell(row=row_idx, column=7, value=item['stock_dispo_m210'])
            ws.cell(row=row_idx, column=8, value=item['statut'])
            
            # Colorer selon le statut
            status_color = "90EE90" if item['statut'] == "OK" else "FFE4B5" if item['statut'] == "À livrer" else "FFB6C1"
            for col in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=col).fill = PatternFill(start_color=status_color, end_color=status_color, fill_type="solid")
        
        # Ajuster la largeur des colonnes
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
        
        # Sauvegarder dans un buffer
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Générer le nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Calcul_Stock_{timestamp}.xlsx"
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'export: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)