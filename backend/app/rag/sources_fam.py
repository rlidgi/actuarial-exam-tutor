"""Exam FAM corpus configuration.

Chapter page ranges are PDF page indices (1-based), derived from each book's
printed-page numbering plus a fixed front-matter offset verified against the
actual source files (spot-checked at both an early and a late chapter, not
just the first):
  Loss Models  pdf_page = printed_page + 17
  Dickson      pdf_page = printed_page + 26
  Brown        pdf_page = printed_page + 14

Topic tags are one of the ten official SOA Exam FAM syllabus topics (2026-07
syllabus). Tagging is chapter-level, matching sources_p.py/sources_fm.py's
approach -- retrieval relies primarily on embedding similarity, so a coarse
tag is sufficient without hand-mapping every subsection.

Two edition/book notes, both resolved with the user before this corpus was
built (see conversation history):
  - Dickson: the syllabus requires the Third Edition (2020,
    ISBN 978-1-108-47808-3) -- the file originally in fam/ was the First
    Edition (2009), whose chapter numbering/content doesn't correspond to
    the syllabus's own chapter references at all (e.g. its "Chapter 16"
    citation doesn't exist in the 1st edition, which only has 14 chapters).
    Replaced with the correct 3rd edition before this module was written.
  - Brown ("Introduction to Ratemaking and Loss Reserving for Property and
    Casualty Insurance"): the syllabus cites the 5th edition (2022, Brown &
    Lennox). What's available is the 3rd edition (2007, Brown & Gottlieb,
    ISBN 978-1-56698-611-3) -- used anyway per explicit user instruction,
    limited to chapters 1-4 (ratemaking/reserving fundamentals are far more
    stable across editions of this specific book than Dickson's content
    was). Chapter 5 (including its Reinsurance section) is NOT ingested,
    so Topic 1(d)/(e) (reinsurance mechanics specifically) has no textbook
    citation available -- the tutor answers from general knowledge there,
    same fallback as any topic with no retrieval match.
"""

from app.rag.book_source import BookSource, Chapter

SHORT_TERM_INSURANCE_REINSURANCE = "Short-Term Insurance and Reinsurance Coverages"
SEVERITY_FREQUENCY_AGGREGATE_MODELS = "Severity, Frequency, and Aggregate Models"
PARAMETRIC_ESTIMATION = "Parametric Estimation"
INTRODUCTION_TO_CREDIBILITY = "Introduction to Credibility"
PRICING_RESERVING_SHORT_TERM = "Pricing and Reserving for Short-Term Insurance Coverages"
OPTION_PRICING_FUNDAMENTALS = "Option Pricing Fundamentals"
LONG_TERM_INSURANCE_RETIREMENT = "Long-Term Insurance Coverages and Retirement Financial Security Programs"
MORTALITY_MODELS = "Mortality Models"
PV_RANDOM_VARIABLES_LONG_TERM = "Present Value Random Variables for Long-Term Insurance Coverages"
PREMIUM_POLICY_VALUE_LONG_TERM = "Premium and Policy Value Calculation for Long-Term Insurance Coverages"

# Midpoints of the July 2026 Exam FAM syllabus's published weight ranges.
TOPIC_WEIGHTS = {
    SHORT_TERM_INSURANCE_REINSURANCE: 7.5,
    SEVERITY_FREQUENCY_AGGREGATE_MODELS: 15.0,
    PARAMETRIC_ESTIMATION: 5.0,
    INTRODUCTION_TO_CREDIBILITY: 3.75,
    PRICING_RESERVING_SHORT_TERM: 12.5,
    OPTION_PRICING_FUNDAMENTALS: 5.0,
    LONG_TERM_INSURANCE_RETIREMENT: 3.75,
    MORTALITY_MODELS: 12.5,
    PV_RANDOM_VARIABLES_LONG_TERM: 16.25,
    PREMIUM_POLICY_VALUE_LONG_TERM: 18.75,
}

TOPIC_NAMES = [
    SHORT_TERM_INSURANCE_REINSURANCE,
    SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    PARAMETRIC_ESTIMATION,
    INTRODUCTION_TO_CREDIBILITY,
    PRICING_RESERVING_SHORT_TERM,
    OPTION_PRICING_FUNDAMENTALS,
    LONG_TERM_INSURANCE_RETIREMENT,
    MORTALITY_MODELS,
    PV_RANDOM_VARIABLES_LONG_TERM,
    PREMIUM_POLICY_VALUE_LONG_TERM,
]


LOSS_MODELS = BookSource(
    key="lossmodels",
    title="Loss Models: From Data to Decisions",
    file_name="Textbook_loss_models_from_data_to_decisions-Fifth Edition.pdf",
    chapters=(
        Chapter(3, "Basic Distributional Quantities", 38, 67, SEVERITY_FREQUENCY_AGGREGATE_MODELS),
        Chapter(4, "Characteristics of Actuarial Models", 68, 77, SEVERITY_FREQUENCY_AGGREGATE_MODELS),
        Chapter(5, "Continuous Models", 78, 97, SEVERITY_FREQUENCY_AGGREGATE_MODELS),
        Chapter(6, "Discrete Distributions", 98, 115, SEVERITY_FREQUENCY_AGGREGATE_MODELS),
        Chapter(8, "Frequency and Severity with Coverage Modifications", 142, 163, SHORT_TERM_INSURANCE_REINSURANCE),
        Chapter(9, "Aggregate Loss Models", 164, 217, SEVERITY_FREQUENCY_AGGREGATE_MODELS),
        Chapter(11, "Maximum Likelihood Estimation", 246, 271, PARAMETRIC_ESTIMATION),
        Chapter(12, "Frequentist Estimation for Discrete Distributions", 272, 291, PARAMETRIC_ESTIMATION),
        Chapter(16, "Introduction to Limited Fluctuation Credibility", 404, 417, INTRODUCTION_TO_CREDIBILITY),
    ),
)

DICKSON = BookSource(
    key="dickson",
    title="Actuarial Mathematics for Life Contingent Risks",
    file_name="Actuarial Mathematics for Life Contingent Risk - Dickson.pdf",
    chapters=(
        Chapter(1, "Introduction to Life and Long-Term Health Insurance", 27, 59, LONG_TERM_INSURANCE_RETIREMENT),
        Chapter(2, "Survival Models", 60, 83, MORTALITY_MODELS),
        Chapter(3, "Life Tables and Selection", 84, 129, MORTALITY_MODELS),
        Chapter(4, "Insurance Benefits", 130, 166, PV_RANDOM_VARIABLES_LONG_TERM),
        Chapter(5, "Annuities", 167, 204, PV_RANDOM_VARIABLES_LONG_TERM),
        Chapter(6, "Premium Calculation", 205, 243, PREMIUM_POLICY_VALUE_LONG_TERM),
        Chapter(7, "Policy Values", 244, 311, PREMIUM_POLICY_VALUE_LONG_TERM),
        Chapter(16, "Option Pricing", 626, 654, OPTION_PRICING_FUNDAMENTALS),
    ),
)

# 3rd edition (Brown & Gottlieb) -- see module docstring for why, and for
# the resulting Topic 1(d)/(e) reinsurance gap. Chapters 1-4 only.
BROWN = BookSource(
    key="brown",
    title="Introduction to Ratemaking and Loss Reserving for Property and Casualty Insurance",
    file_name="Introduction to Ratemaking and Loss Reserving for Property and Casualty Insurance 3rd Edition ( PDFDrive ).pdf",
    chapters=(
        Chapter(1, "Why Insurance?", 15, 36, SHORT_TERM_INSURANCE_REINSURANCE),
        Chapter(2, "Coverages", 37, 64, SHORT_TERM_INSURANCE_REINSURANCE),
        Chapter(3, "Ratemaking", 65, 124, PRICING_RESERVING_SHORT_TERM),
        Chapter(4, "Loss Reserving", 125, 172, PRICING_RESERVING_SHORT_TERM),
    ),
)

SOURCES: tuple[BookSource, ...] = (LOSS_MODELS, DICKSON, BROWN)
