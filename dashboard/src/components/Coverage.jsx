import React from 'react';
import { Panel, Pill } from './Panel';

export const Coverage = ({ data }) => {
  const c = data?.feature_coverage;
  if (!c) return null;

  const blocks = [
    ['Permissions', c.by_block?.permissions],
    ['Intents', c.by_block?.intents],
    ['API calls', c.by_block?.api_calls],
  ];

  return (
    <Panel
      label="Step 01 — Input quality"
      title="Feature coverage"
      lead="How much of the trained model could be populated from this APK. Every result below inherits its reliability from this number."
      aside={<Pill tone={c.reliable ? 'ok' : 'warn'}>{c.reliable ? 'Sufficient' : 'Low coverage'}</Pill>}
    >
      <div className="grid-2">
        <div className="card stack">
          <span className="label">Matched features</span>
          <div className="row" style={{ gap: 10, alignItems: 'baseline' }}>
            <span className="mono" style={{ fontSize: 38, fontWeight: 500, letterSpacing: '-0.02em' }}>
              {c.matched_features?.toLocaleString()}
            </span>
            <span className="muted mono">of {c.total_features?.toLocaleString()}</span>
          </div>
          <div className="bar"><span style={{ width: `${Math.max(c.coverage_percent, 0.4)}%` }} /></div>
          <span className="label">{c.coverage_percent}% of the model vocabulary</span>
        </div>

        <div className="card">
          <table>
            <thead><tr><th>Block</th><th>Matched</th><th>Extracted</th><th>Vocabulary</th></tr></thead>
            <tbody>
              {blocks.map(([name, b]) => b && (
                <tr key={name}>
                  <td>{name}</td>
                  <td className="mono">{b.matched}</td>
                  <td className="mono muted">{b.extracted}</td>
                  <td className="mono dim">{b.vocabulary_size?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {c.warning && <p className="note note-warn">{c.warning}</p>}
    </Panel>
  );
};
