"""
The learning-outcome-level topics under Exam FAM's 10 syllabus sections,
transcribed from the official July 2026 syllabus (2026-07-fam-syllabus.pdf).

This is the single source of truth for granular topic seeding
(scripts/seed_learning_outcomes.py) and for the tool-schema enum
(tools/openai_tools.py) that constrains what the model can report mastery
against. `description` is the syllabus's own wording (condensed where
several lettered/bulleted syllabus items were consolidated into one outcome
here -- FAM's syllabus is considerably denser than P's or FM's, e.g. Topic 2
alone has 14 lettered sub-items, so some grouping of closely related items
was necessary to keep outcomes at a sensible granularity); `name` is a short
label derived from it for use in enums, prompts, and the dashboard UI.

Per-outcome exam_weight is NOT published by the syllabus -- only per-section
ranges are. Weights here are the section's weight midpoint split evenly
across its outcomes, same approximation approach as exam_syllabus_p.py and
exam_syllabus_fm.py.
"""

from dataclasses import dataclass

from app.rag.sources_fam import (
    INTRODUCTION_TO_CREDIBILITY,
    LONG_TERM_INSURANCE_RETIREMENT,
    MORTALITY_MODELS,
    OPTION_PRICING_FUNDAMENTALS,
    PARAMETRIC_ESTIMATION,
    PREMIUM_POLICY_VALUE_LONG_TERM,
    PRICING_RESERVING_SHORT_TERM,
    PV_RANDOM_VARIABLES_LONG_TERM,
    SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    SHORT_TERM_INSURANCE_REINSURANCE,
    TOPIC_WEIGHTS,
)


@dataclass(frozen=True)
class LearningOutcome:
    name: str
    description: str
    category: str


SHORT_TERM_INSURANCE_REINSURANCE_OUTCOMES = [
    LearningOutcome(
        "Coverage Modification Types",
        "Identify the types of coverage modifications for short-term insurance.",
        SHORT_TERM_INSURANCE_REINSURANCE,
    ),
    LearningOutcome(
        "Coverage Modification Calculations",
        "Perform calculations assessing the impact of coverage modifications.",
        SHORT_TERM_INSURANCE_REINSURANCE,
    ),
    LearningOutcome(
        "Loss Elimination Ratio & Inflation",
        "Perform calculations of the loss elimination ratio and the effect of inflation on losses.",
        SHORT_TERM_INSURANCE_REINSURANCE,
    ),
    LearningOutcome(
        "Reinsurance Forms",
        "Identify the operation of basic forms of proportional and excess of loss reinsurance "
        "and understand their impact on reserving and pricing.",
        SHORT_TERM_INSURANCE_REINSURANCE,
    ),
    LearningOutcome(
        "Reinsurance Claim Allocation",
        "Determine the allocation of claim amounts paid by the insurer and reinsurer under "
        "various forms of reinsurance.",
        SHORT_TERM_INSURANCE_REINSURANCE,
    ),
]

SEVERITY_FREQUENCY_AGGREGATE_MODELS_OUTCOMES = [
    LearningOutcome(
        "Severity Model Moments & Percentiles",
        "For severity models, calculate moments and percentiles.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
    LearningOutcome(
        "Severity Model Parameters & Classification",
        "For severity models, identify the role of scale and shape parameters in continuous "
        "models, recognize classes of distributions and their relationships, and characterize "
        "distributions by existence of moments.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
    LearningOutcome(
        "(a,b,0) and (a,b,1) Class Parameters",
        "For frequency models, identify the role of parameters for the (a,b,0) and (a,b,1) "
        "classes of distributions, and recognize these classes and their relationships.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
    LearningOutcome(
        "Frequency Model Calculations & Selection",
        "For frequency models, perform calculations for the (a,b,0) and (a,b,1) classes of "
        "distributions, and identify appropriate distributions for a given application.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
    LearningOutcome(
        "Collective & Individual Risk Models",
        "Define collective and individual risk models and calculate their mean and variance.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
    LearningOutcome(
        "Aggregate Distribution Approximation & Stop-Loss",
        "Use the log-normal or normal approximation to approximate the aggregate distribution, "
        "calculate probabilities using the convolution method, and calculate the expected "
        "payment for stop-loss insurance.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
    LearningOutcome(
        "Value at Risk & Tail Value at Risk",
        "Calculate Value at Risk and Tail Value at Risk, and determine whether a given risk "
        "measure has certain desirable properties.",
        SEVERITY_FREQUENCY_AGGREGATE_MODELS,
    ),
]

PARAMETRIC_ESTIMATION_OUTCOMES = [
    LearningOutcome(
        "MLE for Severity & Frequency Distributions",
        "Estimate the parameters for severity and frequency distributions using Maximum "
        "Likelihood Estimation for complete individual data, complete grouped data, and "
        "truncated or censored data.",
        PARAMETRIC_ESTIMATION,
    ),
]

INTRODUCTION_TO_CREDIBILITY_OUTCOMES = [
    LearningOutcome(
        "Concept of Credibility",
        "Understand the concept of credibility.",
        INTRODUCTION_TO_CREDIBILITY,
    ),
    LearningOutcome(
        "Limited Fluctuation Credibility Calculations",
        "Perform calculations using limited fluctuation (classical) credibility.",
        INTRODUCTION_TO_CREDIBILITY,
    ),
]

PRICING_RESERVING_SHORT_TERM_OUTCOMES = [
    LearningOutcome(
        "Claim Reserve Estimation Techniques",
        "Describe and apply techniques for estimating outstanding claims, using the Expected "
        "Loss Ratio, Chain-Ladder, and Bornhuetter-Ferguson methods.",
        PRICING_RESERVING_SHORT_TERM,
    ),
    LearningOutcome(
        "Ratemaking Objectives & Data",
        "Understand the objectives of ratemaking and the data used for ratemaking.",
        PRICING_RESERVING_SHORT_TERM,
    ),
    LearningOutcome(
        "Ratemaking Data Adjustments",
        "Calculate the adjustments to ratemaking data, including development, trend, and "
        "adjusting premium to current rate levels.",
        PRICING_RESERVING_SHORT_TERM,
    ),
    LearningOutcome(
        "Expense & Profit Loading in Ratemaking",
        "Understand how expenses and the profit and contingencies loading are used in "
        "ratemaking.",
        PRICING_RESERVING_SHORT_TERM,
    ),
    LearningOutcome(
        "Rate Changes: Loss Cost & Loss Ratio Methods",
        "Calculate overall average rates and rate changes using the loss cost and loss ratio "
        "methods.",
        PRICING_RESERVING_SHORT_TERM,
    ),
]

OPTION_PRICING_FUNDAMENTALS_OUTCOMES = [
    LearningOutcome(
        "Puts and Calls: Cash Flows & Characteristics",
        "Identify the cash flows and characteristics of puts and calls.",
        OPTION_PRICING_FUNDAMENTALS,
    ),
    LearningOutcome(
        "Binomial Option Pricing Model",
        "Apply the binomial option pricing model to calculate the price of a simple "
        "European-style derivative on a single non-dividend paying asset.",
        OPTION_PRICING_FUNDAMENTALS,
    ),
    LearningOutcome(
        "Black-Scholes Price & Delta Hedge",
        "Apply the Black-Scholes formula to calculate the price and delta hedge of a simple "
        "European-style derivative on a single non-dividend paying asset.",
        OPTION_PRICING_FUNDAMENTALS,
    ),
    LearningOutcome(
        "Put-Call Parity",
        "Apply put-call parity.",
        OPTION_PRICING_FUNDAMENTALS,
    ),
]

LONG_TERM_INSURANCE_RETIREMENT_OUTCOMES = [
    LearningOutcome(
        "Insurable Interest",
        "Define and apply the concept of insurable interest.",
        LONG_TERM_INSURANCE_RETIREMENT,
    ),
    LearningOutcome(
        "Long-Term Coverages & Pension Plans",
        "Identify the long-term insurance coverages (life, health), annuities, and defined "
        "benefit and defined contribution pension plans.",
        LONG_TERM_INSURANCE_RETIREMENT,
    ),
]

MORTALITY_MODELS_OUTCOMES = [
    LearningOutcome(
        "Parametric Survival Models & Life Tables",
        "Understand parametric survival models, life tables, and the relationships between "
        "them.",
        MORTALITY_MODELS,
    ),
    LearningOutcome(
        "Survival & Mortality Probability Calculations",
        "Given a parametric survival model, calculate survival and mortality probabilities, "
        "the force of mortality function, and moments of the curtate and complete future "
        "lifetime random variable.",
        MORTALITY_MODELS,
    ),
    LearningOutcome(
        "Actuarial Notation for Future Lifetime",
        "Identify and apply standard actuarial notation for future lifetime distributions and "
        "moments, including select and ultimate functions.",
        MORTALITY_MODELS,
    ),
    LearningOutcome(
        "Life Table Calculations with Fractional Ages",
        "Given a life table, calculate survival and mortality probabilities, the force of "
        "mortality function, and moments of the curtate and complete future lifetime random "
        "variable, using appropriate fractional age assumptions where necessary.",
        MORTALITY_MODELS,
    ),
    LearningOutcome(
        "Select Life Tables",
        "Understand and apply select life tables.",
        MORTALITY_MODELS,
    ),
]

PV_RANDOM_VARIABLES_LONG_TERM_OUTCOMES = [
    LearningOutcome(
        "PV Random Variables: Insurance, Endowment, Annuity",
        "Identify the present value random variables associated with life insurance, "
        "endowment, and annuity payments for single lives, based on annual, 1/m-thly and "
        "continuous payment frequency.",
        PV_RANDOM_VARIABLES_LONG_TERM,
    ),
    LearningOutcome(
        "Probabilities, Moments & Covariances of PV Random Variables",
        "Calculate probabilities, means, variances and covariances for present value random "
        "variables, using fractional age or claims acceleration approximations where "
        "appropriate.",
        PV_RANDOM_VARIABLES_LONG_TERM,
    ),
    LearningOutcome(
        "Relationships Between Insurance, Endowment & Annuity PV RVs",
        "Understand the relationships between the insurance, endowment, and annuity present "
        "value random variables, and between their expected values.",
        PV_RANDOM_VARIABLES_LONG_TERM,
    ),
    LearningOutcome(
        "Effect of Assumption Changes on PV Random Variables",
        "Calculate the effect of changes in underlying assumptions (e.g., mortality and "
        "interest) on present value random variables.",
        PV_RANDOM_VARIABLES_LONG_TERM,
    ),
    LearningOutcome(
        "Standard Actuarial Notation for Expected Values",
        "Identify and apply standard actuarial notation for the expected values of present "
        "value random variables.",
        PV_RANDOM_VARIABLES_LONG_TERM,
    ),
]

PREMIUM_POLICY_VALUE_LONG_TERM_OUTCOMES = [
    LearningOutcome(
        "Future Loss Random Variables",
        "Identify the future loss random variables associated with whole life, term life, and "
        "endowment insurance, and with term and whole life annuities, on single lives.",
        PREMIUM_POLICY_VALUE_LONG_TERM,
    ),
    LearningOutcome(
        "Premium Calculation Methods",
        "Calculate premiums based on the equivalence principle, the portfolio percentile "
        "principle, and for a given expected present value of profit.",
        PREMIUM_POLICY_VALUE_LONG_TERM,
    ),
    LearningOutcome(
        "Gross, Net & Modified Net Premium Policy Values",
        "Calculate and interpret gross premium, net premium and modified net premium policy "
        "values.",
        PREMIUM_POLICY_VALUE_LONG_TERM,
    ),
    LearningOutcome(
        "Effect of Assumption Changes on Premiums & Policy Values",
        "Calculate the effect of changes in underlying assumptions (e.g., mortality and "
        "interest) on premiums and policy values.",
        PREMIUM_POLICY_VALUE_LONG_TERM,
    ),
    LearningOutcome(
        "Modeling Extra Risk",
        "Apply the following methods for modelling extra risk: age rating; constant addition "
        "to the force of mortality; constant multiple of the rate of mortality.",
        PREMIUM_POLICY_VALUE_LONG_TERM,
    ),
]

ALL_LEARNING_OUTCOMES: list[LearningOutcome] = (
    SHORT_TERM_INSURANCE_REINSURANCE_OUTCOMES
    + SEVERITY_FREQUENCY_AGGREGATE_MODELS_OUTCOMES
    + PARAMETRIC_ESTIMATION_OUTCOMES
    + INTRODUCTION_TO_CREDIBILITY_OUTCOMES
    + PRICING_RESERVING_SHORT_TERM_OUTCOMES
    + OPTION_PRICING_FUNDAMENTALS_OUTCOMES
    + LONG_TERM_INSURANCE_RETIREMENT_OUTCOMES
    + MORTALITY_MODELS_OUTCOMES
    + PV_RANDOM_VARIABLES_LONG_TERM_OUTCOMES
    + PREMIUM_POLICY_VALUE_LONG_TERM_OUTCOMES
)

_OUTCOMES_BY_CATEGORY = {
    SHORT_TERM_INSURANCE_REINSURANCE: SHORT_TERM_INSURANCE_REINSURANCE_OUTCOMES,
    SEVERITY_FREQUENCY_AGGREGATE_MODELS: SEVERITY_FREQUENCY_AGGREGATE_MODELS_OUTCOMES,
    PARAMETRIC_ESTIMATION: PARAMETRIC_ESTIMATION_OUTCOMES,
    INTRODUCTION_TO_CREDIBILITY: INTRODUCTION_TO_CREDIBILITY_OUTCOMES,
    PRICING_RESERVING_SHORT_TERM: PRICING_RESERVING_SHORT_TERM_OUTCOMES,
    OPTION_PRICING_FUNDAMENTALS: OPTION_PRICING_FUNDAMENTALS_OUTCOMES,
    LONG_TERM_INSURANCE_RETIREMENT: LONG_TERM_INSURANCE_RETIREMENT_OUTCOMES,
    MORTALITY_MODELS: MORTALITY_MODELS_OUTCOMES,
    PV_RANDOM_VARIABLES_LONG_TERM: PV_RANDOM_VARIABLES_LONG_TERM_OUTCOMES,
    PREMIUM_POLICY_VALUE_LONG_TERM: PREMIUM_POLICY_VALUE_LONG_TERM_OUTCOMES,
}


def weight_for(outcome: LearningOutcome) -> float:
    siblings = _OUTCOMES_BY_CATEGORY[outcome.category]
    return TOPIC_WEIGHTS[outcome.category] / len(siblings)


LEARNING_OUTCOME_NAMES: list[str] = [o.name for o in ALL_LEARNING_OUTCOMES]
