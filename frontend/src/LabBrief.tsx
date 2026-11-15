type LabBriefProps = {
  tone: "gases" | "suppression" | "droplet" | "ai";
  dataset: string;
  purpose: string;
  service: string;
  output: string;
};

export default function LabBrief({ tone, dataset, purpose, service, output }: LabBriefProps) {
  return (
    <aside className={`lab-brief lab-brief--${tone}`} aria-label={`${dataset} workspace purpose`}>
      <div className="lab-brief-identity">
        <span>DATASET</span>
        <strong>{dataset}</strong>
      </div>
      <div>
        <span>PURPOSE</span>
        <p>{purpose}</p>
      </div>
      <div>
        <span>SERVICE</span>
        <p>{service}</p>
      </div>
      <div>
        <span>DELIVERS</span>
        <p>{output}</p>
      </div>
    </aside>
  );
}
