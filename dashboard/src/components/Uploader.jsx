import React, { useRef, useState } from 'react';

export const Uploader = ({ onAnalyze, loading, disabled }) => {
  const input = useRef(null);
  const [file, setFile] = useState(null);
  const [over, setOver] = useState(false);
  const [problem, setProblem] = useState(null);

  const take = (f) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.apk')) {
      setProblem(`“${f.name}” is not an .apk file.`);
      setFile(null);
      return;
    }
    setProblem(null);
    setFile(f);
  };

  return (
    <div className="stack">
      <div
        className={`drop${over ? ' over' : ''}`}
        onClick={() => input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files?.[0]); }}
      >
        <input ref={input} type="file" accept=".apk"
               onChange={(e) => take(e.target.files?.[0])} />
        {file ? (
          <div className="stack" style={{ gap: 8, alignItems: 'center' }}>
            <span className="mono" style={{ fontSize: 15 }}>{file.name}</span>
            <span className="label">{(file.size / 1024 / 1024).toFixed(2)} MB — click to change</span>
          </div>
        ) : (
          <div className="stack" style={{ gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 17 }}>Drop an APK here</span>
            <span className="label">or click to browse</span>
          </div>
        )}
      </div>

      {problem && <p className="note note-warn">{problem}</p>}

      <div className="row">
        <button className="btn btn-primary" disabled={!file || loading || disabled}
                onClick={() => onAnalyze(file)}>
          {loading ? <><span className="spinner" />Analysing</> : <>Analyse APK →</>}
        </button>
        {file && !loading && (
          <button className="btn btn-ghost" onClick={() => { setFile(null); setProblem(null); }}>
            Clear
          </button>
        )}
      </div>

      <p className="note">
        The APK is analysed statically and is never executed. It is held in temporary
        storage for the duration of the scan and then deleted.
      </p>
    </div>
  );
};
