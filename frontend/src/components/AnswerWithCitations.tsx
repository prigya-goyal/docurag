import type { Citation } from "../types";

export default function AnswerWithCitations({
  text,
  citations,
  onCitationClick,
}: {
  text: string;
  citations: Citation[];
  onCitationClick: (citation: Citation, index: number) => void;
}) {
  const parts = text.split(/(\[\d+\])/g);

  return (
    <p className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const idx = parseInt(match[1], 10) - 1;
          const citation = citations[idx];
          if (citation) {
            return (
              <button
                key={i}
                className="citation-mark"
                onClick={() => onCitationClick(citation, idx)}
                title={`${citation.filename} · page ${citation.page_number}`}
              >
                {match[1]}
              </button>
            );
          }
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}
