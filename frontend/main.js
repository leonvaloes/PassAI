const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

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

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  createWindow();
  
  // Global hotkeys
  globalShortcut.register('CommandOrControl+Shift+P', () => {
    mainWindow.webContents.send('hotkey', 'pause');
  });
  
  globalShortcut.register('CommandOrControl+Shift+C', () => {
    mainWindow.webContents.send('hotkey', 'clear');
  });
  
  globalShortcut.register('CommandOrControl+Shift+S', () => {
    mainWindow.webContents.send('hotkey', 'save');
  });
  
  // Screenshot hotkey
  globalShortcut.register('F12', () => {
    mainWindow.webContents.send('hotkey', 'screenshot');
  });
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
