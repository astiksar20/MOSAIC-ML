import React from 'react';
import { Panel, Pill } from './Panel';

export const MlResult = ({ data }) => {
  const ml = data?.ml_analysis;
  if (!ml) return null;

  const malware = ml.label === 'MALWARE';
  const p = (ml.malware_probability ?? 0) * 100;
  const reliable = data?.feature_coverage?.reliable !== false;

  return (
    <Panel
      label="Step 02 — Machine learning"
      title="Model classification"
      lead={`${ml.model || "The selected classifier"}, trained on MH-100K static features. This is a similarity judgement against training data, not a verdict about behaviour.`}
      aside={<Pill tone={malware ? 'danger' : 'ok'}>{ml.label}</Pill>}
    >
      <div className="grid-2">
        <div className="card stack">
          <span className="label">Malware probability</span>
          <span className="mono" style={{ fontSize: 44, fontWeight: 500, letterSpacing: '-0.03em' }}>
            {p.toFixed(2)}<span className="dim" style={{ fontSize: 20 }}>%</span>
          </span>
          <div className="bar"><span style={{ width: `${p}%` }} /></div>
          <dl className="kv" style={{ marginTop: 6 }}>
            <dt>Benign probability</dt><dd>{((ml.benign_probability ?? 0) * 100).toFixed(2)}%</dd>
            <dt>Features supplied</dt><dd>{ml.matched_features}</dd>
          </dl>
        </div>

        <div className="card stack">
          <span className="label">How to read this</span>
          <p className="small muted" style={{ lineHeight: 1.7 }}>
            {reliable
              ? 'Coverage was sufficient for the classifier to see meaningful input. The score still reflects resemblance to MH-100K training samples (2010–2022), not an assessment of this app’s actual behaviour.'
              : 'Coverage was too low for this prediction to be treated as evidence. The model is responding to an input unlike anything in its training data.'}
          </p>
          <p className="note">
            A low probability means low indicated risk based on available evidence. It does
            not mean the application is safe.
          </p>
        </div>
      </div>
    </Panel>
  );
};
