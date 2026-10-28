import React from 'react';

export const Panel = ({ label, title, lead, aside, children }) => (
  <section className="section fade">
    <div className="shell stack-lg">
      <div className="row-between">
        <div className="stack" style={{ gap: 10 }}>
          <span className="label">{label}</span>
          <h2 className="title">{title}</h2>
          {lead && <p className="lead">{lead}</p>}
        </div>
        {aside}
      </div>
      {children}
    </div>
  </section>
);

export const Metric = ({ label, value, suffix, tone }) => (
  <div className="card metric">
    <span className="label">{label}</span>
    <span className="value" style={tone ? { color: `var(--${tone})` } : undefined}>
      {value}
      {suffix && <span className="dim" style={{ fontSize: 15, marginLeft: 4 }}>{suffix}</span>}
    </span>
  </div>
);

export const Pill = ({ tone = 'dim', children }) => (
  <span className={`pill pill-${tone}`}><span className="dot" />{children}</span>
);
