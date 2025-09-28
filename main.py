from openai import OpenAI
from ollama import Client
from datetime import datetime
from collections import defaultdict
import os
import json
import tomllib
import subprocess
import argparse

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


def init_argparser_basic():

    parser = argparse.ArgumentParser(description='This program evaluates an input c exams program')
    parser.add_argument(
            'program', action="store", type=str,
            help="File containing the c program to be evaluated")
    parser.add_argument(
            'exams', action="store", type=str,
            help="Directory containing the exams resources (text, pvcheck.test, etc...)")
    parser.add_argument(
            '--user_prompt', '-up', action="store", type=str, default="up2.md",
            help="File containing the user prompt to be given to the model")
    parser.add_argument(
            '--system_prompt', '-sp', action="store", type=str, default="sp3.md",
            help="File containing the system prompt to be given to the model")
    parser.add_argument(
            '--schema', '-s', action="store", type=str, default="s3.json",
            help="File containing the output schema to be given to the model")
    parser.add_argument(
            '--model', '-m', action="store", type=str, choices=['gpt-4.1-mini', 'llama3.2', 'fabric'], default="gpt-4.1-mini",
            help='Model to be used for the program evaluation')
    return parser


def main():
    GENERAL_CONFIG_FILE = "utils/config/general.toml"

    parser = init_argparser_basic()
    input_args = parser.parse_args()

    # CONFIGURATION DATA RETRIEVAL

    # General config
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

    # EXAM QUESTIONS config
    with open(questions_path, "rb") as f:
        questions = tomllib.load(f)

    # Questions Weights
    quest_weights = questions.get("questions_weights")

    # Get program file and name
    program_file = input_args.program
    program_name = input_args.program.split(".", 1)[0]
    with open(os.path.join(programs_path, program_file), "r", encoding="utf-8") as f:
        program = f.read()
    program = add_line_numbers(program)

    # Obtain text exams from program name (hashed with data in the name)
    exam_directory = input_args.exam
    text_exam_full_path = os.path.join(text_exam_path, exam_directory)
    file_target = os.path.join(text_exam_full_path, f"{exam_directory}_programmazione.md")
    with open(file_target, "r", encoding="utf-8") as f:
        text_exam = f.read()
    text_exam = "```markdown\n" + text_exam + "\n```"

    # Objective tests
    c_file_path = os.path.join(programs_path, program_file)
    tests = list(tests_weights.keys())

    pvcheck_csv_scores = defaultdict(list)

    weighted_tests_scores = compile_and_test(c_file_path, text_exam_full_path, tests, quest_weights, pvcheck_csv_scores)
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
    system_prompt_file = input_args.system_prompt
    system_prompt_name = system_prompt_file.split(".", 1)[0]
    with open(os.path.join(system_prompt_path, system_prompt_file), "r", encoding="utf-8") as f:
        system_prompt = f.read()
    system_prompt = "```markdown\n" + system_prompt + "\n```"

    # User prompt
    user_prompt_path = os.path.join(prompt_path, "user")
    user_prompt_file = input_args.user_prompt
    user_prompt_name = user_prompt_file.split(".", 1)[0]
    with open(os.path.join(user_prompt_path, user_prompt_file), "r", encoding="utf-8") as f:
        user_prompt = f.read()
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
            "evidenze": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "commento": {"type": "string"},
                        "righe": {
                            "type": "array",
                            "items": {"type": "string", "pattern": r"^\d+(-\d+)?$"},
                            "default": []
                        }
                    },
                    "required": ["commento"]
                }
            }
        },
        "required": ["punteggio", "evidenze"]
    }

    # Get json schema and name
    json_file = input_args.schema
    json_name = json_file.split(".", 1)[0]
    with open(os.path.join(schema_path, json_file), "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Add arguments to be evaluated in the schema
    args_list = [arg["nome"] for arg in args]
    eval = schema["schema"]["properties"]["valutazione"]
    eval["properties"] = {arg: eval_template for arg in args_list}
    eval["required"] = args_list

    # Model selection
    choice = input_args.model
    if choice == "gpt-4.1-mini":
        dest_dir = "GPTAnalysis"
        parsed = run_openai(system_prompt, user_prompt, schema, model="gpt-4.1-mini")
    elif choice == "llama3.2":
        dest_dir = "llama3.2"
        parsed = run_ollama(system_prompt, user_prompt, schema, model="llama3.2")
    else:
        with open(f"{prompt_path}/fabric_input.md", "r", encoding="utf-8") as f:
            fabric_input = f.read()
        dest_dir = "fabric"
        fabric_input = fabric_input.replace("{{ argomenti }}", args_md_str)
        fabric_input = fabric_input.replace("{{ testo d'esame }}", text_exam)
        fabric_input = fabric_input.replace("{{ programma }}", program)
        fabric_input = fabric_input.replace("{{ schema json }}", f"{schema}")
        parsed = run_fabric(fabric_input)

    #print(parsed)

    # Combine scores
    combined = compute_final_score(weighted_tests_scores, parsed, tests_weights, llm_weights, combined_weights,
                                   quest_weights, pvcheck_csv_scores)

    # Saving
    timestamp = datetime.now().strftime("%H-%M-%S")
    output_file_name = f"{exam_directory}_{timestamp}_{program_name}_{system_prompt_name}_{user_prompt_name}_{json_name}.json"
    output_file_path = os.path.join(output_path, dest_dir, output_file_name)
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump({
            "LLM": parsed,
            "risultato_finale": combined
        }, f, indent=2, ensure_ascii=False)

    print(f"Output saved in {output_file_path}")


if __name__ == "__main__":
    main()