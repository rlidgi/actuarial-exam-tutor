"""
The learning-outcome-level topics under Exam FM's 5 syllabus sections,
transcribed from the official June 2026 syllabus (2026-06-exam-fm-syllabus.pdf).

This is the single source of truth for granular topic seeding
(scripts/seed_learning_outcomes.py) and for the tool-schema enum
(tools/openai_tools.py) that constrains what the model can report mastery
against. `description` is the syllabus's own wording (condensed where one
lettered/bulleted syllabus item was split into multiple outcomes here);
`name` is a short label derived from it for use in enums, prompts, and the
dashboard UI, since the full wording is too long for either.

Per-outcome exam_weight is NOT published by the syllabus -- only per-section
ranges are. Weights here are the section's weight midpoint split evenly
across its outcomes, same approximation approach as exam_syllabus_p.py.
"""

from dataclasses import dataclass

from app.rag.sources_fm import (
    ANNUITIES,
    BONDS,
    GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    LOANS,
    TIME_VALUE_OF_MONEY,
    TOPIC_WEIGHTS,
)


@dataclass(frozen=True)
class LearningOutcome:
    name: str
    description: str
    category: str


TIME_VALUE_OF_MONEY_OUTCOMES = [
    LearningOutcome(
        "Time Value of Money Definitions",
        "Define and recognize the definitions of: interest rate, simple interest, compound "
        "interest, accumulation function, future value, current value, present value, net "
        "present value, discount factor, discount rate, convertible m-thly, nominal rate, "
        "effective rate, inflation and real rate of interest, force of interest, equation of value.",
        TIME_VALUE_OF_MONEY,
    ),
    LearningOutcome(
        "Solving for a Missing TVM Item",
        "Given any three of interest rate, period of time, present value, and future value, "
        "calculate the remaining item using simple or compound interest. Solve time value of "
        "money equations involving variable force of interest.",
        TIME_VALUE_OF_MONEY,
    ),
    LearningOutcome(
        "Interest and Discount Rate Conversions",
        "Given any one of the effective interest rate, the nominal interest rate convertible "
        "m-thly, the effective discount rate, the nominal discount rate convertible m-thly, or "
        "the force of interest, calculate any of the other items.",
        TIME_VALUE_OF_MONEY,
    ),
    LearningOutcome(
        "Equation of Value",
        "Write the equation of value given a set of cash flows and an interest rate.",
        TIME_VALUE_OF_MONEY,
    ),
]

ANNUITIES_OUTCOMES = [
    LearningOutcome(
        "Annuity Definitions",
        "Define and recognize the definitions of: annuity-immediate, annuity due, perpetuity, "
        "payable m-thly or payable continuously, level payment annuity, arithmetic "
        "increasing/decreasing annuity, geometric increasing/decreasing annuity, term of annuity.",
        ANNUITIES,
    ),
    LearningOutcome(
        "Level Annuities and Perpetuities",
        "Given sufficient information of immediate or due, present value, future value, current "
        "value, interest rate, payment amount, and term of annuity, calculate any remaining item "
        "for a level annuity with finite term or a level perpetuity.",
        ANNUITIES,
    ),
    LearningOutcome(
        "Arithmetic Varying Annuities",
        "Given sufficient information of immediate or due, present value, future value, current "
        "value, interest rate, payment amount, and term of annuity, calculate any remaining item "
        "for a non-level annuity/cash flow in arithmetic progression, finite term or perpetuity.",
        ANNUITIES,
    ),
    LearningOutcome(
        "Geometric and Other Non-Level Annuities",
        "Given sufficient information of immediate or due, present value, future value, current "
        "value, interest rate, payment amount, and term of annuity, calculate any remaining item "
        "for a non-level annuity/cash flow in geometric progression (finite term or perpetuity) "
        "or other non-level annuities/cash flows.",
        ANNUITIES,
    ),
]

LOANS_OUTCOMES = [
    LearningOutcome(
        "Loan Definitions",
        "Define and recognize the definitions of: principal, interest, term of loan, outstanding "
        "balance, final payment (drop payment, balloon payment), amortization.",
        LOANS,
    ),
    LearningOutcome(
        "Loan Balance and Payment Calculations",
        "Calculate the missing item given any four of: term of loan, interest rate, payment "
        "amount, payment period, principal. Calculate the outstanding balance at any point in "
        "time, and the amount of interest and principal repayment in a given payment.",
        LOANS,
    ),
    LearningOutcome(
        "Loan Refinancing",
        "Perform outstanding balance, payment, and interest/principal split calculations when "
        "refinancing is involved.",
        LOANS,
    ),
]

BONDS_OUTCOMES = [
    LearningOutcome(
        "Bond Definitions",
        "Define and recognize the definitions of: price, book value, market value, amortization "
        "of premium, accumulation of discount, redemption value, par value/face value, yield "
        "rate, coupon, coupon rate, term of bond, callable/non-callable, call price, call "
        "premium, accumulated value with reinvestment of coupons.",
        BONDS,
    ),
    LearningOutcome(
        "Bond Price and Value Calculations",
        "Given sufficient partial information, calculate the price, book value, market value, "
        "accumulated value with reinvestment of coupons, amortization of premium, or "
        "accumulation of discount of a bond (valuation between coupon payment dates is not "
        "covered).",
        BONDS,
    ),
    LearningOutcome(
        "Bond Yield Rate and Coupon Calculations",
        "Given sufficient partial information, calculate the redemption value, face value, "
        "yield rate, coupon, coupon rate, term of bond, or the point in time that a bond has a "
        "given book value, amortization of premium, or accumulation of discount.",
        BONDS,
    ),
    LearningOutcome(
        "Callable Bond Pricing",
        "Calculate the price of a callable bond to achieve a specified minimum yield.",
        BONDS,
    ),
]

GENERAL_CASH_FLOWS_PORTFOLIOS_ALM_OUTCOMES = [
    LearningOutcome(
        "Yield Rate, Duration, and Portfolio Definitions",
        "Define and recognize the definitions of: yield rate/rate of return, current value, "
        "duration and convexity (Macaulay and modified), portfolio, spot rate, forward rate, "
        "yield curve, cash flow and duration matching, and immunization (including full "
        "immunization and Redington immunization).",
        GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    ),
    LearningOutcome(
        "Duration and Convexity Calculations",
        "Calculate the duration and convexity of a set of cash flows, and calculate either "
        "Macaulay or modified duration given the other.",
        GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    ),
    LearningOutcome(
        "Approximating Price Change from Duration",
        "Calculate the approximate change in present value due to a change in interest rate, "
        "using 1st-order linear approximation based on modified duration or 1st-order "
        "approximation based on Macaulay duration.",
        GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    ),
    LearningOutcome(
        "Present Value Using a Yield Curve",
        "Calculate the present value of a set of cash flows, using a yield curve developed from "
        "forward and spot rates.",
        GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    ),
    LearningOutcome(
        "Redington and Full Immunization",
        "Construct an investment portfolio to protect the value of an asset-liability portfolio "
        "using either Redington or full immunization.",
        GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    ),
    LearningOutcome(
        "Cash Flow Matching",
        "Construct an investment portfolio to exactly match a set of liability cash flows.",
        GENERAL_CASH_FLOWS_PORTFOLIOS_ALM,
    ),
]

ALL_LEARNING_OUTCOMES: list[LearningOutcome] = (
    TIME_VALUE_OF_MONEY_OUTCOMES
    + ANNUITIES_OUTCOMES
    + LOANS_OUTCOMES
    + BONDS_OUTCOMES
    + GENERAL_CASH_FLOWS_PORTFOLIOS_ALM_OUTCOMES
)

_OUTCOMES_BY_CATEGORY = {
    TIME_VALUE_OF_MONEY: TIME_VALUE_OF_MONEY_OUTCOMES,
    ANNUITIES: ANNUITIES_OUTCOMES,
    LOANS: LOANS_OUTCOMES,
    BONDS: BONDS_OUTCOMES,
    GENERAL_CASH_FLOWS_PORTFOLIOS_ALM: GENERAL_CASH_FLOWS_PORTFOLIOS_ALM_OUTCOMES,
}


def weight_for(outcome: LearningOutcome) -> float:
    siblings = _OUTCOMES_BY_CATEGORY[outcome.category]
    return TOPIC_WEIGHTS[outcome.category] / len(siblings)


LEARNING_OUTCOME_NAMES: list[str] = [o.name for o in ALL_LEARNING_OUTCOMES]
