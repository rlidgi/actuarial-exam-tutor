// Pure proficiency-tier bucketing for the dashboard's meters and chips --
// deliberately free of React/API types so it stays trivially testable and
// reusable (e.g. averaging a category's topics uses the exact same
// thresholds as a single topic's own tier).

export type ProficiencyTier = "good" | "warning" | "critical";

export interface ProficiencyRow {
  tier: ProficiencyTier | null;
  label: string;
}

// Mirrors mastery_score's 0-100 scale (see backend student_service.py).
export function proficiencyTier(mastery: number | null): ProficiencyRow {
  if (mastery === null) return { tier: null, label: "Not yet assessed" };
  if (mastery < 45) return { tier: "critical", label: "Needs work" };
  if (mastery < 70) return { tier: "warning", label: "Developing" };
  return { tier: "good", label: "Strong" };
}

export function averageMastery(values: (number | null)[]): number | null {
  const known = values.filter((v): v is number => v !== null);
  if (known.length === 0) return null;
  return Math.round(known.reduce((sum, v) => sum + v, 0) / known.length);
}
