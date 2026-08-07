"""
The 22 learning-outcome-level topics under Exam P's 3 syllabus sections,
transcribed from the official July 2026 syllabus (2026-07-p-syllabus.pdf).

This is the single source of truth for granular topic seeding
(scripts/seed_p_learning_outcomes.py) and for the tool-schema enum
(tools/openai_tools.py) that constrains what the model can report mastery
against. `description` is the syllabus's own wording, verbatim; `name` is
a short label derived from it for use in enums, prompts, and the dashboard
UI, since the full wording is too long for either.

Per-outcome exam_weight is NOT published by the syllabus -- only per-section
ranges are. Weights here are the section's weight midpoint split evenly
across its outcomes, an approximation (see docs/PHASE0_ARCHITECTURE.md-style
reasoning: simple and defensible, not a claim of precision the source data
doesn't support).
"""

from dataclasses import dataclass

from app.rag.sources import (
    EXAM_P_TOPIC_WEIGHTS,
    GENERAL_PROBABILITY,
    MULTIVARIATE_RANDOM_VARIABLES,
    UNIVARIATE_RANDOM_VARIABLES,
)


@dataclass(frozen=True)
class LearningOutcome:
    name: str
    description: str
    category: str


GENERAL_PROBABILITY_OUTCOMES = [
    LearningOutcome(
        "Set Functions & Sample Spaces",
        "Define set functions, Venn diagrams, sample space, and events. Define probability as a "
        "set function on a collection of events and state the basic axioms of probability.",
        GENERAL_PROBABILITY,
    ),
    LearningOutcome(
        "Combinatorics",
        "Calculate probabilities using combinatorics, such as combinations and permutations.",
        GENERAL_PROBABILITY,
    ),
    LearningOutcome(
        "Independent Events",
        "Define independence and calculate probabilities of independent events.",
        GENERAL_PROBABILITY,
    ),
    LearningOutcome(
        "Mutually Exclusive Events",
        "Calculate probabilities of mutually exclusive events.",
        GENERAL_PROBABILITY,
    ),
    LearningOutcome(
        "Addition & Multiplication Rules",
        "Calculate probabilities using addition and multiplication rules.",
        GENERAL_PROBABILITY,
    ),
    LearningOutcome(
        "Conditional Probability",
        "Define and calculate conditional probabilities.",
        GENERAL_PROBABILITY,
    ),
    LearningOutcome(
        "Bayes Theorem & Total Probability",
        "State Bayes Theorem and the law of total probability and use them to calculate "
        "conditional probabilities.",
        GENERAL_PROBABILITY,
    ),
]

UNIVARIATE_RANDOM_VARIABLES_OUTCOMES = [
    LearningOutcome(
        "Random Variables, PDF & CDF",
        "Explain and apply the concepts of probability, random variables, probability density "
        "functions, and cumulative distribution functions.",
        UNIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Conditional Probabilities (Univariate)",
        "Calculate conditional probabilities.",
        UNIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Expected Value & Moments",
        "Explain and calculate expected values, including moments, mode, median, and percentiles.",
        UNIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Variance & Standard Deviation",
        "Explain and calculate variance, standard deviation, and coefficient of variation.",
        UNIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Insurance Payment Calculations",
        "Calculate the amount that an insurance company pays to a policyholder for a claim given "
        "policy information, including deductibles, coinsurance percentages, and benefit limits, "
        "as well as other factors, such as inflation.",
        UNIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Loss & Payment Random Variables",
        "Calculate the expected value, variance, and standard deviation of both the loss random "
        "variable and the corresponding payment amount random variable.",
        UNIVARIATE_RANDOM_VARIABLES,
    ),
]

MULTIVARIATE_RANDOM_VARIABLES_OUTCOMES = [
    LearningOutcome(
        "Joint Probability & CDF",
        "Determine joint probability functions and joint cumulative distribution functions for "
        "discrete random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Conditional & Marginal Distributions",
        "Determine conditional and marginal probability functions for discrete random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Joint/Conditional/Marginal Moments",
        "Calculate moments for joint, conditional, and marginal discrete distributions.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Variance for Conditional & Marginal Distributions",
        "Calculate variance and standard deviation for conditional and marginal probability "
        "distributions for discrete random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Covariance & Correlation",
        "Calculate the covariance and the correlation coefficient for discrete random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Order Statistics",
        "Determine the joint distribution of order statistics for a set of independent random "
        "variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Linear Combinations of Random Variables",
        "Calculate probabilities for linear combinations of independent discrete random variables "
        "as well as for continuous normal random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Moments of Linear Combinations",
        "Calculate moments for linear combinations of independent random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
    LearningOutcome(
        "Central Limit Theorem",
        "Apply the Central Limit Theorem to calculate approximations of probabilities for linear "
        "combinations of independent and identically distributed random variables.",
        MULTIVARIATE_RANDOM_VARIABLES,
    ),
]

ALL_LEARNING_OUTCOMES: list[LearningOutcome] = (
    GENERAL_PROBABILITY_OUTCOMES
    + UNIVARIATE_RANDOM_VARIABLES_OUTCOMES
    + MULTIVARIATE_RANDOM_VARIABLES_OUTCOMES
)

_OUTCOMES_BY_CATEGORY = {
    GENERAL_PROBABILITY: GENERAL_PROBABILITY_OUTCOMES,
    UNIVARIATE_RANDOM_VARIABLES: UNIVARIATE_RANDOM_VARIABLES_OUTCOMES,
    MULTIVARIATE_RANDOM_VARIABLES: MULTIVARIATE_RANDOM_VARIABLES_OUTCOMES,
}


def weight_for(outcome: LearningOutcome) -> float:
    siblings = _OUTCOMES_BY_CATEGORY[outcome.category]
    return EXAM_P_TOPIC_WEIGHTS[outcome.category] / len(siblings)


LEARNING_OUTCOME_NAMES: list[str] = [o.name for o in ALL_LEARNING_OUTCOMES]
