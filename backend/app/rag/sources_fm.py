"""Exam FM corpus configuration.

Chapter page ranges are PDF page indices (1-based), derived from each book's
printed-page numbering plus a fixed front-matter offset verified against the
actual source files (spot-checked at both an early and a late chapter, not
just the first):
  Chan    pdf_page = printed_page + 19
  Vaaler  pdf_page = printed_page + 17

Topic tags are one of the five official SOA Exam FM syllabus topics (2026-06
syllabus): Time Value of Money, Annuities, Loans, Bonds, and General Cash
Flows/Portfolios/ALM. Tagging is chapter-level, matching sources_p.py's
approach -- retrieval relies primarily on embedding similarity, so a coarse
tag is sufficient without hand-mapping every subsection.

Per the syllabus's exact text-reference list, only these chapters are
ingested (sub-section exclusions within an included chapter are NOT sliced
out, same coarse-chapter-granularity precedent as sources_p.py's Hogg):
  Chan (Financial Mathematics for Actuaries, 3rd ed.):
    chapters 1-8 only (1 full; 2 excl 2.4; 3 excl 3.5; 4 excl 4.2/4.5;
    5 excl 5.3; 6 excl 6.4; 7 full; 8 excl 8.6-8.8). Nothing beyond ch. 8
    (chapters 9-10 and appendices are out of syllabus scope).
  Vaaler (Mathematical Interest Theory, 3rd ed.):
    chapters 1-6, 8 (8.3 ONLY -- not the whole chapter), 9. Chapter 7
    ("Stocks and financial markets") is skipped entirely -- not in the
    syllabus's reading list at all.

A third PDF in fm/ (labeled "Ruckman") was found NOT to be the syllabus-
listed Francis/Ruckman text (different title/edition, same authors) and is
deliberately excluded -- see conversation history. FM's corpus is Chan +
Vaaler only.
"""

from app.rag.book_source import BookSource, Chapter

TIME_VALUE_OF_MONEY = "Time Value of Money"
ANNUITIES = "Annuities"
LOANS = "Loans"
BONDS = "Bonds"
GENERAL_CASH_FLOWS_PORTFOLIOS_ALM = "General Cash Flows, Portfolios, and Asset Liability Management"

# Midpoints of the June 2026 Exam FM syllabus's published weight ranges:
# Time Value of Money 5-15%, Annuities 20-30%, Loans 15-25%, Bonds 15-25%,
# General Cash Flows/Portfolios/ALM 20-30%.
TOPIC_WEIGHTS = {
    TIME_VALUE_OF_MONEY: 10.0,
    ANNUITIES: 25.0,
    LOANS: 20.0,
    BONDS: 20.0,
    GENERAL_CASH_FLOWS_PORTFOLIOS_ALM: 25.0,
}

TOPIC_NAMES = [TIME_VALUE_OF_MONEY, ANNUITIES, LOANS, BONDS, GENERAL_CASH_FLOWS_PORTFOLIOS_ALM]


CHAN = BookSource(
    key="chan",
    title="Financial Mathematics for Actuaries",
    file_name="Financial mathematics for actuaries- 3rd ed. - Chan.pdf",
    chapters=(
        Chapter(1, "Interest Accumulation and Time Value of Money", 20, 57, TIME_VALUE_OF_MONEY),
        Chapter(2, "Annuities", 58, 91, ANNUITIES),
        Chapter(3, "Spot Rates, Forward Rates and the Term Structure", 92, 123, GENERAL_CASH_FLOWS_PORTFOLIOS_ALM),
        Chapter(4, "Rates of Return", 124, 165, GENERAL_CASH_FLOWS_PORTFOLIOS_ALM),
        Chapter(5, "Loans and Costs of Borrowing", 166, 205, LOANS),
        Chapter(6, "Bonds and Bond Pricing", 206, 231, BONDS),
        Chapter(7, "Bond Yields and the Term Structure", 232, 263, BONDS),
        Chapter(8, "Bond Management", 264, 309, GENERAL_CASH_FLOWS_PORTFOLIOS_ALM),
    ),
)

VAALER = BookSource(
    key="vaaler",
    title="Mathematical Interest Theory",
    file_name="Mathematical Interest Theory - 3rd Ed - Vaaler.pdf",
    chapters=(
        Chapter(1, "The Growth of Money", 26, 99, TIME_VALUE_OF_MONEY),
        Chapter(2, "Equations of Value and Yield Rates", 100, 137, TIME_VALUE_OF_MONEY),
        Chapter(3, "Annuities (Annuities Certain)", 138, 211, ANNUITIES),
        Chapter(4, "Annuities with Different Payment and Conversion Periods", 212, 245, ANNUITIES),
        Chapter(5, "Loan Repayment", 246, 281, LOANS),
        Chapter(6, "Bonds", 282, 343, BONDS),
        # Only section 8.3 (The term structure of interest rates, printed
        # pp.355-365) -- NOT the whole chapter, per the syllabus.
        Chapter(8, "The Term Structure of Interest Rates (8.3 only)", 372, 382, GENERAL_CASH_FLOWS_PORTFOLIOS_ALM),
        Chapter(9, "Interest Rate Sensitivity", 466, 519, GENERAL_CASH_FLOWS_PORTFOLIOS_ALM),
    ),
)

SOURCES: tuple[BookSource, ...] = (CHAN, VAALER)
