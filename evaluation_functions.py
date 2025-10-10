import subprocess
import time
import csv
import io
import os
import platform
from pathlib import Path


def add_line_numbers(code: str) -> str:
    # Add line numbers for relative comments in the output
    lines = []
    for i, line in enumerate(code.splitlines(), start=1):
        lines.append(f"{i:4d} | {line}")

    return "```c\n" + "\n".join(lines) + "\n```"


def compilation_test(file_path):
    # Gcc compilation
    compile_cmd = ["gcc", "-Wall", "-Wextra", str(Path(file_path))]
    res = 0
    try:
        result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=10)
        warnings = result.stderr.count("warning:")
        res = max(0, 10 - warnings)
        if result.returncode != 0:
            print("Compilation error")
            return 0
    except subprocess.TimeoutExpired:
        print("Expired compilation")
        return 0
    return res


def time_test(p_input):
    # Time performance
    res = 0
    try:
        exec_name = "a.out" if platform.system() != "Windows" else "a.exe"
        compile_cmd = [f"./{exec_name}", str(Path(p_input))]
        start = time.time()
        result = subprocess.run(compile_cmd, capture_output=True, timeout=5)
        elapsed = time.time() - start
        if result.returncode != 0:
            print("Program exited with an error or crashed: error", result.returncode)
        else:
            if elapsed < 1:
                res = 10
            elif elapsed < 2:
                res = 8
            else:
                res = 6
    except subprocess.TimeoutExpired:
        print("Expired execution time")

    return res


def pvcheck_test(pvcheck_weights, pvcheck_csv_scores, exam_dir_path):
    # Test con pvcheck
    res = 0
    try:
        exec_name = "a.out" if platform.system() != "Windows" else "a.exe"
        pvcheck_cmd = ["pvcheck", "-F", "csv", "-f", os.path.join(exam_dir_path, "pvcheck.test"), f"./{exec_name}"]
        result = subprocess.run(pvcheck_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("Pvcheck not exectued: error", result.returncode)

        # CSV output parsing
        csv_data = result.stdout
        fl = io.StringIO(csv_data)
        reader = csv.DictReader(fl)
        headers = reader.fieldnames
        for row in reader:
            for key, val in row.items():
                pvcheck_csv_scores[key].append(val)
        scores_list = [float(values[-1]) for key, values in
                       list(pvcheck_csv_scores.items())[2:]]  # pvcheck scores range: 0-100
        norm_scores = [s / 10 for s in scores_list]
        weights_list = list(pvcheck_weights.values())
        total_weigths = sum(weights_list)
        norm_weights = [w / total_weigths for w in weights_list]

        # Weighted mean
        res = sum(v * w for v, w in zip(norm_scores, norm_weights))
        return res

    except FileNotFoundError:
        print("Command not found")
        return -1

    except subprocess.TimeoutExpired:
        return 0


def compute_final_score(objective_metrics, llm_metrics, tests_weights, llm_weights, combined_weights, quest_weights,
                        pvcheck_csv_scores):
    # Tests score
    tests_names = list(tests_weights.keys())
    tests_score = 0
    tests_weights_sum = 0
    for test in tests_names:
        if objective_metrics.get(test, 0) != -1:
            # don't consider not done tests (with -1 value)
            tests_score += tests_weights[test] * objective_metrics.get(test, 0)
            tests_weights_sum += tests_weights[test]
        else:
            objective_metrics[test] = "Not executed"
            tests_weights[test] = "Not considered"
    tests_score = tests_score / tests_weights_sum


    # LLM score
    llm_score = 0
    llm_metrics_spec = {}
    for arg in llm_metrics["evaluations"]:
        llm_metrics_spec[arg["name"]] = arg["score"]
        llm_score += arg["score"] * llm_weights[arg["name"]]
    llm_score = llm_score / sum(llm_weights.values())

    # Final score
    combined_weights_sum = sum(combined_weights.values())
    final_score = (combined_weights["tests"] * tests_score + combined_weights["llm"] * llm_score) / combined_weights_sum

    return {
        "pvcheck": {k: [(float(x) if x != "MISS" else 0) for x in v] for k, v in list(pvcheck_csv_scores.items())[2:]},
        "tests_scores": {**objective_metrics, "final": tests_score},
        "llm_scores": {**llm_metrics_spec, "final": llm_score},
        "final_score": final_score,
        "weights": {"pvcheck_questions": quest_weights, "tests": tests_weights, "llm": llm_weights,
                    "final": combined_weights}
    }
