// InputField Component
// Text input at top of application

class InputField {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.input = null;
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <input 
        type="text" 
        id="manualInput"
        class="main-input"
        placeholder="Comece a digitar... (pressione Enter para enviar)"
      />
    `;
    
    this.input = document.getElementById('manualInput');
    this.attachListeners();
  }
  
  attachListeners() {
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const text = this.input.value.trim();
        if (text) {
          this.onSubmit(text);
          this.input.value = '';
        }
      }
    });
  }
  
  onSubmit(text) {
    // Override this in app.js
    console.log('Input submitted:', text);
  }
  
  getValue() {
    return this.input.value;
  }
  
  clear() {
    this.input.value = '';
  }
}
