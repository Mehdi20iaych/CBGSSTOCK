# 🚀 Local Hosting Guide

## Quick Start (Recommended)

### 1. Install Dependencies
```bash
# Install all dependencies for both frontend and backend
npm run setup
```

### 2. Start the Application
```bash
# Start both frontend and backend simultaneously
npm start
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## Manual Setup (Alternative)

### Prerequisites
- **Node.js** (v18 or higher) - Download from: https://nodejs.org/
- **Python** (v3.9 or higher) - Download from: https://python.org/
- **MongoDB** (optional) - Download from: https://mongodb.com/

### Step-by-Step Setup

#### 1. Install Frontend Dependencies
```bash
cd frontend
npm install
```

#### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### 3. Setup Environment Files
```bash
# Run the setup script
npm run setup-env
```

#### 4. Start Backend (Terminal 1)
```bash
cd backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

#### 5. Start Frontend (Terminal 2)
```bash
cd frontend
npm start
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start both frontend and backend |
| `npm run start-frontend` | Start only the React frontend |
| `npm run start-backend` | Start only the FastAPI backend |
| `npm run build` | Build the frontend for production |
| `npm run setup` | Install all dependencies and setup environment |
| `npm test` | Run frontend tests |

## Environment Configuration

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
```

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017/inventory_management
GEMINI_API_KEY=AIzaSyA1Sx1oPOq1JOhzbTOxMvJ2PRooGA78fwg
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## Features

✨ **Core Features:**
- Excel file uploads (Commandes, Stock, Transit)
- Inventory calculations with advanced formulas
- Palette and truck logistics optimization
- Depot suggestions based on stock levels
- Professional Excel reporting
- AI-powered assistant for data analysis

📊 **Data Processing:**
- Supports French column headers
- Handles missing data gracefully
- Real-time calculations
- Multi-depot analysis

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Kill processes on ports
npx kill-port 3000 8001
```

**MongoDB Connection Error:**
- Install MongoDB locally or use MongoDB Atlas
- Update `MONGO_URL` in `backend/.env`

**Module Not Found:**
```bash
# Reinstall dependencies
npm run install-all
```

**CORS Issues:**
- Verify `REACT_APP_BACKEND_URL` in `frontend/.env`
- Check backend CORS configuration

### Development Tips

1. **Hot Reload**: Both frontend and backend support hot reload
2. **API Testing**: Use http://localhost:8001/docs for interactive API testing
3. **Logs**: Check terminal outputs for detailed error messages
4. **Data Persistence**: MongoDB stores uploaded data between sessions

## Production Deployment

For production deployment, build the frontend:
```bash
npm run build
```

The built files will be in `frontend/build/` directory.

## Support

If you encounter issues:
1. Check that all services are running
2. Verify environment variables are set correctly
3. Ensure ports 3000 and 8001 are available
4. Check MongoDB connection if using database features