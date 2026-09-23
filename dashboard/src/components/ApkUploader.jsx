import React, { useState, useRef } from 'react';
import { UploadCloud, FileCode, X, Play, AlertCircle } from 'lucide-react';

export const ApkUploader = ({ onAnalyze, isLoading, error, isOnline, onClearError }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileValidationError, setFileValidationError] = useState('');
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    setFileValidationError('');
    if (onClearError) onClearError();

    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.apk')) {
      setFileValidationError('Invalid file type! Please upload an Android Package (.apk) file.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFileValidationError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyzeClick = () => {
    if (!selectedFile) return;
    onAnalyze(selectedFile);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="saas-card p-8 md:p-12 mb-12 relative overflow-hidden border-cyan-500/20">
      {/* Background Ambient Lighting */}
      <div className="absolute -top-32 -right-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -left-32 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Info */}
      <div className="max-w-3xl mb-8">
        <h2 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
          Analyze Android Application
        </h2>
        <p className="text-slate-300 text-sm md:text-base mt-3 leading-relaxed">
          Upload an APK to perform static analysis, machine-learning classification, vulnerability intelligence, intrusion detection, and explainable risk assessment.
        </p>
      </div>

      {/* Error Alert */}
      {(error || fileValidationError) && (
        <div className="mb-8 p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-4 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-bold text-rose-200">Analysis Notice</h4>
            <p className="mt-1">{error || fileValidationError}</p>
          </div>
          {onClearError && (
            <button onClick={onClearError} className="text-rose-400 hover:text-rose-200">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      )}

      {/* Drag & Drop Upload Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-10 md:p-14 text-center transition-all duration-300 cursor-pointer ${
          isDragOver
            ? 'border-cyan-400 bg-cyan-950/40 shadow-[0_0_40px_rgba(6,182,212,0.2)]'
            : selectedFile
            ? 'border-cyan-500/40 bg-slate-900/80'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/60'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".apk"
          className="hidden"
        />

        {!selectedFile ? (
          <div className="flex flex-col items-center justify-center space-y-5">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-b from-cyan-500/20 to-slate-900 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-xl shadow-cyan-500/10 group-hover:scale-105 transition-transform">
              <UploadCloud className="w-10 h-10" />
            </div>

            <div>
              <p className="text-base font-bold text-slate-200">
                Drag & drop your <span className="text-cyan-400 font-mono">.APK</span> file here, or{' '}
                <span className="text-cyan-400 underline underline-offset-4">Browse files</span>
              </p>
              <p className="text-xs text-slate-400 mt-2">
                Supports standard Android Package files (.apk)
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-3">
            <div className="flex items-center gap-5 text-left">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 shrink-0">
                <FileCode className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center gap-3 flex-wrap">
                  <h3 className="text-base md:text-lg font-bold text-slate-100 font-mono break-word-all">
                    {selectedFile.name}
                  </h3>
                  <span className="status-pill pill-low text-[10px] font-mono">
                    APK FILE
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 font-mono">
                  Size: {formatFileSize(selectedFile.size)} • Ready for multi-engine scan
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 w-full md:w-auto">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                className="flex-1 md:flex-none px-5 py-3 rounded-2xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors flex items-center justify-center gap-2"
              >
                <X className="w-4 h-4" />
                <span>Remove</span>
              </button>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAnalyzeClick();
                }}
                disabled={isLoading}
                className="flex-1 md:flex-none px-8 py-3.5 rounded-2xl text-sm font-extrabold transition-all shadow-xl flex items-center justify-center gap-3 bg-gradient-to-r from-cyan-500 via-blue-600 to-violet-600 hover:from-cyan-400 hover:to-violet-500 text-white shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>ANALYZE APK</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
