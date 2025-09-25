from openai import OpenAI
from ollama import Client
from datetime import datetime
import os
import json
import tomllib
import subprocess

from evaluation_functions import (
    select_file, add_line_numbers, compile_and_test, compute_final_score
)


def run_openai(sys_prompt, usr_prompt, schema, model):
    # API call (with Structured Output)
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt}
        ],
        response_format={"type": "json_schema", "json_schema": schema},
        temperature=0
    )

    return json.loads(response.choices[0].message.content)


def run_ollama(sys_prompt, usr_prompt, schema, model):

    client = Client(host="http://localhost:11434")
    # Add output schema in the system prompt
    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
    json_specified_prompt = f"""
{usr_prompt}

---

## Output

Genera un output in **formato JSON** che rispetti esattamente lo schema fornito.

### Schema JSON

{schema_str}
"""
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": json_specified_prompt}
        ]
    )
    output_text = response.message.content.strip()
    if output_text.startswith("```") and output_text.endswith("```"):
        output_text = "\n".join(output_text.split("\n")[1:-1])

    # Parsing
    # fallback: prova a estrarre la parte JSON tra { ... }
    start = output_text.find("{")
    end = output_text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(output_text[start:end + 1])
    else:
        return json.loads(output_text)


def run_fabric(fabric_input, pattern="fabric_prompt"):

    result = subprocess.run(
        ["wsl", "fabric", "-p", pattern, fabric_input],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Errore durante l'esecuzione del comando:")
        print(result.stderr)

    try:
        output_json = json.loads(result.stdout.strip())
    except json.JSONDecodeError as e:
        print("Errore nel parsing del JSON:")
        print(result.stdout)
        print(e)
        return None

    return output_json


def main():
    GENERAL_CONFIG_FILE = "utils/config/general.toml"

    # CONFIGURATION DATA RETRIEVAL

    # STUDENT config
    with open(GENERAL_CONFIG_FILE, "rb") as f:
        general_config = tomllib.load(f)

    # Paths
    questions_path = general_config["paths"].get("questions")
    schema_path = general_config["paths"].get("schema_path")
    programs_path = general_config["paths"].get("programs_path")
    text_exam_path = general_config["paths"].get("exam_text_path")
    prompt_path = general_config["paths"].get("prompt_path")
    output_path = general_config["paths"].get("output_path")

    # LLM
    args = general_config.get("argomenti")
    llm_weights = {arg["nome"]: arg["peso"] for arg in args}
    analysis = general_config.get("analisi")

    # Weights
    tests_weights = general_config.get("tests_weights")
    combined_weights = general_config.get("combined_weights")

    # PROFESSOR config
    with open(questions_path, "rb") as f:
        questions = tomllib.load(f)

    # Questions Weights
    quest_weights = questions.get("questions_weights")

    # Get program file and name
    program, program_name = select_file("c program", programs_path, ".c")
    program = add_line_numbers(program)

    # Obtain text exam from program name (hashed with data in the name)
    exam_date = program_name.split("_")[0]
    exam_date_file = exam_date.replace("-", "")
    text_exam_full_path = os.path.join(text_exam_path, exam_date_file)
    file_target = os.path.join(text_exam_full_path, f"{exam_date_file}_programmazione.md")
    with open(file_target, "r", encoding="utf-8") as f:
        text_exam = f.read()
    text_exam = "```markdown\n" + text_exam + "\n```"

    # Objective tests
    c_file_path = os.path.join(programs_path, program_name)
    tests = list(tests_weights.keys())
    weighted_tests_scores = compile_and_test(c_file_path, text_exam_full_path, tests, quest_weights)
    metrics_json = {"metriche_oggettive": weighted_tests_scores}

    # Prompt construction
    args_md = []
    for arg in args:
        name = arg["nome"]
        desc = arg["descrizione"]
        args_md.append(f"- **{name}**: {desc}")
    for elem in analysis:
        name = elem["nome"]
        desc = elem["descrizione"]
        args_md.append(f"- **{name}**: {desc}")
    args_md_str = "\n".join(args_md)

    # Get prompt file and name

    # System prompt
    system_prompt_path = os.path.join(prompt_path, "system")
    system_prompt, system_prompt_name = select_file("prompt", system_prompt_path, ".md")
    system_prompt = "```markdown\n" + system_prompt + "\n```"

    # User prompt
    user_prompt_path = os.path.join(prompt_path, "user")
    user_prompt, user_prompt_name = select_file("prompt", user_prompt_path, ".md")
    user_prompt = "```markdown\n" + user_prompt + "\n```"

    # Fill prompt with config data
    user_prompt = user_prompt.replace("{{ argomenti }}", args_md_str)
    user_prompt = user_prompt.replace("{{ testo d'esame }}", text_exam)
    user_prompt = user_prompt.replace("{{ programma }}", program)

    # JSON schema

    # Evaluation template
    eval_template = {
        "type": "object",
        "properties": {
            "punteggio": {"type": "integer"},
            "evidenze": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["punteggio", "evidenze"]
    }

    # Get json schema and name
    json_file, json_name = select_file("json", schema_path, ".json")
    with open(f"{schema_path}/{json_name}", "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Add arguments to be evaluated in the schema
    args_list = [arg["nome"] for arg in args]
    eval = schema["schema"]["properties"]["valutazione"]
    eval["properties"] = {arg: eval_template for arg in args_list}
    eval["required"] = args_list

    # --- Selezione modello ---
    print("Scegli il modello:")
    print("1. OpenAI GPT")
    print("2. Ollama (locale)")
    choice = input(">> ")

    if choice == "1":
        dest_dir = "GPTAnalysis"
        parsed = run_openai(system_prompt, user_prompt, schema, model="gpt-4.1-mini")
    elif choice == "2":
        dest_dir = "llama3.2"
        parsed = run_ollama(system_prompt, user_prompt, schema, model="llama3.2")
    else:
        with open(f"{prompt_path}/fabric_input.md", "r", encoding="utf-8") as f:
            fabric_input = f.read()
        fabric_input = fabric_input.replace("{{ argomenti }}", args_md_str)
        fabric_input = fabric_input.replace("{{ testo d'esame }}", text_exam)
        fabric_input = fabric_input.replace("{{ programma }}", program)
        fabric_input = fabric_input.replace("{{ schema json }}", f"{schema}")
        parsed = run_fabric(fabric_input)

    print(parsed)

    # Combine scores
    combined = compute_final_score(weighted_tests_scores, parsed, tests_weights, llm_weights, combined_weights,
                                   quest_weights)

    # Saving
    program_n = os.path.splitext(program_name)[0]
    program_n = program_n.split("_")[1]
    timestamp = datetime.now().strftime("%H-%M-%S")
    system_prompt_version = os.path.splitext(system_prompt_name)[0]
    user_prompt_version = os.path.splitext(user_prompt_name)[0]
    output_file_name = f"{exam_date}_{timestamp}_{program_n}_{system_prompt_version}_{user_prompt_version}_{json_name}"
    output_file_path = os.path.join(output_path, dest_dir, output_file_name)
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump({
            "LLM": parsed,
            "risultato_finale": combined
        }, f, indent=2, ensure_ascii=False)

    print(f"Output salvato in {output_file_path}")


if __name__ == "__main__":
    main()