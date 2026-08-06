// Assistant replies come back as plain markdown-ish text (the model isn't
// instructed to avoid markdown). Rendering just **bold** and line breaks
// covers the vast majority of what the tutor actually produces without
// pulling in a full markdown dependency for one field.
export function MessageContent({ text }: { text: string }) {
  const lines = text.split("\n");

  return (
    <>
      {lines.map((line, i) => (
        <span key={i}>
          {renderBold(line)}
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
}

function renderBold(line: string) {
  const parts = line.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}
