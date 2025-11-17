/**
 * iExporter3 Desktop - Preload Script
 * Exposes secure IPC API to renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose secure API to renderer process
 */
contextBridge.exposeInMainWorld('electronAPI', {
    // Dialog APIs
    openDatabase: () => ipcRenderer.invoke('dialog:openDatabase'),
    openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
    saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),

    // App Info
    getAppInfo: () => ipcRenderer.invoke('app:getInfo'),
    getUserDataPath: () => ipcRenderer.invoke('app:getUserDataPath'),

    // Persistent Storage
    storeGet: (key) => ipcRenderer.invoke('store:get', key),
    storeSet: (key, value) => ipcRenderer.invoke('store:set', key, value),

    // Python Backend Integration
    pythonExecute: (command, args) => ipcRenderer.invoke('python:execute', command, args),

    // Extraction
    runExtraction: (options) => ipcRenderer.invoke('extract:run', options),

    // Conversation
    loadConversation: (dbPath, conversationId) =>
        ipcRenderer.invoke('conversation:load', dbPath, conversationId),

    // Annotations
    saveAnnotation: (annotation) => ipcRenderer.invoke('annotation:save', annotation),
    deleteAnnotation: (annotationId) => ipcRenderer.invoke('annotation:delete', annotationId),

    // Events (for progress updates, etc.)
    onProgress: (callback) => {
        ipcRenderer.on('extraction:progress', (event, data) => callback(data));
    },
    removeProgressListener: () => {
        ipcRenderer.removeAllListeners('extraction:progress');
    },
});

console.log('iExporter3 Preload script loaded');
