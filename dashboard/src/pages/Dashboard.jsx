import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from '../components/Header';
import { Uploader } from '../components/Uploader';
import { Coverage } from '../components/Coverage';
import { MlResult } from '../components/MlResult';
import { PermissionRisk } from '../components/PermissionRisk';
import { CveResult } from '../components/CveResult';
import { HidsResult } from '../components/HidsResult';
import { Assessment } from '../components/Assessment';
import { History } from '../components/History';
import { checkApiHealth, analyzeApk, fetchHistory } from '../services/api';

export const DashboardPage = () => {
  const [online, setOnline] = useState(false);
  const [checking, setChecking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState(null);
  const resultRef = useRef(null);

  const health = useCallback(async () => {
    setChecking(true);
    try {
      const s = await checkApiHealth();
      setOnline(Boolean(s.online));
    } catch {
      setOnline(false);
    } finally {
      setChecking(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try { setHistory(await fetchHistory(10)); } catch { /* storage optional */ }
  }, []);

  useEffect(() => {
    health();
    loadHistory();
    const t = setInterval(health, 30000);
    return () => clearInterval(t);
  }, [health, loadHistory]);

  const analyse = async (file) => {
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await analyzeApk(file);
      setResult(data);
      loadHistory();
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 200);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        err?.message ||
        'The analysis request failed.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Header online={online} checking={checking} onCheck={health} />

      <section className="section-first">
        <div className="shell stack-lg">
          <div className="stack" style={{ gap: 18 }}>
            <span className="label">Android vulnerability &amp; intrusion risk analysis</span>
            <h1 className="display">
              Static evidence about an<br />Android app, reported honestly.
            </h1>
            <p className="lead">
              Upload an APK. Each signal is reported separately with its own
              limitations, rather than collapsed into a single verdict.
            </p>
          </div>

          <Uploader onAnalyze={analyse} loading={loading} disabled={!online} />

          {!online && !checking && (
            <p className="note note-warn">
              The backend is not reachable. Start it with
              {' '}<span className="mono">uvicorn api.main:app --port 8000</span>{' '}
              and check the status above.
            </p>
          )}

          {error && <p className="note note-warn">{error}</p>}
        </div>
      </section>

      <div ref={resultRef} />

      {result && (
        <>
          <Coverage data={result} />
          <MlResult data={result} />
          <PermissionRisk data={result} />
          <CveResult data={result} />
          <HidsResult data={result} />
          <Assessment data={result} />
        </>
      )}

      <History history={history} />

      <footer className="section">
        <div className="shell stack" style={{ gap: 14 }}>
          <span className="label">Limitations</span>
          <p className="muted small" style={{ maxWidth: '72ch', lineHeight: 1.75 }}>
            MOSAIC-ML is an academic prototype. It analyses APKs statically and never
            executes them. HIDS telemetry is simulated. A CVE keyword match does not
            establish that an application is affected. A low score means low indicated
            risk based on available evidence — never that an application is safe. The
            model was trained on MH-100K (2010–2022) and its behaviour on current
            applications is untested.
          </p>
        </div>
      </footer>
    </>
  );
};
