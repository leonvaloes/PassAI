// Window Manager - Handle draggable floating windows

let draggedWindow = null;
let offsetX = 0;
let offsetY = 0;
let highestZ = 100;

// Start dragging a window
function startDrag(event, windowId) {
  event.preventDefault();
  
  draggedWindow = document.getElementById(windowId);
  if (!draggedWindow) return;
  
  // Bring window to front
  bringToFront(draggedWindow);
  
  // Calculate offset
  const rect = draggedWindow.getBoundingClientRect();
  offsetX = event.clientX - rect.left;
  offsetY = event.clientY - rect.top;
  
  // Add event listeners
  document.addEventListener('mousemove', drag);
  document.addEventListener('mouseup', stopDrag);
}

function drag(event) {
  if (!draggedWindow) return;
  
  // Calculate new position
  let newX = event.clientX - offsetX;
  let newY = event.clientY - offsetY;
  
  // Constrain to workspace
  const maxX = window.innerWidth - draggedWindow.offsetWidth;
  const maxY = window.innerHeight - draggedWindow.offsetHeight;
  
  newX = Math.max(0, Math.min(newX, maxX));
  newY = Math.max(0, Math.min(newY, maxY));
  
  // Apply position
  draggedWindow.style.left = newX + 'px';
  draggedWindow.style.top = newY + 'px';
}

function stopDrag() {
  draggedWindow = null;
  document.removeEventListener('mousemove', drag);
  document.removeEventListener('mouseup', stopDrag);
}

// Bring window to front
function bringToFront(window) {
  // Remove active class from all
  document.querySelectorAll('.floating-window').forEach(w => {
    w.classList.remove('active');
  });
  
  // Add to clicked window
  window.classList.add('active');
  window.style.zIndex = ++highestZ;
}

// Click window to bring to front
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.floating-window').forEach(window => {
    window.addEventListener('mousedown', () => {
      bringToFront(window);
    });
  });
});

// Minimize window
function minimizeWindow(windowId) {
  const window = document.getElementById(windowId);
  if (window) {
    window.classList.add('minimized');
  }
}

// Show/restore window
function showWindow(windowId) {
  const window = document.getElementById(windowId);
  if (window) {
    window.classList.remove('minimized');
    window.classList.remove('hidden');
    bringToFront(window);
  }
}

// Close window
function closeWindow(windowId) {
  const window = document.getElementById(windowId);
  if (window) {
    window.classList.add('hidden');
  }
}

// Reset layout to default positions
function resetLayout() {
  const windows = {
    chatWindow: { left: '20px', top: '20px', width: '400px', height: '500px' },
    transcriptionWindow: { left: '440px', top: '20px', width: '320px', height: '400px' },
    audioWindow: { left: '20px', top: '540px', width: '300px', height: '200px' },
    metersWindow: { left: '340px', top: '540px', width: '280px', height: '150px' }
  };
  
  Object.keys(windows).forEach(id => {
    const window = document.getElementById(id);
    if (window) {
      const pos = windows[id];
      window.style.left = pos.left;
      window.style.top = pos.top;
      window.style.width = pos.width;
      window.style.height = pos.height;
      window.classList.remove('minimized');
      window.classList.remove('hidden');
    }
  });
}

// Save layout to localStorage
function saveLayout() {
  const layout = {};
  
  document.querySelectorAll('.floating-window').forEach(window => {
    layout[window.id] = {
      left: window.style.left,
      top: window.style.top,
      width: window.style.width,
      height: window.style.height,
      minimized: window.classList.contains('minimized'),
      hidden: window.classList.contains('hidden')
    };
  });
  
  localStorage.setItem('windowLayout', JSON.stringify(layout));
}

// Load layout from localStorage
function loadLayout() {
  const saved = localStorage.getItem('windowLayout');
  if (!saved) return;
  
  try {
    const layout = JSON.parse(saved);
    
    Object.keys(layout).forEach(id => {
      const window = document.getElementById(id);
      if (!window) return;
      
      const pos = layout[id];
      window.style.left = pos.left;
      window.style.top = pos.top;
      window.style.width = pos.width;
      window.style.height = pos.height;
      
      if (pos.minimized) window.classList.add('minimized');
      if (pos.hidden) window.classList.add('hidden');
    });
  } catch (e) {
    console.error('Failed to load layout:', e);
  }
}

// Auto-save layout on changes
let saveTimeout;
function scheduleLayoutSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(saveLayout, 1000);
}

// Listen for window changes
document.addEventListener('DOMContentLoaded', () => {
  loadLayout();
  
  // Save on drag end
  document.addEventListener('mouseup', scheduleLayoutSave);
  
  // Save on window resize
  const observer = new ResizeObserver(scheduleLayoutSave);
  document.querySelectorAll('.floating-window').forEach(window => {
    observer.observe(window);
  });
});
