type ExperimentPoint = {
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

const COLORS = ["#ffad78", "#74c7c3", "#9aa8ff", "#f0cf75"];

export default function ConditionExplorer({
  experiments,
  selectedIds,
  onToggle,
}: {
  experiments: ExperimentPoint[];
  selectedIds: Set<string>;
  onToggle: (experiment: ExperimentPoint) => void;
}) {
  const points = experiments.filter(
    (item) => item.pressure_bar !== null && item.fuel_flow_mg_s !== null,
  );
  if (!points.length) return null;

  const width = 900;
  const height = 280;
  const pad = { left: 62, right: 28, top: 24, bottom: 48 };
  const flows = points.map((item) => item.fuel_flow_mg_s as number);
  const pressures = points.map((item) => item.pressure_bar as number);
  const burns = points.map((item) => item.burn_time_s ?? 0);
  const xMin = Math.min(...flows);
  const xMax = Math.max(...flows);
  const yMin = Math.min(...pressures);
  const yMax = Math.max(...pressures);
  const burnMax = Math.max(...burns, 1);
  const x = (value: number) =>
    pad.left +
    ((value - xMin) / (xMax - xMin || 1)) *
      (width - pad.left - pad.right);
  const y = (value: number) =>
    yMax === yMin
      ? (height - pad.bottom + pad.top) / 2
      : pad.top +
        (1 - (value - yMin) / (yMax - yMin)) *
          (height - pad.top - pad.bottom);
  const fuels = [...new Set(points.map((item) => item.fuel))];

  return (
    <div className="condition-explorer">
      <div className="condition-heading">
        <div>
          <p className="eyebrow">INTERACTIVE CONDITION MAP</p>
          <h3>Flow, pressure, and reported duration</h3>
        </div>
        <p>Click a point to add or remove it from the comparison.</p>
      </div>
      <div className="condition-chart" role="group" aria-label="Experiment condition scatter plot">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Fuel flow versus pressure; point size represents reported burn time">
          <line className="condition-axis" x1={pad.left} y1={height - pad.bottom} x2={width - pad.right} y2={height - pad.bottom} />
          <line className="condition-axis" x1={pad.left} y1={pad.top} x2={pad.left} y2={height - pad.bottom} />
          {[0, 0.5, 1].map((ratio) => {
            const px = pad.left + ratio * (width - pad.left - pad.right);
            const py = pad.top + ratio * (height - pad.top - pad.bottom);
            return (
              <g key={ratio}>
                <line className="condition-grid" x1={px} y1={pad.top} x2={px} y2={height - pad.bottom} />
                <line className="condition-grid" x1={pad.left} y1={py} x2={width - pad.right} y2={py} />
              </g>
            );
          })}
          {points.map((item) => {
            const selected = selectedIds.has(item.id);
            const radius = 7 + ((item.burn_time_s ?? 0) / burnMax) * 12;
            return (
              <circle
                key={item.id}
                className={`condition-point ${selected ? "is-selected" : ""}`}
                cx={x(item.fuel_flow_mg_s as number)}
                cy={y(item.pressure_bar as number)}
                r={radius}
                fill={COLORS[Math.max(0, fuels.indexOf(item.fuel)) % COLORS.length]}
                tabIndex={0}
                role="button"
                aria-label={`${item.run}, ${item.fuel}, ${item.pressure_bar} bar, ${item.fuel_flow_mg_s} milligrams per second, ${item.burn_time_s ?? "unknown"} seconds`}
                onClick={() => onToggle(item)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") onToggle(item);
                }}
              >
                <title>{`${item.run} · ${item.fuel}\n${item.pressure_bar} bar · ${item.fuel_flow_mg_s} mg/s\n${item.burn_time_s ?? "Unknown"} s burn time`}</title>
              </circle>
            );
          })}
          <text className="condition-label" x={width / 2} y={height - 10}>Fuel flow (mg/s)</text>
          <text className="condition-label" transform={`translate(16 ${height / 2}) rotate(-90)`}>Pressure (bar)</text>
          <text className="condition-tick" x={pad.left} y={height - pad.bottom + 22}>{xMin}</text>
          <text className="condition-tick" textAnchor="end" x={width - pad.right} y={height - pad.bottom + 22}>{xMax}</text>
          <text className="condition-tick" textAnchor="end" x={pad.left - 10} y={y(yMin) + 4}>{yMin}</text>
          {yMax !== yMin && <text className="condition-tick" textAnchor="end" x={pad.left - 10} y={y(yMax) + 4}>{yMax}</text>}
        </svg>
      </div>
      <div className="condition-legend">
        {fuels.map((item, index) => (
          <span key={item}><i style={{ background: COLORS[index % COLORS.length] }} />{item}</span>
        ))}
        <span className="size-key">Bubble size = reported burn time</span>
      </div>
    </div>
  );
}
