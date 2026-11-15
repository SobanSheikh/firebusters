import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import LabBrief from "./LabBrief";
import { api } from "./lib/api";

export type SuppressionRecord = {
  id: string;
  run: string;
  material: string;
  date: string;
  air_display: string | null;
  oxygen_source_value: number | null;
  pressure_atm: number | null;
  observation: string;
  derived_outcome: string;
  suppression_attempted: boolean;
  normalization_note: string;
  citation_id: string;
};

type SuppressionResponse = {
  items: SuppressionRecord[];
  total: number;
  materials: string[];
  outcomes: { outcome: string; total: number }[];
};

const OUTCOME_LABELS: Record<string, string> = {
  suppression_failed: "Suppression did not extinguish",
  suppression_succeeded: "Suppression extinguished",
  suppression_partial: "Partial flame displacement",
  self_extinguished: "Self-extinguished",
  airflow_terminated: "Ended after airflow change",
  fuel_consumed: "Fuel consumed",
  ignition_failed: "Ignition unsuccessful",
  observed_burning: "Burning observed",
  unclassified: "Needs review",
};

const PAGE_SIZE = 9;

export default function SuppressionExplorer({
  onCitation,
  selected,
  onToggle,
  onAskSelection,
  onClearSelection,
}: {
  onCitation: (citationId: string) => void;
  selected: SuppressionRecord[];
  onToggle: (record: SuppressionRecord) => void;
  onAskSelection: () => void;
  onClearSelection: () => void;
}) {
  const [material, setMaterial] = useState("");
  const [outcome, setOutcome] = useState("");
  const [page, setPage] = useState(0);
  const query = useQuery({
    queryKey: ["suppression-experiments", material, outcome, page],
    queryFn: async () =>
      (
        await api.get<SuppressionResponse>("/research/suppression-experiments", {
          params: {
            material: material || undefined,
            outcome: outcome || undefined,
            offset: page * PAGE_SIZE,
            limit: PAGE_SIZE,
          },
        })
      ).data,
  });
  const maxOutcome = Math.max(...(query.data?.outcomes.map((item) => item.total) ?? [1]));
  const changeFilter = (nextMaterial: string, nextOutcome: string) => {
    setMaterial(nextMaterial);
    setOutcome(nextOutcome);
    setPage(0);
  };
  const oxygenLabel = (value: number | null) => {
    if (value === null) return "Not reported";
    return value <= 1
      ? `${(value * 100).toFixed(1)}% (derived from source value ${value})`
      : `${value}%`;
  };

  return (
    <section className="section lab-workspace lab-workspace--suppression" id="suppression">
      <div className="section-heading">
        <div>
          <p className="eyebrow">02 / SOLID FIRE &amp; SUPPRESSION LAB</p>
          <h2>When suppression changes the flame.</h2>
        </div>
        <div className="suppression-filters">
          <label>
            Material
            <select
              value={material}
              onChange={(event) => changeFilter(event.target.value, outcome)}
            >
              <option value="">All materials</option>
              {query.data?.materials.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
        </div>
      </div>
      <LabBrief
        tone="suppression"
        dataset="PSI-26 · BASS"
        purpose="Explore how solid materials behaved during reported airflow and nitrogen-suppression tests."
        service="Filter outcomes and materials, inspect narrative logs, and select exact runs for cited AI comparison."
        output="Observed outcomes and source wording with uncertainty visible—not an extinguisher recommendation."
      />
      <p className="muted">
        PSI-26 · BASS as-run records. Explore how solid materials behaved under changing airflow
        and nitrogen application. Outcome labels are conservative normalizations; the cited
        workbook observation remains authoritative.
      </p>

      <div className="outcome-map" aria-label="Derived outcome filters">
        {query.data?.outcomes.map((item) => (
          <button
            key={item.outcome}
            className={outcome === item.outcome ? "is-active" : ""}
            onClick={() => changeFilter(material, outcome === item.outcome ? "" : item.outcome)}
            aria-pressed={outcome === item.outcome}
          >
            <span>
              <strong>{item.total}</strong>
              {OUTCOME_LABELS[item.outcome] ?? item.outcome}
            </span>
            <i style={{ width: `${Math.max(8, (item.total / maxOutcome) * 100)}%` }} />
          </button>
        ))}
      </div>

      {query.isPending && <p role="status">Loading solid-fire evidence…</p>}
      {query.isError && <p role="alert">The PSI-26 evidence could not be loaded.</p>}
      <div className="suppression-grid">
        {query.data?.items.map((item) => {
          const isSelected = selected.some((record) => record.id === item.id);
          return (
          <article key={item.id} className={isSelected ? "is-selected" : ""}>
            <div className="suppression-card-heading">
              <span className="tag">BASS RUN {item.run}</span>
              <span className={`outcome-chip outcome-${item.derived_outcome}`}>
                {OUTCOME_LABELS[item.derived_outcome] ?? item.derived_outcome}
              </span>
            </div>
            <label className="suppression-select">
              <input
                type="checkbox"
                checked={isSelected}
                disabled={selected.length >= 4 && !isSelected}
                onChange={() => onToggle(item)}
              />
              Compare this run
            </label>
            <h3>{item.material}</h3>
            <dl>
              <div><dt>Air display</dt><dd>{item.air_display ?? "Not reported"}</dd></div>
              <div><dt>O₂</dt><dd>{oxygenLabel(item.oxygen_source_value)}</dd></div>
              <div><dt>Pressure</dt><dd>{item.pressure_atm ?? "Not reported"} atm</dd></div>
              <div><dt>Nitrogen noted</dt><dd>{item.suppression_attempted ? "Yes" : "No"}</dd></div>
            </dl>
            <p>{item.observation || "No narrative observation recorded."}</p>
            <div className="suppression-actions">
              <button onClick={() => onCitation(item.citation_id)}>Inspect workbook row ↗</button>
            </div>
          </article>
          );
        })}
      </div>
      {selected.length > 0 && (
        <div className="selection-dock" role="region" aria-label="Selected BASS run actions">
          <div>
            <strong>{selected.length} BASS run{selected.length === 1 ? "" : "s"} selected</strong>
            <span>{selected.map((item) => item.run).join(" · ")}</span>
          </div>
          <button onClick={onAskSelection}>Ask AI about selection ↗</button>
          <button onClick={onClearSelection}>Clear</button>
        </div>
      )}
      <div className="pagination">
        <span>{query.data?.total ?? 0} matching as-run records</span>
        <button disabled={page === 0} onClick={() => setPage((value) => value - 1)}>Previous</button>
        <span>Page {page + 1}</span>
        <button
          disabled={!query.data || (page + 1) * PAGE_SIZE >= query.data.total}
          onClick={() => setPage((value) => value + 1)}
        >
          Next
        </button>
      </div>
    </section>
  );
}
