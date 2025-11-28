import os
import json
from typing import List

from openai import OpenAI


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "GPT_generated_LLM_input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_artikel_assignments")
PARSER_PROMPT_PATH = os.path.join(BASE_DIR, "parser_prompt.txt")
README_PATH = os.path.join(BASE_DIR, "README.md")

MODEL_NAME = "gpt-5.1"
MAX_FILES = 2  # set to an integer (e.g. 1 or 2) to limit how many files are processed


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def list_input_files() -> List[str]:
    if not os.path.isdir(INPUT_DIR):
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")
    files = []
    for name in os.listdir(INPUT_DIR):
        if name.lower().endswith(".json"):
            files.append(os.path.join(INPUT_DIR, name))
    return sorted(files)


def derive_output_path(input_path: str) -> str:
    """
    Try to mirror the existing convention:
    - If filename contains 'SR-'..., use: large_LLM_artikel_output_<SR-...>.json
    - Otherwise: large_LLM_artikel_output_<basename>.json
    """
    base = os.path.basename(input_path)
    sr_part = None
    # crude SR extraction: look for 'SR-' and take until next '.json'
    if "SR-" in base:
        start = base.index("SR-")
        end = base.lower().rfind(".json")
        if end == -1:
            end = len(base)
        sr_part = base[start:end]

    if sr_part:
        out_name = f"large_LLM_artikel_output_{sr_part}.json"
    else:
        stem = base[:-5] if base.lower().endswith(".json") else base
        out_name = f"large_LLM_artikel_output_{stem}.json"

    return os.path.join(OUTPUT_DIR, out_name)


def build_messages(parser_prompt: str, readme_text: str, input_json_text: str, input_filename: str):
    """
    Build messages for the Chat Completions API, clearly labeling each section.
    """
    system_content = (
        "You are a legal document analyst specializing in Swiss federal law. "
        "Follow the user instructions carefully and return ONLY valid JSON as specified."
    )

    user_content = (
        "You will receive three components:\n\n"
        "1. PARSER_PROMPT (the task and detailed rules you must follow)\n"
        "2. README_MD (project context and how the input JSON was generated)\n"
        "3. INPUT_JSON (the specific GPT_Large_LLM_input file you must analyze)\n\n"
        "Use the PARSER_PROMPT as the primary specification for what to do.\n"
        "Use README_MD only as supporting context.\n"
        "Apply the rules to the INPUT_JSON and produce the required output JSON array.\n\n"
        f"----- BEGIN PARSER_PROMPT -----\n{parser_prompt}\n----- END PARSER_PROMPT -----\n\n"
        f"----- BEGIN README_MD -----\n{readme_text}\n----- END README_MD -----\n\n"
        f"----- BEGIN INPUT_JSON ({input_filename}) -----\n{input_json_text}\n----- END INPUT_JSON -----\n"
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def call_model(client: OpenAI, messages):
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
    )
    return resp.choices[0].message.content


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    parser_prompt = load_text(PARSER_PROMPT_PATH)
    readme_text = load_text(README_PATH)
    input_files = list_input_files()

    client = OpenAI(api_key=api_key)

    for idx, path in enumerate(input_files, start=1):
        base = os.path.basename(path)
        print(f"Processing {base} ...")

        with open(path, "r", encoding="utf-8") as f:
            input_json_text = f.read()

        messages = build_messages(parser_prompt, readme_text, input_json_text, base)
        try:
            output_text = call_model(client, messages)
        except Exception as e:
            print(f"ERROR processing {base}: {e}")
            continue

        out_path = derive_output_path(path)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"  -> wrote {out_path}")

        if MAX_FILES is not None and idx >= MAX_FILES:
            print(f"Reached MAX_FILES={MAX_FILES}, stopping.")
            break


if __name__ == "__main__":
    main()


