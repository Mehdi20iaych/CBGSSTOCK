const { contextBridge } = require('electron');

// Simple bridge to expose whether we are in Electron and backend base URL
contextBridge.exposeInMainWorld('electron', {
	inElectron: true,
	backendBaseUrl: `http://127.0.0.1:${process.env.BACKEND_PORT || '8001'}`,
});

