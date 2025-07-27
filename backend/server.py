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
        
        # Get unique values for filters
        unique_products = sorted(df['Désignation Article'].unique().tolist())
        unique_packaging = sorted(df['Type Emballage'].unique().tolist())
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
            
            results.append({
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
                'priority_text': priority_text
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

@app.post("/api/gemini-query/{session_id}")
async def gemini_query(session_id: str, request: GeminiQueryRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Get data
        data = uploaded_data[session_id]['data']
        df = pd.DataFrame(data)
        
        # Create context for Gemini in French
        context = f"""
        Vous analysez les données de stock et de commandes pour plusieurs dépôts. Voici le résumé des données:
        
        - Total des enregistrements: {len(df)}
        - Plage de dates: {uploaded_data[session_id]['date_range']['start']} à {uploaded_data[session_id]['date_range']['end']}
        - Total des jours: {uploaded_data[session_id]['date_range']['total_days']}
        - Dépôts: {df['Nom Division'].unique().tolist()}
        - Produits: {df['Désignation Article'].nunique()} produits uniques
        - Types d'emballage: {df['Type Emballage'].unique().tolist()}
        
        Exemple de structure de données:
        {df.head().to_dict('records')}
        
        Métriques clés que vous pouvez calculer:
        - Consommation Quotidienne Moyenne (CQM) = Total commandé / Jours dans la période
        - Jours de Couverture (JC) = Stock actuel / CQM
        - Quantité requise pour X jours = (X * CQM) - Stock actuel
        
        Répondez à la question de l'utilisateur en français basée sur ce contexte de données.
        """
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generate response
        response = model.generate_content(context + "\n\nQuestion de l'utilisateur: " + request.query)
        
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