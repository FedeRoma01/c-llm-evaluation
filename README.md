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
│   ├── hashed/              # Input C programs (hashed versions)
│   └── exams/               # Exam-specific resources and related files
└── utils/
    ├── prompt/              # Prompt templates (system and user) for LLMs
    ├── json schema/         # JSON schemas defining expected output structures
    └── config/              # Configuration files (paths, model settings, weights)
```

### Key Components

* **resources**

  * `hashed`: contains student C programs.
  * `exams`: contains exam-related files (texts, test cases, etc.).

* **utils**

  * `prompt`: stores user/system prompts used for guiding the LLMs.
  * `json schema`: defines the expected evaluation schema in JSON format.
  * `config`: configuration files (e.g., TOML) specifying directories, weights, and evaluation details.

* **Scripts**

  * `main.py`: orchestrates the evaluation process, handles prompts, interacts with LLMs, and saves results.
  * `evaluation_functions.py`: manages compilation, test execution (via `pvcheck`), performance metrics, and score aggregation.

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

2. Install Python dependencies (Python 3.10+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

   *(Ensure you have `openai`, `ollama`, and other required packages installed.)*

3. Install external tools required for testing:

   * `gcc` (for compilation)
   * `pvcheck` (for automated exam testing)
   * Optional: `fabric` (if using the Fabric model backend)

## Usage

Run the evaluator with:

```bash
python main.py <program_file.c> <exam_directory> [options]
```

### Arguments

* `program` (str): The C program file to evaluate.
* `exams` (str): The exam directory containing related resources (e.g., text, tests).

### Options

* `--user_prompt, -up`: User prompt file (default: `up2.md`).
* `--system_prompt, -sp`: System prompt file (default: `sp3.md`).
* `--schema, -s`: JSON schema file (default: `s3.json`).
* `--model, -m`: Model to use (`gpt-4.1-mini`, `llama3.2`, or `fabric`).

### Example

```bash
python main.py prova.c 20220728 -m gpt-4.1-mini -up up2.md -sp sp3.md -s s3.json
```

This command evaluates `prova.c` against the exam resources in `20220728/` using GPT-4.1-mini and specified prompt/schema files.

## Output

Results are saved in the `output_path` specified in `utils/config/general.toml`, under subfolders by model type (`GPTAnalysis/`, `llama3.2/`, `fabric/`).
Each output JSON file contains:

* **LLM evaluation** (scores and comments per criterion)
* **Objective metrics** (compilation, tests, performance)
* **Final combined score**

---

## License

This project is provided for academic and research purposes. Please check the repository for licensing details.
