/**
 * iExporter3 Desktop - Main Process
 * Electron main process with Python backend integration
 */

const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');

// Initialize persistent storage
const store = new Store();

// Global references
let mainWindow = null;
let pythonProcess = null;

// Development mode
const isDev = process.argv.includes('--dev');

/**
 * Create main application window
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1200,
        minHeight: 700,
        title: 'iExporter3 - Forensic Message Extraction',
        backgroundColor: '#FFFFFF',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false, // Needed for file system access
        },
    });

    // Load the viewer
    const startUrl = isDev
        ? 'file://' + path.join(__dirname, '../templates/conversation_viewer.html')
        : `file://${path.join(__dirname, 'app/index.html')}`;

    mainWindow.loadURL(startUrl);

    // Open DevTools in development
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    // Handle window close
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });
}

/**
 * Start Python backend process
 */
function startPythonBackend() {
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    const scriptPath = path.join(__dirname, '../../backend/server.py');

    pythonProcess = spawn(pythonPath, [scriptPath]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        pythonProcess = null;
    });
}

/**
 * Stop Python backend process
 */
function stopPythonBackend() {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
    }
}

// ============================================
// IPC Handlers (Renderer ↔ Main)
// ============================================

/**
 * Open database file
 */
ipcMain.handle('dialog:openDatabase', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters: [
            { name: 'Database Files', extensions: ['db', 'sqlite', 'sqlite3'] },
            { name: 'All Files', extensions: ['*'] },
        ],
    });

    if (!result.canceled && result.filePaths.length > 0) {
        const dbPath = result.filePaths[0];
        store.set('lastOpenedDatabase', dbPath);
        return dbPath;
    }

    return null;
});

/**
 * Open directory
 */
ipcMain.handle('dialog:openDirectory', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory', 'createDirectory'],
    });

    if (!result.canceled && result.filePaths.length > 0) {
        return result.filePaths[0];
    }

    return null;
});

/**
 * Save file
 */
ipcMain.handle('dialog:saveFile', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);

    if (!result.canceled && result.filePath) {
        return result.filePath;
    }

    return null;
});

/**
 * Get application info
 */
ipcMain.handle('app:getInfo', () => {
    return {
        version: app.getVersion(),
        name: app.getName(),
        platform: process.platform,
        arch: process.arch,
    };
});

/**
 * Get user data path
 */
ipcMain.handle('app:getUserDataPath', () => {
    return app.getPath('userData');
});

/**
 * Get last opened database
 */
ipcMain.handle('store:get', (event, key) => {
    return store.get(key);
});

/**
 * Set store value
 */
ipcMain.handle('store:set', (event, key, value) => {
    store.set(key, value);
    return true;
});

/**
 * Execute Python command
 */
ipcMain.handle('python:execute', async (event, command, args) => {
    return new Promise((resolve, reject) => {
        const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
        const scriptPath = path.join(__dirname, '../../backend', command);

        const proc = spawn(pythonPath, [scriptPath, ...args]);

        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        proc.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        proc.on('close', (code) => {
            if (code === 0) {
                resolve({ success: true, stdout, stderr });
            } else {
                reject({ success: false, code, stdout, stderr });
            }
        });

        proc.on('error', (error) => {
            reject({ success: false, error: error.message });
        });
    });
});

/**
 * Run extraction
 */
ipcMain.handle('extract:run', async (event, options) => {
    const { caseId, outputPath, user } = options;

    try {
        const result = await ipcMain.handle('python:execute', null, 'extractors/cli.py', [
            'extract',
            caseId,
            '--output',
            outputPath,
            '--user',
            user || 'desktop-user',
        ]);

        return result;
    } catch (error) {
        return { success: false, error: error.message };
    }
});

/**
 * Load conversation
 */
ipcMain.handle('conversation:load', async (event, dbPath, conversationId) => {
    // This would call Python backend to load conversation data
    // For now, return mock data
    return {
        conversationId,
        messages: [],
        annotations: [],
    };
});

/**
 * Save annotation
 */
ipcMain.handle('annotation:save', async (event, annotation) => {
    // This would call Python backend to save annotation
    // For now, just return success
    console.log('Saving annotation:', annotation);
    return { success: true, annotationId: 'ANN_' + Date.now() };
});

/**
 * Delete annotation
 */
ipcMain.handle('annotation:delete', async (event, annotationId) => {
    // This would call Python backend to delete annotation
    console.log('Deleting annotation:', annotationId);
    return { success: true };
});

// ============================================
// App Lifecycle
// ============================================

app.whenReady().then(() => {
    createWindow();

    // Start Python backend (optional, for advanced features)
    // startPythonBackend();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    stopPythonBackend();

    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    stopPythonBackend();
});

// ============================================
// Error Handling
// ============================================

process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);

    dialog.showErrorBox(
        'Application Error',
        'An unexpected error occurred. Please restart the application.'
    );
});

console.log('iExporter3 Desktop starting...');
console.log('Mode:', isDev ? 'Development' : 'Production');
console.log('Platform:', process.platform);
