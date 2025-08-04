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

# Locally manufactured articles list
LOCALLY_MADE_ARTICLES = {
    '1011', '1016', '1021', '1022', '1033', '1040', '1051', '1059', '1069', '1071',
    '1515', '1533', '1540', '1559', '1569', '2011', '2014', '2022', '2033', '2040',
    '2069', '3040', '3043', '3056', '3140', '3149', '3156', '3249', '3256', '3948',
    '3953', '4843', '4942', '5030', '5059', '5130', '5159', '5516', '6010', '6011',
    '6016', '6020', '6030', '6040', '6059', '6069', '6120', '6140', '7435', '7436',
    '7521', '7532', '7620', '7630', '7640', '7659', '7949', '7953'
}

# Pydantic models
class CalculationRequest(BaseModel):
    days: int
    product_filter: Optional[List[str]] = None
    packaging_filter: Optional[List[str]] = None

class EnhancedCalculationRequest(BaseModel):
    days: int
    order_session_id: str
    inventory_session_id: Optional[str] = None
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
inventory_data = {}

@app.get("/")
async def root():
    return {"message": "API de Gestion des Stocks fonctionne"}

@app.post("/api/upload-inventory-excel")
async def upload_inventory_excel(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Veuillez télécharger un fichier Excel (.xlsx ou .xls)")
        
        # Read Excel file
        contents = await file.read()
        
        # Parse Excel with pandas
        df = pd.read_excel(contents)
        
        # Validate required columns for inventory data
        required_columns = ['Division', 'Article', 'Désignation article', 'STOCK À DATE']
        
        # Handle potential variations in column names (especially accented characters)
        df_columns = df.columns.tolist()
        
        # Check for column variations
        column_mapping = {}
        for required_col in required_columns:
            found = False
            for df_col in df_columns:
                if required_col == df_col:
                    column_mapping[required_col] = df_col
                    found = True
                    break
                elif required_col == 'STOCK À DATE' and df_col in ['STOCK A DATE', 'STOCK À DATE', 'STOCK A DATE']:
                    column_mapping[required_col] = df_col
                    found = True
                    break
                elif required_col == 'Désignation article' and df_col in ['Designation article', 'Désignation article']:
                    column_mapping[required_col] = df_col
                    found = True
                    break
            
            if not found:
                column_mapping[required_col] = None
        
        missing_columns = [col for col, mapped in column_mapping.items() if mapped is None]
        if missing_columns:
            available_columns = ', '.join(df.columns.tolist())
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes pour les données d'inventaire: {', '.join(missing_columns)}. Colonnes disponibles: {available_columns}"
            )
        
        # Rename columns to standard names if needed
        rename_dict = {v: k for k, v in column_mapping.items() if v != k and v is not None}
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        # Clean and process inventory data
        df['Article'] = df['Article'].astype(str)
        df['STOCK À DATE'] = pd.to_numeric(df['STOCK À DATE'], errors='coerce')
        
        # Remove rows with invalid data
        df = df.dropna(subset=['Article', 'STOCK À DATE'])
        
        # Convert numpy types to Python native types for MongoDB compatibility
        df['STOCK À DATE'] = df['STOCK À DATE'].astype(float)
        
        # Generate session ID for this inventory upload
        session_id = str(uuid.uuid4())
        
        # Get unique values for overview
        unique_divisions = sorted(df['Division'].unique().tolist())
        unique_articles = sorted(df['Article'].unique().tolist())
        total_stock = float(df['STOCK À DATE'].sum())  # Convert to Python float
        
        # Store inventory data temporarily
        inventory_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'summary': {
                'divisions': unique_divisions,
                'articles_count': len(unique_articles),
                'total_stock': total_stock,
                'records_count': len(df)
            }
        }
        
        # Convert DataFrame to dict with Python native types for MongoDB
        data_records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                # Convert numpy types to Python native types
                if pd.isna(value):
                    record[col] = None
                elif isinstance(value, (np.integer, np.int64)):
                    record[col] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[col] = float(value)
                else:
                    record[col] = value
            data_records.append(record)
        
        # Save to MongoDB
        document = {
            'session_id': session_id,
            'type': 'inventory',
            'data': data_records,
            'upload_time': datetime.now(),
            'summary': inventory_data[session_id]['summary']
        }
        collection.insert_one(document)
        
        return {
            "session_id": session_id,
            "message": "Données d'inventaire téléchargées avec succès",
            "records_count": len(df),
            "summary": inventory_data[session_id]['summary']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du fichier d'inventaire: {str(e)}")

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
            'type': 'orders',
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@app.post("/api/enhanced-calculate")
async def enhanced_calculate_requirements(request: EnhancedCalculationRequest):
    try:
        # Validate order session
        if request.order_session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session de commandes non trouvée")
        
        # Get order data
        order_data = uploaded_data[request.order_session_id]['data']
        order_df = pd.DataFrame(order_data)
        order_df['Date de Commande'] = pd.to_datetime(order_df['Date de Commande'])
        
        # Apply filters to order data
        if request.product_filter and len(request.product_filter) > 0:
            order_df = order_df[order_df['Désignation Article'].isin(request.product_filter)]
        
        if request.packaging_filter and len(request.packaging_filter) > 0:
            order_df = order_df[order_df['Type Emballage'].isin(request.packaging_filter)]
        
        if order_df.empty:
            return {
                "calculations": [],
                "inventory_status": "no_inventory_data",
                "summary": {
                    "total_depots": 0,
                    "total_products": 0,
                    "message": "Aucune donnée trouvée avec les filtres appliqués"
                }
            }
        
        # Calculate requirements (existing logic)
        date_range_days = (order_df['Date de Commande'].max() - order_df['Date de Commande'].min()).days + 1
        
        grouped = order_df.groupby(['Nom Division', 'Article', 'Désignation Article', 'Type Emballage']).agg({
            'Quantité Commandée': 'sum',
            'Stock Utilisation Libre': 'last',
            'Quantité en Palette': 'last',  # Add palette quantity
            'Date de Commande': ['min', 'max']
        }).reset_index()
        
        grouped.columns = [
            'depot', 'article_code', 'article_name', 'packaging_type',
            'total_ordered', 'current_stock', 'palette_quantity', 'first_date', 'last_date'
        ]
        
        # Calculate basic requirements
        results = []
        for _, row in grouped.iterrows():
            adc = row['total_ordered'] / date_range_days if date_range_days > 0 else 0
            doc = row['current_stock'] / adc if adc > 0 else float('inf')
            required_stock = request.days * adc
            quantity_to_send = max(0, required_stock - row['current_stock'])
            
            # Calculate palettes needed for this item
            # Formula: number of palettes = Quantité à Envoyer / 30
            palettes_needed = round(quantity_to_send / 30, 2) if quantity_to_send > 0 else 0
            
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
            
            item_id = f"{row['depot']}_{row['article_code']}_{row['packaging_type']}"
            
            # Check if article is locally made
            is_locally_made = str(row['article_code']) in LOCALLY_MADE_ARTICLES
            sourcing_status = 'local' if is_locally_made else 'external'
            sourcing_text = 'Production Locale' if is_locally_made else 'Sourcing Externe'
            
            result_item = {
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
                'palette_quantity': palettes_needed,
                'priority': priority,
                'priority_text': priority_text,
                'sourcing_status': sourcing_status,
                'sourcing_text': sourcing_text,
                'is_locally_made': is_locally_made,
                'selected': False
            }
            
            # Add inventory availability if inventory data is provided
            if request.inventory_session_id and request.inventory_session_id in inventory_data:
                inventory_df = pd.DataFrame(inventory_data[request.inventory_session_id]['data'])
                
                # Find matching article in inventory
                matching_inventory = inventory_df[inventory_df['Article'].astype(str) == str(row['article_code'])]
                
                if not matching_inventory.empty:
                    total_available = float(matching_inventory['STOCK À DATE'].sum())
                    result_item['inventory_available'] = round(total_available, 2)
                    result_item['can_fulfill'] = bool(total_available >= quantity_to_send)
                    
                    if total_available >= quantity_to_send:
                        result_item['inventory_status'] = 'sufficient'
                        result_item['inventory_status_text'] = 'EN STOCK'
                        result_item['inventory_status_color'] = 'text-green-600 bg-green-50'
                    elif total_available > 0:
                        result_item['inventory_status'] = 'partial'
                        result_item['inventory_status_text'] = 'STOCK FAIBLE'
                        result_item['inventory_status_color'] = 'text-yellow-600 bg-yellow-50'
                        result_item['inventory_shortage'] = round(quantity_to_send - total_available, 2)
                    else:
                        result_item['inventory_status'] = 'insufficient'
                        result_item['inventory_status_text'] = '[X] Insuffisant'
                        result_item['inventory_status_color'] = 'text-red-600 bg-red-50'
                        result_item['inventory_shortage'] = round(quantity_to_send, 2)
                else:
                    result_item['inventory_available'] = 0.00
                    result_item['can_fulfill'] = False
                    result_item['inventory_status'] = 'not_found'
                    result_item['inventory_status_text'] = '[?] Non trouvé'
                    result_item['inventory_status_color'] = 'text-gray-600 bg-gray-50'
                    result_item['inventory_shortage'] = round(quantity_to_send, 2)
            else:
                result_item['inventory_status'] = 'no_data'
                result_item['inventory_status_text'] = '[i] Pas de données'
                result_item['inventory_status_color'] = 'text-blue-600 bg-blue-50'
            
            results.append(result_item)
        
        # ==================== 20-PALETTE DELIVERY OPTIMIZATION ====================
        # Group results by depot to calculate delivery efficiency
        depot_groups = {}
        for item in results:
            depot = item['depot']
            if depot not in depot_groups:
                depot_groups[depot] = {
                    'items': [],
                    'total_palettes': 0,
                    'delivery_status': 'efficient',
                    'suggested_items': []
                }
            depot_groups[depot]['items'].append(item)
            depot_groups[depot]['total_palettes'] += item['palette_quantity']
        
        # Process each depot for 20-palette minimum constraint
        all_depot_items = pd.DataFrame(order_data)  # Get all available items for suggestions
        
        for depot_name, depot_info in depot_groups.items():
            if depot_info['total_palettes'] < 20:
                depot_info['delivery_status'] = 'inefficient'
                palettes_needed = 20 - depot_info['total_palettes']
                
                # Find potential filler items from the same depot
                depot_all_items = all_depot_items[all_depot_items['Nom Division'] == depot_name]
                
                # Get items that are not already in results
                current_item_codes = {item['article_code'] for item in depot_info['items']}
                potential_fillers = depot_all_items[~depot_all_items['Article'].astype(str).isin(current_item_codes)]
                
                # Calculate potential filler suggestions
                filler_suggestions = []
                if not potential_fillers.empty:
                    # Group potential fillers and calculate basic metrics
                    filler_grouped = potential_fillers.groupby(['Article', 'Désignation Article', 'Type Emballage']).agg({
                        'Quantité Commandée': 'sum',
                        'Stock Utilisation Libre': 'last',
                        'Quantité en Palette': 'last'
                    }).reset_index()
                    
                    # Calculate priority for each potential filler
                    for _, filler_row in filler_grouped.iterrows():
                        filler_adc = filler_row['Quantité Commandée'] / date_range_days if date_range_days > 0 else 0
                        filler_doc = filler_row['Stock Utilisation Libre'] / filler_adc if filler_adc > 0 else float('inf')
                        filler_required = request.days * filler_adc
                        filler_to_send = max(0, filler_required - filler_row['Stock Utilisation Libre'])
                        
                        if filler_to_send > 0:  # Only suggest items that actually need restocking
                            filler_suggestions.append({
                                'article_code': filler_row['Article'],
                                'article_name': filler_row['Désignation Article'],
                                'packaging_type': filler_row['Type Emballage'],
                                'current_stock': filler_row['Stock Utilisation Libre'],
                                'quantity_to_send': round(filler_to_send, 2),
                                'palette_quantity': filler_row['Quantité en Palette'],
                                'days_of_coverage': round(filler_doc, 1) if filler_doc != float('inf') else 'Infinie',
                                'average_daily_consumption': round(filler_adc, 2)
                            })
                    
                    # Sort by days of coverage (lowest first - most urgent)
                    filler_suggestions.sort(key=lambda x: x['days_of_coverage'] if isinstance(x['days_of_coverage'], (int, float)) else float('inf'))
                
                depot_info['suggested_items'] = filler_suggestions[:5]  # Limit to top 5 suggestions
                depot_info['palettes_needed_to_reach_minimum'] = palettes_needed
                
                # Modify priority of existing items in inefficient depots
                for item in depot_info['items']:
                    if item['priority'] == 'medium':
                        item['priority'] = 'low'
                        item['priority_text'] = 'Faible (Livr. Inefficace)'
                    elif item['priority'] == 'high':
                        item['priority'] = 'medium' 
                        item['priority_text'] = 'Moyen (Livr. Inefficace)'
                    # Add delivery efficiency flags
                    item['delivery_efficient'] = False
                    item['delivery_status'] = 'Livraison inefficace (<20 palettes)'
                    item['delivery_status_color'] = 'text-orange-600 bg-orange-50'
            else:
                # Efficient delivery - boost priority for urgent items
                for item in depot_info['items']:
                    if item['priority'] == 'medium':
                        item['priority'] = 'high'
                        item['priority_text'] = 'Critique (Livr. Efficace)'
                    # Add delivery efficiency flags
                    item['delivery_efficient'] = True
                    item['delivery_status'] = 'Livraison efficace (≥20 palettes)'
                    item['delivery_status_color'] = 'text-green-600 bg-green-50'
        
        # Update results with delivery optimization information
        optimized_results = []
        depot_summaries = []
        
        for depot_name, depot_info in depot_groups.items():
            # Add depot summary
            depot_summaries.append({
                'depot_name': depot_name,
                'total_palettes': depot_info['total_palettes'],
                'delivery_status': depot_info['delivery_status'],
                'items_count': len(depot_info['items']),
                'suggested_items': depot_info['suggested_items'],
                'palettes_needed': depot_info.get('palettes_needed_to_reach_minimum', 0)
            })
            
            # Add items to optimized results
            optimized_results.extend(depot_info['items'])
        
        # Replace original results with optimized results
        results = optimized_results
        
        # Sort by inventory availability and priority
        if request.inventory_session_id:
            # Priority order: insufficient/not_found first, then by priority
            def sort_key(x):
                inventory_priority = {
                    'insufficient': 0,
                    'not_found': 1,
                    'partial': 2,
                    'sufficient': 3,
                    'no_data': 4
                }
                business_priority = {'high': 0, 'medium': 1, 'low': 2}
                return (inventory_priority.get(x.get('inventory_status', 'no_data'), 4), 
                        business_priority[x['priority']], 
                        -x['quantity_to_send'])
            results.sort(key=sort_key)
        else:
            # Original sorting
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            results.sort(key=lambda x: (priority_order[x['priority']], -x['quantity_to_send']))
        
        # Calculate summary statistics
        summary = {
            "total_depots": len(order_df['Nom Division'].unique()),
            "total_products": len(results),
            "date_range_days": date_range_days,
            "requested_days": request.days,
            "high_priority": [r for r in results if r['priority'] == 'high'],
            "medium_priority": [r for r in results if r['priority'] == 'medium'],
            "low_priority": [r for r in results if r['priority'] == 'low'],
            "no_stock_needed": [r for r in results if r['quantity_to_send'] == 0],
            "locally_made": [r for r in results if r['is_locally_made']],
            "external_sourcing": [r for r in results if not r['is_locally_made']],
            "sourcing_summary": {
                "local_items": len([r for r in results if r['is_locally_made']]),
                "external_items": len([r for r in results if not r['is_locally_made']])
            },
            # Add delivery optimization summary
            "delivery_optimization": {
                "efficient_depots": len([d for d in depot_summaries if d['delivery_status'] == 'efficient']),
                "inefficient_depots": len([d for d in depot_summaries if d['delivery_status'] == 'inefficient']),
                "total_palettes": sum([d['total_palettes'] for d in depot_summaries]),
                "depot_summaries": depot_summaries
            }
        }
        
        # Add inventory-specific summary if available
        if request.inventory_session_id and request.inventory_session_id in inventory_data:
            inventory_summary = {
                "sufficient_items": len([r for r in results if r.get('inventory_status') == 'sufficient']),
                "partial_items": len([r for r in results if r.get('inventory_status') == 'partial']),
                "insufficient_items": len([r for r in results if r.get('inventory_status') == 'insufficient']),
                "not_found_items": len([r for r in results if r.get('inventory_status') == 'not_found']),
                "total_inventory_shortage": sum([r.get('inventory_shortage', 0) for r in results])
            }
            summary.update(inventory_summary)
            summary["inventory_status"] = "available"
        else:
            summary["inventory_status"] = "no_inventory_data"
        
        return {
            "calculations": results,
            "summary": summary,
            "inventory_status": summary["inventory_status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul amélioré: {str(e)}")

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
            'Quantité en Palette': 'last',  # Add palette quantity
            'Date de Commande': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        grouped.columns = [
            'depot', 'article_code', 'article_name', 'packaging_type',
            'total_ordered', 'current_stock', 'palette_quantity', 'first_date', 'last_date'
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
            
            # Calculate palettes needed for this item
            # Formula: number of palettes = Quantité à Envoyer / 30
            palettes_needed = round(quantity_to_send / 30, 2) if quantity_to_send > 0 else 0
            
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
            
            # Check if article is locally made
            is_locally_made = str(row['article_code']) in LOCALLY_MADE_ARTICLES
            sourcing_status = 'local' if is_locally_made else 'external'
            sourcing_text = 'Production Locale' if is_locally_made else 'Sourcing Externe'
            
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
                'palette_quantity': palettes_needed,
                'priority': priority,
                'priority_text': priority_text,
                'sourcing_status': sourcing_status,
                'sourcing_text': sourcing_text,
                'is_locally_made': is_locally_made,
                'selected': False
            })
        
        # ==================== 20-PALETTE DELIVERY OPTIMIZATION ====================
        # Group results by depot to calculate delivery efficiency
        depot_groups = {}
        for item in results:
            depot = item['depot']
            if depot not in depot_groups:
                depot_groups[depot] = {
                    'items': [],
                    'total_palettes': 0,
                    'delivery_status': 'efficient',
                    'suggested_items': []
                }
            depot_groups[depot]['items'].append(item)
            depot_groups[depot]['total_palettes'] += item['palette_quantity']
        
        # Process each depot for 20-palette minimum constraint
        for depot_name, depot_info in depot_groups.items():
            if depot_info['total_palettes'] < 20:
                depot_info['delivery_status'] = 'inefficient'
                palettes_needed = 20 - depot_info['total_palettes']
                
                # Find potential filler items from the same depot
                depot_all_items = df[df['Nom Division'] == depot_name]
                
                # Get items that are not already in results
                current_item_codes = {item['article_code'] for item in depot_info['items']}
                potential_fillers = depot_all_items[~depot_all_items['Article'].astype(str).isin(current_item_codes)]
                
                # Calculate potential filler suggestions
                filler_suggestions = []
                if not potential_fillers.empty:
                    # Group potential fillers and calculate basic metrics
                    filler_grouped = potential_fillers.groupby(['Article', 'Désignation Article', 'Type Emballage']).agg({
                        'Quantité Commandée': 'sum',
                        'Stock Utilisation Libre': 'last',
                        'Quantité en Palette': 'last'
                    }).reset_index()
                    
                    # Calculate priority for each potential filler
                    for _, filler_row in filler_grouped.iterrows():
                        filler_adc = filler_row['Quantité Commandée'] / date_range_days if date_range_days > 0 else 0
                        filler_doc = filler_row['Stock Utilisation Libre'] / filler_adc if filler_adc > 0 else float('inf')
                        filler_required = request.days * filler_adc
                        filler_to_send = max(0, filler_required - filler_row['Stock Utilisation Libre'])
                        
                        if filler_to_send > 0:  # Only suggest items that actually need restocking
                            filler_suggestions.append({
                                'article_code': filler_row['Article'],
                                'article_name': filler_row['Désignation Article'],
                                'packaging_type': filler_row['Type Emballage'],
                                'current_stock': filler_row['Stock Utilisation Libre'],
                                'quantity_to_send': round(filler_to_send, 2),
                                'palette_quantity': filler_row['Quantité en Palette'],
                                'days_of_coverage': round(filler_doc, 1) if filler_doc != float('inf') else 'Infinie',
                                'average_daily_consumption': round(filler_adc, 2)
                            })
                    
                    # Sort by days of coverage (lowest first - most urgent)
                    filler_suggestions.sort(key=lambda x: x['days_of_coverage'] if isinstance(x['days_of_coverage'], (int, float)) else float('inf'))
                
                depot_info['suggested_items'] = filler_suggestions[:5]  # Limit to top 5 suggestions
                depot_info['palettes_needed_to_reach_minimum'] = palettes_needed
                
                # Modify priority of existing items in inefficient depots
                for item in depot_info['items']:
                    if item['priority'] == 'medium':
                        item['priority'] = 'low'
                        item['priority_text'] = 'Faible (Livr. Inefficace)'
                    elif item['priority'] == 'high':
                        item['priority'] = 'medium' 
                        item['priority_text'] = 'Moyen (Livr. Inefficace)'
                    # Add delivery efficiency flags
                    item['delivery_efficient'] = False
                    item['delivery_status'] = 'Livraison inefficace (<20 palettes)'
                    item['delivery_status_color'] = 'text-orange-600 bg-orange-50'
            else:
                # Efficient delivery - boost priority for urgent items
                for item in depot_info['items']:
                    if item['priority'] == 'medium':
                        item['priority'] = 'high'
                        item['priority_text'] = 'Critique (Livr. Efficace)'
                    # Add delivery efficiency flags
                    item['delivery_efficient'] = True
                    item['delivery_status'] = 'Livraison efficace (≥20 palettes)'
                    item['delivery_status_color'] = 'text-green-600 bg-green-50'
        
        # Update results with delivery optimization information
        optimized_results = []
        depot_summaries = []
        
        for depot_name, depot_info in depot_groups.items():
            # Add depot summary
            depot_summaries.append({
                'depot_name': depot_name,
                'total_palettes': depot_info['total_palettes'],
                'delivery_status': depot_info['delivery_status'],
                'items_count': len(depot_info['items']),
                'suggested_items': depot_info['suggested_items'],
                'palettes_needed': depot_info.get('palettes_needed_to_reach_minimum', 0)
            })
            
            # Add items to optimized results
            optimized_results.extend(depot_info['items'])
        
        # Replace original results with optimized results
        results = optimized_results
        
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
                "no_stock_needed": [r for r in results if r['quantity_to_send'] == 0],
                "locally_made": [r for r in results if r['is_locally_made']],
                "external_sourcing": [r for r in results if not r['is_locally_made']],
                "sourcing_summary": {
                    "local_items": len([r for r in results if r['is_locally_made']]),
                    "external_items": len([r for r in results if not r['is_locally_made']])
                },
                # Add delivery optimization summary
                "delivery_optimization": {
                    "efficient_depots": len([d for d in depot_summaries if d['delivery_status'] == 'efficient']),
                    "inefficient_depots": len([d for d in depot_summaries if d['delivery_status'] == 'inefficient']), 
                    "total_palettes": sum([d['total_palettes'] for d in depot_summaries]),
                    "depot_summaries": depot_summaries
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des exigences: {str(e)}")

@app.get("/api/inventory/{session_id}")
async def get_inventory_data(session_id: str):
    try:
        if session_id not in inventory_data:
            raise HTTPException(status_code=404, detail="Session d'inventaire non trouvée")
        
        return inventory_data[session_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données d'inventaire: {str(e)}")

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
        
        # Create Excel workbook with multiple sheets
        wb = openpyxl.Workbook()
        
        # Remove default sheet and create custom sheets
        wb.remove(wb.active)
        
        # Create sheets
        summary_sheet = wb.create_sheet("Résumé Exécutif")
        critical_sheet = wb.create_sheet("Articles Critiques")
        analysis_sheet = wb.create_sheet("Analyse Détaillée")
        
        # Professional color scheme
        colors = {
            'header_bg': "2E4C85",      # Professional blue
            'header_text': "FFFFFF",     # White text
            'critical_bg': "FFE6E6",     # Light red for critical
            'medium_bg': "FFF2CC",       # Light yellow for medium
            'low_bg': "E6F3E6",         # Light green for low
            'local_bg': "E6F7FF",       # Light blue for local
            'external_bg': "FFF7E6",    # Light orange for external
            'summary_bg': "F8F9FA",     # Light gray for summary
            'accent': "4A90E2"          # Accent blue
        }
        
        # Professional fonts
        header_font = Font(name="Calibri", size=12, bold=True, color=colors['header_text'])
        title_font = Font(name="Calibri", size=16, bold=True, color=colors['header_bg'])
        subtitle_font = Font(name="Calibri", size=11, bold=True, color=colors['header_bg'])
        data_font = Font(name="Calibri", size=10)
        
        # ==================== SUMMARY SHEET ====================
        current_row = 1
        
        # Company header with professional styling
        summary_sheet.merge_cells(f'A{current_row}:H{current_row}')
        header_cell = summary_sheet[f'A{current_row}']
        header_cell.value = "CBGS - RAPPORT D'ANALYSE DES STOCKS CRITIQUES"
        header_cell.font = Font(name="Calibri", size=18, bold=True, color=colors['header_bg'])
        header_cell.alignment = Alignment(horizontal="center", vertical="center")
        header_cell.fill = PatternFill(start_color=colors['summary_bg'], end_color=colors['summary_bg'], fill_type="solid")
        summary_sheet.row_dimensions[current_row].height = 30
        current_row += 2
        
        # Report metadata
        metadata = [
            ["Date de génération:", datetime.now().strftime('%d/%m/%Y à %H:%M')],
            ["Nombre d'articles analysés:", len(request.selected_items)],
            ["Session d'analyse:", session_id[:8] + "..."],
            ["Période de couverture demandée:", "30 jours (standard)"]
        ]
        
        for label, value in metadata:
            summary_sheet[f'A{current_row}'] = label
            summary_sheet[f'A{current_row}'].font = subtitle_font
            summary_sheet[f'B{current_row}'] = value
            summary_sheet[f'B{current_row}'].font = data_font
            current_row += 1
        current_row += 1
        
        # Calculate summary statistics
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        sourcing_counts = {'local': 0, 'external': 0}
        total_stock_needed = 0
        total_current_stock = 0
        
        for item in request.selected_items:
            priority_counts[item.get('priority', 'low')] += 1
            if item.get('is_locally_made', False):
                sourcing_counts['local'] += 1
            else:
                sourcing_counts['external'] += 1
            total_stock_needed += item.get('quantity_to_send', 0)
            total_current_stock += item.get('current_stock', 0)
        
        # Summary statistics section
        summary_sheet[f'A{current_row}'] = "RÉSUMÉ STATISTIQUE"
        summary_sheet[f'A{current_row}'].font = title_font
        summary_sheet.merge_cells(f'A{current_row}:H{current_row}')
        current_row += 2
        
        # Priority breakdown
        summary_sheet[f'A{current_row}'] = "Répartition par Priorité:"
        summary_sheet[f'A{current_row}'].font = subtitle_font
        current_row += 1
        
        priority_data = [
            ["🔴 Priorité Critique:", priority_counts['high'], "Réapprovisionnement URGENT requis"],
            ["🟡 Priorité Moyenne:", priority_counts['medium'], "Planification nécessaire"],
            ["🟢 Priorité Faible:", priority_counts['low'], "Surveillance recommandée"]
        ]
        
        for desc, count, action in priority_data:
            summary_sheet[f'A{current_row}'] = desc
            summary_sheet[f'A{current_row}'].font = data_font
            summary_sheet[f'B{current_row}'] = count
            summary_sheet[f'B{current_row}'].font = Font(name="Calibri", size=11, bold=True)
            summary_sheet[f'C{current_row}'] = action
            summary_sheet[f'C{current_row}'].font = data_font
            current_row += 1
        current_row += 1
        
        # Sourcing breakdown
        summary_sheet[f'A{current_row}'] = "Analyse du Sourcing:"
        summary_sheet[f'A{current_row}'].font = subtitle_font
        current_row += 1
        
        sourcing_data = [
            ["🏭 Production Locale:", sourcing_counts['local'], f"{(sourcing_counts['local']/len(request.selected_items)*100):.1f}%"],
            ["🌍 Sourcing Externe:", sourcing_counts['external'], f"{(sourcing_counts['external']/len(request.selected_items)*100):.1f}%"]
        ]
        
        for desc, count, percentage in sourcing_data:
            summary_sheet[f'A{current_row}'] = desc
            summary_sheet[f'A{current_row}'].font = data_font
            summary_sheet[f'B{current_row}'] = count
            summary_sheet[f'B{current_row}'].font = Font(name="Calibri", size=11, bold=True)
            summary_sheet[f'C{current_row}'] = percentage
            summary_sheet[f'C{current_row}'].font = data_font
            current_row += 1
        current_row += 1
        
        # Financial impact section
        summary_sheet[f'A{current_row}'] = "Impact Logistique:"
        summary_sheet[f'A{current_row}'].font = subtitle_font
        current_row += 1
        
        impact_data = [
            ["Stock actuel total:", f"{total_current_stock:,.0f} unités"],
            ["Quantité à réapprovisionner:", f"{total_stock_needed:,.0f} unités"],
            ["Ratio de réapprovisionnement:", f"{(total_stock_needed/total_current_stock*100):.1f}%" if total_current_stock > 0 else "N/A"]
        ]
        
        for label, value in impact_data:
            summary_sheet[f'A{current_row}'] = label
            summary_sheet[f'A{current_row}'].font = data_font
            summary_sheet[f'B{current_row}'] = value
            summary_sheet[f'B{current_row}'].font = Font(name="Calibri", size=11, bold=True)
            current_row += 1
        
        # Format summary sheet columns
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            summary_sheet.column_dimensions[col].width = 25
        
        # ==================== CRITICAL ITEMS SHEET ====================
        current_row = 1
        
        # Sheet header
        critical_sheet.merge_cells(f'A{current_row}:L{current_row}')
        header_cell = critical_sheet[f'A{current_row}']
        header_cell.value = "DÉTAIL DES ARTICLES CRITIQUES"
        header_cell.font = title_font
        header_cell.alignment = Alignment(horizontal="center", vertical="center")
        header_cell.fill = PatternFill(start_color=colors['summary_bg'], end_color=colors['summary_bg'], fill_type="solid")
        critical_sheet.row_dimensions[current_row].height = 25
        current_row += 2
        
        # Enhanced table headers
        headers = [
            ('Dépôt', 'Nom du dépôt concerné'),
            ('Code Article', 'Référence produit unique'),
            ('Désignation', 'Description complète du produit'),
            ('Emballage', 'Type de conditionnement'),
            ('Stock Actuel', 'Quantité en stock actuelle'),
            ('Conso. Quotidienne', 'Consommation moyenne par jour'),
            ('Jours Couverture', 'Autonomie actuelle en jours'),
            ('Quantité Requise', 'Quantité à réapprovisionner'),
            ('Sourcing', 'Mode d\'approvisionnement'),
            ('Priorité', 'Niveau d\'urgence'),
            ('Statut', 'État de criticité'),
            ('Action Recommandée', 'Mesure à prendre')
        ]
        
        # Create header row with professional styling
        for col_num, (header, description) in enumerate(headers, 1):
            cell = critical_sheet.cell(row=current_row, column=col_num, value=header)
            cell.font = header_font
            cell.fill = PatternFill(start_color=colors['header_bg'], end_color=colors['header_bg'], fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = openpyxl.styles.Border(
                left=openpyxl.styles.Side(style='thin'),
                right=openpyxl.styles.Side(style='thin'),
                top=openpyxl.styles.Side(style='thin'),
                bottom=openpyxl.styles.Side(style='thin')
            )
            
            # Add description as comment
            comment = openpyxl.comments.Comment(description, "CBGS System")
            comment.width = 200
            comment.height = 50
            cell.comment = comment
        
        critical_sheet.row_dimensions[current_row].height = 20
        current_row += 1
        
        # Sort items by priority (critical first) then by quantity needed
        sorted_items = sorted(request.selected_items, 
                            key=lambda x: (0 if x.get('priority') == 'high' else 1 if x.get('priority') == 'medium' else 2, 
                                         -x.get('quantity_to_send', 0)))
        
        # Add data rows with enhanced formatting
        for idx, item in enumerate(sorted_items, 1):
            # Determine action and status based on priority and data
            priority = item.get('priority', 'low')
            if priority == 'high':
                action = "🚨 URGENT - Réapprovisionnement IMMÉDIAT"
                status = "CRITIQUE"
                row_fill = colors['critical_bg']
            elif priority == 'medium':
                action = "[!] Planifier réapprovisionnement sous 7 jours"
                status = "ATTENTION"
                row_fill = colors['medium_bg']
            else:
                action = "[OK] Surveiller évolution"
                status = "STABLE"
                row_fill = colors['low_bg']
            
            # Determine sourcing background
            if item.get('is_locally_made', False):
                sourcing_fill = colors['local_bg']
            else:
                sourcing_fill = colors['external_bg']
            
            row_data = [
                item.get('depot', ''),
                item.get('article_code', ''),
                item.get('article_name', ''),
                item.get('packaging_type', ''),
                item.get('current_stock', 0),
                round(item.get('average_daily_consumption', 0), 2),
                item.get('days_of_coverage', 0),
                round(item.get('quantity_to_send', 0), 2),
                item.get('sourcing_text', 'Non défini'),
                item.get('priority_text', ''),
                status,
                action
            ]
            
            for col_num, value in enumerate(row_data, 1):
                cell = critical_sheet.cell(row=current_row, column=col_num, value=value)
                cell.font = data_font
                cell.alignment = Alignment(horizontal="left" if col_num <= 4 else "center" if col_num >= 10 else "right")
                
                # Apply conditional formatting
                if col_num == 9:  # Sourcing column
                    cell.fill = PatternFill(start_color=sourcing_fill, end_color=sourcing_fill, fill_type="solid")
                elif col_num == 10:  # Priority column
                    if priority == 'high':
                        cell.font = Font(name="Calibri", size=10, bold=True, color="CC0000")
                    elif priority == 'medium':
                        cell.font = Font(name="Calibri", size=10, bold=True, color="FF8C00")
                elif col_num == 11:  # Status column
                    cell.fill = PatternFill(start_color=row_fill, end_color=row_fill, fill_type="solid")
                    cell.font = Font(name="Calibri", size=10, bold=True)
                
                # Add borders
                cell.border = openpyxl.styles.Border(
                    left=openpyxl.styles.Side(style='thin'),
                    right=openpyxl.styles.Side(style='thin'),
                    top=openpyxl.styles.Side(style='thin'),
                    bottom=openpyxl.styles.Side(style='thin')
                )
            
            current_row += 1
        
        # ==================== ANALYSIS SHEET ====================
        current_row = 1
        
        # Sheet header
        analysis_sheet.merge_cells(f'A{current_row}:F{current_row}')
        header_cell = analysis_sheet[f'A{current_row}']
        header_cell.value = "ANALYSE APPROFONDIE PAR CATÉGORIE"
        header_cell.font = title_font
        header_cell.alignment = Alignment(horizontal="center", vertical="center")
        header_cell.fill = PatternFill(start_color=colors['summary_bg'], end_color=colors['summary_bg'], fill_type="solid")
        analysis_sheet.row_dimensions[current_row].height = 25
        current_row += 2
        
        # Group items by depot
        depot_groups = {}
        for item in request.selected_items:
            depot = item.get('depot', 'Non spécifié')
            if depot not in depot_groups:
                depot_groups[depot] = []
            depot_groups[depot].append(item)
        
        # Depot analysis
        for depot, items in depot_groups.items():
            analysis_sheet[f'A{current_row}'] = f"DÉPÔT: {depot}"
            analysis_sheet[f'A{current_row}'].font = subtitle_font
            analysis_sheet.merge_cells(f'A{current_row}:F{current_row}')
            current_row += 1
            
            # Depot statistics
            depot_critical = len([item for item in items if item.get('priority') == 'high'])
            depot_total_needed = sum([item.get('quantity_to_send', 0) for item in items])
            depot_local = len([item for item in items if item.get('is_locally_made', False)])
            
            stats = [
                ["Articles critiques:", depot_critical],
                ["Total à réapprovisionner:", f"{depot_total_needed:,.0f} unités"],
                ["Production locale:", f"{depot_local}/{len(items)} articles"],
                ["Taux de criticité:", f"{(depot_critical/len(items)*100):.1f}%"]
            ]
            
            for label, value in stats:
                analysis_sheet[f'B{current_row}'] = label
                analysis_sheet[f'B{current_row}'].font = data_font
                analysis_sheet[f'C{current_row}'] = value
                analysis_sheet[f'C{current_row}'].font = Font(name="Calibri", size=10, bold=True)
                current_row += 1
            
            current_row += 1
        
        # Professional column widths and formatting
        column_widths = {
            'critical': [15, 12, 25, 12, 12, 15, 12, 15, 18, 12, 12, 35],
            'summary': [25, 20, 30, 15, 15, 15, 15, 15],
            'analysis': [20, 25, 20, 15, 15, 15]
        }
        
        # Apply column widths
        for i, width in enumerate(column_widths['critical'], 1):
            critical_sheet.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
        
        for i, width in enumerate(column_widths['summary'], 1):
            summary_sheet.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
            
        for i, width in enumerate(column_widths['analysis'], 1):
            analysis_sheet.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
        
        # Freeze panes for better navigation
        critical_sheet.freeze_panes = 'A4'
        
        # Add auto-filter to critical items
        critical_sheet.auto_filter.ref = f"A3:L{len(sorted_items) + 3}"
        
        # Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        # Create professional filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"CBGS_Rapport_Stocks_Critiques_{timestamp}.xlsx"
        
        # Return file as download
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export professionnel: {str(e)}")

@app.post("/api/gemini-query/{session_id}")
async def gemini_query(session_id: str, request: GeminiQueryRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Get data
        data = uploaded_data[session_id]['data']
        df = pd.DataFrame(data)
        
        # Create enhanced context for Gemini optimized for actionable single-day analysis
        # First, calculate key insights from the data
        top_products = df.groupby('Désignation Article')['Quantité Commandée'].sum().sort_values(ascending=False).head(5)
        depot_summary = df.groupby('Nom Division')['Quantité Commandée'].sum().sort_values(ascending=False)
        packaging_summary = df.groupby('Type Emballage')['Quantité Commandée'].sum().sort_values(ascending=False)
        
        context = f"""
        Vous êtes un expert en analyse de stocks avec accès aux données détaillées. Analysez ces données CONCRÈTES.
        
        IMPORTANT: Donnez une réponse PRÉCISE et ACTIONNABLE basée sur les données réelles, pas de généralités.
        
        DONNÉES DÉTAILLÉES DISPONIBLES:
        - Date d'analyse: {uploaded_data[session_id]['date_range']['start']}
        - Nombre d'enregistrements: {len(df)}
        - Dépôts actifs: {list(df['Nom Division'].unique())}
        - Volume total commandé: {df['Quantité Commandée'].sum():,.0f} unités
        - Stock total disponible: {df['Stock Utilisation Libre'].sum():,.0f} unités
        
        TOP 5 PRODUITS LES PLUS COMMANDÉS AUJOURD'HUI:
        {chr(10).join([f"- {prod}: {qty:,.0f} unités" for prod, qty in top_products.items()])}
        
        RÉPARTITION PAR DÉPÔT:
        {chr(10).join([f"- {depot}: {qty:,.0f} unités" for depot, qty in depot_summary.items()])}
        
        RÉPARTITION PAR EMBALLAGE:
        {chr(10).join([f"- {pkg}: {qty:,.0f} unités" for pkg, qty in packaging_summary.items()])}
        
        STOCKS ACTUELS PAR PRODUIT:
        {chr(10).join([f"- {row['Désignation Article']}: {row['Stock Utilisation Libre']:,.0f} unités (Dépôt: {row['Nom Division']})" for _, row in df[['Désignation Article', 'Stock Utilisation Libre', 'Nom Division']].head(10).iterrows()])}
        
        Utilisez ces données précises pour répondre. Donnez des chiffres exacts, nommez les produits et dépôts spécifiques.
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