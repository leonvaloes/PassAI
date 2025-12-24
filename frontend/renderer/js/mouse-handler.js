// Mouse event handler for click-through

document.addEventListener('DOMContentLoaded', () => {
  // Track if mouse is over any interactive element
  let isOverInteractive = false;
  
  // Function to check if element or its parents are interactive
  function isInteractiveElement(element) {
    if (!element) return false;
    
    // Check if it's a floating window, toolbar, or input
    const interactiveSelectors = [
      '.floating-window',
      '.toolbar',
      'input',
      'button',
      'textarea'
    ];
    
    return interactiveSelectors.some(selector => 
      element.matches(selector) || element.closest(selector)
    );
  }
  
  // Update ignore mouse events based on cursor position
  function updateMouseEvents(event) {
    const elementUnderCursor = document.elementFromPoint(event.clientX, event.clientY);
    const shouldIgnore = !isInteractiveElement(elementUnderCursor);
    
    if (window.electronAPI && window.electronAPI.setIgnoreMouseEvents) {
      window.electronAPI.setIgnoreMouseEvents(shouldIgnore, { forward: true });
    }
  }
  
  // Listen to mouse movement
  document.addEventListener('mousemove', updateMouseEvents);
  
  // Also listen to mouse enter on interactive elements
  document.querySelectorAll('.floating-window, .toolbar').forEach(element => {
    element.addEventListener('mouseenter', () => {
      if (window.electronAPI && window.electronAPI.setIgnoreMouseEvents) {
        window.electronAPI.setIgnoreMouseEvents(false);
      }
    });
  });
});
