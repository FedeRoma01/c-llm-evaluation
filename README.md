# C Program Evaluator

## Overview

This project provides an automated evaluation system for C programs, particularly in the context of exam-like assignments. The evaluator integrates **objective metrics** (compilation checks, automated tests, execution performance) with **qualitative analysis** performed by Large Language Models (LLMs).

Given a C program, the corresponding exam description, and evaluation criteria, the system produces a structured evaluation with scores ranging from **0 to 10** and explanatory feedback.

## Repository Structure

The repository is organized as follows:

```
.
├── main.py                  # Entry point of the application
├── evaluation_functions.py  # Utility functions for compilation, testing, scoring
├── resources/
│   ├── sources/              # Input C programs (hashed versions)
│   └── 20220728/               # Exam-specific resources and related files
├── utils/
│   ├── prompt/              # Prompt templates (system and user) for LLMs
│   ├── json schema/         # JSON schemas defining expected output structures
│   └── config/              # Configuration files (relative to llm and exam)
├── config.toml              # Main configuration file
├── pyproject.toml           # Project and dependencies configuration managed by uv
├── uv.lock                  # Lock file with exact dependency versions
└── .python-version          # Python version used for the environment
```

### Key Components

* **resources**

  * `sources`: contains student C programs.
  * `20220728`: contains exam-related files (texts, test cases, etc.).

* **configuration**

  * `config.toml`: contains the main configurations.

* **utils**

  * `prompt`: stores user/system prompts used for guiding the LLMs.
  * `json schema`: defines the expected evaluation schema in JSON format.
  * `config`: configuration files (e.g., TOML) specifying directories, weights, and evaluation details.

* **Scripts**

  * `main.py`: orchestrates the evaluation process, handles prompts, interacts with LLMs, and saves results.
  * `evaluation_functions.py`: manages compilation, test execution (via `pvcheck`), performance metrics, and score aggregation.

* **uv project files**

  * `pyproject.toml`: defines project metadata and dependencies.
  * `uv.lock`: lock file with exact dependency versions for reproducible builds.
  * `.python-version`: records the Python version used in the environment.

## Features

* **Compilation Check**: evaluates warnings and errors during program compilation.
* **Automated Testing**: executes predefined tests with `pvcheck` and computes weighted scores.
* **Performance Measurement**: measures execution time to assess efficiency.
* **LLM-based Evaluation**: uses configurable LLMs (e.g., OpenAI GPT, Ollama, Fabric) for qualitative feedback.
* **Final Scoring**: combines objective metrics and LLM analysis using configurable weights.
* **Structured Output**: results are saved in JSON format with scores, evidence, and comments.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Install uv (recommended)**

   `uv` is the recommended tool for dependency management and virtual environments in this project.
   You can install it following the official instructions:

   ```bash
   pip install uv
   ```

   or, if you prefer, use one of the prebuilt binaries from [uv’s installation guide](https://github.com/astral-sh/uv).

3. Set up the environment with **uv**:

   ```bash
   uv sync
   ```

   This will create a `.venv/` virtual environment (excluded from version control) and install all dependencies specified in `pyproject.toml`.

4. Install external tools required for testing:

   * `gcc` (for compilation)
   * [`pvcheck`](https://github.com/claudio-unipv/pvcheck.git) (for automated exam testing) 
   * Optional: [`fabric`](https://github.com/danielmiessler/Fabric.git) (if using the Fabric model backend)

## Usage

### Pre requisites

In order to be able to use some models, like gpt-4.1-mini, an API-key is required.
To use it, you have to set it as a environment variable:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

### Execute the program

Run the evaluator with:

```bash
uv run main.py <program_file.c> [options]
```

### Arguments

* `program` (str): The C program file to evaluate.

### Options

* `--user_prompt, -up`: User prompt file (default: `up2.md`).
* `--exam, -ex`: The exam directory containing related resources (e.g., text, tests).
* `--config, -cf`: Boolean value to enable/disable pre-configured input files path (default: `True`).
* `--system_prompt, -sp`: System prompt file (default: `sp3.md`).
* `--schema, -s`: JSON schema file (default: `s3.json`).
* `--model, -m`: Model to use (`gpt-4.1-mini`, `llama3.2`, or `fabric`).

### Example

```bash
uv run main.py prova.c -ex 20220728 -m gpt-4.1-mini -up up2.md -sp sp3.md -s s5.json
```

This command evaluates `prova.c` against the exam resources in `20220728/` using GPT-4.1-mini and specified prompt/schema files.

## Output

Results are saved in the `output_path` specified in `config.toml`, under subfolders by model type (`GPTAnalysis/`, `llama3.2/`, `fabric/`).
Each output JSON file contains:

* **LLM evaluation** (scores and comments per criterion)
* **Objective metrics** (compilation, tests, performance)
* **Final combined score**

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
