// ActionButtons Component
// Analysis and control actions

class ActionButtons {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="action-buttons">
        <button id="ctrlBBtn" class="btn-action btn-secondary">
          Ctrl+B
        </button>
        <button id="analyzeBtn" class="btn-action btn-primary">
          📊 Analisar Transcrição
        </button>
      </div>
    `;
    
    this.attachListeners();
  }
  
  attachListeners() {
    document.getElementById('ctrlBBtn').addEventListener('click', () => {
      this.onCtrlB();
    });
    
    document.getElementById('analyzeBtn').addEventListener('click', () => {
      this.onAnalyze();
    });
  }
  
  onCtrlB() {
    console.log('Ctrl+B clicked');
  }
  
  onAnalyze() {
    console.log('Analyze clicked');
  }
  
  setAnalyzing(isAnalyzing) {
    const btn = document.getElementById('analyzeBtn');
    if (btn) {
      btn.disabled = isAnalyzing;
      btn.textContent = isAnalyzing ? '⌛ Analisando...' : '📊 Analisar Transcrição';
    }
  }
}
