from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import uuid
import json
from typing import List, Dict, Optional
import google.generativeai as genai
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

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

# Store uploaded data temporarily
uploaded_data = {}

@app.get("/")
async def root():
    return {"message": "API de Gestion des Stocks fonctionne"}

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Veuillez télécharger un fichier Excel (.xlsx ou .xls)")
        
        # Read Excel file
        contents = await file.read()
        
        # Parse Excel with pandas
        df = pd.read_excel(contents)
        
        # Validate required columns
        required_columns = [
            'Date de Commande', 'Article', 'Désignation Article', 
            'Point d\'Expédition', 'Nom Division', 'Quantité Commandée',
            'Stock Utilisation Libre', 'Ecart', 'Type Emballage', 'Quantité en Palette'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes requises: {', '.join(missing_columns)}"
            )
        
        # Clean and process data
        df['Date de Commande'] = pd.to_datetime(df['Date de Commande'])
        df['Quantité Commandée'] = pd.to_numeric(df['Quantité Commandée'], errors='coerce')
        df['Stock Utilisation Libre'] = pd.to_numeric(df['Stock Utilisation Libre'], errors='coerce')
        
        # Remove rows with invalid data
        df = df.dropna(subset=['Date de Commande', 'Quantité Commandée', 'Stock Utilisation Libre'])
        
        # Generate session ID for this upload
        session_id = str(uuid.uuid4())
        
        # Get unique values for filters with better packaging display
        unique_products = sorted(df['Désignation Article'].unique().tolist())
        unique_packaging_raw = sorted(df['Type Emballage'].unique().tolist())
        
        # Enhanced packaging display names with filtering for allowed types
        packaging_display_map = {
            'Verre': 'Bouteille en Verre',
            'Pet': 'Bouteille en Plastique (PET)',
            'Ciel': 'Ciel',
            'Canette': 'Canette Aluminium',
            'Tétra': 'Emballage Tétra Pak',
            'Bag': 'Bag-in-Box',
            'Fût': 'Fût'
        }
        
        # Filter packaging to only show allowed types: verre, pet, ciel
        allowed_packaging_types = ['Verre', 'Pet', 'Ciel']
        
        unique_packaging = []
        for pkg in unique_packaging_raw:
            # Only include packaging types that are in the allowed list
            if pkg in allowed_packaging_types:
                display_name = packaging_display_map.get(pkg, pkg)
                unique_packaging.append({"value": pkg, "display": display_name})
        
        unique_depots = sorted(df['Nom Division'].unique().tolist())
        
        # Store data temporarily
        uploaded_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'date_range': {
                'start': df['Date de Commande'].min().strftime('%Y-%m-%d'),
                'end': df['Date de Commande'].max().strftime('%Y-%m-%d'),
                'total_days': (df['Date de Commande'].max() - df['Date de Commande'].min()).days + 1
            },
            'filters': {
                'products': unique_products,
                'packaging': unique_packaging,
                'depots': unique_depots
            }
        }
        
        # Save to MongoDB
        document = {
            'session_id': session_id,
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'date_range': uploaded_data[session_id]['date_range'],
            'filters': uploaded_data[session_id]['filters']
        }
        collection.insert_one(document)
        
        return {
            "session_id": session_id,
            "message": "Fichier téléchargé avec succès",
            "records_count": len(df),
            "date_range": uploaded_data[session_id]['date_range'],
            "filters": uploaded_data[session_id]['filters']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@app.post("/api/calculate/{session_id}")
async def calculate_requirements(session_id: str, request: CalculationRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Get data
        data = uploaded_data[session_id]['data']
        df = pd.DataFrame(data)
        
        # Convert date column back to datetime
        df['Date de Commande'] = pd.to_datetime(df['Date de Commande'])
        
        # Apply filters
        if request.product_filter and len(request.product_filter) > 0:
            df = df[df['Désignation Article'].isin(request.product_filter)]
        
        if request.packaging_filter and len(request.packaging_filter) > 0:
            df = df[df['Type Emballage'].isin(request.packaging_filter)]
        
        if df.empty:
            return {
                "calculations": [],
                "summary": {
                    "total_depots": 0,
                    "total_products": 0,
                    "date_range_days": 0,
                    "requested_days": request.days,
                    "high_priority": [],
                    "medium_priority": [],
                    "low_priority": [],
                    "no_stock_needed": [],
                    "message": "Aucune donnée trouvée avec les filtres appliqués"
                }
            }
        
        # Calculate date range
        date_range_days = (df['Date de Commande'].max() - df['Date de Commande'].min()).days + 1
        
        # Group by depot and article
        grouped = df.groupby(['Nom Division', 'Article', 'Désignation Article', 'Type Emballage']).agg({
            'Quantité Commandée': 'sum',
            'Stock Utilisation Libre': 'last',  # Take the most recent stock level
            'Date de Commande': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        grouped.columns = [
            'depot', 'article_code', 'article_name', 'packaging_type',
            'total_ordered', 'current_stock', 'first_date', 'last_date'
        ]
        
        # Calculate metrics
        results = []
        for _, row in grouped.iterrows():
            # Average Daily Consumption
            adc = row['total_ordered'] / date_range_days if date_range_days > 0 else 0
            
            # Days of Coverage
            doc = row['current_stock'] / adc if adc > 0 else float('inf')
            
            # Required Quantity for X days
            required_stock = request.days * adc
            quantity_to_send = max(0, required_stock - row['current_stock'])
            
            # Determine priority based on days of coverage
            if doc == float('inf'):
                priority = 'low'
                priority_text = 'Faible'
            elif doc < 7:
                priority = 'high'
                priority_text = 'Critique'
            elif doc < 15:
                priority = 'medium'
                priority_text = 'Moyen'
            else:
                priority = 'low'
                priority_text = 'Faible'
            
            # Add unique ID for selection
            item_id = f"{row['depot']}_{row['article_code']}_{row['packaging_type']}"
            
            results.append({
                'id': item_id,
                'depot': row['depot'],
                'article_code': row['article_code'],
                'article_name': row['article_name'],
                'packaging_type': row['packaging_type'],
                'average_daily_consumption': round(adc, 2),
                'days_of_coverage': round(doc, 1) if doc != float('inf') else 'Infinie',
                'current_stock': row['current_stock'],
                'required_for_x_days': round(required_stock, 2),
                'quantity_to_send': round(quantity_to_send, 2),
                'total_ordered_in_period': row['total_ordered'],
                'priority': priority,
                'priority_text': priority_text,
                'selected': False
            })
        
        # Sort by priority (high first) and then by quantity needed (descending)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        results.sort(key=lambda x: (priority_order[x['priority']], -x['quantity_to_send']))
        
        return {
            "calculations": results,
            "summary": {
                "total_depots": len(df['Nom Division'].unique()),
                "total_products": len(results),
                "date_range_days": date_range_days,
                "requested_days": request.days,
                "high_priority": [r for r in results if r['priority'] == 'high'],
                "medium_priority": [r for r in results if r['priority'] == 'medium'],
                "low_priority": [r for r in results if r['priority'] == 'low'],
                "no_stock_needed": [r for r in results if r['quantity_to_send'] == 0]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des exigences: {str(e)}")

@app.get("/api/filters/{session_id}")
async def get_filters(session_id: str):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        return uploaded_data[session_id]['filters']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des filtres: {str(e)}")

@app.post("/api/export-critical/{session_id}")
async def export_critical_items(session_id: str, request: ExportRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Articles Critiques CBGS"
        
        # Company header
        ws['A1'] = "CBGS - Rapport d'Articles Critiques"
        ws['A2'] = f"Date de génération: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A3'] = f"Nombre d'articles critiques: {len(request.selected_items)}"
        
        # Style for header
        header_font = Font(bold=True, size=14)
        ws['A1'].font = header_font
        ws['A2'].font = Font(bold=True)
        ws['A3'].font = Font(bold=True)
        
        # Table headers
        headers = [
            'Dépôt', 'Code Article', 'Désignation Article', 'Type Emballage',
            'Stock Actuel', 'Consommation Quotidienne', 'Jours de Couverture',
            'Quantité Requise', 'Priorité', 'Action Recommandée'
        ]
        
        row_num = 5
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row_num, column=col_num, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center")
        
        # Add data rows
        for idx, item in enumerate(request.selected_items, 1):
            row_num = 5 + idx
            
            # Determine action based on priority
            if item['priority'] == 'high':
                action = "URGENT - Réapprovisionnement immédiat"
            elif item['priority'] == 'medium':
                action = "Planifier réapprovisionnement"
            else:
                action = "Surveiller"
            
            row_data = [
                item['depot'],
                item['article_code'],
                item['article_name'],
                item['packaging_type'],
                item['current_stock'],
                item['average_daily_consumption'],
                item['days_of_coverage'],
                item['quantity_to_send'],
                item['priority_text'],
                action
            ]
            
            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num, value=value)
                if item['priority'] == 'high':
                    cell.fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
                elif item['priority'] == 'medium':
                    cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"CBGS_Articles_Critiques_{timestamp}.xlsx"
        
        # Return file as download
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export: {str(e)}")

@app.post("/api/gemini-query/{session_id}")
async def gemini_query(session_id: str, request: GeminiQueryRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Get data
        data = uploaded_data[session_id]['data']
        df = pd.DataFrame(data)
        
        # Create enhanced context for Gemini optimized for single-day data analysis
        context = f"""
        Vous êtes un expert en analyse de stocks et de supply chain spécialisé dans l'analyse de données journalières.
        
        IMPORTANT: Donnez une réponse INTELLIGENTE et CONCISE (2-4 phrases maximum), avec des chiffres précis. 
        Les données fournies représentent généralement une journée d'activité.
        
        Données journalières actuelles:
        - Enregistrements du jour: {len(df)}
        - Date d'analyse: {uploaded_data[session_id]['date_range']['start']} à {uploaded_data[session_id]['date_range']['end']}
        - Dépôts actifs: {df['Nom Division'].unique().tolist()}
        - Produits traités: {df['Désignation Article'].nunique()} articles uniques
        - Types d'emballage: {df['Type Emballage'].unique().tolist()}
        - Volume total commandé aujourd'hui: {df['Quantité Commandée'].sum():,.0f} unités
        - Stock moyen disponible: {df['Stock Utilisation Libre'].mean():,.0f} unités
        
        Concentrez-vous sur l'analyse des données de cette journée. Fournissez des insights précis basés sur:
        - Les volumes commandés du jour
        - Les niveaux de stock actuels
        - La répartition par dépôt et produit
        - Les priorités de réapprovisionnement
        
        Répondez toujours en français, de manière professionnelle et actionnable pour cette journée d'activité.
        """
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generate response optimized for single-day data analysis
        prompt = context + f"\n\nQuestion: {request.query}\n\nAnalyse des données journalières (réponse concise avec chiffres précis):"
        response = model.generate_content(prompt)
        
        return {
            "response": response.text,
            "query": request.query,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement de la requête Gemini: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "sain", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)