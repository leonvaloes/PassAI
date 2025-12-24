// AudioMeters Component
// Visual audio level indicators

class AudioMeters {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.levels = { you: 0, other: 0 };
    this.animationFrameId = null;
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="audio-meters">
        <div class="meter-title">Medidores de áudio</div>
        <div class="meter-row">
          <span class="meter-label">VOCÊ</span>
          <div class="meter-bar-container">
            <div class="meter-bar" id="meterYou" style="width: 0%"></div>
          </div>
          <span class="meter-value" id="meterYouValue">0%</span>
        </div>
        <div class="meter-row">
          <span class="meter-label">OUTROS</span>
          <div class="meter-bar-container">
            <div class="meter-bar meter-other" id="meterOther" style="width: 0%"></div>
          </div>
          <span class="meter-value" id="meterOtherValue">0%</span>
        </div>
      </div>
    `;
    
    this.meterYou = document.getElementById('meterYou');
    this.meterOther = document.getElementById('meterOther');
    this.meterYouValue = document.getElementById('meterYouValue');
    this.meterOtherValue = document.getElementById('meterOtherValue');
  }
  
  updateLevel(source, level) {
    // Level should be 0-100
    const clampedLevel = Math.max(0, Math.min(100, level));
    this.levels[source] = clampedLevel;
    this.renderMeters();
  }
  
  renderMeters() {
    if (this.meterYou) {
      this.meterYou.style.width = `${this.levels.you}%`;
      this.meterYouValue.textContent = `${Math.round(this.levels.you)}%`;
    }
    
    if (this.meterOther) {
      this.meterOther.style.width = `${this.levels.other}%`;
      this.meterOtherValue.textContent = `${Math.round(this.levels.other)}%`;
    }
  }
  
  simulateActivity(source) {
    // Simulate audio activity (for testing)
    const level = Math.random() * 100;
    this.updateLevel(source, level);
    
    setTimeout(() => {
      this.updateLevel(source, 0);
    }, 1000);
  }
}
