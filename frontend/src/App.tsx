import { lazy, Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import EvidenceDialog from "./EvidenceDialog";
import ResearchAssistant from "./ResearchAssistant";
const ResearchChart = lazy(() => import("./ResearchChart"));
import { api } from "./lib/api";

type Point = { x: number; y: number; record: number; citation_id: string };
type Chart = {
  id: string;
  title: string;
  points: Point[];
  x_label: string;
  y_label: string;
  x_unit: string;
  y_unit: string;
  method: string;
  limitations: string;
};
type Overview = {
  experiment_count: number;
  fuels: string[];
  investigations: { id: string; title: string; subtitle: string }[];
  charts: Chart[];
};
type Experiment = {
  id: string;
  run: string;
  fuel: string;
  pressure_bar: number | null;
  burn_time_s: number | null;
  fuel_flow_mg_s: number | null;
  citation_id: string;
  comments: string;
  termination: string;
};
type Citation = {
  id: string;
  filename: string;
  sha256: string;
  locator: Record<string, unknown>;
  excerpt?: Record<string, unknown>;
  text?: string;
  source_url: string;
};

export default function App() {
  const [fuel, setFuel] = useState("");
  const [page, setPage] = useState(0);
  const [citationId, setCitationId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Experiment[]>([]);
  const [pointIndex, setPointIndex] = useState(0);
  const [presentationMode, setPresentationMode] = useState(false);
  const overview = useQuery({
    queryKey: ["research"],
    queryFn: async () => (await api.get<Overview>("/research/overview")).data,
  });
  const experiments = useQuery({
    queryKey: ["experiments", fuel, page],
    queryFn: async () =>
      (
        await api.get<{ items: Experiment[]; total: number }>(
          "/research/experiments",
          { params: { fuel: fuel || undefined, offset: page * 15, limit: 15 } },
        )
      ).data,
  });
  const citation = useQuery({
    queryKey: ["citation", citationId],
    enabled: !!citationId,
    queryFn: async () =>
      (await api.get<Citation>(`/research/citations/${citationId}`)).data,
  });
  const chart = overview.data?.charts[0];
  const point = chart?.points[pointIndex];
  const format = (value: number | null) =>
    value === null
      ? "Not reported"
      : value.toLocaleString(undefined, { maximumFractionDigits: 3 });
  const exportSelected = () => {
    if (!selected.length) return;
    const safe = (value: unknown) => {
      const raw = value === null ? "" : String(value);
      const protectedValue = /^[=+\-@]/.test(raw) ? `'${raw}` : raw;
      return `"${protectedValue.replaceAll('"', '""')}"`;
    };
    const fields: (keyof Experiment)[] = [
      "run",
      "fuel",
      "pressure_bar",
      "fuel_flow_mg_s",
      "burn_time_s",
      "comments",
      "termination",
      "citation_id",
    ];
    const csv = [
      fields.join(","),
      ...selected.map((item) =>
        fields.map((field) => safe(item[field])).join(","),
      ),
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "firebusters-selected-evidence.csv";
    link.click();
    URL.revokeObjectURL(url);
  };
  const toggle = (experiment: Experiment) =>
    setSelected((items) =>
      items.some((x) => x.id === experiment.id)
        ? items.filter((x) => x.id !== experiment.id)
        : items.length < 4
          ? [...items, experiment]
          : items,
    );

  return (
    <main
      className={`workspace ${presentationMode ? "presentation-mode" : ""}`}
    >
      <nav className="topbar">
        <a href="#" className="brand">
          <span className="brand-mark">F</span> FIREBUSTERS{" "}
          <small>RESEARCH OBSERVATORY</small>
        </a>
        <a href="#mission">Mission</a>
        <a href="#experiments">Experiments</a>
        <a href="#chart">Data lab</a>
        <a href="#assistant">Ask AI</a>
        <button
          className="demo-toggle"
          onClick={() => setPresentationMode((value) => !value)}
          aria-pressed={presentationMode}
        >
          {presentationMode ? "Exit demo" : "3-min demo"}
        </button>
        <span className="status">NASA SOURCE COLLECTION</span>
      </nav>
      {presentationMode && (
        <aside
          className="demo-rail"
          aria-label="Three minute demonstration route"
        >
          <strong>JUDGE ROUTE</strong>
          <a href="#mission">1 · Mission</a>
          <a href="#experiments">2 · Evidence</a>
          <a href="#chart">3 · Chart</a>
          <a href="#assistant">4 · Ask + cite</a>
          <button onClick={() => setPresentationMode(false)}>Reset view</button>
        </aside>
      )}
      <header className="hero">
        <div>
          <p className="eyebrow">MICROGRAVITY / COMBUSTION SCIENCE</p>
          <h1>
            Follow the flame.
            <br />
            <span>Find the evidence.</span>
          </h1>
          <p className="intro">
            Find relevant NASA combustion investigations, extract usable data,
            and trace every interpretation back to source evidence.
          </p>
          <a className="button primary" href="#mission">
            Start the mission ↗
          </a>
        </div>
        <div className="hero-note">
          <span className="orbit" aria-hidden="true">
            ◎
          </span>
          <p>
            SMALL DROPLETS.
            <br />
            EXTRAORDINARY QUESTIONS.
          </p>
          <small>
            How does combustion change when gravity no longer dominates?
          </small>
        </div>
      </header>
      {overview.isError && (
        <div role="alert" className="notice">
          Research data is unavailable. The API may be waking or the research
          schema has not been loaded.{" "}
          <button
            onClick={() => {
              void overview.refetch();
              void experiments.refetch();
            }}
          >
            Retry
          </button>
        </div>
      )}
      {overview.isPending && (
        <p role="status">Connecting to the research collection…</p>
      )}
      <section className="metrics" aria-label="Collection coverage">
        <article>
          <strong>{overview.data?.experiment_count ?? "—"}</strong>
          <span>Reported experiment records</span>
        </article>
        <article>
          <strong>{overview.data?.investigations.length ?? "—"}</strong>
          <span>Investigations in this workspace</span>
        </article>
        <article>
          <strong>{chart?.points.length ?? "—"}</strong>
          <span>Cited experimental chart points</span>
        </article>
      </section>
      <section className="section mission-brief" id="mission">
        <div className="section-heading">
          <div>
            <p className="eyebrow">00 / CHALLENGE MISSION</p>
            <h2>Complex combustion data. Clear, defensible answers.</h2>
          </div>
          <span className="coverage-badge">REVIEWED MVP SLICE</span>
        </div>
        <p className="mission-copy">
          NASA asks for an intelligent dashboard that helps users identify
          relevant investigations, extract data for predictive work, and connect
          research to safer crew environments. Firebusters turns that brief into
          one traceable path.
        </p>
        <div className="outcome-grid">
          <article>
            <span>01</span>
            <h3>Find what matters</h3>
            <p>
              Hybrid retrieval ranks evidence for a mission question and
              explains why it matches.
            </p>
            <a href="#assistant">Ask a habitat question →</a>
          </article>
          <article>
            <span>02</span>
            <h3>Extract usable evidence</h3>
            <p>
              Compare documented conditions, inspect measurements, and export
              selected rows with citation IDs.
            </p>
            <a href="#experiments">Build a data subset →</a>
          </article>
          <article>
            <span>03</span>
            <h3>Design with limits visible</h3>
            <p>
              Connect findings to crew-fire-safety questions without inventing
              lunar predictions or thresholds.
            </p>
            <a href="#chart">Inspect the evidence →</a>
          </article>
        </div>
        <div className="coverage-panel">
          <div>
            <p className="eyebrow">CURRENT EVIDENCE COVERAGE</p>
            <strong>
              2 reviewed investigations · 3 source PDFs · 922 semantic passages
            </strong>
            <p>
              This MVP ranks only the indexed PSI-117 and PSI-159 evidence. It
              does not claim coverage of the full PSI combustion archive.
            </p>
          </div>
          <div className="investigation-list">
            {overview.data?.investigations.map((item, index) => (
              <article key={item.id}>
                <span>0{index + 1}</span>
                <div>
                  <strong>{item.id}</strong>
                  <p>{item.title}</p>
                  <small>{item.subtitle}</small>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
      <section className="section" id="experiments">
        <div className="section-heading">
          <div>
            <p className="eyebrow">01 / INVESTIGATION EXPLORER</p>
            <h2>Inside the experiment.</h2>
          </div>
          <label>
            Filter fuel
            <select
              value={fuel}
              onChange={(e) => {
                setFuel(e.target.value);
                setPage(0);
              }}
            >
              <option value="">All fuels</option>
              {overview.data?.fuels.map((f) => (
                <option key={f}>{f}</option>
              ))}
            </select>
          </label>
        </div>
        <p className="muted">
          PSI-159 · CFI-G normal flames. Select up to four records to compare
          reported conditions. Blank values remain unknown.
        </p>
        {experiments.isError && (
          <p role="alert">Experiment records could not be loaded.</p>
        )}
        {experiments.isPending ? (
          <p role="status">Loading experiments…</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Compare</th>
                  <th>Test</th>
                  <th>Fuel</th>
                  <th>Pressure (bar)</th>
                  <th>Fuel flow (mg/s)</th>
                  <th>Burn time (s)</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {experiments.data?.items.map((e) => (
                  <tr key={e.id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Compare ${e.run}`}
                        checked={selected.some((x) => x.id === e.id)}
                        disabled={
                          selected.length >= 4 &&
                          !selected.some((x) => x.id === e.id)
                        }
                        onChange={() => toggle(e)}
                      />
                    </td>
                    <td className="mono">{e.run}</td>
                    <td>{e.fuel}</td>
                    <td>{format(e.pressure_bar)}</td>
                    <td>{format(e.fuel_flow_mg_s)}</td>
                    <td>{format(e.burn_time_s)}</td>
                    <td>
                      <button onClick={() => setCitationId(e.citation_id)}>
                        Source ↗
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {experiments.data?.total === 0 && (
              <p>No experiments match this filter.</p>
            )}
          </div>
        )}
        <div className="pagination">
          <span>{experiments.data?.total ?? 0} matching records</span>
          <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <span>Page {page + 1}</span>
          <button
            disabled={
              !experiments.data || (page + 1) * 15 >= experiments.data.total
            }
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
        {selected.length > 0 && (
          <div className="comparison">
            <div className="section-heading">
              <h3>Selected conditions</h3>
              <div className="comparison-actions">
                <button onClick={exportSelected}>Export cited CSV ↓</button>
                <button onClick={() => setSelected([])}>Clear selection</button>
              </div>
            </div>
            <div className="comparison-grid">
              {selected.map((e) => (
                <article key={e.id}>
                  <p className="eyebrow">{e.run}</p>
                  <h3>{e.fuel}</h3>
                  <p>
                    {format(e.pressure_bar)} bar · {format(e.fuel_flow_mg_s)}{" "}
                    mg/s
                  </p>
                  <p>{format(e.burn_time_s)} s reported burn time</p>
                  <p className="muted">
                    {e.comments || "No additional comment recorded."}
                  </p>
                  <button onClick={() => setCitationId(e.citation_id)}>
                    Inspect original record
                  </button>
                </article>
              ))}
            </div>
            <p className="muted">
              Descriptive comparison only. Different conditions do not establish
              a causal effect.
            </p>
          </div>
        )}
      </section>
      <section className="section" id="chart">
        <p className="eyebrow">02 / THE DATA LAB</p>
        <h2>A droplet’s changing history.</h2>
        <p className="muted">
          PSI-117 · Experimental series from the three-stage combustion dataset.
          Normalized quantities preserve the source’s units.
        </p>
        {chart && (
          <>
            <div className="chart-panel">
              <div className="section-heading">
                <h3>{chart.title}</h3>
                <span className="tag">EXPERIMENTAL DATA</span>
              </div>
              <p>
                {chart.y_label} · {chart.y_unit}
              </p>
              <div
                role="img"
                aria-label="Experimental normalized squared droplet diameter versus normalized time. Use the point inspector below for exact values and citations."
                className="chart"
              >
                <Suspense fallback={<p role="status">Loading chart…</p>}>
                  <ResearchChart points={chart.points} />
                </Suspense>
              </div>
              <p className="axis-label">
                {chart.x_label} ({chart.x_unit})
              </p>
              <label className="point-slider">
                Inspect source point {pointIndex + 1} of {chart.points.length}
                <input
                  type="range"
                  min={0}
                  max={chart.points.length - 1}
                  value={pointIndex}
                  onChange={(e) => setPointIndex(Number(e.target.value))}
                />
              </label>
              {point && (
                <div className="point-details">
                  <span>t/D₀² = {point.x.toPrecision(6)} s/mm²</span>
                  <span>(D/D₀)² = {point.y.toPrecision(6)}</span>
                  <button onClick={() => setCitationId(point.citation_id)}>
                    Inspect CSV record {point.record} ↗
                  </button>
                </div>
              )}
            </div>
            <details>
              <summary>Method and interpretation limits</summary>
              <p>{chart.method}</p>
              <p>{chart.limitations}</p>
            </details>
          </>
        )}
      </section>
      <ResearchAssistant
        experimentIds={selected.map((e) => e.id)}
        chartId={chart?.id}
        onCitation={setCitationId}
      />
      <footer>
        FIREBUSTERS · NASA evidence, independently explored.{" "}
        <span>Every value has a source.</span>
      </footer>
      {citationId && (
        <EvidenceDialog onClose={() => setCitationId(null)}>
          <div className="section-heading">
            <h2>Source evidence</h2>
            <button
              onClick={() => setCitationId(null)}
              aria-label="Close source evidence"
            >
              Close ×
            </button>
          </div>
          {citation.isPending && <p role="status">Resolving citation…</p>}
          {citation.isError && (
            <p role="alert">
              Citation unavailable.{" "}
              <button onClick={() => void citation.refetch()}>Retry</button>
            </p>
          )}
          {citation.data && (
            <>
              <p className="eyebrow">
                {citation.data.locator.kind === "pdf_page"
                  ? "PDF PAGE EVIDENCE"
                  : "ORIGINAL CSV RECORD"}
              </p>
              <h3>{citation.data.filename}</h3>
              <pre>{JSON.stringify(citation.data.locator, null, 2)}</pre>
              {citation.data.text && (
                <pre style={{ whiteSpace: "pre-wrap" }}>
                  {citation.data.text}
                </pre>
              )}
              <dl>
                {Object.entries(citation.data.excerpt ?? {}).map(
                  ([key, value]) => (
                    <div key={key}>
                      <dt>{key}</dt>
                      <dd>{String(value ?? "Not reported")}</dd>
                    </div>
                  ),
                )}
              </dl>
              <a
                className="button primary"
                href={
                  new URL(
                    citation.data.source_url,
                    api.defaults.baseURL?.startsWith("http")
                      ? api.defaults.baseURL
                      : window.location.origin,
                  ).href
                }
                target="_blank"
                rel="noreferrer"
              >
                Download original source ↗
              </a>
              <p className="muted">Immutable source checksum</p>
              <code className="checksum">{citation.data.sha256}</code>
            </>
          )}
        </EvidenceDialog>
      )}
    </main>
  );
}
