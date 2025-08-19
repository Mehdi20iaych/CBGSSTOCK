const fs = require('fs');
const path = require('path');

console.log('🔧 Setting up environment files...');

// Frontend .env setup
const frontendEnvPath = path.join(__dirname, '../frontend/.env');
const frontendEnvContent = `# Frontend environment variables
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
`;

if (!fs.existsSync(frontendEnvPath)) {
  fs.writeFileSync(frontendEnvPath, frontendEnvContent);
  console.log('✅ Created frontend/.env');
} else {
  console.log('ℹ️ frontend/.env already exists');
}

// Backend .env setup
const backendEnvPath = path.join(__dirname, '../backend/.env');
const backendEnvContent = `# Backend environment variables
MONGO_URL=mongodb://localhost:27017/inventory_management
GEMINI_API_KEY=AIzaSyA1Sx1oPOq1JOhzbTOxMvJ2PRooGA78fwg
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
`;

if (!fs.existsSync(backendEnvPath)) {
  fs.writeFileSync(backendEnvPath, backendEnvContent);
  console.log('✅ Created backend/.env');
} else {
  console.log('ℹ️ backend/.env already exists');
}

console.log('🎉 Environment setup complete!');