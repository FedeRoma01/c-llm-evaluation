import argparse
import json
import os
import re
import sys
import tomllib
from collections import defaultdict
from datetime import datetime

import requests
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI

from evaluation_functions import (
    add_line_numbers,
    compilation_test,
    compute_final_score,
    pvcheck_test,
    time_test,
)


class APIError(Exception):
    pass


class InvalidResponseError(APIError):
    pass


def run_openrouter(sys_prompt, usr_prompt, schema, model, temperature, debug=True):
    """Execute an API call using OpenRouter with structured JSON output"""
    key = check_api_key("OPENROUTER_API_KEY1")

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
            temperature=temperature,
        )
    except Exception as e:
        raise APIError(f"OpenRouter API call failed: {e}") from e

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
        raise InvalidResponseError(f"Empty or malformed response: {response}")

    try:
        parsed = json.loads(content.strip())
    except json.JSONDecodeError as e:
        raise InvalidResponseError(f"Invalid JSON in response: {content}") from e

    return parsed, response.usage.model_dump()


def run_router_request(
    sys_prompt,
    usr_prompt,
    schema,
    model,
    prompt_max_price,
    completion_max_price,
    temperature,
    debug=False,
):
    """Execute direct OpenRouter API call with explicit provider control and price constraints."""
    key = check_api_key("OPENROUTER_API_KEY1")

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
        "temperature": temperature,
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
        raise APIError(f"OpenRouter HTTP error: {e}") from e
    except json.JSONDecodeError as e:
        raise InvalidResponseError(
            f"Invalid JSON from OpenRouter: {response.text}"
        ) from e

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
        raise InvalidResponseError(f"Malformed OpenRouter response: {data}") from e

    return parsed, data.get("usage", {}), data.get("provider")


def run_gemini(sys_prompt, usr_prompt, schema, model, temperature, debug=False):
    """Execute a Gemini API call with structured JSON output"""

    # Check for the API key and initialize the client
    # The genai library automatically looks for the GEMINI_API_KEY environment variable.
    key = check_api_key("GEMINI_API_KEY")
    gemini_schema = json_to_gemini_schema(schema)
    client = genai.Client(api_key=key)

    # Construct the request contents.
    # Gemini models often handle system instructions best when prepended to the user prompt.
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"[SYSTEM]\n{sys_prompt}\n\n[USER]\n{usr_prompt}"
                )
            ],
        )
    ]

    try:
        # Execute the API call with JSON configuration
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=gemini_schema,
                candidate_count=1,
            ),
        )
    except APIError as e:
        raise APIError(f"Gemini API call failed: {e}") from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e

    if debug:
        # The raw JSON string is in the 'text' attribute
        print(response.text)

    try:
        # The model returns a valid JSON string compliant with the schema.
        parsed = json.loads(response.text)
    except json.JSONDecodeError as e:
        # Catch case where the response is not valid JSON, though rare with structured output.
        raise InvalidResponseError(
            f"Malformed or invalid JSON in Gemini response: {response.text}"
        ) from e

    # Usage information is in 'usage_metadata'. Use .model_dump() for a standard dict.
    usage_info = response.usage_metadata.model_dump() if response.usage_metadata else {}

    return parsed, usage_info


def run_openai(
    sys_prompt, usr_prompt, schema, model, temperature, provider, debug=False
):
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
            temperature=temperature,
        )
    except Exception as e:
        raise APIError(f"OpenAI API call failed: {e}") from e

    if debug:
        print(response)

    try:
        text = response.output[0].content[0].text
        parsed = json.loads(text)
    except (AttributeError, IndexError, json.JSONDecodeError) as e:
        raise InvalidResponseError(
            f"Malformed or invalid JSON in OpenAI response: {response}"
        ) from e

    return parsed, response.usage.model_dump()


def check_api_key(env_var) -> str:
    key = os.getenv(env_var)
    if not key:
        raise OSError(f"Missing {env_var}")
    return key


def json_to_gemini_schema(node: dict) -> types.Schema:
    """Convert a JSON Schema Draft7-like dict to google.genai.types.Schema."""
    type_map = {
        "string": types.Type.STRING,
        "number": types.Type.NUMBER,
        "integer": types.Type.INTEGER,
        "boolean": types.Type.BOOLEAN,
        "array": types.Type.ARRAY,
        "object": types.Type.OBJECT,
    }

    # Determine the type
    json_type = node.get("type")
    gem_type = type_map.get(json_type, types.Type.STRING)

    schema_kwargs = {"type": gem_type}

    # Handle arrays
    if json_type == "array" and "items" in node:
        schema_kwargs["items"] = json_to_gemini_schema(node["items"])

    # Handle objects
    if json_type == "object":
        properties = node.get("properties", {})
        schema_kwargs["properties"] = {
            k: json_to_gemini_schema(v) for k, v in properties.items()
        }
        schema_kwargs["required"] = node.get("required", [])

    return types.Schema(**schema_kwargs)


def get_paths(config: dict, config_flag: bool) -> dict:
    """Return file paths from the TOML configuration, with optional overrides."""
    base = config["paths"]
    paths = {
        "llm_config": base["llm"],
        "questions_config": base["questions"],
        "combined_weights": config.get("combined_weights"),
    }
    if config_flag:
        paths.update(
            {
                "output": base.get("output_path"),
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
                [
                    "output",
                    "schema",
                    "programs",
                    "exam_text",
                    "sys_prompt",
                    "usr_prompt",
                ],
                ".",
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
        "--solution", "-sol", type=str, help="File containing example solution program"
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
        default="sp6.md",
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
    parser.add_argument(
        "--temperature",
        "-t",
        type=int,
        default=0.3,
        help="Temperature value to be used in the model",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output directory where evaluation will be saved",
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


def generate_schema_from_toml(topics, analysis):
    """Create JSON schema for the LLM output"""

    # Template for evidence object
    evidence_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "comment": {
                "type": "string",
                "description": "It is an observation done on the user's program that must enlight a correct aspect or "
                "a problem in it. The observations must refer to impactful problems related to user "
                "specifications. It must be useful for providing a summary of the goodness of the code.",
            },
            "lines": {
                "type": "array",
                "items": {"type": "string", "pattern": "^\\d+(-\\d+)?$"},
                "default": [],
                "description": "It contains comment's relative code lines numbers (e.g., '42' or '10-15'). "
                "Consecutive line numbers must not be in different array elements.",
            },
            "criticality": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "It enlight the relative comment criticality level. 'low' confirms correct or "
                "acceptable code, 'medium' is for already functional parts that could improved, "
                "'high' identifies an actual problem, error, or violation of the topic’s evaluation "
                "rules that must be corrected.",
            },
        },
        "required": ["comment", "lines", "criticality"],
        "description": "Evidence entry providing justification for a topic's score. Each score below 10 must "
        "correspond to at least one comment describing a necessary correction or improvement ('medium' "
        "or 'high' criticality).",
    }

    # Build prefixItems list — one entry per topic
    prefix_items = []
    for topic in topics:
        prefix_items.append(
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "type": "string",
                        "const": topic["name"],
                    },
                    "score": {
                        "type": "integer",
                        "description": "It must be a number between 0 and 10. It evaluates the topic satisfaction basing "
                        "exclusively on the specifications provided by the user. Score must be 10 when all "
                        "topic related comments have 'low' criticality.",
                    },
                    "evidences": {
                        "type": "array",
                        "items": evidence_schema,
                        "description": f"List of evidences supporting the evaluation for '{topic['name']}'.",
                    },
                },
                "required": ["name", "score", "evidences"],
                "description": topic["description"],
            }
        )

    # Add analysis sections dynamically
    analysis_props = {}
    for a in analysis:
        analysis_props[a["name"]] = {
            "type": "array",
            "description": a["description"],
            "items": {"type": "string", "description": f"Entry for '{a['name']}'."},
        }

    # Combine into one schema
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "evaluations": {
                "type": "array",
                "prefixItems": prefix_items,
                "items": {"type": "object", "additionalProperties": False},
                "minItems": len(prefix_items),
                "maxItems": len(prefix_items),
            },
            **analysis_props,
        },
        "required": ["evaluations", *list(analysis_props.keys())],
        "description": "Output json_schema to be respected",
    }

    return schema


def render_prompts(sys_prompt_path, usr_prompt_path, context_dict):
    """
    Renders system and user prompts from Jinja2 templates.

    Parameters
    ----------
    sys_prompt_path : str
        Path to the system prompt template file.
    usr_prompt_path : str
        Path to the user prompt template file.
    context_dict : dict
        Dictionary with all variables available to the templates.

    Returns
    -------
    tuple[str, str]
        Rendered (system_prompt, user_prompt)
    """
    env = Environment(
        loader=FileSystemLoader(
            [os.path.dirname(sys_prompt_path), os.path.dirname(usr_prompt_path)]
        ),
        autoescape=select_autoescape(),
    )

    sys_template = env.get_template(os.path.basename(sys_prompt_path))
    usr_template = env.get_template(os.path.basename(usr_prompt_path))

    system_prompt = sys_template.render(context_dict)
    user_prompt = usr_template.render(context_dict)

    return system_prompt, user_prompt


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
    programs_names = []
    is_single = False
    if input_args.program.endswith(".c"):
        # single program case
        is_single = True
        programs_names = os.path.splitext(os.path.basename(input_args.program))[0]
    else:
        # directory case
        program_path = input_args.program
        programs_names = os.listdir(input_args.program)

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
        exam_path = os.path.normpath(os.path.join(paths["exam_text"], input_args.exam))
        if not os.path.splitext(input_args.exam)[1]:  # directory case
            entries = {e.name for e in os.scandir(exam_path) if e.is_file()}
            pvcheck_flag = "pvcheck.test" in entries
            dat_files = [f for f in entries if f.endswith(".dat")]  # program input
            md_files = [f for f in entries if f.endswith(".md")]  # program context
            solutions = [f for f in entries if f.endswith(".c")]  # solution program
            if not (pvcheck_flag and dat_files and md_files and solutions):
                sys.exit(
                    "--exam directory missing required files (.dat, .md, pvcheck.test, .c)"
                )

            quest_weights = questions["questions_weights"]
            program_input = os.path.normpath(os.path.join(exam_path, dat_files[0]))
            file_target = os.path.normpath(os.path.join(exam_path, md_files[0]))
            sol_program = os.path.normpath(os.path.join(exam_path, solutions[0]))
        else:
            sys.exit("--exam argument must be a directory")
    else:
        program_input = os.path.normpath(
            os.path.join(paths["exam_text"], input_args.input or "")
        )
        file_target = os.path.normpath(
            os.path.join(paths["exam_text"], input_args.context or "")
        )
        sol_program = os.path.normpath(
            os.path.join(paths["exam_text"], input_args.solution or "")
        )

    # CONTEXT
    context = ""
    if exam_dir or bool(input_args.context):
        context = load_file(file_target)
        context = "```markdown\n" + context + "\n```"

    # SOLUTION PROGRAM
    solution = ""
    if exam_dir or bool(input_args.solution):
        solution = load_file(sol_program)

    # SCHEMA
    schema_path = os.path.normpath(os.path.join(paths["schema"], input_args.schema))
    schema = load_file(schema_path)
    json_name = os.path.splitext(os.path.basename(schema_path))[0]

    # schema = generate_schema_from_toml(topics, analysis)

    # PROMPTS CONSTRUCTION
    args_md_parts = []
    args_md_parts.extend(
        load_file(os.path.join("utils", topic["description"])) for topic in topics
    )
    args_md_parts.extend(f"### {a['name']}\n{a['description']}" for a in analysis)
    args_md = "\n".join(args_md_parts)

    sys_prompt_path = os.path.normpath(
        os.path.join(paths["sys_prompt"], input_args.system_prompt)
    )
    usr_prompt_path = os.path.normpath(
        os.path.join(paths["usr_prompt"], input_args.user_prompt)
    )
    system_prompt_name = os.path.splitext(os.path.basename(sys_prompt_path))[0]
    user_prompt_name = os.path.splitext(os.path.basename(usr_prompt_path))[0]

    for program_name in programs_names:
        if is_single:
            # single program case
            program_path = os.path.normpath(
                os.path.join(paths["programs"], input_args.program)
            )
        else:
            # directory case
            program_path = os.path.normpath(
                os.path.join(input_args.program, program_name)
            )
        program = add_line_numbers(load_file(program_path))

        # OBJECTIVE TESTS
        metrics = dict.fromkeys(tests, -1.0)
        metrics[tests[0]] = compilation_test(program_path)
        metrics[tests[1]] = time_test(program_input)
        pvcheck_csv_scores = defaultdict(list)
        if exam_dir and pvcheck_flag:
            metrics[tests[2]] = pvcheck_test(
                questions["questions_weights"], pvcheck_csv_scores, exam_path
            )

        # PROMPT COMPILING
        templ_context = {
            "schema_flag": False,
            "schema": schema,
            "topics": args_md,
            "context": context,
            "solution": solution,
            "program": program,
        }

        system_prompt, user_prompt = render_prompts(
            sys_prompt_path, usr_prompt_path, templ_context
        )

        # TEMPERATURE
        temperature = input_args.temperature

        # MODEL CALL
        model = input_args.model
        provider = input_args.provider

        try:
            if provider == "openai":
                parsed, tokens = run_openai(
                    system_prompt, user_prompt, schema, model, temperature, provider
                )
                tokens = openai_reshape_usage(tokens)
            elif provider == "gemini":
                parsed, tokens = run_gemini(
                    system_prompt, user_prompt, schema, model, temperature, provider
                )

            elif provider:
                parsed, tokens = run_openrouter(
                    system_prompt, user_prompt, schema, model, temperature
                )
            else:
                parsed, tokens, provider = run_router_request(
                    system_prompt,
                    user_prompt,
                    schema,
                    model,
                    input_args.prompt_price,
                    input_args.completion_price,
                    temperature,
                )
        except InvalidResponseError as e:
            print(e)
            sys.exit(1)
        except APIError as e:
            print(e)
            sys.exit(1)
        except OSError as e:
            print(e)
            sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)

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

        # SAVE OUTPUTpath
        output_dir = os.path.normpath(
            os.path.join(paths["output"], input_args.output or "")
        )
        timestamp = datetime.now().strftime("%H-%M-%S")
        exam_prefix = f"{input_args.exam}_" if exam_dir else ""
        output_file_name = f"{exam_prefix}{timestamp}_{program_name}_{system_prompt_name}_{user_prompt_name}_{json_name}.json"
        final_output_dir = os.path.normpath(
            os.path.join(output_dir, make_safe_dirname(model))
        )
        os.makedirs(final_output_dir, exist_ok=True)
        output_file_path = os.path.normpath(
            os.path.join(final_output_dir, output_file_name)
        )

        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "LLM": parsed,
                    "model": {"name": model, "provider": provider},
                    "usage": tokens,
                    "call_cost": call_cost,
                    **combined,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"Output saved in {output_file_path}")

        with open(output_file_path, encoding="utf-8") as f:
            data = json.load(f)
        env = Environment(loader=FileSystemLoader("."))
        template = env.get_template("report_template.html")
        html_output = template.render(data=data)

        output_html_name = os.path.splitext(output_file_name)[0]
        output_html_path = os.path.normpath(
            os.path.join(final_output_dir, f"{output_html_name}.html")
        )
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_output)


if __name__ == "__main__":
    main()
