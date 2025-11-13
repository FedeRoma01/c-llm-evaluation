import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.checkmyc.api.openai_api import run_openai
from src.checkmyc.code.config import load_file, render_prompts

# === Basic paths consistent with the repo ===
timestamp = datetime.now().strftime("%H-%M-%S")
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # repo root
PKG_ROOT = Path(__file__).resolve().parents[1]  # src/checkmyc
DATA_DIR = PKG_ROOT / "data"
INTERMEDIATE_OUTPUT_PATH = (
    PROJECT_ROOT / "output" / f"{timestamp}_all_evaluation_comments.json"
)
OUTPUT_DIR = PROJECT_ROOT / "output"
INPUT_DIR = OUTPUT_DIR / "comments_extraction" / "gpt-4_1-mini"
OUTPUT_JSON = OUTPUT_DIR / "extraction" / "gpt-4_1-mini" / f"{timestamp}_comments.json"


def process_json_files_single_output(
    file_paths: list[Path], output_path: str
) -> dict[str, list[str]]:
    """
    Process a list of JSON files to extract comments with 'goodness' == '-'.
    Group all comments by evaluation name and save the result in a single JSON file.
    """
    grouped_comments: dict[str, list[str]] = {}

    for file_path in file_paths:
        try:
            with open(file_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
        except FileNotFoundError:
            print(f"File non trovato: {file_path}")
            continue
        except json.JSONDecodeError:
            print(f"Errore JSON in: {file_path}")
            continue

        evaluations: list[dict[str, Any]] = data.get("LLM", {}).get("evaluations", [])
        for evaluation in evaluations:
            name = evaluation.get("name")
            evidences = evaluation.get("evidences", [])

            if not name:
                continue
            grouped_comments.setdefault(name, [])

            for ev in evidences:
                comment = ev.get("comment")
                goodness = ev.get("goodness")
                if (
                    goodness == "-"
                    and comment
                    and comment not in grouped_comments[name]
                ):
                    grouped_comments[name].append(comment)

    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        with Path(output_path).open("w", encoding="utf-8") as f:
            json.dump(grouped_comments, f, indent=4, ensure_ascii=False)
        print(f"All comments extracted in: {output_path}")
    except OSError:
        print(f"Error writing output file: {output_path}")
    """

    return grouped_comments


def get_input_files_from(files_dir: Path) -> list[Path]:
    """Returns a list of JSON file paths in a directory."""
    return [files_dir / f for f in os.listdir(files_dir) if f.endswith(".json")]


def init_argparser():
    parser = argparse.ArgumentParser(
        description="Extract different negative meaning comments per topic from "
        "different analysis"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=INPUT_DIR,
        help="Directory containing the evaluations from "
        "which extract negative comments",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=OUTPUT_JSON, help="Output path"
    )

    return parser


def main():
    # Input directory with previous results
    parser = init_argparser()
    input_args = parser.parse_args()
    input_files = get_input_files_from(input_args.input_dir)

    # Extracting and saving comments
    comments = process_json_files_single_output(input_files, INTERMEDIATE_OUTPUT_PATH)
    print("\nProcessing complete.")

    # PROMPT CONSTRUCTION
    templ_context = {"comments": comments}
    system_prompt, user_prompt = render_prompts(
        DATA_DIR / "prompts" / "system/sys_comm_extr.md",
        DATA_DIR / "prompts" / "user/usr_comm_extr.md",
        templ_context,
    )

    # OUTPUT JSON SCHEMA
    schema = load_file(DATA_DIR / "json_schema" / "comments_schema.json")

    # API CALL
    parsed, tokens = run_openai(
        system_prompt, user_prompt, schema, "gpt-4.1-mini", 0.3, "openai"
    )

    # JSON SAVING
    output_json = input_args.output
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    # HTML SAVING
    output_html = output_json.with_suffix(".html")
    env = Environment(
        loader=FileSystemLoader(DATA_DIR / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("extract_template.html")
    html = template.render(data=parsed)

    # SAVING
    output_html.write_text(html, encoding="utf-8")

    print(f"Output saved to {input_args.output}")


if __name__ == "__main__":
    main()
