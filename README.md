# C Program Evaluator

## Overview

This project provides an automated evaluation system for C programs, particularly in the context of exam-like assignments. The evaluator integrates **objective metrics** (compilation checks, automated tests, execution performance) with **qualitative analysis** performed by Large Language Models (LLMs).

Given a C program, the corresponding exam description, and evaluation criteria, the system produces a structured evaluation with scores ranging from **0 to 10** and explanatory feedback.

---

## Repository Structure

The repository is organized as follows:

```
.
├── main.py                  # Entry point of the application
├── evaluation_functions.py  # Utility functions for compilation, testing, scoring
├── resources/
│   ├── sources/              # Input C programs (hashed versions)
│   └── 20220728/             # Exam-specific resources and related files
├── utils/
│   ├── prompt/              # Prompt templates (system and user) for LLMs
│   ├── json schema/         # JSON schemas defining expected output structures
│   └── config/              # Configuration files (relative to llm and tests)
├── config.toml              # Main configuration file
├── pyproject.toml           # Project and dependencies configuration managed by uv
└── uv.lock                  # Lock file with exact dependency versions
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
  * `config`: configuration .toml files specifying directories, weights, and evaluation details.

* **Scripts**

  * `main.py`: orchestrates the evaluation process, handles prompts, interacts with LLMs, and saves results.
  * `evaluation_functions.py`: manages compilation, test execution (via `pvcheck`), performance metrics, and score aggregation.

* **uv project files**

  * `pyproject.toml`: defines project metadata and dependencies.
  * `uv.lock`: lock file with exact dependency versions for reproducible builds.

---

## Features

* **Compilation Check** — evaluates compiler diagnostics, counting warnings and detecting build errors.  
* **Automated Testing** — runs objective checks (`pvcheck`) and performance tests, generating weighted numeric scores for correctness and efficiency.  
* **Performance Measurement** — measures execution time and contributes to the final quantitative assessment.  
* **LLM-based Evaluation** — uses configurable large language models to perform topic-based qualitative analysis of the C program.  
  - Produces detailed evaluations per topic (`score`, `evidences`, and `criticality` for each comment).  
  - Identifies **priority issues** and provides **practical improvement tips**.  
* **Final Scoring** — integrates quantitative test results with LLM-derived evaluations using configurable weighting rules.  
* **Structured Output** — stores all results in a hierarchical JSON structure including:
  - Used model and relative provider.
  - LLM evaluations with per-topic scores, evidences, and criticality levels.  
  - Token usage and cost statistics.  
  - Objective test scores (warnings, performance, pvcheck).  
  - Aggregated scores and weighting parameters used for final computation.
* **HTML file** - visualizes the output in a web page.


---

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

---

## Usage

### Pre requisites

### LLM Model API Key Requirements

To use LLM models, an API key is required. Two types of keys are supported depending on the chosen model: `openrouter_api_key` and `openai_api_key`.

- **`openrouter_api_key`**: This key is used when the provider is not explicitly specified. In this case, OpenRouter automatically selects the appropriate provider for the requested model, handling API usage and costs according to the parameters provided in the request.

- **`openai_api_key`**: This key is used when the specified provider is `OpenAI`. API calls are made directly to OpenAI, bypassing OpenRouter, and usage is billed according to OpenAI's pricing.

To use them, you have to set it as a environment variable:

**macOS/Linux**:
```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENROUTER_API_KEY="your_api_key_here"
```
**Windows**:
```bash
setx OPENAI_API_KEY "your_api_key_here"
setx OPENROUTER_API_KEY "your_api_key_here"
```

### Execute the program

Run the evaluator with:

```bash
uv run main.py <program_file.c> [options]
```

### Arguments

* `program` (str): The C program file to evaluate.
* `model` (str): LLM model to use.

### Options

* `--exam, -ex` (str): Directory containing exam resources (e.g., exam text, pvcheck test, input for the C program).  
* `--input, -i` (str): Input for the C program.  
* `--context, -cx` (str): Context for the C program.  
* `--config, -cf`: Enables pre-configured input file paths.  
* `--system_prompt, -sp` (str): System prompt file (default: `sp6.md`).  
* `--user_prompt, -up` (str): User prompt file (default: `up4.md`).  
* `--schema, -s` (str): JSON schema file (default: `s5.json`).  
* `--provider, -pr` (str): Provider to use for the specified model. 
* `--prompt_price, -pp` (float): Maximum price per 1M tokens for the prompt (default: '0').  
* `--completion_price, -cp` (float): Maximum price per 1M tokens for the completion (default: '0').

### Specifications

#### option `--exam`
When specifying the exam directory, it must contain the following files:

* `pvcheck.test` – Test file for pvcheck.  
* `<my_context>.md` – Context for the C program (e.g., exam text).  
* `<my_input>.dat` – Input file for the C program. If this file exists, any input passed via `--input` will be ignored.

**Notes:**

- The file names `my_context` and `my_input` are examples; file extensions must be `.md` and `.dat`.  
- Using `--exam` automatically ignores `--input` and `--context` options.  
- Recommended when the directory contains both context and input files along with `pvcheck.test` to perform the pvcheck test.

#### option `--provider`
Behavior changes depending on whether a provider is specified:

* **Provider specified**:  
  - The API call will be made **only using that provider** with its default pricing.  

* **Provider not specified**:
  - The API call will attempt multiple providers for the chosen model, starting from the **least expensive**.  
  - Maximum prices set via `--prompt_price` and `--completion_price` will be applied.  

**Note:** Price constraints are only applied when no provider is explicitly specified.

### Example

#### Execution with pvcheck

```bash
uv run main.py prova.c -cf -ex 20220728 -m openai/gpt-4.1-mini -up up4.md -sp sp6.md -s s5.json
```

This command evaluates `prova.c` against the exam resources in `20220728/` using `gpt-4.1-mini` and specified prompt/schema files. All files refer to pre-configured paths.

#### Execution without pvcheck

```bash
uv run main.py prova.c -cf -i 20220728/Esempio_nel_testo.dat -m openai/gpt-4.1-mini -up up4.md -sp sp6.md -s s5.json
```
This command evaluates `prova.c` without any context using GPT-4.1-mini, `Esempio_nel_testo.dat` as input for `prova.c`, and specified prompt/schema files. All files refer to pre-configured paths.

---

## Output

Results are saved in the `output_path` specified in `config.toml`, organized by model type (`<model>/`).
Each evaluation produces two output files with identical base names but different extensions:
* `<timestamp>_<program>_<systemPrompt>_<userPrompt>_<schema>.json`
* `<timestamp>_<program>_<systemPrompt>_<userPrompt>_<schema>.html`

Each output JSON file includes the following sections, while the corresponding HTML file renders the results in a human-readable format using a predefined Jinja2 template (`report_template.html`), allowing quick visualization of the evaluation outcome:

### **LLM**
Contains the model’s qualitative evaluation of the C program:

- **`evaluations`** — list of evaluated topics. Each topic includes:
  - **`name`**: the concept evaluated (e.g., *Control structures*, *Functions*).
  - **`score`**: numeric score from 0 to 10.
  - **`evidences`** — list of observations with:
    - **`comment`**: textual explanation of the issue or observation.
    - **`lines`**: list of line ranges in the source code (e.g., `"51-55"`, `"118-171"`).
    - **`criticality`**: qualitative severity level (`"high"`, `"medium"`, `"low"`).
- **`priority issues`** — concise list of the most severe problems detected.
- **`practical_tips`** — prioritized suggestions for fixing or improving the code.

### **usage**
Information about model usage and cost:
- `input_tokens`, `output_tokens`, and `total_tokens` indicate the number of tokens processed.
- `call_cost` gives the estimated monetary cost of the model call.

### **tests_scores**
Objective evaluation metrics:
- **`warning`** — compilation quality based on compiler diagnostics.
- **`performance`** — runtime efficiency evaluation.
- **`pvcheck`** — correctness of program behavior against expected outputs.
- **`final`** — combined test score.

### **llm_scores**
Aggregated scores per topic and their weighted average:
- Each key corresponds to a topic (e.g., *Pointers*, *File handling*).
- The `final` field represents the weighted LLM-based score.

### **final_score**
Overall combined score derived from LLM evaluation and objective tests.

### **weights**
Weighting coefficients used for score aggregation:
- `pvcheck_questions`, `tests`, and `llm` define how partial scores contribute to the total.
- The `final` section specifies the relative influence of LLM and test scores.


---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
