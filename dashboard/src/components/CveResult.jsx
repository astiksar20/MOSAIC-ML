import React from 'react';
import { Panel, Pill } from './Panel';

export const CveResult = ({ data }) => {
  const look = data?.cve_lookup;
  const records = data?.cve_analysis?.results || data?.cve_analysis || [];
  if (!look) return null;

  const sc = look.status_counts || {};
  const failed = sc.lookup_failed || 0;
  const zero = sc.zero_records || 0;
  const found = sc.records_returned || 0;
  const list = Array.isArray(records) ? records : [];

  const tone = failed > 0 ? 'warn' : found > 0 ? 'accent' : 'dim';
  const summary = failed > 0 ? `${failed} lookup${failed > 1 ? 's' : ''} failed`
    : found > 0 ? `${list.length} record${list.length !== 1 ? 's' : ''}`
    : 'No matching records';

  return (
    <Panel
      label="Step 04 — Vulnerability intelligence"
      title="CVE / NVD lookup"
      lead="Component strings are searched against the National Vulnerability Database. A keyword match is a candidate, not proof that this APK is affected."
      aside={<Pill tone={tone}>{summary}</Pill>}
    >
      <div className="grid-3">
        <div className="card metric">
          <span className="label">Records returned</span>
          <span className="value">{found}</span>
        </div>
        <div className="card metric">
          <span className="label">Zero records</span>
          <span className="value">{zero}</span>
        </div>
        <div className="card metric">
          <span className="label">Lookup failed</span>
          <span className="value" style={{ color: failed ? 'var(--warn)' : undefined }}>{failed}</span>
        </div>
      </div>

      {list.length > 0 && (
        <div className="card">
          <table>
            <thead><tr><th>CVE</th><th>CVSS</th><th>Severity</th><th>Component</th></tr></thead>
            <tbody>
              {list.slice(0, 10).map((r, i) => (
                <tr key={r.cve_id || i}>
                  <td className="mono">{r.cve_id}</td>
                  <td className="mono">{r.cvss_score ?? '—'}</td>
                  <td className="mono muted">{r.cvss_severity ?? '—'}</td>
                  <td className="mono dim" style={{ fontSize: 12 }}>{r.searched_component}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="note note-warn">{look.interpretation}</p>
      <p className="note">
        Searched {look.components_searched} of {look.components_available} components.
        Rate limit: {look.rate_limit}.
      </p>
    </Panel>
  );
};
