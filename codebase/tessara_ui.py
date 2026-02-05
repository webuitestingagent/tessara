import streamlit as st
import yaml
import os
import sys
from pathlib import Path
import multiprocessing
import time
from PIL import Image
import json
from datetime import datetime
import subprocess

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Page config
st.set_page_config(
    page_title="Tessara - Web Automation System",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    /* Set dark theme for the entire app */
    .stApp {
        background-color: #0e1117;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    .status-running {
        background-color: #1e3a2e;
        border: 2px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #ffffff;
    }
    .status-stopped {
        background-color: #3a1e1e;
        border: 2px solid #dc3545;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #ffffff;
    }
    .output-box {
        background-color: #0e1117;
        border: 2px solid #3a3a3a;
        padding: 1rem;
        border-radius: 0.5rem;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: #ffffff;
    }
    /* Style text areas to match dark theme */
    .stTextArea textarea {
        background-color: #0e1117 !important;
        color: #ffffff !important;
        border: 2px solid #3a3a3a !important;
    }
    /* Style code blocks */
    .stCode {
        background-color: #0e1117 !important;
        border: 2px solid #3a3a3a !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
    }
    .stCode code {
        color: #ffffff !important;
    }
    /* Style JSON displays */
    .stJson {
        background-color: #0e1117 !important;
        border: 2px solid #3a3a3a !important;
        color: #ffffff !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
    }
    /* Style info boxes */
    .stInfo {
        background-color: #0e1117 !important;
        border: 2px solid #3a3a3a !important;
        color: #ffffff !important;
    }
    /* Style headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    /* Style text */
    p, .stMarkdown, div[data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }
    /* Style captions */
    .stCaption {
        color: #aaaaaa !important;
    }
    /* Style main content area */
    .main .block-container {
        background-color: #0e1117;
    }
    /* Style sidebar */
    .css-1d391kg {
        background-color: #0e1117;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'problem_id' not in st.session_state:
    st.session_state.problem_id = "TestTask"
if 'last_planner_output' not in st.session_state:
    st.session_state.last_planner_output = ""
if 'last_scripter_output' not in st.session_state:
    st.session_state.last_scripter_output = ""
if 'last_llm_output' not in st.session_state:
    st.session_state.last_llm_output = ""
if 'current_iteration' not in st.session_state:
    st.session_state.current_iteration = 0
if 'execution_log' not in st.session_state:
    st.session_state.execution_log = []

def load_latest_responses(problem_id):
    """Load latest responses from JSON file"""
    responses_file = f"../responses/{problem_id}_responses.json"
    if os.path.exists(responses_file):
        try:
            with open(responses_file, "r") as f:
                responses = json.load(f)
            
            # Get latest planner response
            planner_responses = [r for r in responses if r.get("stage") == "planner_response"]
            if planner_responses:
                st.session_state.last_planner_output = planner_responses[-1].get("content", "")
            
            # Get latest scripter response
            scripter_responses = [r for r in responses if r.get("stage") == "scripter_response"]
            if scripter_responses:
                st.session_state.last_scripter_output = scripter_responses[-1].get("content", "")
            
            # Get latest answering LLM response
            answering_responses = [r for r in responses if r.get("stage") == "answering_llm"]
            if answering_responses:
                llm_content = answering_responses[-1].get("content", {})
                if isinstance(llm_content, dict):
                    st.session_state.last_llm_output = llm_content.get("response", "")
                else:
                    st.session_state.last_llm_output = str(llm_content)
        except Exception as e:
            pass

def get_screenshot_path(problem_id):
    """Get the path to the current screenshot"""
    paths = [
        "../responses/last_update.png",
        f"../responses/{problem_id}_screenshot.png"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

# Header
st.markdown('<div class="main-header">🤖 Tessara - Web Automation System</div>', unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Intent/Task
    intent = st.text_area(
        "Task/Intent",
        height=150,
        help="Describe the task you want the system to perform",
        value="find the cost of the cheapest flight from Dallas to Philadelphia on May 6 2026"
    )
    
    st.divider()
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    api_key = st.text_input("API Key", type="password", value="79240e27c4db4193892082f348e77ac1")
    api_version = st.text_input("API Version", value="2024-12-01-preview")
    model_name = st.text_input("Model Name", value="gpt-4o")
    azure_endpoint = st.text_input("Azure Endpoint", value="https://tien.openai.azure.com/")
    
    st.divider()
    
    # Start URL
    start_url = st.text_input("Start URL", value="https://www.google.com/travel/flights?gl=US&hl=en-US")
    
    st.divider()
    
    # Problem ID
    problem_id = st.text_input("Problem ID", value="TestTask")
    st.session_state.problem_id = problem_id
    
    st.divider()
    
    # Run button
    col1, col2 = st.columns(2)
    with col1:
        run_button = st.button("🚀 Run", type="primary", use_container_width=True)
    with col2:
        stop_button = st.button("⏹️ Stop", use_container_width=True)
    
    st.divider()
    st.caption("💡 Fill in all fields and click Run to start automation")

# Handle run/stop buttons
if run_button and not st.session_state.running:
    if not intent or not api_key or not start_url:
        st.error("❌ Please fill in all required fields: Intent, API Key, and Start URL")
    else:
        # Create config dict matching the expected structure
        config = {
            'intent': intent,
            'nlp_task': intent,
            'start_url': start_url,
            'problem_id': problem_id,
            'playwright_user_data_dir': None,  # Optional
            'planner': {
                'api_key': api_key,
                'api_version': api_version,
                'azure_endpoint': azure_endpoint
            },
            'scripter': {
                'api_key': api_key,
                'api_version': api_version,
                'azure_endpoint': azure_endpoint
            }
        }
        
        # Save config to the expected location (for reference, but execute_pipeline_until_success uses the dict directly)
        config_path = "../config.yaml"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        # Reset session state
        st.session_state.running = True
        st.session_state.last_planner_output = ""
        st.session_state.last_scripter_output = ""
        st.session_state.last_llm_output = ""
        st.session_state.current_iteration = 0
        st.session_state.execution_log = []
        st.session_state.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline started")
        
        # Run pipeline in a separate process to avoid event loop conflicts with Playwright
        # The config is already saved to ../config.yaml above
        try:
            # Change to codebase directory
            codebase_dir = os.path.dirname(os.path.abspath(__file__))
            main_script = os.path.join(codebase_dir, "main.py")
            
            # Run the pipeline in a subprocess (separate process avoids asyncio conflicts)
            process = subprocess.Popen(
                [sys.executable, main_script],
                cwd=codebase_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Store process for status checking
            st.session_state.pipeline_process = process
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            st.session_state.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")
            st.session_state.running = False
        
        # Initialize process tracking if not exists
        if 'pipeline_process' not in st.session_state:
            st.session_state.pipeline_process = None
        
        st.rerun()

if stop_button:
    # Kill the process if it's running
    if st.session_state.pipeline_process is not None:
        try:
            st.session_state.pipeline_process.terminate()
            # Wait a bit, then force kill if needed
            try:
                st.session_state.pipeline_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                st.session_state.pipeline_process.kill()
            st.session_state.pipeline_process = None
        except Exception as e:
            st.session_state.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Error stopping process: {e}")
    
    st.session_state.running = False
    st.session_state.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline stopped by user")
    st.warning("⏹️ Stopping pipeline...")
    st.rerun()

# Load latest data
if st.session_state.running or st.session_state.problem_id:
    load_latest_responses(st.session_state.problem_id)

# Main layout
col1, col2 = st.columns([1.2, 1])

with col1:
    # Planner Output
    st.header("📋 Planner Output")
    planner_container = st.container()
    with planner_container:
        if st.session_state.last_planner_output:
            st.markdown(f'<div class="output-box">{st.session_state.last_planner_output[:2000]}</div>', unsafe_allow_html=True)
            if len(st.session_state.last_planner_output) > 2000:
                st.caption(f"... ({len(st.session_state.last_planner_output) - 2000} more characters)")
        else:
            st.info("⏳ Waiting for planner output...")
    
    st.divider()
    
    # Generated Script
    st.header("📝 Generated Script")
    script_container = st.container()
    with script_container:
        if st.session_state.last_scripter_output:
            # Show first 3000 chars
            script_preview = st.session_state.last_scripter_output[:3000]
            st.code(script_preview, language="python")
            if len(st.session_state.last_scripter_output) > 3000:
                st.caption(f"... ({len(st.session_state.last_scripter_output) - 3000} more characters)")
        else:
            st.info("⏳ Waiting for script generation...")
    
    st.divider()
    
    # Answering LLM Output
    st.header("💬 Answering LLM Output")
    llm_container = st.container()
    with llm_container:
        if st.session_state.last_llm_output:
            st.markdown(f'<div class="output-box">{st.session_state.last_llm_output}</div>', unsafe_allow_html=True)
        else:
            st.info("⏳ Waiting for LLM evaluation...")

with col2:
    # Iteration Status
    st.header("🔄 Iteration Status")
    status_container = st.container()
    with status_container:
        if st.session_state.running:
            st.markdown('<div class="status-running">🟢 <strong>RUNNING</strong> - Pipeline is executing</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-stopped">⚪ <strong>STOPPED</strong> - Pipeline is not running</div>', unsafe_allow_html=True)
        
        # Execution log
        if st.session_state.execution_log:
            st.subheader("📜 Execution Log")
            log_text = "\n".join(st.session_state.execution_log[-15:])  # Show last 15 entries
            st.text_area("Execution Log", value=log_text, height=200, key="log_display", label_visibility="collapsed")
    
    st.divider()
    
    # Current Screenshot
    st.header("📸 Current Screenshot")
    screenshot_container = st.container()
    with screenshot_container:
        screenshot_path = get_screenshot_path(st.session_state.problem_id)
        if screenshot_path:
            try:
                img = Image.open(screenshot_path)
                st.image(img, caption=f"Current Screenshot", width='stretch')
                st.caption(f"Path: {screenshot_path}")
            except Exception as e:
                st.error(f"Error loading screenshot: {e}")
        else:
            st.info("⏳ No screenshot available yet")
    
    st.divider()
    
    # State Information
    st.header("📊 State Information")
    state_container = st.container()
    with state_container:
        state_file = f"../responses/{st.session_state.problem_id}_state.json"
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                st.json(state)
            except:
                st.info("State file exists but could not be loaded")
        else:
            st.info("No state file found")

# Auto-refresh when running - check process status
if st.session_state.running and st.session_state.pipeline_process is not None:
    # Check if process is still running (non-blocking)
    return_code = st.session_state.pipeline_process.poll()
    if return_code is not None:
        # Process has finished
        try:
            stdout, stderr = st.session_state.pipeline_process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", ""
        
        if return_code == 0:
            st.session_state.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Pipeline completed successfully")
        else:
            error_msg = f"Pipeline failed with return code {return_code}"
            if stderr:
                # Show last 500 chars of error
                error_msg += f"\nError: {stderr[-500:]}"
            st.session_state.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {error_msg}")
        
        st.session_state.running = False
        st.session_state.pipeline_process = None
    else:
        # Process still running, refresh UI to show updates
        time.sleep(3)  # Refresh every 3 seconds
        st.rerun()
elif st.session_state.running:
    # Running but no process yet, just refresh
    time.sleep(3)
    st.rerun()

# Footer
st.divider()
st.caption("🤖 Tessara - Web Automation System | Real-time monitoring and execution")
