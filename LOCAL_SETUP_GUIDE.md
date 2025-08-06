# 🏠 Local Development Setup Guide

## Prerequisites
- **Node.js** (v18 or higher) - Download from: https://nodejs.org/
- **Python** (v3.9 or higher) - Download from: https://python.org/
- **MongoDB** (or MongoDB Atlas for cloud) - Download from: https://mongodb.com/

## 📁 Project Structure
```
inventory-management-system/
├── backend/          # FastAPI Python backend
├── frontend/         # React frontend
└── README.md
```

## 🚀 Quick Start

### 1️⃣ **Backend Setup**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Start the backend server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### 2️⃣ **Frontend Setup**
```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies (use npm if you don't have yarn)
npm install
# OR
yarn install

# Start the development server
npm start
# OR 
yarn start
```

### 3️⃣ **MongoDB Setup**

#### Option A: Local MongoDB
1. Install MongoDB locally
2. Start MongoDB service
3. Database will be created automatically

#### Option B: MongoDB Atlas (Cloud)
1. Create free account at mongodb.com
2. Create cluster and get connection string
3. Update MONGO_URL in backend/.env

## 🔧 Configuration Files

### Backend Environment (.env)
```
MONGO_URL=mongodb://localhost:27017/inventory_management
```

### Frontend Environment (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🌐 Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## ✨ Features
- Excel file uploads (Commandes, Stock, Transit)
- Inventory calculations with simplified formula
- Palette and truck logistics optimization
- Depot suggestions based on lowest stock quantities
- Professional Excel reporting
- AI-powered assistant for data analysis

## 🔧 Troubleshooting

### Common Issues:

1. **MongoDB Connection Error**
   - Make sure MongoDB is running
   - Check MONGO_URL in backend/.env

2. **Port Already in Use**
   - Backend: Change port in uvicorn command
   - Frontend: Choose different port when prompted

3. **Module Not Found**
   - Backend: Make sure virtual environment is activated
   - Frontend: Run `npm install` or `yarn install`

4. **CORS Issues**
   - Make sure REACT_APP_BACKEND_URL matches backend URL
   - Check backend CORS configuration

## 📝 Important Notes
- The application uses French language interface
- Supports Excel files with specific column structures
- Optimized for depot inventory management with M210 logic
- Enhanced suggestion system prioritizes low-stock items

## 🆘 Support
If you encounter issues, check:
1. All services are running (MongoDB, Backend, Frontend)
2. Environment variables are correctly set
3. Dependencies are properly installed
4. Ports are not conflicting with other applications