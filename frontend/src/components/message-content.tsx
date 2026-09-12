import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

// The model is asked to use $...$ / $$...$$ (what remark-math expects), but
// LLMs commonly fall back to LaTeX's own \( \) / \[ \] delimiters regardless
// of instruction -- normalize both to the $ convention rather than relying
// on prompt compliance alone.
function normalizeMathDelimiters(text: string): string {
  return neutralizeUnbalancedBlockMath(
    isolateMultilineBlockMathClosers(
      text
        .replace(/\\\[([\s\S]+?)\\\]/g, (_, inner) => `$$${inner}$$`)
        .replace(/\\\(([\s\S]+?)\\\)/g, (_, inner) => `$${inner}$`)
    )
  );
}

// A "$$...$$" pair whose content spans multiple lines is parsed by
// remark-math as flow/display math -- the same tokenizer family as fenced
// code blocks (micromark-extension-math's math-flow.js) -- which imposes
// two rules a single-line "$$...$$" isn't subject to:
//   1. Anything between the opening "$$" and the next line break is read
//      as a fence "meta" string (like a code fence's language tag) and
//      silently DROPPED, not rendered -- e.g. "$$=\frac{a}{b}\n...\n$$"
//      loses the "=\frac{a}{b}" that shares the opening fence's line.
//   2. The closing "$$" is only recognized when it sits ALONE on its own
//      line. A closer glued onto the last content line (".319.$$" instead
//      of ".319.\n$$") isn't recognized as a closer at all -- remark-math
//      just keeps scanning forward for one that qualifies, sweeping
//      everything in between (including real prose, and any other
//      un-isolated "$$" mid-sentence) into one doomed KaTeX render that
//      shows as a wall of raw red text (see KATEX_OPTIONS below).
// Confirmed against a real reply that hit both: gluing the opener to
// "=\frac{0.35(0.80)}" silently dropped that numerator even though the
// block otherwise rendered, and gluing the closer to "0.319." triggered
// the red-text failure. Give each multi-line pair's opener and closer
// their own line so both rules are satisfied without changing anything
// about single-line "$$...$$" usage, which isn't subject to either rule.
function isolateMultilineBlockMathClosers(text: string): string {
  const parts = text.split("$$");
  if (parts.length < 3) return text; // fewer than one full pair
  let result = parts[0];
  for (let i = 1; i < parts.length; i++) {
    const isOpener = i % 2 === 1;
    const isCloser = i % 2 === 0;
    if (isOpener && parts[i].includes("\n")) {
      result += "$$";
      const content = parts[i];
      result += content.startsWith("\n") ? content : `\n${content}`;
    } else if (isCloser && parts[i - 1].includes("\n")) {
      if (!result.endsWith("\n")) result += "\n";
      result += "$$";
      const rest = parts[i];
      result += rest.startsWith("\n") || rest.length === 0 ? rest : `\n${rest}`;
    } else {
      result += `$$${parts[i]}`;
    }
  }
  return result;
}

// Even after isolating multi-line pairs above, the model can still drop a
// "$$" partway through a reply (seen separately: a plugged-in-numbers
// calculation followed immediately by a bolded prose conclusion, all on
// one line). The odd one left over has no closing partner, so remark-math
// treats it as an unterminated opener and keeps searching forward for the
// next "$$" it can find -- sweeping real prose into the same failure mode
// described above. An odd overall count of "$$" means exactly one is
// unpaired; dropping the last occurrence (rather than trying to guess
// which pairing was "meant") keeps every delimiter before it correctly
// paired, so at worst one block loses its math formatting instead of the
// whole reply losing its prose too.
function neutralizeUnbalancedBlockMath(text: string): string {
  const count = (text.match(/\$\$/g) || []).length;
  if (count % 2 === 0) return text;
  const lastIndex = text.lastIndexOf("$$");
  return text.slice(0, lastIndex) + text.slice(lastIndex + 2);
}

// Markdown parsing + KaTeX typesetting is real work, redone from scratch on
// every render. Without memoizing, every keystroke in the chat input
// re-renders ChatPage, which re-renders every past message bubble, which
// reruns that work for the *entire* conversation history on every
// character typed -- input lag that gets worse the longer the chat gets.
// Memoizing on `text` means a keystroke only touches components whose
// content actually changed.
// If the model emits a malformed expression (unbalanced delimiters, stray
// \boxed{} outside math mode, etc.), KaTeX falls back to rendering the raw
// source instead of crashing the page -- in its own hardcoded error red by
// default, which reads as a much louder "broken" signal than it should.
// Match the app's own error color instead of KaTeX's stock #cc0000.
const KATEX_OPTIONS = { errorColor: "#b23a2e" };

export const MessageContent = memo(function MessageContent({ text }: { text: string }) {
  return (
    <div className="prose-chat">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, KATEX_OPTIONS]]}
      >
        {normalizeMathDelimiters(text)}
      </ReactMarkdown>
    </div>
  );
});
