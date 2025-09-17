import base64  
import yaml  
import json, os
from pathlib import Path  
from openai import AzureOpenAI  
from mimetypes import guess_type  
from utils import log_interaction
  
def load_config(path="../config.yaml"):  
    with open(path, "r") as file:  
        return yaml.safe_load(file)  
  
def evaluate_task_completion(screenshot_path):  
    # Load config  
    config = load_config()  
    problem_id = config['problem_id']  
    question = config['intent']  
    planner_conf = config['planner']  
  
    # Verify and load screenshot  
    if not Path(screenshot_path).exists():  
        raise FileNotFoundError(f"Screenshot not found at: {screenshot_path}")  
      
    screenshot_bytes = Path(screenshot_path).read_bytes()  
    mime_type, _ = guess_type(screenshot_path)  
    if mime_type is None:  
        raise ValueError("Could not determine MIME type of screenshot.")  
      
    base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")  
  
    # Load system prompt  
    with open("../prompts/answering_instructions.txt", "r") as f:  
        system_prompt = f.read()  
  
    # Initialize Azure OpenAI client  
    client = AzureOpenAI(  
        azure_endpoint=planner_conf['azure_endpoint'],  
        api_key=planner_conf['api_key'],  
        api_version=planner_conf['api_version']  
    )  
  
    # Compose messages  
    messages = [  
        {"role": "system", "content": system_prompt},  
        {  
            "role": "user",  
            "content": [  
                {"type": "text", "text": question},  
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}  
            ]  
        }  
    ]  
  
    print("📤 Sending request to Azure OpenAI...")  
    # Send request to model  
    response = client.chat.completions.create(  
        model="gpt-4o",  
        messages=messages,  
        temperature=0.7,  
        max_tokens=8000  
    )  
  
    # Extract response text  
    response_text = response.choices[0].message.content  
    print("\n✅ Model Response:\n")  
    print(response_text)  
  
    # Log interaction  
    log_interaction(problem_id, "answering_llm", {  
        "question": question,  
        "screenshot_path": screenshot_path,  
        "response": response_text  
    })  
  
    # Determine task completion status  
    if "Task Complete: Success" in response_text:  
        return "Success", response_text
    elif "Task Complete: Failure" in response_text:  
        return "Failure", response_text
    else:  
        raise ValueError("Unexpected response format from LLM.")  
  
