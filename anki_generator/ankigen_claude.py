import json
import os

def escape_tsv(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace("\t", " ").replace("\n", " ").replace("\r", " ")

base_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = base_dir
output_dir = os.path.join(base_dir, "Anki_Generated")

print("Input dir:", input_dir)
if not os.path.exists(input_dir):
    print("❌ Input directory does not exist!")
    exit()

os.makedirs(output_dir, exist_ok=True)
files = os.listdir(input_dir)
print("Files found:", files)

for filename in sorted(files):
    if not filename.endswith(".json"):
        continue
    print("Processing:", filename)

    input_path = os.path.join(input_dir, filename)
    tag = os.path.splitext(filename)[0]
    output_file = os.path.join(output_dir, f"{tag}.tsv")

    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON: {filename}")
            continue

    print(f"Loaded {len(data)} items from {filename}")

    with open(output_file, "w", encoding="utf-8") as out_f:
        for item in data:
            csorszam = escape_tsv(str(item.get("csorszam", "")))
            question = escape_tsv(item.get("leirasPlaintext", ""))
            options = item.get("kerdesValasz", [])
            elementary = item.get("kerdesElemiValasz", [])

            # Front: ID + bold question + extra line + elementary + options
            front_lines = [f"ID: {csorszam}", f"<b>{question}</b>", "<br>"]
            if elementary:
                front_lines.append("Elementary answers:")
                for el in elementary:
                    el_text = escape_tsv(el.get("szoveg", ""))
                    front_lines.append(f"{el.get('szam', '')}. {el_text}")
                front_lines.append("")
            for opt in options:
                opt_text = escape_tsv(opt.get("szovegPlaintext", ""))
                front_lines.append(f"{opt.get('betujel', '')}. {opt_text}")
            front = "<br>".join(front_lines)

            # Back: bold correct answer + extra line + explanation
            correct = next((o for o in options if o.get("helyes") == 1), None)
            if correct:
                correct_text = escape_tsv(correct.get("szovegPlaintext", ""))
                explanation = escape_tsv(correct.get("magyarazatPlaintext") or item.get("magyarazatPlaintext") or "")
                back_lines = [f"<b>Correct: {correct.get('betujel', '')}. {correct_text}</b>"]
                if explanation:
                    back_lines.append("<br>")
                    back_lines.append(f"Explanation: {explanation}")
                back = "<br>".join(back_lines)
            else:
                back = "No correct answer provided"

            out_f.write(f"{front}\t{back}\t{tag}\n")

    print(f"Created: {output_file}")

print("✅ Done!")
