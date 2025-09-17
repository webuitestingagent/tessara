# scripter.py
import base64, re
from openai import AzureOpenAI
from utils import log_interaction

def generate_script(plan_steps, filtered_dom, start_url, screenshot, scripter_conf, problem_id):
    with open("../prompts/scripter_instructions.txt", "r") as f:
        system_prompt = f.read()

    plan_text = "\n".join(
        [f"Step {i+1} - {step['action_label']} - {step['element_type']} - {step['action']}" for i, step in enumerate(plan_steps)]
    )
    user_prompt_text = f"Start URL: {start_url}\n\nSteps:\n{plan_text}\n\nRelevant DOM:\n{str(filtered_dom)}"

    base64_image = base64.b64encode(screenshot).decode("utf-8")

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

    script_code = response.choices[0].message.content.strip()

    script_code = re.sub(r"^```(?:\w+)?\s*", "", script_code)
    script_code = re.sub(r"\s*```$", "", script_code)


    log_interaction(problem_id, "scripter_response", script_code)

    return script_code
