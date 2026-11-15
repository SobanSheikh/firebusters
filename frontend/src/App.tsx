import { lazy, Suspense, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ConditionExplorer from "./ConditionExplorer";
import EvidenceDialog from "./EvidenceDialog";
import LabBrief from "./LabBrief";
import ResearchAssistant from "./ResearchAssistant";
import SuppressionExplorer, { type SuppressionRecord } from "./SuppressionExplorer";
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
  termination_label: string;
  flame_type: string;
  hot_ignition: string | null;
  oxygen_before: number | null;
  oxygen_after: number | null;
  peak_burner_temperature_c: number | null;
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

const SECTIONS = [
  ["mission", "00", "Mission"],
  ["experiments", "01", "Experiments"],
  ["suppression", "02", "Suppression"],
  ["chart", "03", "Data lab"],
  ["assistant", "04", "Ask AI"],
] as const;
const EXPERIMENT_PAGE_SIZE = 10;

export default function App() {
  const [fuel, setFuel] = useState("");
  const [page, setPage] = useState(0);
  const [citationId, setCitationId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Experiment[]>([]);
  const [selectedSuppression, setSelectedSuppression] = useState<SuppressionRecord[]>([]);
  const [pointIndex, setPointIndex] = useState(0);
  const [presentationMode, setPresentationMode] = useState(false);
  const [assistantDraft, setAssistantDraft] = useState("");
  const [commandQuestion, setCommandQuestion] = useState("");
  const [activeSection, setActiveSection] = useState("mission");
  const [scrollProgress, setScrollProgress] = useState(0);
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
          {
            params: {
              fuel: fuel || undefined,
              offset: page * EXPERIMENT_PAGE_SIZE,
              limit: EXPERIMENT_PAGE_SIZE,
            },
          },
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
      "flame_type",
      "hot_ignition",
      "oxygen_before",
      "oxygen_after",
      "peak_burner_temperature_c",
      "comments",
      "termination",
      "termination_label",
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
  const toggle = (experiment: Experiment) => {
    setSelectedSuppression([]);
    setSelected((items) =>
      items.some((x) => x.id === experiment.id)
        ? items.filter((x) => x.id !== experiment.id)
        : items.length < 4
          ? [...items, experiment]
          : items,
    );
  };
  const toggleSuppression = (record: SuppressionRecord) => {
    setSelected([]);
    setSelectedSuppression((items) =>
      items.some((item) => item.id === record.id)
        ? items.filter((item) => item.id !== record.id)
        : items.length < 4
          ? [...items, record]
          : items,
    );
  };
  const askAboutSelection = () => {
    if (!selected.length) return;
    setAssistantDraft(
      `Compare the selected experiment runs ${selected.map((item) => item.run).join(", ")}. What differs, what is supported by the records, and what remains unknown?`,
    );
    requestAnimationFrame(() =>
      document.getElementById("assistant")?.scrollIntoView({ behavior: "smooth" }),
    );
  };
  const askAboutSuppressionSelection = () => {
    if (!selectedSuppression.length) return;
    setAssistantDraft(
      `Compare the selected BASS runs ${selectedSuppression.map((item) => item.run).join(", ")}. For each run, describe the reported material, airflow, oxygen, nitrogen application, and observed outcome. What differs, what is supported by the records, and what remains unknown? Do not infer causation.`,
    );
    requestAnimationFrame(() =>
      document.getElementById("assistant")?.scrollIntoView({ behavior: "smooth" }),
    );
  };
  const askFromCommandBar = () => {
    const question = commandQuestion.trim();
    if (!question) return;
    setAssistantDraft(question);
    requestAnimationFrame(() =>
      document.getElementById("assistant")?.scrollIntoView({ behavior: "smooth" }),
    );
  };

  useEffect(() => {
    const sections = ["mission", "experiments", "suppression", "chart", "assistant"]
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => section !== null);
    let frame = 0;
    const updateActiveSection = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const marker = window.innerHeight * 0.32;
        let current = sections[0]?.id ?? "mission";
        for (const section of sections) {
          if (section.getBoundingClientRect().top <= marker) current = section.id;
          else break;
        }
        setActiveSection(current);
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        setScrollProgress(scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0);
      });
    };
    updateActiveSection();
    window.addEventListener("scroll", updateActiveSection, { passive: true });
    window.addEventListener("resize", updateActiveSection);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", updateActiveSection);
      window.removeEventListener("resize", updateActiveSection);
    };
  }, []);

  useEffect(() => {
    const keepBackendWarm = () => {
      void api.get("/health/live", { timeout: 10_000 }).catch(() => undefined);
    };
    const interval = window.setInterval(keepBackendWarm, 10 * 60 * 1000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) entry.target.classList.add("is-visible");
        }
      },
      { threshold: 0.08 },
    );
    const elements = document.querySelectorAll(".section, .metrics");
    elements.forEach((element) => {
      element.classList.add("reveal-section");
      observer.observe(element);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <main
      className={`app-shell ${presentationMode ? "presentation-mode" : ""}`}
    >
      <div className="scroll-progress" aria-hidden="true">
        <span style={{ width: `${scrollProgress}%` }} />
      </div>
      <aside className="mission-rail" aria-label="Mission journey">
        <a href="#" className="brand rail-brand">
          <img className="brand-logo" src="/firebusters-favicon.svg" alt="" />
          <span>FIREBUSTERS</span>
        </a>
        <p className="rail-label">MISSION JOURNEY</p>
        <nav className="rail-navigation">
          {SECTIONS.map(([id, number, label]) => (
            <a
              key={id}
              href={`#${id}`}
              className={activeSection === id ? "is-active" : ""}
              aria-current={activeSection === id ? "step" : undefined}
            >
              <span>{number}</span>
              {label}
            </a>
          ))}
        </nav>
        <div className="rail-coverage">
          <p>EVIDENCE COVERAGE</p>
          <strong>{overview.data?.investigations.length ?? "—"} investigations</strong>
          <i><span /></i>
          <small>{overview.data?.experiment_count ?? "—"} records · 721 citations</small>
        </div>
        <button
          className="rail-demo"
          onClick={() => setPresentationMode((value) => !value)}
          aria-pressed={presentationMode}
        >
          {presentationMode ? "Exit judge route" : "▶ Start 3-min demo"}
        </button>
      </aside>
      <div className="workspace">
        <nav className="topbar">
          <a href="#" className="brand mobile-brand">
            <img className="brand-logo" src="/firebusters-favicon.svg" alt="" />
            FIREBUSTERS
          </a>
          <span className="topbar-context">MICROGRAVITY / COMBUSTION SCIENCE</span>
          <span className="source-status"><i /> NASA evidence online</span>
        </nav>
        {presentationMode && (
          <aside
            className="demo-rail"
            aria-label="Three minute demonstration route"
          >
            <strong>JUDGE ROUTE</strong>
            {SECTIONS.map(([id, number, label]) => (
              <a
                key={id}
                href={`#${id}`}
                className={activeSection === id ? "is-active" : ""}
                aria-current={activeSection === id ? "step" : undefined}
              >
                {number} · {label}
              </a>
            ))}
            <button onClick={() => setPresentationMode(false)}>Reset view</button>
          </aside>
        )}
        <header className="hero">
          <div className="hero-copy">
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
            <form
              className="command-bar"
              onSubmit={(event) => {
                event.preventDefault();
                askFromCommandBar();
              }}
            >
              <span aria-hidden="true">✦</span>
              <label className="sr-only" htmlFor="mission-question">Ask across the evidence</label>
              <input
                id="mission-question"
                value={commandQuestion}
                onChange={(event) => setCommandQuestion(event.target.value)}
                placeholder="Ask about a fuel, material, run, or suppression outcome…"
              />
              <button type="submit" disabled={!commandQuestion.trim()}>
                Ask ↗
              </button>
            </form>
            <div className="command-suggestions" aria-label="Suggested starting points">
              {["Why did N₂ suppression fail?", "Compare reported conditions", "Show available variables"].map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => setCommandQuestion(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
          <div className="hero-note" aria-hidden="true">
            <div className="orbit-system">
              <i className="orbit-ring orbit-ring-outer" />
              <i className="orbit-ring orbit-ring-inner" />
              <i className="orbit-node" />
              <i className="orbit-core" />
            </div>
            <p>LIVE EVIDENCE ORBIT</p>
            <small>Scroll to move through the mission</small>
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
              {overview.data?.investigations.length ?? "—"} reviewed investigations · cited
              tables, charts, and PDF evidence
            </strong>
            <p>
              This release indexes reviewed PSI-26, PSI-117, and PSI-159 evidence. It
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
      <section className="section lab-workspace lab-workspace--gases" id="experiments">
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
        <LabBrief
          tone="gases"
          dataset="PSI-159 · CFI-G"
          purpose="Understand the reported conditions and outcomes of gaseous cool-flame runs in microgravity."
          service="Filter fuels, map pressure and flow, select exact runs, and compare documented conditions."
          output="A cited experimental subset for inspection, export, or an AI-assisted comparison."
        />
        <p className="muted">
          PSI-159 · CFI-G normal flames. Select up to four records to compare
          reported conditions. Blank values remain unknown.
        </p>
        {experiments.data?.items && (
          <ConditionExplorer
            experiments={experiments.data.items}
            selectedIds={new Set(selected.map((item) => item.id))}
            onToggle={toggle}
          />
        )}
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
                  <th>Outcome</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {experiments.data?.items.map((e) => (
                  <tr
                    key={e.id}
                    className={selected.some((item) => item.id === e.id) ? "is-selected" : ""}
                  >
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
                    <td>{e.termination_label}</td>
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
              !experiments.data ||
              (page + 1) * EXPERIMENT_PAGE_SIZE >= experiments.data.total
            }
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
        {selected.length > 0 && (
          <div className="selection-dock" role="region" aria-label="Selected experiment actions">
            <div>
              <strong>{selected.length} experiment{selected.length === 1 ? "" : "s"} selected</strong>
              <span>{selected.map((item) => item.run).join(" · ")}</span>
            </div>
            <button onClick={askAboutSelection}>Ask AI about selection ↗</button>
            <button onClick={exportSelected}>Export CSV ↓</button>
            <button onClick={() => setSelected([])}>Clear</button>
          </div>
        )}
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
                  <p>{e.termination_label} · hot ignition {e.hot_ignition ?? "not reported"}</p>
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
      <SuppressionExplorer
        onCitation={setCitationId}
        selected={selectedSuppression}
        onToggle={toggleSuppression}
        onAskSelection={askAboutSuppressionSelection}
        onClearSelection={() => setSelectedSuppression([])}
      />
      <section className="section lab-workspace lab-workspace--droplet" id="chart">
        <p className="eyebrow">03 / THE DATA LAB</p>
        <h2>A droplet’s changing history.</h2>
        <LabBrief
          tone="droplet"
          dataset="PSI-117 · DROPLET SERIES"
          purpose="See how normalized droplet size changed through the recorded three-stage combustion history."
          service="Explore the curve, move through its 205 source points, and inspect any exact CSV record."
          output="A traceable visual measurement—not an AI-generated curve or a causal prediction."
        />
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
        key={assistantDraft}
        experimentIds={[
          ...selected.map((item) => item.id),
          ...selectedSuppression.map((item) => item.id),
        ]}
        chartId={chart?.id}
        onCitation={setCitationId}
        draftQuestion={assistantDraft}
      />
      <footer>
        FIREBUSTERS · NASA evidence, independently explored.{" "}
        <span>Every value has a source.</span>
      </footer>
      <nav className="mobile-dock" aria-label="Mobile mission navigation">
        {SECTIONS.map(([id, number, label]) => (
          <a
            key={id}
            href={`#${id}`}
            className={activeSection === id ? "is-active" : ""}
            aria-current={activeSection === id ? "step" : undefined}
          >
            <span>{number}</span>
            {label}
          </a>
        ))}
      </nav>
      </div>
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
                  : citation.data.locator.kind === "xlsx_record"
                    ? "ORIGINAL WORKBOOK ROW"
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
