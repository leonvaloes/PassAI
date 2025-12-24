// ControlButtons Component
// Capture and control buttons

class ControlButtons {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.isCapturing = false;
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="control-buttons">
        <button id="captureBtn" class="btn-control btn-capture">
          <span class="btn-icon">🎙️</span>
          <span class="btn-text">Iniciar Captura</span>
        </button>
        <button id="pauseBtn" class="btn-control">
          <span class="btn-icon">⏸️</span>
          <span class="btn-text">Pausar</span>
        </button>
        <button id="clearBtn" class="btn-control btn-danger">
          <span class="btn-icon">🗑️</span>
          <span class="btn-text">Limpar</span>
        </button>
      </div>
    `;
    
    this.captureBtn = document.getElementById('captureBtn');
    this.attachListeners();
  }
  
  attachListeners() {
    this.captureBtn.addEventListener('click', () => {
      this.toggleCapture();
    });
    
    document.getElementById('pauseBtn').addEventListener('click', () => {
      this.onPause();
    });
    
    document.getElementById('clearBtn').addEventListener('click', () => {
      this.onClear();
    });
  }
  
  toggleCapture() {
    this.isCapturing = !this.isCapturing;
    
    if (this.isCapturing) {
      this.captureBtn.classList.add('active');
      this.captureBtn.innerHTML = `
        <span class="btn-icon">⏹️</span>
        <span class="btn-text">Parar Captura</span>
      `;
      this.onStart();
    } else {
      this.captureBtn.classList.remove('active');
      this.captureBtn.innerHTML = `
        <span class="btn-icon">🎙️</span>
        <span class="btn-text">Iniciar Captura</span>
      `;
      this.onStop();
    }
  }
  
  onStart() {
    console.log('Start capture');
  }
  
  onStop() {
    console.log('Stop capture');
  }
  
  setCapturing(isCapturing) {
    this.isCapturing = isCapturing;
    const btn = document.getElementById('captureBtn');
    if (btn) {
      btn.classList.toggle('active', isCapturing);
    }
  }
}
