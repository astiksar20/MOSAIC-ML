import React from 'react';
import { Panel, Pill } from './Panel';

export const HidsResult = ({ data }) => {
  const h = data?.hids_analysis;
  if (!h) return null;

  const alerts = h.alerts || h.rule_alerts || [];
  const score = h.hids_score ?? h.score ?? 0;

  return (
    <Panel
      label="Step 05 — Host intrusion detection"
      title="HIDS prototype"
      lead="Rule matches and anomaly detection over runtime events."
      aside={<Pill tone="warn">Synthetic data</Pill>}
    >
      <p className="note note-warn">
        The telemetry below is simulated prototype data defined in the backend. It was not
        produced by the uploaded APK and is not from a monitored device. These results
        demonstrate the module only.
      </p>

      <div className="grid-2">
        <div className="card metric">
          <span className="label">Prototype HIDS score (simulated)</span>
          <span className="value">{typeof score === 'number' ? score.toFixed(2) : score}</span>
          <div className="bar"><span style={{ width: `${Math.min(score, 100)}%` }} /></div>
        </div>
        <div className="card stack">
          <span className="label">Rule alerts on simulated events</span>
          {alerts.length ? (
            <ul className="stack" style={{ gap: 8, listStyle: 'none' }}>
              {alerts.map((a, i) => (
                <li key={i} className="row" style={{ gap: 10 }}>
                  <span className="dot" style={{ color: 'var(--warn)' }} />
                  <span className="mono small">{a.event || a}</span>
                </li>
              ))}
            </ul>
          ) : <span className="muted small">No rules triggered.</span>}
        </div>
      </div>
    </Panel>
  );
};
