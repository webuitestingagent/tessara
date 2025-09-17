import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from bs4 import BeautifulSoup
import yaml, json, os

def log_interaction(problem_id, stage, content, log_file=None):
    log_file = f"../{problem_id}_responses.json"
    log_entry = {
        "problem_id": problem_id,
        "stage": stage,
        "content": content
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

def initialize_webdriver(geckodriver_path):  
    service = Service(geckodriver_path)  
    options = Options()  
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)  
    return driver 

def get_dom_tree(url, driver_path):
    options = Options()
    options.add_argument("--headless")

    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(url)
    time.sleep(3)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    return soup

def get_screenshot(url, output_path, driver_path, profile_path=None):
    options = Options()
    options.add_argument("--headless")

    # Attach custom profile if provided
    if profile_path:
        profile = FirefoxProfile(profile_path)
        options.profile = profile  # ✅ Correct new way to attach it

    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)  # ❌ don't pass firefox_profile anymore

    driver.get(url)
    time.sleep(2)

    total_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, total_height)
    driver.save_screenshot(output_path)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
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

def wrap_script_with_exit_handling(script_code):
    final_block = '''
try:
    # Original script logic
{script_body}
finally:
    try:
        current_url = driver.current_url
        with open("recovery_url.txt", "w") as f:
            f.write(current_url)
        driver.save_screenshot("recovery_screenshot.png")
    except Exception as e:
        print("Failed to capture final URL or screenshot:", e)
    try:
        driver.quit()
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

    with open(script_path, "w", encoding="utf-8") as file:
        for line in lines:
            if "driver.quit()" in line or "driver.close()" in line:
                file.write(f"# {line.strip()}  # Disabled by pipeline\n")
            else:
                file.write(line)
