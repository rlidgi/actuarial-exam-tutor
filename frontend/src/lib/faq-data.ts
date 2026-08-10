// Single source of truth for the landing page's FAQ section -- rendered as
// visible content in landing-content.tsx and as FAQPage structured data in
// page.tsx. Keeping both in one place avoids the two ever drifting apart,
// which search engines can treat as spam if the structured data doesn't
// match what's actually shown on the page.
export const FAQ_ITEMS = [
  {
    question: "Which textbooks does it actually use?",
    answer: "We use the textbooks the Society of Actuaries lists in the exam syllabus.",
  },
  {
    question: "Is there anything free before I subscribe?",
    answer:
      "Yes -- once you register, the full study manual for each exam and 6 messages with the " +
      "AI tutor are free, no subscription required.",
  },
  {
    question: "Do I need to subscribe to all three exams?",
    answer:
      "No, each exam is billed and accessed separately, so you only pay for the one you're " +
      "currently studying for.",
  },
  {
    question: "Can I cancel anytime?",
    answer: "Yes, with one click from your account, no minimum commitment.",
  },
  {
    question: "What if I already have a screenshot of a problem?",
    answer:
      "Paste or attach it directly into the chat. It's transcribed automatically and answered " +
      "like any typed question.",
  },
];
