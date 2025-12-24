// UI update functions

console.log('🎨 UI.js loaded');

const transcriptionEl = document.getElementById('transcription');
const suggestionEl = document.getElementById('suggestion');
const statusEl = document.getElementById('status');
const closeBtn = document.getElementById('closeBtn');

console.log('📦 Elements found:', {
  transcription: !!transcriptionEl,
  suggestion: !!suggestionEl,
  status: !!statusEl,
  closeBtn: !!closeBtn
});

// Close button
if (closeBtn) {
  closeBtn.addEventListener('click', () => {
    console.log('❌ Close button clicked');
    window.close();
  });
} else {
  console.error('❌ Close button not found!');
}

// Update transcription with fade animation
function updateTranscription(text) {
  console.log('🔄 updateTranscription called, element exists:', !!transcriptionEl);
  if (!transcriptionEl) {
    console.error('❌ transcriptionEl is null!');
    return;
  }
  
  transcriptionEl.classList.add('fade-out');
  
  setTimeout(() => {
    transcriptionEl.textContent = text;
    transcriptionEl.classList.remove('fade-out');
    transcriptionEl.classList.add('fade-in');
    console.log('✅ Transcription DOM updated to:', text.substring(0, 50) + '...');
  }, 125);
}

// Update suggestion with fade animation
function updateSuggestion(text) {
  console.log('🔄 updateSuggestion called, element exists:', !!suggestionEl);
  if (!suggestionEl) {
    console.error('❌ suggestionEl is null!');
    return;
  }
  
  suggestionEl.classList.add('fade-out');
  
  setTimeout(() => {
    suggestionEl.textContent = text;
    suggestionEl.classList.remove('fade-out');
    suggestionEl.classList.add('fade-in');
    console.log('✅ Suggestion DOM updated to:', text.substring(0, 50) + '...');
  }, 150);
}

// Update status
function updateStatus(text, className = 'ready') {
  console.log('🔄 updateStatus called:', text, className);
  if (!statusEl) {
    console.error('❌ statusEl is null!');
    return;
  }
  statusEl.textContent = text;
  statusEl.className = `status ${className}`;
  console.log('✅ Status DOM updated');
}

// Export functions
window.updateTranscription = updateTranscription;
window.updateSuggestion = updateSuggestion;
window.updateStatus = updateStatus;

console.log('✅ UI functions exported to window');
