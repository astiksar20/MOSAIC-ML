import React from 'react';
import { Panel, Pill } from './Panel';

export const Assessment = ({ data }) => {
  const r = data?.risk_analysis;
  if (!r) return null;

  const tone = r.risk_category === 'HIGH' ? 'danger'
    : r.risk_category === 'MEDIUM' ? 'warn' : 'ok';

  return (
    <Panel
      label="Step 06 — Prototype assessment"
      title="Combined category"
      lead="A project-specific prototype formula. It is retained for continuity and is not an established standard."
      aside={<Pill tone={tone}>{r.risk_category}</Pill>}
    >
      <div className="grid-2">
        <div className="card metric">
          <span className="label">Prototype score</span>
          <span className="value">{r.risk_score}<span className="dim" style={{ fontSize: 17 }}> / 100</span></span>
          <span className="mono tiny dim" style={{ marginTop: 8 }}>{r.formula}</span>
        </div>
        <div className="card stack">
          <span className="label">Recommendation</span>
          <p style={{ fontSize: 16 }}>{r.recommendation}</p>
          <p className="muted tiny">
            This prototype cannot block, remove or quarantine an application.
          </p>
        </div>
      </div>

      {r.caveats && (
        <div className="stack" style={{ gap: 10 }}>
          <span className="label">Limitations of this score</span>
          {r.caveats.map((c, i) => <p key={i} className="note note-warn">{c}</p>)}
        </div>
      )}
    </Panel>
  );
};
