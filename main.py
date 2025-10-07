from openai import OpenAI
from ollama import Client
from datetime import datetime
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import json
import tomllib
import argparse

from evaluation_functions import (
    add_line_numbers, compilation_test, pvcheck_test, time_test, compute_final_score
)


def run_openai(sys_prompt, usr_prompt, schema, model):
    """Execute an OpenAI API call with structured JSON output"""
    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "response_schema",
                "strict": True,
                "schema": schema
            }
        },
        temperature=0
    )
    return json.loads(response.output[0].content[0].text)


def run_ollama(sys_prompt, usr_prompt, schema, model):
    """Execute an Ollama API call with structured JSON output."""
    client = Client()
    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
    sys_prompt = sys_prompt.replace("{{ schema }}", schema_str)

    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt}
        ],
        options={
            "temperature": 0,
            "top_k": 10
        },
        format=schema
    )

    output_text = response.message.content.strip()
    if output_text.startswith("```") and output_text.endswith("```"):
        output_text = "\n".join(output_text.split("\n")[1:-1])

    parsed = json.loads(output_text)
    with open("prova_ollama.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    return parsed


def run_fabric(exam, schema, args, program):
    """
    fab = Fabric()
    result = fab.run(
        pattern="evaluate_c",
        inputs={
            "schema": f"{schema}",
            "argomenti": args,
            "testo d'esame": exam,
            "programma": program
        }
    )

    try:
        output_json = json.loads(result.output)
    except json.JSONDecodeError as e:
        print("Errore nel parsing del JSON:")
        print(result.ouput)
        return None

    return output_json
    """


def get_paths(config: dict, config_flag: bool) -> dict:
    """Return file paths from the TOML configuration, with optional overrides."""
    base = config["paths"]
    paths = {
        "llm_config": base["llm"],
        "output": base["output_path"],
        "questions_config": base["questions"],
        "combined_weights": config.get("combined_weights")
    }
    if config_flag:
        paths.update({
            "schema": base.get("schema_path"),
            "programs": base.get("programs_path"),
            "exam_text": base.get("exam_text_path"),
            "sys_prompt": base.get("sys_prompt_path"),
            "usr_prompt": base.get("usr_prompt_path"),
        })
    else:
        paths.update({k: "." for k in ["schema", "programs", "exam_text", "sys_prompt", "usr_prompt"]})
    return paths


def load_file(path: str, mode="r", encoding="utf-8"):
    """Load text or JSON file based on its extension."""
    with open(path, mode, encoding=encoding) as f:
        return json.load(f) if path.endswith(".json") else f.read()


def init_argparser() -> argparse.ArgumentParser:
    """Define command-line arguments."""
    parser = argparse.ArgumentParser(description='Evaluates a given C program')
    parser.add_argument('program', type=str, help="C program file to evaluate")
    parser.add_argument('--input', '-i', type=str,
                        help="Input file for the C program")
    parser.add_argument('--exam', '-ex', type=str,
                        help="Directory containing program context resources")
    parser.add_argument('--config', '-cf', action="store_true",
                        help="Use preconfigured paths from the TOML file")
    parser.add_argument('--user_prompt', '-up', type=str, default="up2.md",
                        help="User prompt file for the model")
    parser.add_argument('--system_prompt', '-sp', type=str, default="sp3.md",
                        help="System prompt file for the model")
    parser.add_argument('--schema', '-s', type=str, default="s3.json",
                        help="JSON output schema for the model")
    parser.add_argument('--model', '-m', action="store", type=str,
                        choices=['gpt-4.1-mini', 'llama3.2', 'fabric', 'deepseek-r1:1.5b'],
                        default="gpt-4.1-mini", help='Model to use for evaluation')
    return parser


def main():
    parser = init_argparser()
    input_args = parser.parse_args()
    path_flag = input_args.config

    # CONFIGURATION DATA RETRIEVAL

    # General config
    general_config = tomllib.load(open("config.toml", "rb"))
    paths = get_paths(general_config, path_flag)
    combined_weights = general_config.get("combined_weights")

    # Get program file and name
    program_path = os.path.join(paths["programs"], input_args.program)
    program_name = os.path.splitext(os.path.basename(program_path))[0]
    program = load_file(program_path)
    program = add_line_numbers(program)

    # LLM
    llm_config = tomllib.load(open(paths["llm_config"], "rb"))
    topics = llm_config.get("argomenti")
    analysis = llm_config.get("analisi")
    llm_weights = {a["nome"]: a["peso"] for a in topics}

    # EXAM QUESTIONS config
    """
    Dipende da cosa passo in input da cl con -ex (contesto):
    - "file.md": solo contesto, non c'è il pvcheck da fare ==> solo altri test oggettivi
    - "cartella" (no estensione): c'è contesto e pvcheck nella stessa cartella ==> si pvcheck e altri test 
    - niente: no pvcheck, solo altri test
    """

    questions = tomllib.load(open(paths["questions_config"], "rb"))
    tests_weights = questions.get("tests_weights")
    tests = list(tests_weights.keys())

    context_dir = bool(input_args.exam)
    extension = False
    program_input = input_args.input if (input_args.input is not None) else ""
    if context_dir:
        text_exam_full_path = os.path.join(paths["exam_text"], input_args.exam)
        extension = os.path.splitext(os.path.basename(input_args.exam))[1]
        if not extension:
            # pvcheck (directory case)
            quest_weights = questions.get("questions_weights")
            last_file_flag = False
            for file in os.listdir(text_exam_full_path):
                # program input
                if file.endswith(".dat"):
                    program_input = os.path.join(text_exam_full_path, file)
                    if last_file_flag:
                        break
                    last_file_flag = True
                # context file
                elif file.endswith(".md"):
                    file_target = os.path.join(text_exam_full_path, file)
                    if last_file_flag:
                        break
                    last_file_flag = True
        else:
            # File case
            file_target = text_exam_full_path

        # Get exam text for input context
        text_exam = load_file(file_target)
        text_exam = "```markdown\n" + text_exam + "\n```"

    # Objective tests
    metrics = {tests[i]: -1 for i in range(len(tests))}  # range 0-10
    metrics[tests[0]] = compilation_test(program_path)
    metrics[tests[1]] = time_test(program_input)
    if context_dir and (not extension):
        pvcheck_csv_scores = defaultdict(list)
        metrics[tests[2]] = pvcheck_test(quest_weights, pvcheck_csv_scores, text_exam_full_path)

    # JSON schema
    schema_path = input_args.schema
    schema = load_file(os.path.join(paths["schema"], schema_path))
    json_name = os.path.splitext(os.path.basename(schema_path))[0]

    # Prompt construction
    args_md = "\n".join(
        f"- **{a['nome']}**: {a['descrizione']}" for a in topics + analysis
    )

    # Get prompts paths

    # System prompt
    system_prompt_path = os.path.join(paths["sys_prompt"], input_args.system_prompt)
    system_prompt_name = os.path.splitext(os.path.basename(system_prompt_path))[0]

    # User prompt
    user_prompt_path = os.path.join(paths["usr_prompt"], input_args.user_prompt)
    user_prompt_name = os.path.splitext(os.path.basename(user_prompt_path))[0]


    # Fill prompts with config data
    env = Environment(
        loader=FileSystemLoader(
            [os.path.dirname(user_prompt_path),
             os.path.dirname(system_prompt_path)]
        ),
        autoescape=select_autoescape()
    )
    sys_template = env.get_template("sp4.md")
    usr_template = env.get_template("up3.md")
    context = {
        "context_flag": context_dir,
        "schema_flag": False,
        "schema": schema,
        "argomenti": args_md,
        "testo_consegna": text_exam,
        "programma": program,
    }
    system_prompt = sys_template.render(context)
    system_prompt = "```markdown\n" + system_prompt + "\n```"
    user_prompt = usr_template.render(context)
    user_prompt = "```markdown\n" + user_prompt + "\n```"

    # Model selection
    model = input_args.model
    if model == "gpt-4.1-mini":
        dest_dir = "GPTAnalysis"
        parsed = run_openai(system_prompt, user_prompt, schema, model="gpt-4.1-mini")
    elif model in {"llama3.2", "deepseek-r1:1.5b"}:
        dest_dir = model
        parsed = run_ollama(system_prompt, user_prompt, schema, model="llama3.2")
    """
    else:
        dest_dir = "fabric"
        parsed = run_fabric(text_exam, schema, args_md, program)
    """

    #print("RISULTATO: \n", parsed)

    # Combine scores
    if context_dir:
        combined = compute_final_score(
            metrics, parsed, tests_weights, llm_weights,
            combined_weights, quest_weights, pvcheck_csv_scores
        )

    # Saving
    timestamp = datetime.now().strftime("%H-%M-%S")
    exam_date = f"{input_args.exam}_" if context_dir else ""
    output_file_name = f"{exam_date}{timestamp}_{program_name}_{system_prompt_name}_{user_prompt_name}_{json_name}.json"
    output_file_path = os.path.join(paths["output"], dest_dir, output_file_name)
    with open(output_file_path, "w", encoding="utf-8") as f:
        if context_dir:
            json.dump({
                "LLM": parsed,
                "risultato_finale": combined
            }, f, indent=2, ensure_ascii=False)
        else:
            json.dump({
                "LLM": parsed,
             }, f, indent=2, ensure_ascii=False)

    print(f"Output saved in {output_file_path}")


if __name__ == "__main__":
    main()
