# planner.py
import base64, re
from openai import AzureOpenAI
from utils import log_interaction  # Assume this exists

def generate_plan(nlp_task, screenshot, planner_conf, problem_id):
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

    log_interaction(problem_id, "planner_prompt", messages)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=8000
    )

    response_text = response.choices[0].message.content
    log_interaction(problem_id, "planner_response", response_text)

    parsed_plan = parse_plan(response_text)
    return response_text, parsed_plan


def parse_plan(plan_text):
    steps = []
    lines = plan_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match pattern like: Step 1 - Click search bar - Text Box - Type "converse shoes"
        match = re.match(r"Step\s*\d+\s*-\s*(.*?)\s*-\s*(.*?)\s*-\s*(.*)", line)
        if match:
            action_label = match.group(1).strip()
            element_type = match.group(2).strip()
            action = match.group(3).strip()
            steps.append({
                "action_label": action_label,
                "element_type": element_type,
                "action": action
            })
        else:
            print(f"[WARNING] Could not parse line: {line}")

    return steps

