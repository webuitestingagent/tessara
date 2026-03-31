"""
Tessara Setup Script
Run this to verify installation and set up the environment
"""

import sys
import subprocess
import os


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'playwright',
        'beautifulsoup4',
        'openai',
        'yaml',
        'psutil',
        'streamlit',
        'PIL'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'yaml':
                __import__('yaml')
            elif package == 'PIL':
                __import__('PIL')
            else:
                __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("\n🌐 Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright browsers installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Playwright browsers")
        return False

def check_config():
    """Check if config.yaml exists"""
    if os.path.exists("config.yaml"):
        print("✅ config.yaml exists")
        return True
    else:
        print("⚠️  config.yaml not found")
        print("   Please copy config.yaml.template to config.yaml and fill in your details")
        return False

def main():
    print("=" * 60)
    print("Tessara Setup and Verification")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check dependencies
    print("\n📋 Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        response = input("Would you like to install missing dependencies? (y/n): ")
        if response.lower() == 'y':
            if not install_dependencies():
                return
        else:
            print("Please install dependencies manually: pip install -r requirements.txt")
            return
    
    # Check Playwright browsers
    print("\n🌐 Checking Playwright browsers...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("✅ Playwright browsers are installed")
    except Exception as e:
        print("⚠️  Playwright browsers not found or not working")
        response = input("Would you like to install Playwright browsers? (y/n): ")
        if response.lower() == 'y':
            if not install_playwright_browsers():
                return
    
    # Check config
    print("\n⚙️  Checking configuration...")
    check_config()
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If config.yaml doesn't exist, copy config.yaml.template to config.yaml")
    print("2. Edit config.yaml with your API credentials")
    print("3. Run the UI: run_ui.bat (Windows) or ./run_ui.sh (Linux/Mac)")
    print("   Or manually: cd codebase && streamlit run tessara_ui.py")

if __name__ == "__main__":
    main()

