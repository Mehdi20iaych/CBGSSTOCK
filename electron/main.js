const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = process.env.BACKEND_PORT || '8001';

let backendProcess = null;
let mainWindow = null;

function resolveFrontendIndex() {
	// In dev, files live in project; in production they are under resources
	const devIndex = path.join(__dirname, '..', 'frontend', 'build', 'index.html');
	const prodIndex = path.join(process.resourcesPath || path.join(__dirname, '..'), 'frontend', 'build', 'index.html');
	return app.isPackaged ? prodIndex : devIndex;
}

function getPythonCommand() {
	if (process.env.PYTHON_PATH) return process.env.PYTHON_PATH;
	// Try common commands
	if (process.platform === 'win32') {
		return 'python';
	}
	return 'python3';
}

function startBackend() {
	const pythonCmd = getPythonCommand();
	const args = ['-m', 'uvicorn', 'backend.server:app', '--host', BACKEND_HOST, '--port', BACKEND_PORT];
	backendProcess = spawn(pythonCmd, args, {
		cwd: path.join(__dirname, '..'),
		env: { ...process.env },
		detached: false,
	});

	backendProcess.stdout?.on('data', (data) => {
		console.log(`[backend] ${data}`.toString());
	});
	backendProcess.stderr?.on('data', (data) => {
		console.error(`[backend] ${data}`.toString());
	});
	backendProcess.on('exit', (code) => {
		console.log(`[backend] exited with code ${code}`);
		backendProcess = null;
	});
}

function waitForBackendReady(timeoutMs = 30000, intervalMs = 500) {
	const deadline = Date.now() + timeoutMs;
	return new Promise((resolve, reject) => {
		const check = () => {
			const req = http.request({ host: BACKEND_HOST, port: BACKEND_PORT, path: '/', method: 'GET' }, (res) => {
				resolve(true);
			});
			req.on('error', () => {
				if (Date.now() > deadline) {
					reject(new Error('Backend did not become ready in time'));
					return;
				}
				setTimeout(check, intervalMs);
			});
			req.end();
		};
		check();
	});
}

async function createWindow() {
	startBackend();
	try {
		await waitForBackendReady();
	} catch (err) {
		console.error(err);
		dialog.showErrorBox('Backend Error', 'Failed to start backend server. Ensure Python and dependencies are installed.');
	}

	mainWindow = new BrowserWindow({
		width: 1400,
		height: 900,
		webPreferences: {
			preload: path.join(__dirname, 'preload.js'),
			contextIsolation: true,
			nodeIntegration: false,
		},
	});

	const indexPath = resolveFrontendIndex();
	await mainWindow.loadFile(indexPath);

	mainWindow.on('closed', () => {
		mainWindow = null;
	});
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
	if (process.platform !== 'darwin') {
		app.quit();
	}
	if (backendProcess && !backendProcess.killed) {
		try { backendProcess.kill(); } catch {}
	}
});

app.on('activate', () => {
	if (mainWindow === null) {
		createWindow();
	}
});

