const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');

let mainWindow;
let resumeWindow = null; // Resume Generator window

function createWindow() {
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  mainWindow = new BrowserWindow({
    x: 0,
    y: 0,
    width: width,
    height: height,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile('renderer/index.html');
  
  // DevTools disabled for production

  // Allow clicking through transparent areas
  mainWindow.setIgnoreMouseEvents(true, { forward: true });
  
  // Listen for mouse enter/leave events from renderer
  const { ipcMain } = require('electron');
  
  ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    win.setIgnoreMouseEvents(ignore, options);
  });
  
  ipcMain.on('set-opacity', (event, opacity) => {
    if (mainWindow) {
      mainWindow.setOpacity(opacity);
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Resume Generator window
function createResumeWindow() {
  if (resumeWindow) {
    resumeWindow.focus();
    return;
  }

  resumeWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    title: 'Resume Generator - PassAI',
    backgroundColor: '#1a1a2e'
  });

  resumeWindow.loadFile('renderer/windows/resume-generator/resume-generator.html');
  resumeWindow.webContents.openDevTools(); // For debugging

  resumeWindow.on('closed', () => {
    resumeWindow = null;
  });
}

// IPC Handler for opening Resume Generator
ipcMain.on('open-resume-generator', () => {
  createResumeWindow();
});

app.on('ready', () => {
  createWindow();
  
  // Global hotkeys
  const registered = {
    pause: globalShortcut.register('CommandOrControl+Shift+P', () => {
      mainWindow.webContents.send('hotkey', 'pause');
    }),
    clear: globalShortcut.register('CommandOrControl+Shift+C', () => {
      mainWindow.webContents.send('hotkey', 'clear');
    }),
    save: globalShortcut.register('CommandOrControl+Shift+S', () => {
      mainWindow.webContents.send('hotkey', 'save');
    }),
    // Changed from F12 to Ctrl+Shift+X (F12 often blocked by system)
    screenshot: globalShortcut.register('CommandOrControl+Shift+X', () => {
      console.log('Screenshot hotkey pressed!');
      mainWindow.webContents.send('hotkey', 'screenshot');
    })
  };
  
  // Log registration status
  console.log('Hotkeys registered:', registered);
  if (!registered.screenshot) {
    console.error('❌ Failed to register screenshot hotkey!');
  }
});

app.on('window-all-closed', () => {
  globalShortcut.unregisterAll();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
