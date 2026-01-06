const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  send: (channel, data) => {
    ipcRenderer.send(channel, data);
  },
  setIgnoreMouseEvents: (ignore, options) => {
    ipcRenderer.send('set-ignore-mouse-events', ignore, options);
  },
  setOpacity: (opacity) => {
    ipcRenderer.send('set-opacity', opacity);
  },
  onHotkey: (callback) => {
    ipcRenderer.on('hotkey', (event, action) => callback(action));
  },
  openExternal: (url) => {
    ipcRenderer.send('open-external-url', url);
  }
});
