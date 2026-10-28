import React from 'react';
import { Panel, Pill } from './Panel';

export const History = ({ history }) => {
  if (!history) return null;
  const rows = history.scans || [];

  return (
    <Panel
      label="Scan history"
      title="Previous analyses"
      lead="Stored scan records. The APK itself is never retained — only its SHA-256 and the analysis result."
      aside={<Pill tone={history.error ? 'warn' : 'dim'}>
        {history.error ? 'Unavailable' : `${rows.length} stored`}
      </Pill>}
    >
      {history.error ? (
        <p className="note note-warn">Storage unavailable: {history.error}</p>
      ) : rows.length === 0 ? (
        <p className="muted small">No scans recorded yet. Analyse an APK to create the first record.</p>
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>When</th><th>File</th><th>Package</th><th>Coverage</th><th>ML</th><th>Permission</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.scan_id}>
                  <td className="mono dim" style={{ fontSize: 12 }}>
                    {(r.created_utc || '').slice(0, 19).replace('T', ' ')}
                  </td>
                  <td className="mono" style={{ fontSize: 12.5 }}>{r.file_name}</td>
                  <td className="mono muted" style={{ fontSize: 12 }}>{r.package_name || '—'}</td>
                  <td className="mono">{r.matched_features ?? '—'}</td>
                  <td className="mono" style={{
                    color: r.ml_label === 'MALWARE' ? 'var(--danger)' : 'var(--ok)'
                  }}>{r.ml_label || '—'}</td>
                  <td className="mono">
                    {r.permission_score != null ? r.permission_score.toFixed(3) : 'n/a'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
};
