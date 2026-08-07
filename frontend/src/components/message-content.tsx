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

export function MessageContent({ text }: { text: string }) {
  return (
    <div className="prose-chat">
      <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
        {normalizeMathDelimiters(text)}
      </ReactMarkdown>
    </div>
  );
}
