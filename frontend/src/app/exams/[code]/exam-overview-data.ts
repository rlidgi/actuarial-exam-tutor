import type { TopicIconKey } from "./topic-icons";

// Shared between page.tsx (server, for metadata/generateStaticParams) and
// exam-overview-content.tsx (client) -- kept in one place so the two never
// drift apart on exam names/copy.
export const EXAM_CODES = ["P", "FM", "FAM"] as const;
export type ExamCode = (typeof EXAM_CODES)[number];

interface ExamTopic {
  icon: TopicIconKey;
  title: string;
  points: string[];
}

interface ExamOverview {
  fullName: string;
  shortName: string;
  tagline: string;
  // Matches the accent colors landing-content.tsx's EXAMS array uses for
  // this same exam's hero card -- undefined falls back to the default ink
  // color there and to --ledger here, same reasoning.
  accent?: string;
  topics: ExamTopic[];
}

export const EXAM_OVERVIEW: Record<ExamCode, ExamOverview> = {
  P: {
    fullName: "Exam P -- Probability",
    shortName: "Probability",
    tagline:
      "Build the probability foundation the rest of the actuarial exam track depends on, from combinatorics through joint distributions.",
    accent: "var(--sky)",
    topics: [
      {
        icon: "sets",
        title: "General probability",
        points: [
          "Set theory and combinatorics (counting rules, permutations, combinations)",
          "Conditional probability and independence",
          "Bayes' theorem",
        ],
      },
      {
        icon: "curve",
        title: "Univariate probability distributions",
        points: [
          "Discrete distributions (binomial, Poisson, geometric, negative binomial, hypergeometric)",
          "Continuous distributions (normal, exponential, uniform, gamma, and more)",
          "Moments: mean, variance, and moment generating functions",
        ],
      },
      {
        icon: "scatter",
        title: "Multivariate probability distributions",
        points: [
          "Joint, marginal, and conditional distributions",
          "Covariance and correlation",
          "Transformations and combinations of random variables",
        ],
      },
    ],
  },
  FM: {
    fullName: "Exam FM -- Financial Mathematics",
    shortName: "Financial Mathematics",
    tagline:
      "Develop fluency in the time-value-of-money and interest theory concepts that underpin every later actuarial exam.",
    accent: "var(--gold)",
    topics: [
      {
        icon: "clock",
        title: "Time value of money and annuities",
        points: [
          "Simple and compound interest; present and future value",
          "Annuity-immediate and annuity-due, level and varying",
          "Amortization schedules and sinking funds",
        ],
      },
      {
        icon: "certificate",
        title: "Bonds and general cash flows",
        points: [
          "Bond pricing and yield rates",
          "General cash flow and portfolio valuation",
          "Yield curves and spot/forward rates",
        ],
      },
      {
        icon: "scale",
        title: "Interest rate risk",
        points: [
          "Duration and convexity",
          "Immunization strategies",
          "Asset-liability matching",
        ],
      },
    ],
  },
  FAM: {
    fullName: "Exam FAM -- Fundamentals of Actuarial Mathematics",
    shortName: "Fundamentals of Actuarial Mathematics",
    tagline:
      "Connect life contingencies with financial economics through structured, textbook-grounded practice.",
    accent: "var(--ledger-bright)",
    topics: [
      {
        icon: "survivalCurve",
        title: "Survival models and life tables",
        points: [
          "Survival and mortality functions",
          "Life tables and select mortality",
          "Force of mortality",
        ],
      },
      {
        icon: "shield",
        title: "Life insurance and annuity valuation",
        points: [
          "Whole life, term, and endowment insurance",
          "Life annuities",
          "Benefit reserves",
        ],
      },
      {
        icon: "branch",
        title: "Financial economics fundamentals",
        points: [
          "Options and hedging strategies",
          "The term structure of interest rates",
          "Binomial option pricing",
        ],
      },
    ],
  },
};
