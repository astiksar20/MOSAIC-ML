import React, { useState, useEffect, useRef } from 'react';
import { Header } from '../components/Header';
import { ApkUploader } from '../components/ApkUploader';
import { AnalysisAnimation } from '../components/AnalysisAnimation';
import { ResultReveal } from '../components/ResultReveal';
import { RiskScore } from '../components/RiskScore';
import { SummaryCards } from '../components/SummaryCards';
import { MlAnalysis } from '../components/MlAnalysis';
import { HidsAnalysis } from '../components/HidsAnalysis';
import { CveAnalysis } from '../components/CveAnalysis';
import { ApkStaticAnalysis } from '../components/ApkStaticAnalysis';
import { Explainability } from '../components/Explainability';
import { Recommendation } from '../components/Recommendation';
import { Footer } from '../components/Footer';
import { checkApiHealth, analyzeApk } from '../services/api';

export const DashboardPage = () => {
  const [isOnline, setIsOnline] = useState(true);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyzedFileName, setAnalyzedFileName] = useState('');

  const resultRef = useRef(null);

  const handleCheckHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const status = await checkApiHealth();
      setIsOnline(status.online);
    } catch (err) {
      setIsOnline(false);
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    handleCheckHealth();
    const interval = setInterval(handleCheckHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyzeFile = async (file) => {
    setIsLoading(true);
    setError(null);
    setAnalyzedFileName(file.name);
    setAnalysisResult(null);

    try {
      const data = await analyzeApk(file);
      setAnalysisResult(data);

      // Smooth scroll to results reveal
      setTimeout(() => {
        if (resultRef.current) {
          resultRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 300);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Unable to connect to MOSAIC-ML backend at http://127.0.0.1:8000.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setError(null);
    setAnalyzedFileName('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        {/* 1. Header */}
        <Header
          isOnline={isOnline}
          onCheckHealth={handleCheckHealth}
          isCheckingHealth={isCheckingHealth}
        />

        {/* Spacious Main Container */}
        <main className="max-w-[1440px] mx-auto px-6 md:px-12 lg:px-16 space-y-12 lg:space-y-16">
          {/* 2. APK Upload Hero */}
          <ApkUploader
            onAnalyze={handleAnalyzeFile}
            isLoading={isLoading}
            error={error}
            isOnline={isOnline}
            onClearError={() => setError(null)}
          />

          {/* 3. Analysis Animation Experience during active API request */}
          {isLoading && (
            <AnalysisAnimation fileName={analyzedFileName} />
          )}

          {/* Analysis Results Flow */}
          {analysisResult && (
            <div ref={resultRef} className="space-y-12 lg:space-y-16 animate-fade-in">
              {/* 4. Result Reveal Banner & Reset Control */}
              <ResultReveal
                data={analysisResult}
                onReset={handleReset}
              />

              {/* 5. Risk Score Centerpiece */}
              <RiskScore data={analysisResult} />

              {/* 6. Executive Summary Cards */}
              <SummaryCards data={analysisResult} />

              {/* 7. Machine Learning Analysis */}
              <MlAnalysis data={analysisResult} />

              {/* 8. Host-Based Intrusion Detection (HIDS) */}
              <HidsAnalysis data={analysisResult} />

              {/* 9. CVE / NVD Intelligence */}
              <CveAnalysis data={analysisResult} />

              {/* 10. APK Static Analysis */}
              <ApkStaticAnalysis data={analysisResult} />

              {/* 11. Explainability ("Why did MOSAIC-ML produce this result?") */}
              <Explainability data={analysisResult} />

              {/* 12. Recommendation ("Recommended Action") */}
              <Recommendation data={analysisResult} />
            </div>
          )}
        </main>
      </div>

      {/* 13. Footer */}
      <Footer />
    </div>
  );
};
