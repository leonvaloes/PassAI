"""
Setup script for AI Copilot
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run setup process"""
    print("🚀 AI Copilot Setup")
    print("=" * 50)
    
    # 1. Check Python version
    print("\n1. Checking Python version...")
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}")
    
    # 2. Create virtual environment
    print("\n2. Creating virtual environment...")
    venv_path = Path("venv")
    if not venv_path.exists():
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("⚠️  Virtual environment already exists")
    
    # 3. Get pip executable
    if sys.platform == "win32":
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        pip_exe = venv_path / "bin" / "pip"
    
    # 4. Upgrade pip (use python -m pip to avoid Windows issues)
    print("\n3. Upgrading pip...")
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
    
    try:
        subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("✅ Pip upgraded")
    except subprocess.CalledProcessError:
        print("⚠️  Pip upgrade failed (não crítico, continuando...)")
    
    # 5. Install dependencies
    print("\n4. Installing dependencies...")
    print("   This may take a few minutes...")
    try:
        subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], check=True)
        print("✅ Core dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("   Try manually: venv\\Scripts\\pip install -r requirements.txt")
        sys.exit(1)
    
    # 6. Ask about GPU
    print("\n5. GPU Support (CUDA)")
    response = input("   Do you have an NVIDIA GPU? (y/n): ").lower()
    if response == 'y':
        print("   Installing GPU dependencies...")
        subprocess.run([
            str(pip_exe), "install", "-r", "requirements-gpu.txt",
            "--extra-index-url", "https://download.pytorch.org/whl/cu118"
        ], check=True)
        print("✅ GPU dependencies installed")
    
    # 7. Ask about dev dependencies
    print("\n6. Development Dependencies")
    response = input("   Install development dependencies? (y/n): ").lower()
    if response == 'y':
        subprocess.run([str(pip_exe), "install", "-r", "requirements-dev.txt"], check=True)
        print("✅ Dev dependencies installed")
    
    # 8. Create directories
    print("\n7. Creating directories...")
    directories = ["logs", "models", "data", "sessions"]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Directories created")
    
    # 9. Copy config
    print("\n8. Configuration")
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        import shutil
        shutil.copy("config/config.example.yaml", "config/config.yaml")
        print("✅ Config file created (config/config.yaml)")
        print("   ⚠️  Remember to edit config.yaml with your settings")
    else:
        print("⚠️  Config already exists")
    
    # 10. Copy .env
    env_path = Path(".env")
    if not env_path.exists():
        import shutil
        shutil.copy(".env.example", ".env")
        print("✅ .env file created")
        print("   ⚠️  Remember to add your API keys to .env")
    else:
        print("⚠️  .env already exists")
    
    # 11. Check Ollama
    print("\n9. Checking Ollama...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed")
            print("\n   Available models:")
            print(result.stdout)
            
            if "llama3.1" not in result.stdout:
                print("\n   Recommended: Download llama3.1 model")
                print("   Run: ollama pull llama3.1:8b-instruct-q4_K_M")
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("❌ Ollama not found")
        print("   Install from: https://ollama.ai")
        print("   After installing, run: ollama pull llama3.1:8b-instruct-q4_K_M")
    
    # 12. Check Tesseract
    print("\n10. Checking Tesseract OCR...")
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract is installed")
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("❌ Tesseract not found")
        if sys.platform == "win32":
            print("   Install from: https://github.com/UB-Mannheim/tesseract/wiki")
        else:
            print("   Install with: apt-get install tesseract-ocr")
    
    # Done
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit config/config.yaml with your preferences")
    print("2. Add API keys to .env (if using cloud LLMs)")
    print("3. Install Ollama and download models (if not done)")
    print("4. Run: python src/main.py")
    print("\nActivate virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")


if __name__ == "__main__":
    main()
