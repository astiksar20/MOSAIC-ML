import React from 'react';

export const Header = ({ online, checking, onCheck }) => (
  <header style={{ borderBottom: '1px solid var(--line-soft)' }}>
    <div className="shell row-between" style={{ paddingBlock: 22 }}>
      <div className="row" style={{ gap: 12 }}>
        <span style={{ color: 'var(--accent)', fontSize: 20, lineHeight: 1 }}>✳</span>
        <strong style={{ letterSpacing: '-0.02em', fontSize: 16 }}>MOSAIC-ML</strong>
        <span className="label" style={{ marginLeft: 6 }}>Android Risk Analyzer</span>
      </div>
      <button className="btn btn-ghost" onClick={onCheck} disabled={checking}
              style={{ padding: '9px 14px' }}>
        {checking ? <span className="spinner" /> : <span className="dot"
          style={{ color: online ? 'var(--ok)' : 'var(--danger)' }} />}
        {checking ? 'Checking' : online ? 'API Online' : 'API Offline'}
      </button>
    </div>
  </header>
);
