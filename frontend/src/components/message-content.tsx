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
    text
      .replace(/\\\[([\s\S]+?)\\\]/g, (_, inner) => `$$${inner}$$`)
      .replace(/\\\(([\s\S]+?)\\\)/g, (_, inner) => `$${inner}$`)
  );
}

// remark-math decides math-block boundaries purely by scanning for "$$"
// pairs in the raw text -- rehype-katex has no say in that and just renders
// whatever span it's handed. If the model occasionally drops a "$$" partway
// through a reply (seen a couple of times: a plugged-in-numbers calculation
// followed immediately by a bolded prose conclusion), the odd one left over
// has no closing partner, so remark-math treats it as an unterminated
// opener and keeps searching forward for the *next* "$$" it can find --
// which can be many sentences later, sweeping real prose into one doomed
// KaTeX render that shows as a wall of raw red text (see KATEX_OPTIONS
// below). An odd overall count of "$$" means exactly one is unpaired;
// dropping the last occurrence (rather than trying to guess which pairing
// was "meant") keeps every delimiter before it correctly paired, so at
// worst one block loses its math formatting instead of the whole reply
// losing its prose too.
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
