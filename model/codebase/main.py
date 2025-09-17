import os
import shutil
import tempfile
from subprocess import run, CalledProcessError
from utils import (
    get_screenshot,
    get_dom_tree,
    filter_dom_by_whitelist,
    save_script_to_file,
    load_config,
)
from planner import generate_plan
from scripter import generate_script
from answering import evaluate_task_completion
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile


def initialize_webdriver(geckodriver_path, base_profile_path=None):
    """
    Initializes a headless Firefox WebDriver using a specified GeckoDriver path and optional base Firefox profile.

    Args:
        geckodriver_path (str): Path to the geckodriver executable.
        base_profile_path (str, optional): Path to a base Firefox profile directory.

    Returns:
        tuple: (webdriver.Firefox instance, str path to temporary profile)
    """
    firefox_options = Options()
    firefox_options.add_argument("--headless")

    if base_profile_path:
        temp_profile_root = tempfile.mkdtemp()
        temp_profile_path = os.path.join(temp_profile_root, "profile")

        # Custom copy that skips parent.lock
        def ignore_files(_, filenames):
            return {"parent.lock"} if "parent.lock" in filenames else set()

        shutil.copytree(base_profile_path, temp_profile_path, ignore=ignore_files)
        firefox_options.profile = base_profile_path
    else:
        temp_profile_path = tempfile.mkdtemp()
        firefox_options.profile = base_profile_path

    service = Service(geckodriver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver, temp_profile_path


def wrap_script_with_exit_handling(script_code):
    """
    Adds task success flag handling to the generated script for easier result interpretation.

    Args:
        script_code (str): Original generated Python script code.

    Returns:
        str: Script code with task success status handling prepended and appended.
    """
    lines = script_code.strip().splitlines()
    new_lines = ["success_status = True"]
    new_lines.extend(lines)
    new_lines.append("print('Task completion status:', 'Success' if success_status else 'Failed')")
    return "\n".join(new_lines)


def run_script_and_check(script_path):
    """
    Executes the generated Python script and checks if it ran successfully.

    Args:
        script_path (str): Path to the Python script file to be executed.

    Returns:
        bool: True if the script executes successfully, False otherwise.
    """
    try:
        result = run(["python", script_path], check=True)
        return True
    except CalledProcessError as e:
        print("Exit code from script:", e.returncode)
        return False


def run_pipeline(start_url, screenshot_path, script_path, config, problem_id, failure_reason=None):
    """
    Executes a single run of the task completion pipeline:
    - Takes a screenshot
    - Plans and scripts the task
    - Executes the task

    Args:
        start_url (str): The initial URL to begin the task.
        screenshot_path (str): Path to store the screenshot image.
        script_path (str): Path to store the generated script.
        config (dict): Configuration parameters.
        problem_id (str): Identifier for the current task/problem.
        failure_reason (str, optional): Feedback from previous failed attempts.

    Returns:
        bool: True if the script execution was successful, False otherwise.
    """
    dom_tree, _ = get_screenshot(start_url, screenshot_path, config['geckodriver_path'], config['firefox_profile_path'])
    with open(screenshot_path, "rb") as f:
        screenshot_bytes = f.read()

    nlp_input = config['intent']
    if failure_reason:
        nlp_input += f"\n\n[Previous Failure Reason]: {failure_reason}"

    plan_text, parsed_plan = generate_plan(nlp_input, screenshot_bytes, config['planner'], problem_id)

    whitelist = list({step['element_type'].lower() for step in parsed_plan})
    filtered_dom = filter_dom_by_whitelist(dom_tree, whitelist)

    script_code = generate_script(parsed_plan, filtered_dom, start_url, screenshot_bytes, config['scripter'], problem_id)
    wrapped_script = wrap_script_with_exit_handling(script_code)
    save_script_to_file(wrapped_script, path=script_path)

    return run_script_and_check(script_path)


def execute_pipeline_until_success(config, problem_id):
    """
    Executes the pipeline iteratively until success is achieved or a maximum number of attempts is reached.

    Args:
        config (dict): Configuration parameters for the pipeline.
        problem_id (str): Identifier for the current task/problem.
    """
    original_url = config['start_url']
    screenshot_path = f"../responses/{problem_id}_screenshot.png"
    script_path = f"../responses/{problem_id}_selenium_script.py"

    iteration_count = 0
    success = False
    previous_llm_result = None
    MAX_ITERATIONS = 15

    while not success and iteration_count < MAX_ITERATIONS:
        print(f"Starting iteration {iteration_count + 1}...")
        iteration_success = run_pipeline(original_url, screenshot_path, script_path, config, problem_id, failure_reason=previous_llm_result)

        if iteration_success:
            try:
                with open("../responses/recovery_url.txt", "r") as f:
                    latest_url = f.read().strip()
                print("Fetching fresh screenshot from latest URL:", latest_url)
            except Exception as e:
                print("Could not load latest URL for fresh screenshot, using original_url instead:", e)
                latest_url = original_url

            try:
                dom_tree, new_sc_path = get_screenshot(latest_url, screenshot_path, config['geckodriver_path'], config['firefox_profile_path'])
                screenshot_path = new_sc_path
            except Exception as e:
                print("Failed to capture fresh screenshot, reusing previous one:", e)

            print("Answering LLM with new screenshot path: ", screenshot_path)
            llm_result, llm_output = evaluate_task_completion(screenshot_path)
            print("\n🧪 LLM Raw Output:\n" + "-" * 40)
            print(repr(llm_result))
            print("-" * 40)

            if "Success" in llm_result:
                print("Answering LLM reported success. Ending process.")
                success = True
            elif "Failure" in llm_result:
                print("Answering LLM reported failure. Continuing with recovery.")
                previous_llm_result = llm_output
                try:
                    with open("../responses/recovery_url.txt", "r") as f:
                        updated_url = f.read().strip()
                    updated_screenshot_path = "../responses/last_update.png"
                    original_url = updated_url
                    screenshot_path = updated_screenshot_path
                except Exception as e:
                    print("Failed during recovery:", e)
                    original_url = config['start_url']
                    screenshot_path = f"../responses/{problem_id}_screenshot.png"
            else:
                print("Unexpected response from LLM. Re-evaluating.")
                previous_llm_result = None
        else:
            print("Iteration failed. Restarting with original setup.")
            original_url = config['start_url']
            screenshot_path = f"../responses/{problem_id}_screenshot.png"
            previous_llm_result = None

        iteration_count += 1

    if not success:
        print(f"❌ Task failed after {MAX_ITERATIONS} iterations. Terminating.")


if __name__ == "__main__":
    """
    Entry point for running the automated web task completion pipeline.

    Loads the configuration, executes the pipeline, and ensures temporary resources are cleaned up on exit.
    """
    config = load_config()
    temp_profile_root = None
    try:
        print("Using geckodriver at:", config['geckodriver_path'])
        print("Exists:", os.path.exists(config['geckodriver_path']))
        problem_id = config['problem_id']
        execute_pipeline_until_success(config, problem_id)
    except Exception as e:
        print("A geckodriver error occurred:", e)
    finally:
        # Clean up temporary profile
        if temp_profile_root and os.path.exists(temp_profile_root):
            try:
                shutil.rmtree(temp_profile_root, ignore_errors=True)
                print("🧹 Cleaned up temporary Firefox profile.")
            except Exception as cleanup_error:
                print("⚠️ Failed to clean temporary profile:", cleanup_error)
