# Changelog

## Version 1.0 - February 2025

### Initial Release

#### Features
- **Intelligent Planning**: LLM-powered task planning with step-by-step breakdown
- **Script Generation**: Automatic Playwright script generation from plans
- **Iterative Execution**: Multi-iteration approach with step concatenation
- **Real-time Monitoring**: Streamlit UI for live monitoring of execution
- **State Management**: Centralized state tracking across iterations
- **Screenshot Capture**: Automatic screenshot capture and reuse
- **Error Recovery**: Robust error handling and logging

#### Components
- Planner LLM module
- Scripter LLM module
- Answering LLM module
- Playwright-based browser automation
- Streamlit web UI
- State management system

#### Technical Details
- Uses Playwright for browser automation
- Chrome browser support
- Azure OpenAI API integration
- JSON-based state management
- Screenshot-based task evaluation

#### Known Limitations
- Maximum 8 iterations per task
- Requires Azure OpenAI API access
- Chrome browser must be installed
- Some websites may have anti-automation measures

