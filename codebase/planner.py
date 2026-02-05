# planner.py
import base64, re
from openai import AzureOpenAI
from utils import log_interaction, log_token_usage  # Assume this exists
import time

def generate_plan(nlp_task, screenshot, planner_conf, problem_id):
    start_time = time.time()
    with open("../prompts/planner_instructions.txt", "r") as f:
        system_prompt = f.read()

    base64_image = base64.b64encode(screenshot).decode("utf-8") if isinstance(screenshot, bytes) else screenshot

    client = AzureOpenAI(
        azure_endpoint=planner_conf['azure_endpoint'],
        api_key=planner_conf['api_key'],
        api_version=planner_conf['api_version']
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": nlp_task},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]
        }
    ]

    # Print planner prompt input
    print(f"\n{'='*60}")
    print(f"[PLANNER PROMPT INPUT]")
    print(f"System Prompt :\n{system_prompt}...")
    print(f"\nUser Prompt:\n{nlp_task}")
    print(f"[Image included: base64 encoded screenshot]")
    print(f"{'='*60}\n")

    log_interaction(problem_id, "planner_prompt", messages)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=8000
    )
    log_token_usage(response, problem_id, "generate_plan")
    # Calculate time taken
    elapsed_time = time.time() - start_time
    print(f"Time taken for generating plan: {elapsed_time} seconds")

    response_text = response.choices[0].message.content
    
    # Print planner response output
    print(f"\n{'='*60}")
    print(f"[PLANNER RESPONSE OUTPUT]")
    print(response_text)
    print(f"{'='*60}\n")
    
    log_interaction(problem_id, "planner_response", response_text)

    parsed_plan = parse_plan(response_text)
    return response_text, parsed_plan


def parse_plan(plan_text):
    """
    Parse plan text into structured steps.
    Supports multiple formats for robustness:
    - Step X - Action Label - Element Type - Action
    - Step X: Action Label - Element Type - Action
    - X. Action Label - Element Type - Action
    """
    steps = []
    lines = plan_text.strip().split('\n')
    step_number = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try multiple patterns for robustness
        patterns = [
            # Standard format: Step 1 - Action Label - Element Type - Action
            r"Step\s*(\d+)\s*-\s*(.*?)\s*-\s*(.*?)\s*-\s*(.*)",
            # With colon: Step 1: Action Label - Element Type - Action
            r"Step\s*(\d+)\s*:\s*(.*?)\s*-\s*(.*?)\s*-\s*(.*)",
            # Numbered list: 1. Action Label - Element Type - Action
            r"^(\d+)\.\s*(.*?)\s*-\s*(.*?)\s*-\s*(.*)",
            # Just number and dashes: 1 - Action Label - Element Type - Action
            r"^(\d+)\s*-\s*(.*?)\s*-\s*(.*?)\s*-\s*(.*)",
        ]
        
        match = None
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                break
        
        if match:
            step_num = int(match.group(1))
            action_label = match.group(2).strip()
            element_type = match.group(3).strip()
            action = match.group(4).strip()
            
            steps.append({
                "step_number": step_num,  # Store step number for reference
                "action_label": action_label,
                "element_type": element_type,
                "action": action
            })
            step_number = step_num
        else:
            # Try to extract step number even if format is slightly off
            step_match = re.search(r"(?:Step\s*|^)(\d+)", line, re.IGNORECASE)
            if step_match:
                print(f"[WARNING] Could not fully parse line (format issue): {line}")
                print(f"[WARNING] Detected step number: {step_match.group(1)}, but format doesn't match expected pattern")
            # Skip lines that don't look like steps

    if not steps:
        print("[ERROR] No steps could be parsed from the plan!")
        print("[DEBUG] Plan text preview:")
        print(plan_text[:500])
        
        # Fallback: Try to create a single error step if the planner returned explanatory text
        # This allows the pipeline to continue and provide feedback
        if len(plan_text.strip()) > 0:
            # Create a single step indicating the issue
            steps.append({
                "step_number": 1,
                "action_label": "Task cannot be completed based on available information",
                "element_type": "Information",
                "action": plan_text[:200]  # Truncate if too long
            })
            print("[WARNING] Created fallback error step from planner response")
    else:
        print(f"[INFO] Successfully parsed {len(steps)} steps from plan")
    
    return steps

