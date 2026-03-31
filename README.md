# Step-Aligned Script Generation with Verification and Recovery for Web Automation Testing

Generating executable, replayable, and adaptive web automation scripts from natural-language task descriptions remains challenging due to the dynamic and error-prone nature of modern web interfaces. Existing LLM-based approaches often struggle with maintaining script robustness and recovering from interaction failures. We present Tessara, an agentic framework that integrates high-level planning with step-aligned scripting, layered verification, and adaptive recovery. Given a task description, Tessara first decomposes it into a sequence of high-level actions and grounds each action into an executable Playwright code fragment. This design enables fine-grained failure localization, selective regeneration of failing segments, and reversibility-aware backtracking during execution. Tessara further applies syntactic, execution-level, and semantic
verification to detect and repair malformed code, interaction errors, and incorrect landing states. Experimental results demonstrate that Tessara automates test script generation while substantially improving action-sequence correctness over state-of-the-art baselines, offering a reliable solution for web automation testing.

## Features

- **Intelligent Planning**: LLM-powered task planning with step-by-step breakdown
- **Script Generation**: Automatic Playwright script generation from plans
- **Iterative Execution**: Multi-iteration approach with step concatenation
- **Real-time Monitoring**: Streamlit UI for live monitoring of execution
- **Backtracking**: Centralized state tracking and backtracking across steps and iterations
- **Screenshot Capture**: Automatic screenshot capture and reuse
- **Error Recovery**: Robust error handling and logging

## Architecture

Tessara consists of three main LLM components:

1. **Planner**: Analyzes the task and screenshot, generates a step-by-step plan
2. **Scripter**: Converts the plan into executable Playwright scripts
3. **Answering LLM**: Evaluates task completion by analyzing final screenshots

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- Azure OpenAI API access (or compatible OpenAI API)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install Playwright Browsers

```bash
playwright install chromium
```

### Step 3: Configure the System

1. Copy the configuration template:
   ```bash
   cp config.yaml.template config.yaml
   ```

2. Edit `config.yaml` and fill in:
   - Your Azure OpenAI API credentials
   - Your task description (`intent` and `nlp_task`)
   - Starting URL (`start_url`)
   - Problem ID (`problem_id`)

### Step 4: Verify Installation

Test your API connection:
```bash
cd codebase
python test_api_connection.py
```

## Usage

### Option 1: Using the Streamlit UI (Recommended)

1. Start the UI:
   ```bash
   cd codebase
   streamlit run tessara_ui.py
   ```

2. Open your browser to `http://localhost:8501`

3. Fill in the configuration in the sidebar:
   - Task/Intent
   - API Key
   - API Version
   - Model Name
   - Azure Endpoint
   - Start URL
   - Problem ID

4. Click "🚀 Run" to start automation

5. Monitor the execution in real-time:
   - **Planner Output**: See the generated plan
   - **Generated Script**: View the Playwright script
   - **Answering LLM Output**: Check task completion status
   - **Iteration Status**: Monitor execution progress
   - **Current Screenshot**: See the current state of the webpage
   - **State Information**: View the current state JSON

### Option 2: Command Line Interface

1. Edit `config.yaml` with your task details

2. Run the pipeline:
   ```bash
   cd codebase
   python main.py
   ```

## Project Structure

```
tessara_package/
├── codebase/
│   ├── main.py              # Main pipeline orchestration
│   ├── planner.py           # LLM planner module
│   ├── scripter.py          # LLM scripter module
│   ├── answering_llm.py     # Task evaluation module
│   ├── utils.py             # Utility functions (screenshot, DOM, etc.)
│   └── tessara_ui.py        # Streamlit UI
├── prompts/
│   ├── planner_instructions.txt
│   ├── scripter_instructions.txt
│   └── answering_instructions.txt
├── responses/               # Output directory (created automatically)
│   ├── {problem_id}_responses.json
│   ├── {problem_id}_screenshot.png
│   ├── {problem_id}_playwright_script.py
│   ├── {problem_id}_state.json
│   ├── {problem_id}_final_plan.txt
│   └── {problem_id}_final_script.py
├── config.yaml             # Configuration file (create from template)
├── config.yaml.template     # Configuration template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## How It Works

1. **Task Input**: User provides a natural language task description
2. **Screenshot Capture**: System captures a screenshot of the starting URL
3. **Planning**: Planner LLM analyzes the task and screenshot, generates a step-by-step plan
4. **Script Generation**: Scripter LLM converts the plan into executable Playwright code
5. **Execution**: Script is executed, capturing URLs after each successful step
6. **Evaluation**: Answering LLM evaluates if the task is complete
7. **Iteration**: If incomplete, the system re-plans and re-executes (up to 8 iterations)
8. **Concatenation**: All successful steps and scripts are concatenated into final outputs

## Output Files

After execution, the following files are created in the `responses/` directory:

- `{problem_id}_responses.json`: Complete log of all LLM interactions
- `{problem_id}_screenshot.png`: Initial screenshot
- `{problem_id}_playwright_script.py`: Generated Playwright script
- `{problem_id}_state.json`: State tracking (last successful step, URLs, etc.)
- `{problem_id}_final_plan.txt`: Concatenated final plan
- `{problem_id}_final_script.py`: Concatenated final script
- `last_update.png`: Latest screenshot from execution

## Configuration Options

### API Configuration

- `api_key`: Your Azure OpenAI API key
- `api_version`: API version (typically "2024-12-01-preview")
- `azure_endpoint`: Your Azure OpenAI endpoint URL

### Task Configuration

- `intent`: Natural language description of the task
- `start_url`: URL where automation should begin
- `problem_id`: Unique identifier for this task

### Optional Configuration

- `playwright_user_data_dir`: Path to Chrome user data directory for persistent profiles

## Troubleshooting

### Playwright Browser Issues

If you encounter browser-related errors:

1. Ensure Chrome is installed
2. Run `playwright install chromium`
3. Check that the browser path is correct

### API Connection Issues

1. Verify your API key and endpoint in `config.yaml`
2. Test connection with `python test_api_connection.py`
3. Check your Azure OpenAI quota and limits

### Import Errors

1. Ensure you're running from the `codebase/` directory
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Verify Python version: `python --version` (should be 3.8+)

### UI Not Loading

1. Ensure Streamlit is installed: `pip install streamlit`
2. Check that port 8501 is not in use
3. Try accessing `http://localhost:8501` directly

## Limitations

- Maximum 8 iterations per task
- Requires Azure OpenAI API access
- Chrome browser must be installed
- Some websites may have anti-automation measures

## Contributing

This is a research tool. For issues or questions, please refer to the main project documentation.

## License

This tool is provided for research purposes.

## Citation

If you use Tessara in your research, please cite appropriately.

## Support

For issues or questions, please check:
- Configuration file is correctly set up
- All dependencies are installed
- API credentials are valid
- Browser is properly installed

---

**Version**: 1.0  
**Last Updated**: February 2025


