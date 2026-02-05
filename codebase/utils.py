from subprocess import PIPE, Popen
from bs4 import BeautifulSoup
import time, yaml, json, os, re
from playwright.sync_api import sync_playwright

def sanitize_content_for_logging(content):
    """Recursively remove image_url fields from content to avoid saving large base64 images"""
    if isinstance(content, dict):
        return {k: sanitize_content_for_logging(v) for k, v in content.items() if k != "image_url"}
    elif isinstance(content, list):
        return [sanitize_content_for_logging(item) for item in content]
    else:
        return content

def log_interaction(problem_id, stage, content, log_file=None):
    log_file = f"../responses/{problem_id}_responses.json"
    # Remove image_url from content before logging
    sanitized_content = sanitize_content_for_logging(content)
    
    log_entry = {
        "problem_id": problem_id,
        "stage": stage,
        "content": sanitized_content
    }

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

def load_config(path="../config.yaml"):
    with open(path, "r") as file:
        return yaml.safe_load(file)
    #print("🤬 utils load_config()")

def get_dom_tree(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        # Use larger viewport to ensure full page content is loaded
        context = browser.new_context(viewport={"width": 2560, "height": 1440})
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        time.sleep(2)
        
        html = page.content()
        context.close()
        browser.close()
    
    soup = BeautifulSoup(html, 'html.parser')
    return soup

# def get_screenshot(url, output_path, profile_path=None):
#     options = Options()
#     options.add_argument("--headless")
#     #options.set_preference("permissions.default.image", 2)
#     options.set_preference("media.autoplay.default", 1)
#     options.set_preference("media.autoplay.block-webaudio", True)
#     options.set_preference("layers.acceleration.disabled", True)

#     if profile_path:
#         profile = FirefoxProfile(profile_path)
#         options.profile = profile

#     driver = webdriver.Firefox(options=options)
#     driver.set_page_load_timeout(10)

#     try:
#         driver.get(url)

#         WebDriverWait(driver, 10).until(
#             lambda d: d.execute_script('return document.readyState') == 'complete'
#         )

#         #driver.set_window_size(1920, 1080)
#         driver.save_screenshot(output_path)

#         html = driver.page_source
#         soup = BeautifulSoup(html, 'html.parser')

#     finally:
#         driver.quit()
#     return soup, output_path

from bs4 import BeautifulSoup
import time

def get_screenshot(url, output_path, profile_path=None):
    """Get screenshot and DOM tree using Playwright"""
    with sync_playwright() as p:
        # Use Chrome for better compatibility
        # Use larger viewport to ensure full page visibility
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 2560, "height": 1440})
        page = context.new_page()
        
        try:
            # Navigate to URL
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("load", timeout=10000)
            
            # Wait for networkidle with timeout
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                pass  # Continue if networkidle times out
            
            # Small buffer delay for lazy-loaded content
            time.sleep(2)
            
            # Get the actual page dimensions to ensure we capture everything
            scroll_height = page.evaluate("""
                () => Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.offsetHeight,
                    document.body.clientHeight,
                    document.documentElement.clientHeight
                )
            """)
            
            scroll_width = page.evaluate("""
                () => Math.max(
                    document.body.scrollWidth,
                    document.documentElement.scrollWidth,
                    document.body.offsetWidth,
                    document.documentElement.offsetWidth,
                    document.body.clientWidth,
                    document.documentElement.clientWidth
                )
            """)
            
            # Set viewport to match page dimensions (with minimums to ensure good visibility)
            # Note: full_page=True will still capture everything by scrolling, but larger viewport shows more at once
            viewport_width = max(2560, scroll_width)
            viewport_height = max(1440, scroll_height)
            # Cap at reasonable maximum to avoid performance issues (but full_page screenshot will still capture all)
            viewport_width = min(viewport_width, 5120)
            viewport_height = min(viewport_height, 2880)
            page.set_viewport_size({"width": viewport_width, "height": viewport_height})
            
            # Take full-page screenshot
            page.screenshot(path=output_path, full_page=True)
            
            # Get HTML content
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
        finally:
            context.close()
            browser.close()
    
    return soup, output_path


def filter_dom_by_whitelist(dom_tree, whitelist):
    filtered_elements = []
    for tag in dom_tree.find_all(True):
        for item in whitelist:
            item_lower = item.lower()
            if item_lower == "button" and tag.name == "button":
                filtered_elements.append(tag)
            elif item_lower == "text box" and tag.name == "input":
                if tag.get("type") in ["text", "search", None]:
                    filtered_elements.append(tag)
            elif item_lower == "link" and tag.name == "a":
                filtered_elements.append(tag)
    return "\n".join(str(el) for el in filtered_elements)

def save_script_to_file(script_text, path="generated_script.py"):
    with open(path, "w") as f:
        f.write(script_text)
    #print("🤬 utils save_script_to_file()")

def wrap_script_with_exit_handling(script_code):
    final_block = '''
try:
    # Original script logic
{script_body}
finally:
    try:
        current_url = page.url
        page.screenshot(path="../responses/last_update.png", full_page=True)
        
        # Save state to JSON file (replaces individual text files)
        problem_id_placeholder = "REPLACE_PROBLEM_ID"  # This should be replaced by scripter
        if 'last_executed_step' in locals() and 'step_urls' in locals():
            import json
            import os
            state_file = f"../responses/{{problem_id_placeholder}}_state.json"
            state = {{
                "last_successful_step": last_executed_step,
                "step_urls": step_urls,
                "recovery_url": current_url
            }}
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Failed to capture final URL or screenshot/save step data: {{e}}")
    try:
        context.close()
        browser.close()
    except:
        pass
'''
    indented_script = "\n".join(["    " + line for line in script_code.strip().splitlines()])
    return final_block.format(script_body=indented_script)

def indent(text, prefix):
    return "".join(prefix + line if line.strip() else line for line in text.splitlines(True))

def disable_browser_quit_calls(script_path):
    with open(script_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    #print("🤬 utils disable_browser_quit_calls()")

    with open(script_path, "w", encoding="utf-8") as file:
        for line in lines:
            if "browser.close()" in line or "context.close()" in line or "page.close()" in line:
                file.write(f"# {line.strip()}  # Disabled by pipeline\n")
            else:
                file.write(line)

def get_state_file_path(problem_id):
    """Get the path to the state JSON file"""
    return f"../responses/{problem_id}_state.json"

def load_state(problem_id):
    """Load state from JSON file"""
    state_file = get_state_file_path(problem_id)
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "last_successful_step": 0,
        "step_urls": {},
        "recovery_url": None
    }

def save_state(problem_id, last_successful_step=None, step_urls=None, recovery_url=None):
    """Save state to JSON file, updating only provided fields"""
    state_file = get_state_file_path(problem_id)
    state = load_state(problem_id)
    
    if last_successful_step is not None:
        state["last_successful_step"] = last_successful_step
    if step_urls is not None:
        state["step_urls"].update(step_urls)
    if recovery_url is not None:
        state["recovery_url"] = recovery_url
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    
    return state

def log_token_usage(response, problem_id, stage):
    usage_fields = getattr(response, "usage", None)
    log_dict = {}

    if usage_fields:
        usage_dict = usage_fields.__dict__ if hasattr(usage_fields, "__dict__") else dict(usage_fields)
        print(f"[DEBUG] Available usage fields: {usage_dict}")

        input_tokens = getattr(usage_fields, "prompt_tokens", None) or \
                       getattr(usage_fields, "total_input_tokens", None) or \
                       getattr(usage_fields, "input_tokens", None)

        output_tokens = getattr(usage_fields, "completion_tokens", None) or \
                        getattr(usage_fields, "total_output_tokens", None) or \
                        getattr(usage_fields, "output_tokens", None)

        total_tokens = getattr(usage_fields, "total_tokens", None)
        cost = getattr(usage_fields, "total_cost", None) or "N/A"

        log_dict = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "timestamp": time.time()
        }
    else:
        print("[WARNING] No usage information found in response")
        log_dict = {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "cost": "N/A",
            "timestamp": time.time()
        }

    # ✅ Add token log entry to the same JSON interaction log file
    log_interaction(problem_id, stage + "_token_usage", log_dict)


def extract_successful_plan_steps(parsed_plan, last_successful_step):
    """
    Extracts the steps from the parsed plan up to the last successful step.
    """
    return parsed_plan[:last_successful_step]

def extract_script_prefix_by_step(script_code, steps_count):
    """
    Extracts lines from script_code for the given number of steps.
    """
    lines = script_code.splitlines()
    prefix_lines = []
    step_start_pattern = re.compile(r'Executing Step (\d+) -')
    current_step = 0

    for line in lines:
        match = step_start_pattern.search(line)
        if match:
            current_step = int(match.group(1))
        if current_step <= steps_count:
            prefix_lines.append(line)

    return "\n".join(prefix_lines)

def final_save_and_run(plan_steps, script_code, problem_id):
    # Log final plan and script to JSON
    plan_json = [{"step": i+1, "action": step} for i, step in enumerate(plan_steps)]
    log_interaction(problem_id, "final_plan", plan_json)
    log_interaction(problem_id, "final_script", script_code)

    # Save script to file and run it
    with open(f"../responses/{problem_id}_final_script.py", "w") as f:
        f.write(script_code)

    save_script_to_file(script_code, path="../responses/final_script.py")
    proc = Popen(["python", "../responses/final_script.py"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    print(stdout.decode('utf-8'), stderr.decode('utf-8'))


