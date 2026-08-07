import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

// The model is asked to use $...$ / $$...$$ (what remark-math expects), but
// LLMs commonly fall back to LaTeX's own \( \) / \[ \] delimiters regardless
// of instruction -- normalize both to the $ convention rather than relying
// on prompt compliance alone.
function normalizeMathDelimiters(text: string): string {
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, inner) => `$$${inner}$$`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, inner) => `$${inner}$`);
}

// Markdown parsing + KaTeX typesetting is real work, redone from scratch on
// every render. Without memoizing, every keystroke in the chat input
// re-renders ChatPage, which re-renders every past message bubble, which
// reruns that work for the *entire* conversation history on every
// character typed -- input lag that gets worse the longer the chat gets.
// Memoizing on `text` means a keystroke only touches components whose
// content actually changed.
export const MessageContent = memo(function MessageContent({ text }: { text: string }) {
  return (
    <div className="prose-chat">
      <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
        {normalizeMathDelimiters(text)}
      </ReactMarkdown>
    </div>
  );
});
