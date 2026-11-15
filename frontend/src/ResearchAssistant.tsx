import { useRef, useState } from "react";
import axios from "axios";
import { api } from "./lib/api";

type Answer = {
  claims: { text: string; citation_ids: string[] }[];
  evidence: {
    citation_id: string;
    label: string;
    kind: string;
    data: Record<string, unknown>;
  }[];
  mode: string;
  message: string;
  visuals: {
    chart_id: string;
    title: string;
    reason: string;
    citation_ids: string[];
  }[];
  follow_up_questions: string[];
  usage: {
    retrieval_passes?: number;
    generation_calls?: number;
    evidence_records?: number;
  };
};

export default function ResearchAssistant({
  experimentIds,
  chartId,
  onCitation,
}: {
  experimentIds: string[];
  chartId?: string;
  onCitation: (id: string) => void;
}) {
  const [question, setQuestion] = useState("");
  const [includeChart, setIncludeChart] = useState(false);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const suggestions = [
    "Which indexed evidence is most relevant to cool-flame extinction, and why?",
    "What pressures and burn times are reported for ethane tests?",
    "What can this evidence support about an oxygen-enriched lunar habitat—and what remains unknown?",
    "Which available variables could support predictive modeling?",
  ];
  const controller = useRef<AbortController | null>(null);
  async function submit() {
    if (busy || question.trim().length < 3) return;
    setBusy(true);
    setError("");
    setAnswer(null);
    const request = new AbortController();
    controller.current = request;
    try {
      const result = await api.post<Answer>(
        "/assistant/ask",
        {
          question,
          experiment_ids: experimentIds,
          chart_id: includeChart ? chartId : null,
        },
        { signal: request.signal, timeout: 75_000 },
      );
      setAnswer(result.data);
    } catch (e) {
      if (axios.isCancel(e)) setError("Request cancelled.");
      else
        setError(
          axios.isAxiosError(e) && typeof e.response?.data?.detail === "string"
            ? e.response.data.detail
            : "The assistant is unavailable. You can still inspect experiments and citations above.",
        );
    } finally {
      setBusy(false);
      controller.current = null;
    }
  }
  return (
    <section className="section" id="assistant">
      <p className="eyebrow">03 / ASK FIREBUSTERS</p>
      <h2>Ask the evidence.</h2>
      <p className="muted">
        Search experiment records, chart points, and PDF passages with semantic
        retrieval and keyword fallback. PDF extraction may omit diagrams or
        table structure.{" "}
        {experimentIds.length
          ? `${experimentIds.length} selected experiments will be used as context.`
          : "Mention a fuel or test ID to find records."}
      </p>
      <div className="question-chips" aria-label="Suggested research questions">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => setQuestion(suggestion)}
            disabled={busy}
          >
            {suggestion}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <label htmlFor="research-question">Your research question</label>
        <textarea
          id="research-question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          minLength={3}
          maxLength={1500}
          required
          rows={3}
          disabled={busy}
          placeholder="What pressures and burn times are reported for ethane tests?"
          style={{
            display: "block",
            width: "100%",
            padding: 16,
            margin: "12px 0",
            background: "#101c27",
            border: "1px solid #344351",
            borderRadius: 8,
            color: "inherit",
            font: "inherit",
          }}
        />
        <div className="point-details">
          <label>
            <input
              type="checkbox"
              checked={includeChart}
              disabled={busy || !chartId}
              onChange={(e) => setIncludeChart(e.target.checked)}
            />{" "}
            Include the droplet-history chart
          </label>
          <button type="submit" disabled={busy || question.trim().length < 3}>
            {busy ? "Retrieving and checking evidence…" : "Ask Firebusters ↗"}
          </button>
          {busy && (
            <button type="button" onClick={() => controller.current?.abort()}>
              Cancel
            </button>
          )}
        </div>
      </form>
      {busy && (
        <p role="status" className="muted">
          Retrieving source records and preparing a cited response…
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {answer && (
        <div className="chart-panel" aria-live="polite">
          <p className="eyebrow">
            {answer.mode === "ai"
              ? "AI EXPLANATION · CHECK THE SOURCES"
              : "SOURCE EVIDENCE"}
          </p>
          {answer.message && <p>{answer.message}</p>}
          {answer.visuals?.map((visual) => (
            <article className="answer-visual" key={visual.chart_id}>
              <div>
                <p className="eyebrow">RELEVANT REVIEWED VISUAL</p>
                <h3>{visual.title}</h3>
                <p className="muted">
                  {visual.reason}. It shows source values, not an AI-generated
                  chart.
                </p>
              </div>
              <div className="visual-actions">
                <a className="button primary" href="#chart">
                  Open chart ↑
                </a>
                {visual.citation_ids.slice(0, 2).map((id) => (
                  <button key={id} onClick={() => onCitation(id)}>
                    Source ↗
                  </button>
                ))}
              </div>
            </article>
          ))}
          {answer.claims.map((claim, index) => (
            <article key={index}>
              <p>{claim.text}</p>
              <div className="point-details">
                {claim.citation_ids.map((id) => (
                  <button key={id} onClick={() => onCitation(id)}>
                    {answer.evidence.find((e) => e.citation_id === id)?.label ??
                      "Inspect source"}{" "}
                    ↗
                  </button>
                ))}
              </div>
            </article>
          ))}
          {answer.follow_up_questions?.length > 0 && (
            <div className="follow-ups">
              <p className="eyebrow">USEFUL NEXT QUESTIONS</p>
              {answer.follow_up_questions.map((item) => (
                <button
                  key={item}
                  onClick={() => {
                    setQuestion(item);
                    setAnswer(null);
                  }}
                >
                  {item}
                </button>
              ))}
            </div>
          )}
          {answer.evidence.length > 0 && (
            <details open={!answer.claims.length}>
              <summary>
                {answer.evidence.length} supporting source records
              </summary>
              {answer.evidence.map((item) => (
                <article key={item.citation_id}>
                  <h3>{item.label}</h3>
                  <pre
                    style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
                  >
                    {JSON.stringify(item.data, null, 2)}
                  </pre>
                  <button onClick={() => onCitation(item.citation_id)}>
                    Inspect original evidence ↗
                  </button>
                </article>
              ))}
            </details>
          )}
          <p className="query-budget">
            One retrieval pass ·{" "}
            {answer.usage?.evidence_records ?? answer.evidence.length} evidence
            records · {answer.usage?.generation_calls ?? 0} generation call
          </p>
          <p className="muted">
            Citation IDs are checked against retrieved records. This does not
            guarantee every generated interpretation is correct; inspect the
            sources. Results cover retrieved records, not necessarily the full
            investigation.
          </p>
        </div>
      )}
    </section>
  );
}
