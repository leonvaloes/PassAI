// Global hotkeys handler

if (window.electron) {
  window.electron.onHotkey((action) => {
    console.log(`Hotkey triggered: ${action}`);
    
    // Send command to backend
    if (window.wsClient) {
      window.wsClient.sendCommand(action);
    }
  });
}
