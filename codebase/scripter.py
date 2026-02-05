# scripter.py
import base64, re, time
from openai import AzureOpenAI
from utils import log_interaction, log_token_usage

def generate_script(plan_steps, filtered_dom, start_url, screenshot, scripter_conf, problem_id):
    with open("../prompts/scripter_instructions.txt", "r") as f:
        system_prompt = f.read()

    plan_text = "\n".join(
        [f"Step {i+1} - {step['action_label']} - {step['element_type']} - {step['action']}" for i, step in enumerate(plan_steps)]
    )
    user_prompt_text = f"Start URL: {start_url}\n\nProblem ID: {problem_id}\n\nIMPORTANT: In the script, replace {{PROBLEM_ID_PLACEHOLDER}} with: {problem_id}\n\nSteps:\n{plan_text}\n\nRelevant DOM:\n{str(filtered_dom)}\n\nCRITICAL FOR BACKTRACKING: You MUST record the URL after EVERY successful step execution. This is not optional - it is required for the backtracking feature to work. For each step:\n1. Before executing: print('Executing Step <N> - <action>')\n2. Update: last_executed_step = <N>\n3. After successful execution (inside try block, after the action succeeds):\n   - step_urls[<N>] = page.url\n   - Print: print(f'[SUCCESS] Step {{<N>}} completed. URL: {{page.url}}')\n\nIMPORTANT: Do NOT save individual step URL files. The step_urls dictionary will be saved to JSON at the end. Only record URLs for successfully completed steps in the step_urls dictionary.\n\nIf a step fails, do NOT record its URL. Only record URLs for successfully completed steps."

    base64_image = base64.b64encode(screenshot).decode("utf-8")
    start_time = time.time()
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]
        }
    ]

    # Print scripter prompt input
    print(f"\n{'='*60}")
    print(f"[SCRIPTER PROMPT INPUT]")
    print(f"System Prompt (first 500 chars):\n{system_prompt[:500]}...")
    print(f"\nUser Prompt:\n{user_prompt_text}")
    print(f"[Image included: base64 encoded screenshot]")
    print(f"{'='*60}\n")

    log_interaction(problem_id, "scripter_prompt", messages)

    client = AzureOpenAI(
        azure_endpoint=scripter_conf['azure_endpoint'],
        api_key=scripter_conf['api_key'],
        api_version=scripter_conf['api_version']
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.1,
        max_tokens=10000
    )

    log_token_usage(response, problem_id, "generate_script")
    # Calculate time taken
    elapsed_time = time.time() - start_time
    print(f"Time taken for generating script: {elapsed_time} seconds")

    script_code = response.choices[0].message.content.strip()
    
    # Print scripter response output (first 1000 chars)
    print(f"\n{'='*60}")
    print(f"[SCRIPTER RESPONSE OUTPUT]")
    print(f"Generated Script (first 1000 chars):\n{script_code[:1000]}...")
    if len(script_code) > 1000:
        print(f"[... {len(script_code) - 1000} more characters ...]")
    print(f"{'='*60}\n")
    
    # Extract Python code block if present
    python_code_block = re.search(r"```(?:python)?\s*\n(.*?)\n```", script_code, re.DOTALL)
    if python_code_block:
        script_code = python_code_block.group(1)
    else:
        # If no code block, try to find code after common prefixes
        # Remove markdown code block markers
        script_code = re.sub(r"^```(?:\w+)?\s*", "", script_code, flags=re.MULTILINE)
        script_code = re.sub(r"\s*```$", "", script_code, flags=re.MULTILINE)
        
        # Remove common explanatory prefixes
        lines = script_code.split('\n')
        code_start = 0
        for i, line in enumerate(lines):
            # Skip lines that are clearly explanatory text
            if any(phrase in line.lower() for phrase in [
                "to create a", "follow the format", "here's", "below is", 
                "the script", "python script", "playwright script"
            ]):
                continue
            # Start from first import or from playwright
            if line.strip().startswith(('import ', 'from ', 'with sync_playwright', 'from playwright')):
                code_start = i
                break
        
        script_code = '\n'.join(lines[code_start:])
    
    # Clean up any remaining markdown artifacts
    script_code = script_code.strip()
    
    # Replace problem_id placeholder with actual problem_id
    script_code = script_code.replace("{PROBLEM_ID_PLACEHOLDER}", problem_id)
    script_code = script_code.replace("{problem_id}", problem_id)  # Also handle lowercase version

    # Validate that we have actual Python code
    if not script_code or len(script_code) < 50:
        error_msg = "Generated script is too short or empty. Scripter may have generated explanatory text instead of code."
        print(f"[ERROR] {error_msg}")
        log_interaction(problem_id, "scripter_error", error_msg)
        raise ValueError(error_msg)
    
    # Check for common non-code patterns
    if any(phrase in script_code.lower()[:200] for phrase in [
        "to create a", "follow the format", "here's how", "the following",
        "you can use", "this script", "example script"
    ]):
        error_msg = "Generated script appears to contain explanatory text instead of code."
        print(f"[ERROR] {error_msg}")
        log_interaction(problem_id, "scripter_error", error_msg)
        raise ValueError(error_msg)

    log_interaction(problem_id, "scripter_response", script_code)

    return script_code

def correct_script(script_code, error_message, scripter_conf, problem_id):
    with open("../prompts/script_correction_instructions.txt", "r") as f:
        system_prompt = f.read()
    
    user_prompt_text = f"Original Script:\n{script_code}\n\nError Message:\n{error_message}\n\nPlease correct the script."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_text}
    ]
    
    log_interaction(problem_id, "script_correction_prompt", messages)
    
    client = AzureOpenAI(
        azure_endpoint=scripter_conf['azure_endpoint'],
        api_key=scripter_conf['api_key'],
        api_version=scripter_conf['api_version']
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5",
        messages=messages,
        temperature=0.1,
        max_tokens=10000
    )
    
    corrected_script = response.choices[0].message.content.strip()
    
    # Log tokens used
    log_token_usage(response, problem_id, "script_correction")
    
    log_interaction(problem_id, "script_correction_response", corrected_script)
    
    return corrected_script
