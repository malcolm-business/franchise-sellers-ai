#!/usr/bin/env python3
"""Build the fillable ICP review PDF for Eric.

A real AcroForm PDF (typeable text fields) explaining — in plain English — what an
Ideal Customer Profile is, showing our current draft per brand, and asking Eric to
refine it. He types in the boxes (any PDF reader), saves, and emails it back.

    pip install reportlab
    python3 scripts/icp/build_icp_pdf.py
-> cold-email-outbound/docs/ICP-REVIEW-ERIC.pdf
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

FIELD_BORDER = Color(0.70, 0.75, 0.80)
FIELD_BG = Color(0.98, 0.99, 1.0)
FIELD_TEXT = Color(0, 0, 0)

OUT = Path(__file__).resolve().parents[2] / "docs" / "ICP-REVIEW-ERIC.pdf"
W, H = letter
ML, MR = 54, 54                      # left / right margins
TOP, BOT = H - 54, 60
TEAL = (0.05, 0.58, 0.53)
FS_RED = (0.86, 0.15, 0.15)
CS_BLUE = (0.23, 0.51, 0.96)
DARK = (0.10, 0.13, 0.18)
GREY = (0.36, 0.40, 0.46)
LIGHT = (0.90, 0.93, 0.96)


class Doc:
    def __init__(self, c):
        self.c = c
        self.y = TOP
        self.field = 0

    def _room(self, need):
        if self.y - need < BOT:
            self.c.showPage()
            self.y = TOP

    def para(self, text, size=10.5, color=DARK, lead=14, gap=6, bold=False):
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.c.setFillColorRGB(*color)
        for line in simpleSplit(text, "Helvetica-Bold" if bold else "Helvetica", size, W - ML - MR):
            self._room(lead)
            self.c.drawString(ML, self.y, line)
            self.y -= lead
        self.y -= gap

    def h1(self, text):
        self._room(34)
        self.c.setFillColorRGB(*TEAL)
        self.c.setFont("Helvetica-Bold", 20)
        self.c.drawString(ML, self.y, text)
        self.y -= 26

    def band(self, text, color):
        self._room(34)
        self.c.setFillColorRGB(*color)
        self.c.roundRect(ML, self.y - 22, W - ML - MR, 26, 6, fill=1, stroke=0)
        self.c.setFillColorRGB(1, 1, 1)
        self.c.setFont("Helvetica-Bold", 13)
        self.c.drawString(ML + 12, self.y - 14, text)
        self.y -= 36

    def rule(self):
        self._room(12)
        self.c.setStrokeColorRGB(*LIGHT)
        self.c.line(ML, self.y, W - ML, self.y)
        self.y -= 14

    def question(self, q, height=58, hint=""):
        self.para(q, size=11, color=DARK, lead=14, gap=4, bold=True)
        self._room(height + 8)
        self.field += 1
        self.c.acroForm.textfield(
            name=f"f{self.field}", tooltip=hint or q,
            x=ML, y=self.y - height, width=W - ML - MR, height=height,
            borderWidth=1, borderColor=FIELD_BORDER, fillColor=FIELD_BG,
            textColor=FIELD_TEXT, fontSize=10, fieldFlags="multiline",
        )
        self.y -= height + 14


QUESTIONS = [
    ("1. Which industries or business types are the BEST fits — and are there any we should avoid?",
     "List the industries that make great sellers, and any to steer clear of."),
    ("2. What size is the sweet spot? (Roughly how many employees / how much yearly revenue — and what's too small or too big?)",
     "e.g. 'best around 10-40 staff and $2-15M; under $1M is usually too small.'"),
    ("3. What makes a GREAT seller (one we really want), versus one that just barely qualifies?",
     "What separates an ideal seller from an okay one?"),
    ("4. What usually makes an owner decide to sell? (retirement, burnout, health, partner split, market timing, an unsolicited offer...)",
     "The real-life triggers that get an owner to the table."),
    ("5. What are their biggest worries or objections about selling?",
     "What makes them hesitate, and what reassures them?"),
    ("6. What message or angle lands best with this kind of owner?",
     "How should we open the conversation so it resonates?"),
    ("7. Anything here we have WRONG, or anything important we're missing?",
     "Correct our assumptions or add what we left out."),
]


def brand_block(d, title, color, plain):
    d.band(title, color)
    d.para("Who we think we're targeting today:", size=10.5, bold=True, gap=3)
    d.para(plain, size=10.5, color=GREY, gap=10)
    for q, hint in QUESTIONS:
        d.question(q, height=54, hint=hint)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Ideal Customer Profile — Review & Refine")
    d = Doc(c)

    d.h1("Ideal Customer Profile — Your Review")
    d.para("Franchise Sellers  &  Company Sellers", size=11, color=GREY, gap=12, bold=True)

    d.para("What is this?", size=12, color=TEAL, bold=True, gap=4)
    d.para("An \"Ideal Customer Profile\" (ICP) is just a short description of our perfect-fit customer — "
           "the kind of business owner we most want to reach with our marketing. The clearer we are about who "
           "that is, the better our outreach works and the less time we waste on the wrong people.", gap=8)
    d.para("We've written a first draft for each of our two brands, based on the rules we use today. You know "
           "these sellers better than anyone, so we'd love your help sharpening it.", gap=8)
    d.para("How to use this form:", size=11, color=TEAL, bold=True, gap=4)
    d.para("Read each brand's draft below, then type your thoughts into the boxes (you can type directly in this "
           "PDF in any reader — Acrobat, Preview, or a browser). When you're done, choose File > Save and email it "
           "back to Theodore. That's it — no logins, nothing to install.", gap=6)
    d.para("Your name and the date (optional):", size=10.5, bold=True, gap=3)
    d.field += 1
    c.acroForm.textfield(name="who", tooltip="Your name / date", x=ML, y=d.y - 22,
                         width=W - ML - MR, height=22, borderWidth=1, borderColor=FIELD_BORDER,
                         fillColor=FIELD_BG, textColor=FIELD_TEXT, fontSize=10)
    d.y -= 34
    d.rule()

    brand_block(
        d, "FRANCHISE SELLERS  (FS)", FS_RED,
        "Franchise Sellers helps franchise owners sell their franchise business. Right now we aim for a "
        "U.S.-based owner who currently runs their franchise (not retired, and hasn't already sold it), "
        "operating up to about 25 locations. Any franchise industry is currently in scope.",
    )

    c.showPage(); d.y = TOP
    brand_block(
        d, "COMPANY SELLERS  (CS)", CS_BLUE,
        "Company Sellers helps owners of private, independent (non-franchise) businesses sell. Right now we aim "
        "for a U.S.-based owner who currently runs a privately-held business (not private-equity-owned or "
        "publicly traded), that has been operating 3+ years, with up to about 50 employees and up to about "
        "$25M in yearly revenue, and 3 or fewer owners.",
    )

    d.rule()
    d.para("Thank you! When you're finished: File > Save, then email this back to Theodore "
           "(theodore@franchisesellers.com).", size=10.5, color=TEAL, bold=True)

    c.save()
    print(f"Wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
