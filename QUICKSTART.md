# Quick Start Guide

Get Tessara running in 5 minutes!

## 1. Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. Configure (1 minute)

```bash
# Copy template
cp config.yaml.template config.yaml

# Edit config.yaml - add your:
# - Azure OpenAI API key
# - Endpoint URL
# - Task description
# - Start URL
```

## 3. Run UI (30 seconds)

**Windows:**
```bash
run_ui.bat
```

**Linux/Mac:**
```bash
chmod +x run_ui.sh
./run_ui.sh
```

## 4. Use the UI (1 minute)

1. Open browser to `http://localhost:8501`
2. Fill in the sidebar:
   - Task/Intent: "Find the cheapest flight from NYC to LA"
   - API Key: Your Azure OpenAI key
   - Start URL: "https://www.google.com/travel/flights"
   - Problem ID: "FlightSearch"
3. Click "🚀 Run"
4. Watch it automate!

## Example Configuration

```yaml
intent: "Find the cheapest flight from New York to Los Angeles"
start_url: "https://www.google.com/travel/flights"
problem_id: "FlightSearch"
planner:
  api_key: "your-key-here"
  azure_endpoint: "https://your-resource.openai.azure.com/"
  api_version: "2024-12-01-preview"
scripter:
  api_key: "your-key-here"
  azure_endpoint: "https://your-resource.openai.azure.com/"
  api_version: "2024-12-01-preview"
```

That's it! You're ready to automate.

## Need Help?

- See `README.md` for detailed documentation
- See `INSTALL.md` for troubleshooting
- Check the UI execution log for errors

