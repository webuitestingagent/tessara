## Program-for-Thought: Towards Adaptive Planning for Web Test Script Generation
<p align="justify">Large Language Models (LLMs) have shown promise in reasoning and code-related tasks, but they continue to struggle with dynamic software behaviors, especially in Web environments involving interactive Graphical User Interfaces (GUIs), leading to limited successes in test script generation for Web applications.  </p>

<p align="justify">This paper presents Tessara, a novel agentic framework designed to enhance LLM’s capability of generating sequences of executable actions and subsequently test script generation for Web applications. </p>

<p align="justify">Unlike prior approaches that lack adaptability and tractability, Tessara integrates Chain-of-Thought (CoT) prompting with a new Program-for-Thought (PfT) scripting strategy, which expresses each reasoning step as executable code for fine-grained verification and backtracking. </p>

<p align="justify">By combining CoT-based planning, PfT-guided scripting, and multimodal inputs (DOM+screenshots), Tessara supports adaptive re-planning and precise failure recovery without full re-planning. </p>

<p align="justify">We demonstrate that Tessara outperforms state-of-the-art baselines in automated Web test script generation, offering a more robust, scalable, and user-accessible solution for Web test automation. </p>


---

### 📁 Project Structure
```
atlas
├── model
│   ├── prompts
│   │   ├── planner_instructions.txt
│   │   ├── scripter_instructions.txt
│   │   ├── answering_instructions.txt
│   ├── codebase
│   │   ├── config.yaml
│   │   ├── main.py
│   │   ├── planner.py
│   │   ├── scripter.py
│   │   ├── answering_llm.py
└── README.md
```

---

### 🧠 Prompt Instructions

Instruction files guiding different components of the agent:

- `planner_instructions.txt`: Instructions for the planning component
- `scripter_instructions.txt`: Instructions for the scripting component

---

### ⚙️ Core Scripts

- `main.py`: Main entry point to execute tasks
- `planner.py`: CoT-based planner module
- `scripter.py`: PfT-guided scripting module
- `answering_llm.py`: LLM-based reasoning and response handler
- `config.yaml`: Configuration file for experimental setup

---

### ⚙️ How to Run
- Clone the official github repository for ATLAS
```
git clone https://github.com/atlaswebagent/tessara.git
```
-  Add the necessary details, including API keys, models and endpoints required for fuzzing in model/codebase/config.yaml
-  Run the 'model/main.py' file through terminal in the following format - 
```
python main.py 
```
  ### 📄 License & Citation

For licensing and citation details, please refer to the accompanying LICENSE file and cite our paper if you use ATLAS in your work.

