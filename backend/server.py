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
GEMINI_API_KEY = "AIzaSyDaUyWzYQEDBqFwuniG8KiqKHgtk-l5Dco"
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
    print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")

# Pydantic models
class CalculationRequest(BaseModel):
    days: int
    product_filter: Optional[str] = None
    packaging_filter: Optional[str] = None

class GeminiQueryRequest(BaseModel):
    query: str
    session_id: str

# Store uploaded data temporarily
uploaded_data = {}

@app.get("/")
async def root():
    return {"message": "Stock Management API is running"}

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")
        
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
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Clean and process data
        df['Date de Commande'] = pd.to_datetime(df['Date de Commande'])
        df['Quantité Commandée'] = pd.to_numeric(df['Quantité Commandée'], errors='coerce')
        df['Stock Utilisation Libre'] = pd.to_numeric(df['Stock Utilisation Libre'], errors='coerce')
        
        # Remove rows with invalid data
        df = df.dropna(subset=['Date de Commande', 'Quantité Commandée', 'Stock Utilisation Libre'])
        
        # Generate session ID for this upload
        session_id = str(uuid.uuid4())
        
        # Store data temporarily
        uploaded_data[session_id] = {
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'date_range': {
                'start': df['Date de Commande'].min().strftime('%Y-%m-%d'),
                'end': df['Date de Commande'].max().strftime('%Y-%m-%d'),
                'total_days': (df['Date de Commande'].max() - df['Date de Commande'].min()).days + 1
            }
        }
        
        # Save to MongoDB
        document = {
            'session_id': session_id,
            'data': df.to_dict('records'),
            'upload_time': datetime.now(),
            'date_range': uploaded_data[session_id]['date_range']
        }
        collection.insert_one(document)
        
        return {
            "session_id": session_id,
            "message": "File uploaded successfully",
            "records_count": len(df),
            "date_range": uploaded_data[session_id]['date_range'],
            "depots": df['Nom Division'].unique().tolist(),
            "products": df['Désignation Article'].unique().tolist(),
            "packaging_types": df['Type Emballage'].unique().tolist()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/calculate/{session_id}")
async def calculate_requirements(session_id: str, request: CalculationRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get data
        data = uploaded_data[session_id]['data']
        df = pd.DataFrame(data)
        
        # Convert date column back to datetime
        df['Date de Commande'] = pd.to_datetime(df['Date de Commande'])
        
        # Apply filters
        if request.product_filter:
            df = df[df['Désignation Article'].str.contains(request.product_filter, case=False, na=False)]
        
        if request.packaging_filter:
            df = df[df['Type Emballage'].str.contains(request.packaging_filter, case=False, na=False)]
        
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
            
            results.append({
                'depot': row['depot'],
                'article_code': row['article_code'],
                'article_name': row['article_name'],
                'packaging_type': row['packaging_type'],
                'average_daily_consumption': round(adc, 2),
                'days_of_coverage': round(doc, 1) if doc != float('inf') else 'Infinite',
                'current_stock': row['current_stock'],
                'required_for_x_days': round(required_stock, 2),
                'quantity_to_send': round(quantity_to_send, 2),
                'total_ordered_in_period': row['total_ordered']
            })
        
        # Sort by depot and then by quantity needed (descending)
        results.sort(key=lambda x: (x['depot'], -x['quantity_to_send']))
        
        return {
            "calculations": results,
            "summary": {
                "total_depots": len(df['Nom Division'].unique()),
                "total_products": len(results),
                "date_range_days": date_range_days,
                "requested_days": request.days,
                "high_priority": [r for r in results if isinstance(r['days_of_coverage'], (int, float)) and r['days_of_coverage'] < 7],
                "no_stock_needed": [r for r in results if r['quantity_to_send'] == 0]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating requirements: {str(e)}")

@app.post("/api/gemini-query/{session_id}")
async def gemini_query(session_id: str, request: GeminiQueryRequest):
    try:
        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get data
        data = uploaded_data[session_id]['data']
        df = pd.DataFrame(data)
        
        # Create context for Gemini
        context = f"""
        You are analyzing stock and order data for multiple depots. Here's the data summary:
        
        - Total records: {len(df)}
        - Date range: {uploaded_data[session_id]['date_range']['start']} to {uploaded_data[session_id]['date_range']['end']}
        - Total days: {uploaded_data[session_id]['date_range']['total_days']}
        - Depots: {df['Nom Division'].unique().tolist()}
        - Products: {df['Désignation Article'].nunique()} unique products
        - Packaging types: {df['Type Emballage'].unique().tolist()}
        
        Sample data structure:
        {df.head().to_dict('records')}
        
        Key metrics you can calculate:
        - Average Daily Consumption (ADC) = Total ordered / Days in period
        - Days of Coverage (DOC) = Current stock / ADC
        - Required quantity for X days = (X * ADC) - Current stock
        
        Answer the user's question based on this data context.
        """
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        response = model.generate_content(context + "\n\nUser question: " + request.query)
        
        return {
            "response": response.text,
            "query": request.query,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Gemini query: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)