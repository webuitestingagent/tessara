import os, shutil, re, tempfile, time,psutil
from sys import stdout
from subprocess import run, CalledProcessError, PIPE, Popen
from utils import (get_screenshot, get_dom_tree, filter_dom_by_whitelist, save_script_to_file, load_config, final_save_and_run, load_state, save_state)
from planner import (generate_plan, parse_plan)
from scripter import generate_script, correct_script
from answering_llm import evaluate_task_completion


def wrap_script_with_exit_handling(script_code):
    lines = script_code.strip().splitlines()
    new_lines = ["success_status = True"]
    new_lines.extend(lines)
    new_lines.append("print('Task completion status:', 'Success' if success_status else 'Failed')")
    return "\n".join(new_lines)

def run_script_and_check(script_path, problem_id):
    """
    Run script and check result. Returns (success: bool, last_successful_step: int, output: str)
    """
    try:
        # Run the script with UTF-8 decoding to avoid Windows charmap issues
        result = run(
            ["python", script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",     # ✅ Force UTF-8 decoding
            errors="replace"      # ✅ Replace invalid characters instead of crashing
        )
        
        output_text = result.stdout + result.stderr
        
        from utils import log_interaction
        log_interaction(problem_id, "script_run_output", {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        })

        # Parse last successful step from output
        last_successful_step = parse_last_successful_step_from_output(output_text)
        
        # Also try to load from state JSON (in case script saved it)
        try:
            state = load_state(problem_id)
            file_step = state.get("last_successful_step", 0)
            if file_step > last_successful_step:
                last_successful_step = file_step
        except:
            pass
        
        # Save last successful step to state JSON
        try:
            save_state(problem_id, last_successful_step=last_successful_step)
        except Exception as e:
            print(f"[WARNING] Failed to save last successful step: {e}")

        if result.returncode == 0:
            return True, last_successful_step, output_text
        else:
            print("Exit code from script:", result.returncode)
            print("---- Script STDOUT ----\n", result.stdout)
            print("---- Script STDERR ----\n", result.stderr)
            return False, last_successful_step, output_text

    except CalledProcessError as e:
        print("Exit code from script:", e.returncode)
        # Try to parse last successful step even on error
        last_successful_step = 0
        try:
            state = load_state(problem_id)
            last_successful_step = state.get("last_successful_step", 0)
        except:
            pass
        return False, last_successful_step, ""



def kill_browser_processes():
    """Kill all running browser processes (Chrome/Firefox)."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower() if proc.info['name'] else ""
            if any(browser in name for browser in ["firefox", "chrome", "msedge", "chromium"]):
                proc.kill()
                print(f"[INFO] Killed browser process (PID: {proc.info['pid']}, Name: {proc.info['name']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def run_pipeline(start_url, screenshot_path, script_path, config, problem_id, failure_reason=None, iteration_num=0):
    """
    Run pipeline.
    Returns: (success: bool, last_successful_step: int, output: str, parsed_plan: list, script_code: str)
    """
    # Check if screenshot already exists (from previous iteration)
    # If it exists and is last_update.png, use it; otherwise take fresh screenshot
    if os.path.exists(screenshot_path) and screenshot_path.endswith("last_update.png"):
        print(f"[INFO] Reusing existing screenshot: {screenshot_path}")
        # Still need DOM tree, so get it from the URL
        profile_path = config.get('playwright_user_data_dir', None)
        dom_tree = get_dom_tree(start_url)
    else:
        # Take fresh screenshot
        profile_path = config.get('playwright_user_data_dir', None)
        dom_tree, _ = get_screenshot(start_url, screenshot_path, profile_path)
        print("screenshot captured")
    
    with open(screenshot_path, "rb") as f:
        screenshot_bytes = f.read()

    nlp_input = config['intent']
    if failure_reason:
        nlp_input += f"\n\n[Previous Failure Reason]: {failure_reason}"

    print(f"\n[ITERATION {iteration_num + 1}] Calling Planner...")
    plan_text, parsed_plan = generate_plan(nlp_input, screenshot_bytes, config['planner'], problem_id)
    
    # Validate that we have a parsable plan
    if not parsed_plan or len(parsed_plan) == 0:
        error_msg = f"Failed to parse plan. Planner response: {plan_text[:500]}"
        print(f"[ERROR] {error_msg}")
        return False, 0, error_msg, [], ""

    whitelist = list({step['element_type'].lower() for step in parsed_plan})
    filtered_dom = filter_dom_by_whitelist(dom_tree, whitelist)

    print(f"\n[ITERATION {iteration_num + 1}] Calling Scripter...")
    script_code = generate_script(parsed_plan, filtered_dom, start_url, screenshot_bytes, config['scripter'], problem_id)
    
    try:
        wrapped_script = wrap_script_with_exit_handling(script_code)
        save_script_to_file(wrapped_script, path=script_path)
    except Exception as e:
        error_msg = f"Failed to wrap or save script: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, 0, error_msg, [], ""

    try:
        success, last_step, output = run_script_and_check(script_path, problem_id)
        return success, last_step, output, parsed_plan, script_code

    except SyntaxError as e:  # Capturing syntax errors specifically
        print(f"Syntax Error encountered: {str(e)}")
        try:
            corrected_script = correct_script(script_code, str(e), config['scripter'], problem_id)
            save_script_to_file(corrected_script, path=script_path)
            success, last_step, output = run_script_and_check(script_path, problem_id)
            return success, last_step, output, parsed_plan, corrected_script
        except Exception as correction_error:
            error_msg = f"Failed to correct script: {str(correction_error)}"
            print(f"[ERROR] {error_msg}")
            return False, 0, error_msg, parsed_plan, script_code

    except Exception as e:
        print(f"An error occurred while executing the script: {str(e)}")
        return False, 0, str(e), parsed_plan, script_code

def extract_successful_steps_from_script(script_code, last_successful_step):
    """
    Extract the successful steps from script code up to last_successful_step.
    Returns the script code for successful steps only.
    """
    if last_successful_step == 0:
        return ""
    
    lines = script_code.splitlines()
    successful_lines = []
    step_start_pattern = re.compile(r'Executing Step (\d+) -')
    current_step = 0
    found_successful_steps = False
    
    for line in lines:
        match = step_start_pattern.search(line)
        if match:
            current_step = int(match.group(1))
            found_successful_steps = True
        
        # Include all lines up to and including the last successful step
        if not found_successful_steps or current_step <= last_successful_step:
            successful_lines.append(line)
        elif current_step > last_successful_step:
            # Stop at first step beyond successful
            break
    
    return "\n".join(successful_lines)

def execute_pipeline_until_success(config, problem_id):
    original_url = config['start_url']
    print("Start URL - ", original_url)
    screenshot_path = f"../responses/{problem_id}_screenshot.png"
    script_path = f"../responses/{problem_id}_playwright_script.py"

    iteration_count = 0
    success = False
    previous_llm_result = None
    last_successful_step = 0  # Track last successful step
    MAX_ITERATIONS = 8
    
    # Track successful steps and scripts across all iterations
    all_successful_steps = []  # List of step dictionaries
    all_successful_scripts = []  # List of script code strings

    while not success and iteration_count < MAX_ITERATIONS:
        print(f"\n{'='*60}")
        print(f"Starting iteration {iteration_count + 1}/{MAX_ITERATIONS}...")
        if last_successful_step > 0:
            print(f"[INFO] Last successful step: {last_successful_step}")
        
        # Always start from beginning (no backtracking)
        original_url = config['start_url']
        
        # Check if last_update.png exists from previous iteration - use it instead of taking fresh screenshot
        last_update_path = "../responses/last_update.png"
        if iteration_count > 0 and os.path.exists(last_update_path):
            print(f"[INFO] Using screenshot from previous iteration: {last_update_path}")
            screenshot_path = last_update_path
        elif iteration_count == 0:
            # First iteration: take fresh screenshot
            print(f"[INFO] First iteration: taking fresh screenshot from {original_url}")
        else:
            # No last_update.png found, will take fresh screenshot in run_pipeline
            print(f"[INFO] No previous screenshot found, will take fresh screenshot")
        
        # Prepare failure reason for planner feedback
        failure_reason = None
        if iteration_count > 0:
            if previous_llm_result:
                failure_reason = f"[Task Evaluation Feedback from Previous Iteration]:\n{previous_llm_result}\n\n[Last Successful Step]: {last_successful_step}"
            elif last_successful_step > 0:
                failure_reason = f"[Script Execution]: Failed at step {last_successful_step + 1}. Last successful step: {last_successful_step}"
        
        iteration_success, step_reached, output, parsed_plan, script_code = run_pipeline(
            original_url, 
            screenshot_path, 
            script_path, 
            config, 
            problem_id, 
            failure_reason=failure_reason,
            iteration_num=iteration_count
        )
        
        # Update last successful step if we made progress
        if step_reached > last_successful_step:
            last_successful_step = step_reached
            print(f"[INFO] Updated last successful step to {last_successful_step}")
            
            # Extract successful steps from this iteration's plan
            successful_steps = parsed_plan[:step_reached] if step_reached <= len(parsed_plan) else parsed_plan
            all_successful_steps.extend(successful_steps)
            
            # Extract successful script parts from this iteration
            successful_script = extract_successful_steps_from_script(script_code, step_reached)
            if successful_script:
                all_successful_scripts.append(successful_script)
            
            # Save URL and screenshot at last successful step
            try:
                state = load_state(problem_id)
                step_urls = state.get("step_urls", {})
                if str(last_successful_step) in step_urls:
                    step_url = step_urls[str(last_successful_step)]
                    print(f"[INFO] Saved URL at step {last_successful_step}: {step_url}")
                
                # Screenshot is already saved at last_update.png by the script
                if os.path.exists("../responses/last_update.png"):
                    print(f"[INFO] Screenshot saved at last_update.png for step {last_successful_step}")
            except Exception as e:
                print(f"[WARNING] Failed to save step URL/screenshot: {e}")
            
            try:
                save_state(problem_id, last_successful_step=last_successful_step)
            except Exception as e:
                print(f"[WARNING] Failed to save last successful step: {e}")
        
        if iteration_success:
            # Use last_update.png from script execution instead of taking fresh screenshot
            last_update_path = "../responses/last_update.png"
            if os.path.exists(last_update_path):
                print(f"[INFO] Using screenshot saved by script execution: {last_update_path}")
                screenshot_path = last_update_path
            else:
                # Fallback: take fresh screenshot if last_update.png doesn't exist
                try:
                    state = load_state(problem_id)
                    latest_url = state.get("recovery_url", original_url)
                except Exception as e:
                    latest_url = original_url

                try:
                    profile_path = config.get('playwright_user_data_dir', None)
                    dom_tree, new_sc_path = get_screenshot(
                        latest_url,
                        screenshot_path,
                        profile_path
                    )
                    screenshot_path = new_sc_path
                except Exception as e:
                    print("Failed to capture fresh screenshot, reusing previous one:", e)

            print(f"\n[ITERATION {iteration_count + 1}] Calling Answering LLM...")
            llm_result, llm_output = evaluate_task_completion(screenshot_path)

            if "Success" in llm_result:
                print("Answering LLM reported success. Ending process.")
                success = True
            elif "Failure" in llm_result:
                print("Answering LLM reported failure. Continuing to next iteration.")
                previous_llm_result = llm_output
                try:
                    state = load_state(problem_id)
                    updated_url = state.get("recovery_url", config['start_url'])
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
            print(f"[INFO] Plan execution failed. Last successful step: {last_successful_step}")
            
            # Try to parse last successful step from output if available
            if 'output' in locals() and output:
                parsed_step = parse_last_successful_step_from_output(output)
                if parsed_step > 0 and parsed_step > last_successful_step:
                    print(f"[INFO] Parsed last successful step from output: {parsed_step}")
                    last_successful_step = parsed_step
                    
                    # Extract successful steps from this iteration's plan
                    successful_steps = parsed_plan[:parsed_step] if parsed_step <= len(parsed_plan) else parsed_plan
                    all_successful_steps.extend(successful_steps)
                    
                    # Extract successful script parts from this iteration
                    successful_script = extract_successful_steps_from_script(script_code, parsed_step)
                    if successful_script:
                        all_successful_scripts.append(successful_script)
                    
                    try:
                        save_state(problem_id, last_successful_step=last_successful_step)
                    except Exception as e:
                        print(f"[WARNING] Failed to save last successful step: {e}")
        
        print(f"[INFO] Iteration {iteration_count + 1} completed")
        iteration_count += 1

    # Concatenate all successful steps and scripts
    if all_successful_steps:
        print(f"\n{'='*60}")
        print(f"[FINAL] Concatenating {len(all_successful_steps)} successful steps from {iteration_count} iterations")
        
        # Renumber steps sequentially
        final_steps = []
        for i, step in enumerate(all_successful_steps):
            final_step = step.copy()
            final_step['step_number'] = i + 1
            final_steps.append(final_step)
        
        # Save final action sequence
        final_plan_text = "\n".join([
            f"Step {step['step_number']} - {step['action_label']} - {step['element_type']} - {step['action']}"
            for step in final_steps
        ])
        
        final_plan_path = f"../responses/{problem_id}_final_plan.txt"
        with open(final_plan_path, "w") as f:
            f.write(final_plan_text)
        print(f"[FINAL] Saved final action sequence to {final_plan_path}")
        
        # Save final plan as JSON
        from utils import log_interaction
        log_interaction(problem_id, "final_action_sequence", final_steps)
        
        # Concatenate all successful scripts
        if all_successful_scripts:
            # Combine all successful script parts with iteration markers
            script_parts = []
            for i, script_part in enumerate(all_successful_scripts):
                script_parts.append(f"# === Successful script from iteration {i+1} ===\n{script_part}")
            combined_script = "\n\n".join(script_parts)
            combined_script = "# Combined successful script parts from all iterations\n\n" + combined_script
            
            final_script_path = f"../responses/{problem_id}_final_script.py"
            with open(final_script_path, "w") as f:
                f.write(combined_script)
            print(f"[FINAL] Saved final combined script to {final_script_path}")
            
            log_interaction(problem_id, "final_combined_script", combined_script)

    if not success:
        print(f"❌ Task failed after {MAX_ITERATIONS} iterations. Terminating.")

def extract_successful_plan_steps(parsed_plan, last_successful_step):
    """
    Extracts the steps from the parsed plan up to the last successful step.
    """
    return parsed_plan[:last_successful_step]

def extract_script_prefix_by_step(script_code, last_successful_step):
    """
    Extract the lines of script_code up to the last successful step.
    """
    lines = script_code.splitlines()
    prefix_lines = []
    step_start_pattern = re.compile(r'Executing Step (\d+) -')
    current_step = 0

    for line in lines:
        match = step_start_pattern.search(line)
        if match:
            current_step = int(match.group(1))
        if current_step <= last_successful_step:
            prefix_lines.append(line)

    return "\n".join(prefix_lines)

def parse_last_successful_step_from_output(output_text):
    """
    Parses the output to determine the last successful step.
    """
    executed_steps = re.findall(r'Executing Step (\d+) -', output_text)
    if not executed_steps:
        return 0
    return max(map(int, executed_steps))



if __name__ == "__main__":
    config = load_config()
    problem_id = config['problem_id']
    try:
        execute_pipeline_until_success(config, problem_id)
    except Exception as e:
        print("Pipeline error occurred:", e)
