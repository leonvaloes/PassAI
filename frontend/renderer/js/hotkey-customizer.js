// Hotkey Customization Handler

let capturingFor = null;

function captureHotkey(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    field.value = 'Pressione uma tecla...';
    field.style.background = '#fff3cd';
    capturingFor = fieldId;
    
    // Add event listener for keydown
    document.addEventListener('keydown', handleHotkeyCapture);
}

function handleHotkeyCapture(e) {
    if (!capturingFor) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    const field = document.getElementById(capturingFor);
    
    // Build hotkey string
    let hotkey = '';
    
    if (e.ctrlKey || e.metaKey) hotkey += 'CommandOrControl+';
    if (e.shiftKey) hotkey += 'Shift+';
    if (e.altKey) hotkey += 'Alt+';
    
    // Get the actual key
    let key = e.key;
    
    // Special keys mapping
    const specialKeys = {
        'F1': 'F1', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4',
        'F5': 'F5', 'F6': 'F6', 'F7': 'F7', 'F8': 'F8',
        'F9': 'F9', 'F10': 'F10', 'F11': 'F11', 'F12': 'F12',
        ' ': 'Space',
        'Enter': 'Enter',
        'Escape': 'Escape',
        'Tab': 'Tab',
        'Delete': 'Delete',
        'Insert': 'Insert',
        'Home': 'Home',
        'End': 'End',
        'PageUp': 'PageUp',
        'PageDown': 'PageDown',
        'ArrowUp': 'Up',
        'ArrowDown': 'Down',
        'ArrowLeft': 'Left',
        'ArrowRight': 'Right'
    };
    
    if (specialKeys[key]) {
        key = specialKeys[key];
    } else if (key.length === 1) {
        key = key.toUpperCase();
    } else {
        // Ignore modifier-only presses
        if (['Control', 'Shift', 'Alt', 'Meta'].includes(key)) {
            return;
        }
    }
    
    hotkey += key;
    
    // Set the value
    field.value = hotkey;
    field.style.background = '';
    
    // Clean up
    document.removeEventListener('keydown', handleHotkeyCapture);
    capturingFor = null;
}

function resetHotkeys() {
    // Reset to default values
    const defaults = {
        hotkeyScreenshot: 'CommandOrControl+Shift+X',
        hotkeyPause: 'CommandOrControl+Shift+P',
        hotkeyClear: 'CommandOrControl+Shift+C',
        hotkeySave: 'CommandOrControl+Shift+S'
    };
    
    for (const [id, value] of Object.entries(defaults)) {
        const field = document.getElementById(id);
        if (field) field.value = value;
    }
    
    console.log('Hotkeys reset to defaults');
}

// Initialize default values on load
document.addEventListener('DOMContentLoaded', () => {
    const settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
    
    document.getElementById('hotkeyScreenshot').value = settings.hotkeyScreenshot || 'CommandOrControl+Shift+X';
    document.getElementById('hotkeyPause').value = settings.hotkeyPause || 'CommandOrControl+Shift+P';
    document.getElementById('hotkeyClear').value = settings.hotkeyClear || 'CommandOrControl+Shift+C';
    document.getElementById('hotkeySave').value = settings.hotkeySave || 'CommandOrControl+Shift+S';
});

console.log('⌨️ Hotkey customization loaded');
