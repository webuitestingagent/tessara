# Installation Guide

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Set Up Configuration

```bash
# Copy the template
cp config.yaml.template config.yaml

# Edit config.yaml with your API credentials and task details
# Use any text editor to edit the file
```

### 4. Run the UI

**Windows:**
```bash
run_ui.bat
```

**Linux/Mac:**
```bash
chmod +x run_ui.sh
./run_ui.sh
```

**Or manually:**
```bash
cd codebase
streamlit run tessara_ui.py
```

## Detailed Installation

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, Linux, or macOS
- **Browser**: Chrome (installed and accessible)
- **API Access**: Azure OpenAI API credentials

### Step-by-Step Installation

#### Step 1: Python Environment

Ensure Python 3.8+ is installed:
```bash
python --version
```

If not installed, download from [python.org](https://www.python.org/downloads/)

#### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This installs:
- `playwright`: Browser automation
- `beautifulsoup4`: HTML parsing
- `openai`: Azure OpenAI client
- `pyyaml`: Configuration file parsing
- `psutil`: Process management
- `streamlit`: Web UI framework
- `Pillow`: Image processing

#### Step 3: Install Playwright Browsers

Playwright needs to download browser binaries:

```bash
playwright install chromium
```

This may take a few minutes as it downloads the Chromium browser.

#### Step 4: Configure API Access

1. Get your Azure OpenAI credentials:
   - API Key
   - Endpoint URL
   - API Version (typically "2024-12-01-preview")

2. Create `config.yaml` from the template:
   ```bash
   cp config.yaml.template config.yaml
   ```

3. Edit `config.yaml`:
   ```yaml
   planner:
     api_key: "your-api-key-here"
     azure_endpoint: "https://your-resource.openai.azure.com/"
     api_version: "2024-12-01-preview"
   
   scripter:
     api_key: "your-api-key-here"
     azure_endpoint: "https://your-resource.openai.azure.com/"
     api_version: "2024-12-01-preview"
   ```

#### Step 5: Verify Installation

Test that everything works:

```bash
cd codebase
python -c "import playwright; import streamlit; import openai; print('All imports successful!')"
```

## Troubleshooting Installation

### Issue: `playwright` command not found

**Solution**: Ensure Playwright is installed:
```bash
pip install playwright
playwright install chromium
```

### Issue: Browser not found

**Solution**: Install Chromium:
```bash
playwright install chromium
```

### Issue: Import errors

**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Streamlit not found

**Solution**: Install Streamlit:
```bash
pip install streamlit
```

### Issue: Permission denied (Linux/Mac)

**Solution**: Make scripts executable:
```bash
chmod +x run_ui.sh
```

## Next Steps

After installation:

1. Configure `config.yaml` with your API credentials
2. Run the UI: `run_ui.bat` (Windows) or `./run_ui.sh` (Linux/Mac)
3. Open browser to `http://localhost:8501`
4. Start automating!

## Uninstallation

To remove Tessara:

```bash
# Uninstall Python packages
pip uninstall playwright beautifulsoup4 openai pyyaml psutil streamlit Pillow

# Remove the directory
rm -rf tessara_package  # Linux/Mac
# or
rmdir /s tessara_package  # Windows
```

