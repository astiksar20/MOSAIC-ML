import React from 'react';
import { Panel, Pill } from './Panel';

export const PermissionRisk = ({ data }) => {
  const p = data?.permission_risk;
  if (!p) return null;

  const undefinedScore = p.score === null || p.score === undefined;

  return (
    <Panel
      label="Step 03 — Permission risk"
      title="Dangerous-permission score"
      lead="Each permission carries a weight learned from how often malicious and benign training apps request it. The score is the mean weight of the permissions this APK actually asks for."
      aside={<Pill tone={undefinedScore ? 'dim' : 'accent'}>
        {undefinedScore ? 'No evidence' : `${p.score_0_100} / 100`}
      </Pill>}
    >
      {undefinedScore ? (
        <div className="card stack">
          <span className="sub">Insufficient permission evidence</span>
          <p className="muted small">{p.explanation}</p>
          <p className="note note-warn">
            This is an absence of evidence, not evidence of low risk. No score is reported
            rather than reporting zero.
          </p>
        </div>
      ) : (
        <div className="grid-2">
          <div className="card stack">
            <span className="label">R(a) — mean weight</span>
            <span className="mono" style={{ fontSize: 44, fontWeight: 500, letterSpacing: '-0.03em' }}>
              {p.score.toFixed(4)}
            </span>
            <div className="bar"><span style={{ width: `${p.score * 100}%` }} /></div>
            <dl className="kv" style={{ marginTop: 6 }}>
              <dt>Permissions matched</dt><dd>{p.permissions_matched} of {p.selected_set_size}</dd>
              <dt>Display scale</dt><dd>{p.score_0_100} / 100</dd>
            </dl>
          </div>

          <div className="card">
            <table>
              <thead><tr><th>Permission</th><th>α</th><th>β</th><th>r</th></tr></thead>
              <tbody>
                {(p.contributions || []).map((c) => (
                  <tr key={c.permission}>
                    <td className="mono" style={{ fontSize: 12.5 }}>{c.permission}</td>
                    <td className="mono muted">{c.alpha.toFixed(3)}</td>
                    <td className="mono muted">{c.beta.toFixed(3)}</td>
                    <td className="mono accent">{c.r.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="stack" style={{ gap: 12 }}>
        <span className="label">Method</span>
        <p className="mono small muted">r = √(α × (1 − β))&nbsp;&nbsp;·&nbsp;&nbsp;R(a) = Σ λ·r ⁄ k, for k &gt; 0</p>
        <p className="note">
          Adapted from Ogwara et al. (2024), Future Internet 16(8) 271. Weights fitted on the
          training split only. The 0–100 form is a display rescaling, not a probability of malware.
        </p>
      </div>
    </Panel>
  );
};
