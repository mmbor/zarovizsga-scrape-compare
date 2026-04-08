import os
import json
import argparse
import glob
from datetime import datetime
from fpdf import FPDF
import html

# ======================== HELPERS ========================

def ensure_dirs():
    os.makedirs('JSON', exist_ok=True)
    os.makedirs('fonts', exist_ok=True)

def load_json_file(filepath):
    if not os.path.isfile(filepath):
        print(f"File not found: {filepath}")
        return None
    with open(filepath, 'r', encoding='utf8') as f:
        return json.load(f)

def compare_jsons(old_json, new_json):
    """
    Compare two JSON lists of questions.
    Returns only questions that are new or have changed.
    """
    differences = []

    # map old questions by csorszam
    old_map = {q.get('csorszam'): q for q in old_json}

    for new_q in new_json:
        csorszam = new_q.get('csorszam')
        old_q = old_map.get(csorszam)

        if not old_q:
            # new question
            differences.append(new_q)
        else:
            # check for differences
            changed = False

            # compare main question text
            if new_q.get('leirasPlaintext') != old_q.get('leirasPlaintext'):
                changed = True

            # compare explanations at question level
            if new_q.get('magyarazatPlaintext') != old_q.get('magyarazatPlaintext'):
                changed = True

            # compare case description
            if new_q.get('esetleiras') != old_q.get('esetleiras'):
                changed = True

            # compare answers
            old_answers = sorted(old_q.get('kerdesValasz', []), key=lambda x: x.get('betujel', ''))
            new_answers = sorted(new_q.get('kerdesValasz', []), key=lambda x: x.get('betujel', ''))

            if old_answers != new_answers:
                changed = True

            if changed:
                differences.append(new_q)

    return differences if differences else None

def save_diff_as_json(name, json_data):
    out_path = os.path.join('JSON', f"{name} - Differences.json")
    with open(out_path, 'w', encoding='utf8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def check_font_files():
    required_fonts = ['DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf']
    for font in required_fonts:
        font_path = os.path.join('fonts', font)
        if not os.path.isfile(font_path):
            print(f"❌ Missing font file: {font_path}")
            print("Please place the required .ttf files in the 'fonts/' folder.")
            exit(1)

# ======================== PDF RESULT GENERATION ========================

class CombinedPDF(FPDF):
    def __init__(self, highlight_correct=True, show_explanation=True):
        super().__init__()
        self.highlight_correct = highlight_correct
        self.show_explanation = show_explanation

        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages()

        # Unicode fonts
        self.add_font('DejaVu', '', os.path.join('fonts', 'DejaVuSans.ttf'), uni=True)
        self.add_font('DejaVu', 'B', os.path.join('fonts', 'DejaVuSans-Bold.ttf'), uni=True)
        self.add_font('DejaVu', 'I', os.path.join('fonts', 'DejaVuSans-Oblique.ttf'), uni=True)
        self.set_font('DejaVu', '', 12)

        self.creation_date = datetime.now().strftime('%d.%m.%Y')
        self.add_page()

    def header(self):
        self.set_font('DejaVu', 'B', 14)
        self.cell(0, 10, 'Question Differences', border=False, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.cell(0, 0, f'Created on {self.creation_date} | by M. M. Borka | Page {self.page_no()} of {{nb}}', align='C')

    def add_question(self, question_data):
        question_prefix = question_data.get('csorszam', '???')
        leiras_text = html.unescape(question_data.get('leirasPlaintext', ''))

        # Question title
        self.set_font('DejaVu', 'B', 12)
        self.set_fill_color(230, 230, 250)
        self.multi_cell(0, 8, f"{question_prefix}: {leiras_text}", fill=True)
        self.ln(1)

        # Case description
        esetleiras = question_data.get('esetleiras')
        if esetleiras:
            nev_text = esetleiras.get('nevPlaintext')
            if nev_text:
                self.set_x(self.get_x() + 5)
                self.set_font('DejaVu', 'I', 11)
                self.multi_cell(0, 8, html.unescape(nev_text), fill=True)
                self.ln(2)

        # Answers
        answers = sorted(question_data.get('kerdesValasz', []), key=lambda x: x.get('betujel', ''))
        for ans in answers:
            answer_text = html.unescape(f"{ans.get('betujel', '?')}) {ans.get('szovegPlaintext', '')}")
            explanation_text = html.unescape(ans.get('magyarazatPlaintext', '') or '')

            if self.highlight_correct and ans.get('helyes', 0) == 1:
                self.set_font('DejaVu', 'B', 12)
            else:
                self.set_font('DejaVu', '', 12)

            self.multi_cell(0, 6, answer_text)
            self.ln(1)

            if self.show_explanation and explanation_text.strip():
                self.set_fill_color(245, 245, 245)
                self.set_font('DejaVu', 'I', 11)
                self.multi_cell(0, 5, f"   ➔ {explanation_text}", fill=True)
                self.ln(2)

        self.ln(5)

# ======================== MAIN ========================
print ("=====================================================")
print ("FINAL EXAM JSON COMPARITOR===========================")
print ("=====================================================")
print ("by Maximilian Marius Borka===========================")
print ("=====================================================")
print ("please read documentation, atleast run this script in")
print ("a folder with this script, dependecies and 2 folders")
blank = input("Press enter to continue: ")
# Ask the user to type the folder paths
print ("=====================================================")
print ("==be aware of spaces and CAPITALIZED/small letters===")
old_folder = input("Enter the path to the old folder (default: Old): ") or "Scrape1"
new_folder = input("Enter the path to the new folder (default: New): ") or "Scrape2"
print ("=====================================================")
# Remove any trailing slashes or backslashes
old_folder = old_folder.rstrip('/\\')
new_folder = new_folder.rstrip('/\\')
print("Old folder:", old_folder)
print("New folder:", new_folder)
print ("=====================================================")

#if removing abouvementioned manual input
#
# makes it easier for people not wanting to touch the source
#
#parser = argparse.ArgumentParser(description="Compare two folders with JSON files and generate PDFs.")
#parser.add_argument('--old-files-path', type=str, default='Scrape1', help='Path to old folder')
#parser.add_argument('--new-files-path', type=str, default='Scrape2', help='Path to new folder')
#args = parser.parse_args()
#old_folder = args.old_files_path.rstrip('/\\')
#new_folder = args.new_files_path.rstrip('/\\')

ensure_dirs()
check_font_files()

old_files = glob.glob(os.path.join(old_folder, '*.json'))
if not old_files:
    print(f"ERROR: No JSON files found in: {old_folder}")
    exit(1)

print("🏁 File locations vertified")

pdf_diff = CombinedPDF(highlight_correct=True, show_explanation=True)
pdf_exercise = CombinedPDF(highlight_correct=False, show_explanation=False)

print("🟩 Begining scan")
for old_file_path in old_files:
    file_name = os.path.basename(old_file_path)
    new_file_path = os.path.join(new_folder, file_name)

    if not os.path.exists(new_file_path):
        print(f"New file missing: {file_name}")
        continue

    old_json = load_json_file(old_file_path)
    new_json = load_json_file(new_file_path)

    if old_json is None or new_json is None:
        print(f"Error loading {file_name}")
        continue

    differences = compare_jsons(old_json, new_json)
    if differences:
        name = os.path.splitext(file_name)[0]
        save_diff_as_json(name, differences)

        for q in differences:
            pdf_diff.add_question(q)
            pdf_exercise.add_question(q)

        print(f"❌ {file_name} is changed! (UPADTED QUESTIONS)")
    else:
        print(f"✅ {file_name} has no recognized changes")

print("🏁 All files have been scanned")

# Save PDFs
pdf_diff.output('Differences_Combined.pdf')
print("🏁 Differences PDF saved as 'Differences_Combined.pdf'")

pdf_exercise.output('Exercise_Combined.pdf')
print("🏁 Exercise PDF saved as 'Exercise_Combined.pdf'")

print("🏁 Program finished")
print("=====================================================")
