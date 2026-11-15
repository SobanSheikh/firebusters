import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function ResearchChart({
  points,
}: {
  points: { x: number; y: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={points}
        margin={{ top: 15, right: 20, bottom: 20, left: 0 }}
      >
        <CartesianGrid stroke="#28313b" strokeDasharray="3 4" />
        <XAxis
          dataKey="x"
          type="number"
          domain={["dataMin", "dataMax"]}
          stroke="#98a5b3"
          tickFormatter={(v) => Number(v).toFixed(1)}
        />
        <YAxis stroke="#98a5b3" domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{
            background: "#15202b",
            border: "1px solid #52616d",
            borderRadius: 8,
          }}
          labelFormatter={(v) => `t/D₀²: ${Number(v).toPrecision(5)} s/mm²`}
        />
        <Line
          type="linear"
          dataKey="y"
          name="(D/D₀)²"
          stroke="#ffab73"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
