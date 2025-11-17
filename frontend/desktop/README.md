# iExporter3 Desktop Application

Electron-based desktop application for forensic iMessage extraction and annotation.

## Features

- **Cross-platform**: macOS, Windows, Linux
- **Python Integration**: Calls Python backend for extraction and database operations
- **Annotation UI**: Full CRUD operations with modal editor
- **File System Access**: Local SQLite database access
- **Secure IPC**: Context isolation with preload script
- **Persistent Storage**: electron-store for user preferences

## Requirements

- **Node.js** 18+ (for building and running)
- **Python** 3.11+ (for backend)
- **Electron** 28+

## Installation

```bash
cd frontend/desktop
npm install
```

## Development

```bash
# Start in development mode
npm run dev

# This will:
# 1. Launch Electron app
# 2. Open DevTools
# 3. Load local HTML templates
# 4. Enable hot reload
```

## Building

```bash
# Build for current platform
npm run build

# Build for specific platform
npm run build:mac    # macOS (.dmg, .zip)
npm run build:win    # Windows (.exe, portable)
npm run build:linux  # Linux (.AppImage, .deb)
```

## Architecture

```
frontend/desktop/
├── main.js           # Main Electron process
├── preload.js        # Secure IPC bridge
├── package.json      # Dependencies and build config
├── renderer/         # UI components (future)
└── assets/           # Icons and resources
```

## Python Backend Integration

The Electron app communicates with Python backend via:

1. **Direct execution** (spawn Python scripts)
2. **IPC handlers** (async/await API)
3. **Optional server mode** (HTTP/WebSocket for advanced features)

### Example: Running Extraction

```javascript
// From renderer process
const result = await window.electronAPI.runExtraction({
    caseId: 'ABC2024',
    outputPath: '/path/to/output.db',
    user: 'attorney@lawfirm.com'
});

if (result.success) {
    console.log('Extraction complete!');
}
```

### Example: Saving Annotation

```javascript
const annotation = {
    messageId: 'MSG_ABC2024_...',
    tags: ['Key', 'Timeline'],
    note: 'Important evidence'
};

const result = await window.electronAPI.saveAnnotation(annotation);
console.log('Annotation ID:', result.annotationId);
```

## Security

- **Context Isolation**: Enabled (renderer can't access Node.js)
- **Sandbox**: Disabled for file system access (necessary for SQLite)
- **Preload Script**: Only exposes specific, validated APIs
- **No Remote**: Remote module disabled
- **CSP**: Content Security Policy enforced

## File Access

The app can access:
- User's home directory (for iMessage database)
- Application data directory (for settings)
- User-selected files/directories (via dialogs)

## Persistent Storage

Uses `electron-store` to remember:
- Last opened database
- Window size and position
- User preferences
- Recent cases

## Platform-Specific Features

### macOS
- Full Disk Access required for iMessage database
- Native menu bar
- Touch Bar support (future)
- Code signing required for distribution

### Windows
- NSIS installer
- Portable build (no installation needed)
- Auto-updater (future)

### Linux
- AppImage (portable)
- Debian package (.deb)
- Desktop integration

## Distribution

### macOS
```bash
npm run build:mac

# Outputs:
# - dist/iExporter3-1.0.0.dmg        # Installer
# - dist/iExporter3-1.0.0-mac.zip    # Portable
```

### Windows
```bash
npm run build:win

# Outputs:
# - dist/iExporter3 Setup 1.0.0.exe  # Installer
# - dist/iExporter3 1.0.0.exe        # Portable
```

### Linux
```bash
npm run build:linux

# Outputs:
# - dist/iExporter3-1.0.0.AppImage   # Portable
# - dist/iExporter3_1.0.0_amd64.deb  # Debian package
```

## Code Signing (Production)

### macOS
Requires Apple Developer ID certificate:
```bash
export CSC_LINK=/path/to/certificate.p12
export CSC_KEY_PASSWORD=your_password
npm run build:mac
```

### Windows
Requires code signing certificate:
```bash
export CSC_LINK=/path/to/certificate.pfx
export CSC_KEY_PASSWORD=your_password
npm run build:win
```

## Auto-Updates (Future)

Can be implemented with:
- `electron-updater`
- GitHub Releases
- Private update server

## Troubleshooting

### Python not found
- Ensure Python 3.11+ is in PATH
- On Windows, use `python` instead of `python3`
- Set custom Python path in settings

### Database access denied (macOS)
- Grant Full Disk Access to Terminal or Electron app
- System Preferences > Security & Privacy > Privacy > Full Disk Access

### Build fails
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Ensure Electron version matches package.json

## Development Tools

### Useful Commands

```bash
# Clear electron cache
rm -rf ~/Library/Application\ Support/iExporter3

# Reset persistent storage
rm -rf ~/Library/Application\ Support/iexporter3-desktop

# Check Electron version
npx electron --version

# Inspect main process
npx electron --inspect=9229 .
```

### DevTools

- **Main Process**: `--inspect` flag + Chrome DevTools
- **Renderer Process**: Built-in DevTools (Cmd+Option+I)

## Next Steps

1. **Implement renderer UI** (`renderer/` directory)
2. **Add Python server mode** (optional, for real-time updates)
3. **Build annotation modal** (integrated with HTML viewer)
4. **Add progress indicators** (for long-running operations)
5. **Implement auto-updater**
6. **Add crash reporting**

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [Electron Builder](https://www.electron.build/)
- [electron-store](https://github.com/sindresorhus/electron-store)

---

**Built with Electron for forensic professionals.**
