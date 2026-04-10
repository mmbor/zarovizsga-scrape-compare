"""
=====================================================
FINAL EXAM JSON COMPARATOR v2
by Maximilian Marius Borka
=====================================================
Compares two folders of JSON exam question files.
Detects: new, changed, and DELETED questions.
Also compares kerdesElemiValasz (elementary answers).
Outputs: diff PDF, exercise PDF, and diff JSON files.
=====================================================
"""

import os
import sys
import json
import glob
import html
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

VERSION = "2.0"
AUTHOR  = "M. M. Borka"

COLOR_HEADER_BG   = colors.HexColor("#2C3E50")
COLOR_CORRECT     = colors.HexColor("#1A6B2E")
COLOR_DELETED_BG  = colors.HexColor("#FDECEA")
COLOR_DELETED_TXT = colors.HexColor("#B71C1C")
COLOR_NEW_BG      = colors.HexColor("#E8F5E9")
COLOR_NEW_TXT     = colors.HexColor("#1A6B2E")
COLOR_CHANGED_BG  = colors.HexColor("#FFF8E1")
COLOR_CHANGED_TXT = colors.HexColor("#E65100")
COLOR_EXPL_BG     = colors.HexColor("#F5F5F5")
COLOR_CASE_BG     = colors.HexColor("#EAF4FB")
COLOR_ANSWER_BG   = colors.HexColor("#FAFAFA")


# ─────────────────────────────────────────────
# DIRECTORY / FILE HELPERS
# ─────────────────────────────────────────────

def ensure_dirs():
    os.makedirs("JSON", exist_ok=True)


def load_json(filepath):
    if not os.path.isfile(filepath):
        print(f"  [!] File not found: {filepath}")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [!] JSON parse error in {filepath}: {e}")
            return None


def save_diff_json(name, data):
    out = os.path.join("JSON", f"{name} - Differences.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"     JSON saved → {out}")


def unescape(text):
    if not text:
        return ""
    return html.unescape(str(text)).strip()


# ─────────────────────────────────────────────
# COMPARISON LOGIC
# ─────────────────────────────────────────────

def normalise_kerdes_valasz(answers):
    """Sort and normalise kerdesValasz list for comparison."""
    return sorted(
        [{k: v for k, v in a.items()} for a in answers],
        key=lambda x: x.get("betujel", "")
    )


def normalise_elemi_valasz(answers):
    """Sort and normalise kerdesElemiValasz list for comparison."""
    return sorted(
        [{k: v for k, v in a.items()} for a in answers],
        key=lambda x: str(x.get("szam", ""))
    )


def questions_differ(old_q, new_q):
    """Return True if any meaningful field changed between two question dicts."""
    checks = [
        ("leirasPlaintext",    lambda q: q.get("leirasPlaintext")),
        ("magyarazatPlaintext",lambda q: q.get("magyarazatPlaintext")),
        ("esetleiras",         lambda q: q.get("esetleiras")),
        ("leiras",             lambda q: q.get("leiras")),
        ("magyarazat",         lambda q: q.get("magyarazat")),
        ("nehezseg",           lambda q: q.get("nehezseg")),
        ("feladatTipusId",     lambda q: q.get("feladatTipusId")),
        ("statuszId",          lambda q: q.get("statuszId")),
        ("aktiv",              lambda q: q.get("aktiv")),
    ]
    for label, getter in checks:
        if getter(old_q) != getter(new_q):
            return True

    # kerdesValasz (multiple-choice answers with betujel)
    if normalise_kerdes_valasz(old_q.get("kerdesValasz", [])) != \
       normalise_kerdes_valasz(new_q.get("kerdesValasz", [])):
        return True

    # kerdesElemiValasz (elementary / matching answers with szam)
    if normalise_elemi_valasz(old_q.get("kerdesElemiValasz", [])) != \
       normalise_elemi_valasz(new_q.get("kerdesElemiValasz", [])):
        return True

    return False


def compare_folders(old_folder, new_folder):
    """
    Compare every JSON file found in old_folder against new_folder.
    Returns a list of result dicts, one per file pair.
    """
    old_files = glob.glob(os.path.join(old_folder, "*.json"))
    new_files  = {os.path.basename(p) for p in glob.glob(os.path.join(new_folder, "*.json"))}

    if not old_files:
        print(f"\n[ERROR] No JSON files found in: {old_folder}")
        sys.exit(1)

    results = []

    for old_path in sorted(old_files):
        fname = os.path.basename(old_path)
        new_path = os.path.join(new_folder, fname)

        print(f"\n  Scanning {fname} …")

        if fname not in new_files:
            print(f"    ⚠️  Entire file MISSING in new folder — all questions treated as deleted")
            old_json = load_json(old_path)
            if old_json:
                results.append({
                    "file": fname,
                    "new":     [],
                    "changed": [],
                    "deleted": old_json,
                })
            continue

        old_json = load_json(old_path)
        new_json = load_json(new_path)

        if old_json is None or new_json is None:
            print(f"    ⚠️  Could not load — skipping")
            continue

        old_map = {q.get("csorszam"): q for q in old_json}
        new_map = {q.get("csorszam"): q for q in new_json}

        new_qs     = []
        changed_qs = []
        deleted_qs = []

        for csorszam, new_q in new_map.items():
            old_q = old_map.get(csorszam)
            if old_q is None:
                new_qs.append(new_q)
            elif questions_differ(old_q, new_q):
                changed_qs.append(new_q)

        for csorszam, old_q in old_map.items():
            if csorszam not in new_map:
                deleted_qs.append(old_q)

        total = len(new_qs) + len(changed_qs) + len(deleted_qs)
        if total == 0:
            print(f"    ✅ No changes")
        else:
            if new_qs:
                print(f"    🆕 {len(new_qs)} new question(s)")
            if changed_qs:
                print(f"    ❌ {len(changed_qs)} changed question(s)")
            if deleted_qs:
                print(f"    🗑️  {len(deleted_qs)} deleted question(s)")

        results.append({
            "file":    fname,
            "new":     new_qs,
            "changed": changed_qs,
            "deleted": deleted_qs,
        })

    # Also flag JSON files present only in new folder
    old_names = {os.path.basename(p) for p in old_files}
    for fname in sorted(new_files - old_names):
        new_path = os.path.join(new_folder, fname)
        new_json = load_json(new_path)
        if new_json:
            print(f"\n  Scanning {fname} … (new file, all questions are NEW)")
            results.append({
                "file":    fname,
                "new":     new_json,
                "changed": [],
                "deleted": [],
            })

    return results


# ─────────────────────────────────────────────
# PDF STYLES
# ─────────────────────────────────────────────

def build_styles():
    base = getSampleStyleSheet()
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "q_new": S("q_new",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=COLOR_NEW_TXT, backColor=COLOR_NEW_BG,
            borderPad=4, leading=15, spaceAfter=2),

        "q_changed": S("q_changed",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=COLOR_CHANGED_TXT, backColor=COLOR_CHANGED_BG,
            borderPad=4, leading=15, spaceAfter=2),

        "q_deleted": S("q_deleted",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=COLOR_DELETED_TXT, backColor=COLOR_DELETED_BG,
            borderPad=4, leading=15, spaceAfter=2),

        "case": S("case",
            fontName="Helvetica-Oblique", fontSize=10,
            backColor=COLOR_CASE_BG,
            borderPad=3, leading=14, spaceAfter=2, leftIndent=10),

        "answer_correct": S("ans_correct",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=COLOR_CORRECT,
            leading=13, leftIndent=8, spaceAfter=1),

        "answer_normal": S("ans_normal",
            fontName="Helvetica", fontSize=10,
            leading=13, leftIndent=8, spaceAfter=1),

        "explanation": S("expl",
            fontName="Helvetica-Oblique", fontSize=9,
            textColor=colors.HexColor("#555555"),
            backColor=COLOR_EXPL_BG,
            borderPad=2, leading=12, leftIndent=16, spaceAfter=3),

        "tag": S("tag",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.white,
            leading=10),

        "section_header": S("sec_hdr",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=colors.HexColor("#888888"),
            leading=11, spaceBefore=6, spaceAfter=2),

        "file_banner": S("file_banner",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=colors.white,
            leading=16),
    }


# ─────────────────────────────────────────────
# PDF BUILDER
# ─────────────────────────────────────────────

def tag_table(label, bg_color, text_color=colors.white):
    """Small coloured tag pill."""
    style = ParagraphStyle("_tag", fontName="Helvetica-Bold",
                           fontSize=8, textColor=text_color, leading=10)
    t = Table([[Paragraph(label, style)]],
              colWidths=[28*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg_color),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def build_question_block(q, kind, styles, show_correct=True, show_explanation=True):
    """
    Build a list of flowables for one question.
    kind: "new" | "changed" | "deleted"
    """
    story = []

    csorszam     = q.get("csorszam", "???")
    leiras_text  = unescape(q.get("leirasPlaintext") or q.get("leiras") or "")
    esetleiras   = q.get("esetleiras")

    # ── Status tag + question heading ──
    tag_cfg = {
        "new":     ("🆕 NEW",     COLOR_NEW_BG,      COLOR_NEW_TXT),
        "changed": ("✏️ CHANGED",  COLOR_CHANGED_BG,  COLOR_CHANGED_TXT),
        "deleted": ("🗑 DELETED",  COLOR_DELETED_BG,  COLOR_DELETED_TXT),
    }
    tag_label, tag_bg, tag_fg = tag_cfg[kind]
    q_style = styles[f"q_{kind}"]

    heading_text = f"<b>{csorszam}:</b>  {leiras_text}"
    heading = Paragraph(heading_text, q_style)

    tag_para_style = ParagraphStyle("_tp", fontName="Helvetica-Bold",
                                    fontSize=8, textColor=tag_fg, leading=10)
    tag_cell = Table([[Paragraph(tag_label, tag_para_style)]],
                     colWidths=[32*mm])
    tag_cell.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), tag_bg),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
    ]))

    # Put tag + heading side by side
    header_table = Table([[tag_cell, heading]],
                         colWidths=[34*mm, None])
    header_table.setStyle(TableStyle([
        ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(KeepTogether([header_table]))

    # ── Case description ──
    if esetleiras:
        nev = unescape(esetleiras.get("nevPlaintext") or esetleiras.get("nev") or "")
        if nev:
            story.append(Paragraph(f"📋 {nev}", styles["case"]))

    # ── Answers (kerdesValasz) ──
    answers_kv = sorted(q.get("kerdesValasz", []),
                        key=lambda x: x.get("betujel", ""))
    if answers_kv:
        story.append(Paragraph("Answers:", styles["section_header"]))
        for ans in answers_kv:
            betujel   = ans.get("betujel", "?")
            szoveg    = unescape(ans.get("szovegPlaintext") or ans.get("szoveg") or "")
            is_correct= ans.get("helyes", 0) == 1
            expl      = unescape(ans.get("magyarazatPlaintext") or ans.get("magyarazat") or "")

            prefix = "✔" if (show_correct and is_correct) else "○"
            ans_style = styles["answer_correct"] if (show_correct and is_correct) else styles["answer_normal"]
            story.append(Paragraph(f"{prefix}  <b>{betujel})</b>  {szoveg}", ans_style))

            if show_explanation and expl:
                story.append(Paragraph(f"➔ {expl}", styles["explanation"]))

    # ── Elementary answers (kerdesElemiValasz) ──
    answers_ev = sorted(q.get("kerdesElemiValasz", []),
                        key=lambda x: str(x.get("szam", "")))
    if answers_ev:
        story.append(Paragraph("Elementary Answers:", styles["section_header"]))
        for ans in answers_ev:
            szam   = ans.get("szam", "?")
            szoveg = unescape(ans.get("szoveg") or "")
            story.append(Paragraph(f"  {szam}.  {szoveg}", styles["answer_normal"]))

    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.4,
                            color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 2*mm))
    return story


def make_header_footer(title, creation_date):
    """Returns header/footer functions for SimpleDocTemplate."""
    def on_page(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Header bar
        canvas.setFillColor(COLOR_HEADER_BG)
        canvas.rect(0, h - 22*mm, w, 22*mm, fill=1, stroke=0)

        canvas.setFont("Helvetica-Bold", 13)
        canvas.setFillColor(colors.white)
        canvas.drawString(15*mm, h - 14*mm, title)

        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 15*mm, h - 14*mm, f"Generated {creation_date}  |  {AUTHOR}")

        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawCentredString(w / 2, 10*mm,
            f"Page {doc.page}  |  Final Exam JSON Comparator v{VERSION}")
        canvas.restoreState()

    return on_page


def build_pdf(output_path, file_results, show_correct, show_explanation, pdf_title):
    creation_date = datetime.now().strftime("%d.%m.%Y  %H:%M")
    on_page = make_header_footer(pdf_title, creation_date)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=28*mm,
        bottomMargin=20*mm,
        leftMargin=15*mm,
        rightMargin=15*mm,
    )

    styles = build_styles()
    story  = []

    # Cover summary
    total_new     = sum(len(r["new"])     for r in file_results)
    total_changed = sum(len(r["changed"]) for r in file_results)
    total_deleted = sum(len(r["deleted"]) for r in file_results)

    cover_style = ParagraphStyle("cover", fontName="Helvetica",
                                 fontSize=11, leading=16)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f"<b>Summary:</b>  "
        f"🆕 {total_new} new  &nbsp;&nbsp;  "
        f"✏️ {total_changed} changed  &nbsp;&nbsp;  "
        f"🗑 {total_deleted} deleted",
        cover_style
    ))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=COLOR_HEADER_BG))
    story.append(Spacer(1, 4*mm))

    any_questions = False

    for result in file_results:
        fname   = result["file"]
        new_qs  = result["new"]
        chg_qs  = result["changed"]
        del_qs  = result["deleted"]

        all_q = (
            [("new",     q) for q in new_qs]  +
            [("changed", q) for q in chg_qs]  +
            [("deleted", q) for q in del_qs]
        )

        if not all_q:
            continue

        any_questions = True

        # File banner
        banner_style = ParagraphStyle("banner", fontName="Helvetica-Bold",
                                      fontSize=12, textColor=colors.white,
                                      leading=15)
        banner_cell  = Paragraph(f"📁  {fname}", banner_style)
        counts_style = ParagraphStyle("cnts", fontName="Helvetica",
                                      fontSize=9, textColor=colors.HexColor("#CCCCCC"),
                                      leading=12)
        counts_cell  = Paragraph(
            f"🆕 {len(new_qs)} new   ✏️ {len(chg_qs)} changed   🗑 {len(del_qs)} deleted",
            counts_style)

        banner = Table([[banner_cell], [counts_cell]],
                       colWidths=[doc.width])
        banner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), COLOR_HEADER_BG),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ]))
        story.append(banner)
        story.append(Spacer(1, 4*mm))

        for kind, q in all_q:
            block = build_question_block(
                q, kind, styles,
                show_correct=show_correct,
                show_explanation=show_explanation
            )
            story.extend(block)

        story.append(Spacer(1, 6*mm))

    if not any_questions:
        story.append(Paragraph(
            "✅  No differences found across all scanned files.",
            ParagraphStyle("none", fontName="Helvetica", fontSize=12,
                           textColor=colors.green, leading=16)
        ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def banner():
    print("=" * 55)
    print("  FINAL EXAM JSON COMPARATOR  v" + VERSION)
    print("  by " + AUTHOR)
    print("=" * 55)
    print("  Detects: new / changed / deleted questions")
    print("  Checks:  kerdesValasz + kerdesElemiValasz")
    print("=" * 55)


def main():
    banner()
    input("\nPress Enter to continue …\n")

    print("Enter folder paths (press Enter for defaults):")
    old_folder = input("  Old folder [Scrape1]: ").strip().rstrip("/\\") or "Scrape1"
    new_folder = input("  New folder [Scrape2]: ").strip().rstrip("/\\") or "Scrape2"

    print(f"\n  Old → {old_folder}")
    print(f"  New → {new_folder}")
    print("=" * 55)

    if not os.path.isdir(old_folder):
        print(f"\n[ERROR] Folder not found: {old_folder}")
        sys.exit(1)
    if not os.path.isdir(new_folder):
        print(f"\n[ERROR] Folder not found: {new_folder}")
        sys.exit(1)

    ensure_dirs()

    print("\n🔍 Scanning files …")
    file_results = compare_folders(old_folder, new_folder)

    # Save diff JSONs
    print("\n💾 Saving JSON diffs …")
    for r in file_results:
        all_diffs = r["new"] + r["changed"] + r["deleted"]
        if all_diffs:
            name = os.path.splitext(r["file"])[0]
            save_diff_json(name, {
                "new":     r["new"],
                "changed": r["changed"],
                "deleted": r["deleted"],
            })

    # Build PDFs
    print("\n📄 Building PDFs …")

    diff_path     = "Differences_Combined.pdf"
    exercise_path = "Exercise_Combined.pdf"

    build_pdf(
        diff_path, file_results,
        show_correct=True,
        show_explanation=True,
        pdf_title="Question Differences"
    )
    print(f"  ✅ {diff_path}")

    # Exercise PDF: only new + changed questions, no correct highlighting
    exercise_results = [
        {**r, "deleted": []}   # exclude deleted from exercise
        for r in file_results
    ]
    build_pdf(
        exercise_path, exercise_results,
        show_correct=False,
        show_explanation=False,
        pdf_title="Question Differences — Exercise (no answers)"
    )
    print(f"  ✅ {exercise_path}")

    print("\n" + "=" * 55)
    print("  🏁 All done!")
    print("=" * 55)


if __name__ == "__main__":
    main()
