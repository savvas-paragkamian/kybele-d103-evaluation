"""Draw the specialist spot-check sample from the KYBELE trait benchmark and write it as a workbook.

Stratified random sample, proportional to the question types of the benchmark (fixed seed, so the
draw can be repeated): 12 body size, 12 habitat, 1 trophic guild = 25 of 126 questions.

Usage: python3 scripts/make_spotcheck.py data/benchmark_traits.csv spotcheck/
Writes spotcheck/spotcheck_sample.csv and spotcheck/KYBELE_D10.3_specialist_spotcheck.xlsx
"""

import csv
import random
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

SEED = 20260928
QUOTA = {"body_size": 12, "habitat": 12, "trophic_guild": 1}
TRAIT_LABEL = {"body_size": "Body size", "habitat": "Habitat", "trophic_guild": "Trophic guild"}
VERDICTS = ["Correct", "Partly correct", "Wrong", "Cannot judge"]

FONT = "Arial"
F = Font(name=FONT, size=10)
FB = Font(name=FONT, size=10, bold=True)
FH = Font(name=FONT, size=10, bold=True, color="FFFFFF")
FT = Font(name=FONT, size=14, bold=True)
FLINK = Font(name=FONT, size=10, color="0563C1", underline="single")
HEAD_FILL = PatternFill("solid", fgColor="1F4E79")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")   # cells the reviewer fills in
GREY_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")


def draw(rows):
    rng = random.Random(SEED)
    sample = []
    for qt, k in QUOTA.items():
        pool = sorted((r for r in rows if r["question_type"] == qt), key=lambda r: r["qid"])
        sample += rng.sample(pool, k)
    return sorted(sample, key=lambda r: r["qid"])


def tidy(context):
    """Cut the partial words at the edges of the passage window and mark the cuts."""
    c = context.strip()
    if c and not (c[0].isupper() or c[0].isdigit()):
        c = "… " + c.split(" ", 1)[-1]
    if c and c[-1] not in ".;:)":
        c = c.rsplit(" ", 1)[0] + " …"
    return c


def passage_rich(context, gold):
    """The passage with the gold answer (longest alternative found in it) in bold."""
    context = tidy(context)
    alts = sorted((a.strip() for a in gold.split("||") if a.strip()), key=len, reverse=True)
    for a in alts:
        i = context.find(a)
        if i >= 0:
            return CellRichText(context[:i], TextBlock(InlineFont(rFont=FONT, sz=10, b=True), a),
                                context[i + len(a):])
    return context


def build(sample, out):
    wb = Workbook()

    # --- Instructions -------------------------------------------------------------------
    ws = wb.active
    ws.title = "Instructions"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 95
    ws["B2"] = "KYBELE D10.3 - specialist spot-check of the Collembola trait benchmark"
    ws["B2"].font = FT
    lines = [
        ("Purpose", "The benchmark has 126 questions on body size, habitat and trophic guild, each with a gold "
                    "answer taken from a Plazi taxonomic treatment. The gold answers were checked with AI "
                    "assistance. This sheet asks a Collembola specialist to check a random sample of 25, so the "
                    "deliverable can report expert agreement."),
        ("What to check", "For each row, is the gold answer what the treatment states for this species? The passage "
                          "column shows the text around the answer (answer in bold); open the Plazi link if the "
                          "passage is not enough."),
        ("Where to write", "Only the yellow columns on the 'Spot-check' sheet: Verdict (drop-down), Correct answer "
                           "(if different) and Comment. The 'Summary' sheet counts the verdicts by itself."),
        ("Gold answer format", "Alternatives that are all acceptable are separated by '||', e.g. "
                               "'0.88 mm || up to 0.88 mm'. Body sizes are body length in mm."),
        ("Correct", "The gold answer states what the treatment says about this species (all alternatives are fine)."),
        ("Partly correct", "Right but incomplete or too broad, e.g. only one of two habitats, or a size range where "
                           "the treatment gives separate male and female values."),
        ("Wrong", "The treatment says something else, or the answer belongs to another taxon, life stage or "
                  "measurement (e.g. antenna length instead of body length), or a habitat answer is only a place."),
        ("Cannot judge", "The treatment does not let you decide."),
        ("Sample", f"Stratified random draw, proportional to the benchmark: 12 body size, 12 habitat, 1 trophic "
                   f"guild (seed {SEED}; scripts/make_spotcheck.py). Trophic guilds get their own spot-check "
                   f"on the separate trophic benchmark."),
        ("Time needed", "About 1-2 minutes per row, 30-50 minutes in total."),
        ("Reviewer", ""),
        ("Date", ""),
    ]
    r = 4
    for k, v in lines:
        ws.cell(r, 2, k).font = FB
        c = ws.cell(r, 3, v)
        c.font = F
        c.alignment = WRAP
        if k in ("Reviewer", "Date"):
            c.fill = INPUT_FILL
            c.border = BOX
        r += 1
    ws["B3"].font = F
    r += 1
    ws.cell(r, 2, "Example of a filled row (not part of the sample)").font = FB
    r += 1
    ex_head = ["Gold answer", "Verdict", "Correct answer (if different)", "Comment"]
    ex_val = ["1.2 mm || up to 1.2 mm", "Partly correct", "1.2 mm (female), 0.9 mm (male)",
              "The treatment gives separate values for the two sexes."]
    for i, (h, v) in enumerate(zip(ex_head, ex_val)):
        ws.cell(r + i, 2, h).font = F
        c = ws.cell(r + i, 3, v)
        c.font = F
        c.fill = GREY_FILL
        c.border = BOX
    for row in ws.iter_rows(min_row=4, max_row=r + 4):
        for c in row:
            c.alignment = WRAP
    for rr in range(4, 4 + len(lines)):  # explicit heights: not every viewer auto-fits wrapped rows
        ws.row_dimensions[rr].height = 14 * max(1, -(-len(str(ws.cell(rr, 3).value or "")) // 100)) + 4

    # --- Spot-check ---------------------------------------------------------------------
    sc = wb.create_sheet("Spot-check")
    heads = ["#", "QID", "Trait", "Species", "Question", "Gold answer", "Passage from the treatment (gold answer in bold)",
             "Plazi treatment", "Verdict", "Correct answer (if different)", "Comment"]
    widths = [4, 7, 12, 24, 30, 24, 70, 14, 15, 26, 30]
    for j, (h, w) in enumerate(zip(heads, widths), 1):
        c = sc.cell(1, j, h)
        c.font = FH
        c.fill = HEAD_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BOX
        sc.column_dimensions[c.column_letter].width = w
    sc.row_dimensions[1].height = 30
    for i, s in enumerate(sample, 1):
        uri = s["treatment_uri"].replace("http://", "https://")
        vals = [i, s["qid"], TRAIT_LABEL[s["question_type"]], s["taxon"], s["question"],
                s["gold_answer"].replace(" || ", "  ||  "), passage_rich(s["gold_context"], s["gold_answer"]),
                "Open treatment", None, None, None]
        for j, v in enumerate(vals, 1):
            c = sc.cell(i + 1, j, v)
            c.font = F
            c.alignment = WRAP
            c.border = BOX
            if j >= 9:
                c.fill = INPUT_FILL
        link = sc.cell(i + 1, 8)
        link.hyperlink = uri
        link.font = FLINK
        sc.cell(i + 1, 4).font = Font(name=FONT, size=10, italic=True)
        sc.row_dimensions[i + 1].height = max(60, 13 * -(-len(tidy(s["gold_context"])) // 80) + 8)
    n = len(sample)
    dv = DataValidation(type="list", formula1='"' + ",".join(VERDICTS) + '"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Verdict", error="Pick one of: " + ", ".join(VERDICTS))
    dv.add(f"I2:I{n + 1}")
    sc.add_data_validation(dv)
    sc.freeze_panes = "E2"
    sc.auto_filter.ref = f"A1:K{n + 1}"
    sc.cell(1, 9).comment = Comment("Pick from the drop-down: " + ", ".join(VERDICTS), "KYBELE")

    # --- Summary ------------------------------------------------------------------------
    sm = wb.create_sheet("Summary")
    sm.sheet_view.showGridLines = False
    sm.column_dimensions["A"].width = 3
    sm.column_dimensions["B"].width = 30
    for col in "CDEF":
        sm.column_dimensions[col].width = 15
    sm["B2"] = "Summary (calculated from the Spot-check sheet)"
    sm["B2"].font = FT
    cols = ["All", "Body size", "Habitat", "Trophic guild"]
    for j, h in enumerate(cols, 3):
        c = sm.cell(4, j, h)
        c.font = FH
        c.fill = HEAD_FILL
        c.border = BOX
    sm.cell(4, 2, "Verdict").font = FH
    sm.cell(4, 2).fill = HEAD_FILL
    rng_v = f"'Spot-check'!$I$2:$I${n + 1}"
    rng_t = f"'Spot-check'!$C$2:$C${n + 1}"
    labels = ["Items in sample"] + VERDICTS + ["Not yet reviewed", "Agreement (Correct / judged)",
                                               "Agreement incl. partly correct"]
    for i, lab in enumerate(labels):
        row = 5 + i
        sm.cell(row, 2, lab).font = FB if i in (0, 6, 7) else F
        for j, trait in enumerate(cols, 3):
            L = sm.cell(row, j).column_letter
            crit = "" if trait == "All" else f',{rng_t},"{trait}"'
            if lab == "Items in sample":
                f = f"=ROWS({rng_v})" if trait == "All" else f'=COUNTIF({rng_t},"{trait}")'
            elif lab in VERDICTS:
                f = f'=COUNTIFS({rng_v},"{lab}"{crit})'
            elif lab == "Not yet reviewed":
                f = f"={L}5-{L}6-{L}7-{L}8-{L}9"
            elif lab == "Agreement (Correct / judged)":
                f = f'=IFERROR({L}6/({L}6+{L}7+{L}8),"-")'
            else:
                f = f'=IFERROR(({L}6+{L}7)/({L}6+{L}7+{L}8),"-")'
            c = sm.cell(row, j, f)
            c.font = F
            c.border = BOX
            if lab.startswith("Agreement"):
                c.number_format = "0%"
        sm.cell(row, 2).border = BOX
    sm.cell(14, 2, "'Judged' = Correct + Partly correct + Wrong; 'Cannot judge' is left out of the agreement.").font = \
        Font(name=FONT, size=9, italic=True)

    for sheet in (ws, sc, sm):
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sc.print_title_rows = "1:1"

    wb.active = 1
    out.mkdir(parents=True, exist_ok=True)
    path = out / "KYBELE_D10.3_specialist_spotcheck.xlsx"
    wb.save(path)
    return path


def main(bench_path, out_dir):
    rows = list(csv.DictReader(open(bench_path, encoding="utf-8")))
    sample = draw(rows)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "spotcheck_sample.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "qid", "question_type", "taxon", "question", "gold_answer", "treatment_uri"])
        for i, s in enumerate(sample, 1):
            w.writerow([i, s["qid"], s["question_type"], s["taxon"], s["question"], s["gold_answer"],
                        s["treatment_uri"]])
    print(build(sample, out), len(sample), "items")


if __name__ == "__main__":
    main(*sys.argv[1:])
