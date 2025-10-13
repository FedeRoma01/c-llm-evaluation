import argparse
import json
import os
import re
import sys
import tomllib
from collections import defaultdict
from datetime import datetime

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI

from evaluation_functions import (
    add_line_numbers,
    compilation_test,
    compute_final_score,
    pvcheck_test,
    time_test,
)


def run_openrouter(sys_prompt, usr_prompt, schema, model, debug=True):
    """Execute an API call using OpenRouter with structured JSON output"""
    key = check_api_key("OPENROUTER_API_KEY")

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "output_schema",
                    "strict": True,
                    "schema": schema,
                },
            },
            temperature=0,
        )
    except Exception as e:
        raise RuntimeError(f"OpenRouter API call failed: {e}") from e

    if debug:
        print(response)

    # Robust extraction
    message = getattr(response.choices[0], "message", {})
    content = getattr(message, "content", "").strip()

    # Fallback: try reasoning field if content empty
    if not content:
        reasoning = getattr(message, "reasoning", "")
        if reasoning:
            match = re.search(r"```json\s*(\{.*\})\s*```", reasoning, re.DOTALL)
            content = match.group(1).strip() if match else reasoning.strip()

    if not content:
        raise RuntimeError(f"Empty or malformed response: {response}")

    try:
        parsed = json.loads(content.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in response: {content}") from e

    return parsed, response.usage.model_dump()


def run_router_request(
    sys_prompt,
    usr_prompt,
    schema,
    model,
    prompt_max_price,
    completion_max_price,
    debug=False,
):
    """Execute direct OpenRouter API call with explicit provider control and price constraints."""
    key = check_api_key("OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "output_schema", "strict": True, "schema": schema},
        },
        "provider": {
            "sort": "price",
            "max_price": {
                "prompt": prompt_max_price,
                "completion": completion_max_price,
            },
            "allow_fallbacks": True,  # to customize set this False and specify providers to be used
            # as fallbacks with "order": [providers]
        },
        "temperature": 0,
        "structured_output": True,
        "usage": {"include": True},
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"OpenRouter HTTP error: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from OpenRouter: {response.text}") from e

    if debug:
        print(data)

    try:
        message = data["choices"][0]["message"]
        content = message.get("content", "").strip()

        # Fallback: if content empty, try to extract from reasoning field
        if not content:
            reasoning = message.get("reasoning", "")
            if reasoning:
                # try to extract json between triple backticks
                match = re.search(r"```json\s*(\{.*\})\s*```", reasoning, re.DOTALL)
                content = match.group(1).strip() if match else reasoning.strip()

        parsed = json.loads(content)
    except (KeyError, json.JSONDecodeError) as e:
        raise ValueError(f"Malformed OpenRouter response: {data}") from e

    return parsed, data.get("usage", {}), data.get("provider")


def run_openai(sys_prompt, usr_prompt, schema, model, debug=False):
    """Execute an OpenAI API call with structured JSON output"""
    key = check_api_key("OPENAI_API_KEY")
    client = OpenAI(api_key=key)
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "response_schema",
                    "strict": True,
                    "schema": schema,
                }
            },
            temperature=0,
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}") from e

    if debug:
        print(response)

    try:
        text = response.output[0].content[0].text
        parsed = json.loads(text)
    except (AttributeError, IndexError, json.JSONDecodeError) as e:
        raise ValueError(
            f"Malformed or invalid JSON in OpenAI response: {response}"
        ) from e

    return parsed, response.usage.model_dump()


def check_api_key(env_var) -> str:
    key = os.getenv(env_var)
    if not key:
        raise OSError(f"Missing {env_var}")
    return key


def get_paths(config: dict, config_flag: bool) -> dict:
    """Return file paths from the TOML configuration, with optional overrides."""
    base = config["paths"]
    paths = {
        "llm_config": base["llm"],
        "output": base["output_path"],
        "questions_config": base["questions"],
        "combined_weights": config.get("combined_weights"),
    }
    if config_flag:
        paths.update(
            {
                "schema": base.get("schema_path"),
                "programs": base.get("programs_path"),
                "exam_text": base.get("exam_text_path"),
                "sys_prompt": base.get("sys_prompt_path"),
                "usr_prompt": base.get("usr_prompt_path"),
            }
        )
    else:
        paths.update(
            dict.fromkeys(
                ["schema", "programs", "exam_text", "sys_prompt", "usr_prompt"], "."
            )
        )
    return paths


def load_file(path: str, mode="r", encoding="utf-8"):
    """Load text or JSON file based on its extension."""
    with open(path, mode, encoding=encoding) as f:
        return json.load(f) if path.endswith(".json") else f.read()


def init_argparser() -> argparse.ArgumentParser:
    """Define command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluates a given C program")
    parser.add_argument("program", type=str, help="C program file to evaluate")
    parser.add_argument("model", type=str, help="Model to use for evaluation")
    parser.add_argument("--input", "-i", type=str, help="Input file for the C program")
    parser.add_argument(
        "--context", "-cx", type=str, help="File containing program context"
    )
    parser.add_argument(
        "--exam", "-ex", type=str, help="Directory containing program context resources"
    )
    parser.add_argument(
        "--config",
        "-cf",
        action="store_true",
        help="Use preconfigured paths from the TOML file",
    )
    parser.add_argument(
        "--user_prompt",
        "-up",
        type=str,
        default="up4.md",
        help="User prompt file for the model",
    )
    parser.add_argument(
        "--system_prompt",
        "-sp",
        type=str,
        default="sp5.md",
        help="System prompt file for the model",
    )
    parser.add_argument(
        "--schema",
        "-s",
        type=str,
        default="s5.json",
        help="JSON output schema for the model",
    )
    parser.add_argument(
        "--provider", "-pr", type=str, help="Provider for the model to use"
    )
    parser.add_argument(
        "--prompt_price",
        "-pp",
        type=float,
        default=0,
        help="Max price for 1M tokens for the the prompt",
    )
    parser.add_argument(
        "--completion_price",
        "-cp",
        type=float,
        default=0,
        help="Max price for 1M tokens for the completion",
    )
    return parser


def compute_cost(model_name, tokens_count, pricing_data):
    if model_name not in pricing_data:
        # OPENAI: return f"Model {model_name} not in config.toml"
        return "Prices not specified in llm.toml"

    model_prices = pricing_data[model_name]
    tot_cost = 0
    for token_type, count in tokens_count.items():
        if token_type not in model_prices:
            continue
        rate = model_prices[token_type]  # USD per 1M tokens
        tot_cost += (count / 1000000) * rate
    return tot_cost


def openai_reshape_usage(usage):
    reshaped = {
        **{k: v for k, v in usage.items() if not k.endswith("_details")},
        **usage["input_tokens_details"],
        **usage["output_tokens_details"],
    }
    return reshaped


def make_safe_dirname(s: str) -> str:
    # Replace any character that is not alphanumeric, dash, or underscore with _
    safe_name = re.sub(r"[^a-zA-Z0-9-_]", "_", s)

    # Optionally, collapse multiple underscores
    safe_name = re.sub(r"_+", "_", safe_name)

    # Strip leading/trailing underscores
    safe_name = safe_name.strip("_")

    return safe_name


def main():
    parser = init_argparser()
    input_args = parser.parse_args()
    path_flag = input_args.config

    # CONFIGURATION LOAD
    with open("config.toml", "rb") as f:
        general_config = tomllib.load(f)
    paths = get_paths(general_config, path_flag)
    combined_weights = general_config.get("combined_weights")

    # PROGRAM LOAD
    program_path = os.path.join(paths["programs"], input_args.program)
    program_name = os.path.splitext(os.path.basename(program_path))[0]
    program = add_line_numbers(load_file(program_path))

    # LLM CONFIG LOAD
    with open(paths["llm_config"], "rb") as f:
        llm_config = tomllib.load(f)
    topics, analysis = llm_config["topics"], llm_config["analysis"]
    llm_weights = {a["name"]: a["weight"] for a in topics}
    pricing = llm_config["models"]

    # QUESTIONS CONFIG LOAD
    with open(paths["questions_config"], "rb") as f:
        questions = tomllib.load(f)
    tests_weights = questions["tests_weights"]
    tests = list(tests_weights.keys())

    # EXAM / CONTEXT HANDLING
    exam_dir = bool(input_args.exam)
    pvcheck_flag = False
    quest_weights, program_input, file_target = {}, "", ""

    if exam_dir:
        exam_path = os.path.join(paths["exam_text"], input_args.exam)
        if not os.path.splitext(input_args.exam)[1]:  # directory case
            entries = {e.name for e in os.scandir(exam_path) if e.is_file()}
            pvcheck_flag = "pvcheck.test" in entries
            dat_files = [f for f in entries if f.endswith(".dat")]  # program input
            md_files = [f for f in entries if f.endswith(".md")]  # program context

            if not (pvcheck_flag and dat_files and md_files):
                sys.exit(
                    "--exam directory missing required files (.dat, .md, pvcheck.test)"
                )

            quest_weights = questions["questions_weights"]
            program_input = os.path.join(exam_path, dat_files[0])
            file_target = os.path.join(exam_path, md_files[0])
        else:
            sys.exit("--exam argument must be a directory")
    else:
        program_input = os.path.join(paths["exam_text"], input_args.input or "")
        file_target = os.path.join(paths["exam_text"], input_args.context or "")

    # CONTEXT
    context = load_file(file_target)
    context = "```markdown\n" + context + "\n```"

    # OBJECTIVE TESTS
    metrics = dict.fromkeys(tests, -1)
    metrics[tests[0]] = compilation_test(program_path)
    metrics[tests[1]] = time_test(program_input)
    pvcheck_csv_scores = defaultdict(list)
    if exam_dir and pvcheck_flag:
        metrics[tests[2]] = pvcheck_test(
            questions["questions_weights"], pvcheck_csv_scores, exam_path
        )

    # SCHEMA
    schema_path = os.path.join(paths["schema"], input_args.schema)
    schema = load_file(schema_path)
    json_name = os.path.splitext(os.path.basename(schema_path))[0]

    # PROMPTS CONSTRUCTION
    args_md = "\n".join(
        f"- **{a['name']}**: {a['description']}" for a in topics + analysis
    )
    sys_prompt_path = os.path.join(paths["sys_prompt"], input_args.system_prompt)
    usr_prompt_path = os.path.join(paths["usr_prompt"], input_args.user_prompt)
    system_prompt_name = os.path.splitext(os.path.basename(sys_prompt_path))[0]
    user_prompt_name = os.path.splitext(os.path.basename(usr_prompt_path))[0]

    env = Environment(
        loader=FileSystemLoader(
            [os.path.dirname(usr_prompt_path), os.path.dirname(sys_prompt_path)]
        ),
        autoescape=select_autoescape(),
    )
    sys_template = env.get_template("sp4.md")
    usr_template = env.get_template("up3.md")
    templ_context = {
        "context_flag": exam_dir or bool(context),
        "schema_flag": False,
        "schema": schema,
        "topics": args_md,
        "context": context,
        "program": program,
    }
    system_prompt = sys_template.render(templ_context)
    user_prompt = usr_template.render(templ_context)

    # MODEL CALL
    model = input_args.model
    provider = input_args.provider

    if provider == "openai":
        parsed, tokens = run_openai(system_prompt, user_prompt, schema, model)
        tokens = openai_reshape_usage(tokens)
    elif provider:
        parsed, tokens = run_openrouter(system_prompt, user_prompt, schema, model)
    else:
        parsed, tokens, provider = run_router_request(
            system_prompt,
            user_prompt,
            schema,
            model,
            input_args.prompt_price,
            input_args.completion_price,
        )

    call_cost = compute_cost(model, tokens, pricing)

    # FINAL SCORE
    combined = compute_final_score(
        metrics,
        parsed,
        tests_weights,
        llm_weights,
        combined_weights,
        quest_weights,
        pvcheck_csv_scores,
    )

    # SAVE OUTPUT
    timestamp = datetime.now().strftime("%H-%M-%S")
    exam_prefix = f"{input_args.exam}_" if exam_dir else ""
    output_file_name = f"{exam_prefix}{timestamp}_{program_name}_{system_prompt_name}_{user_prompt_name}_{json_name}.json"
    output_dir = os.path.join(paths["output"], make_safe_dirname(model))
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, output_file_name)

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(
            {"LLM": parsed, "usage": tokens, "call_cost": call_cost, **combined},
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Output saved in {output_file_path}")


if __name__ == "__main__":
    main()
