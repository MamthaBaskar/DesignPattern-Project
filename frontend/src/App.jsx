import React, { useState } from 'react';
import {
  FileText,
  Upload,
  ArrowRight,
  ArrowLeft,
  Download,
  AlertCircle,
  CheckCircle2,
  FileCheck,
  Filter,
  RefreshCw,
  Sparkles,
  ShieldAlert
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

export default function App() {
  // Screen state: 'upload' or 'results'
  const [currentScreen, setCurrentScreen] = useState('upload');

  // Upload Screen State
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  // Default to semantic strategy internally without exposing technical selection UI
  const [strategy] = useState('semantic');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  // Results Screen State
  const [comparisonResult, setComparisonResult] = useState(null);
  const [activeFilter, setActiveFilter] = useState('All'); // 'All', 'Added', 'Deleted', 'Modified', 'High', 'Medium', 'Low'

  // Handle file selections
  const handleOldFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setOldFile(e.target.files[0]);
      setErrorMessage('');
    }
  };

  const handleNewFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setNewFile(e.target.files[0]);
      setErrorMessage('');
    }
  };

  // Quick load sample files (75% -> 80% attendance policy demo)
  const handleLoadSample = () => {
    setErrorMessage('');
    const oldName = 'attendance_policy_2025.txt';
    const newName = 'attendance_policy_2026.txt';
    const mimeType = 'text/plain';

    const oldContent = `# Academic Attendance and Governance Policy\n\nSection 1: General Student Requirements\nAll enrolled full-time students must register their biometric presence upon entering the campus.\nMinimum attendance is 75%.\nStudents must submit the form to the academic registrar before the deadline.\n\nSection 2: Examination Clearance\nAny candidate failing to satisfy the attendance threshold will be prohibited from taking final examinations.`;
    const newContent = `# Academic Attendance and Governance Policy\n\nSection 1: General Student Requirements\nAll enrolled full-time students must register their biometric presence upon entering the campus.\nMinimum attendance is 80%.\nStudents are required to submit the form to the academic registrar before the deadline.\n\nSection 2: Examination Clearance\nAny candidate failing to satisfy the attendance threshold will be prohibited from taking final examinations.\n\nSection 3: Appeals and Exemptions\nStudents with verified medical exemptions may submit an appeal within 5 business days of publication.`;

    const oldBlob = new Blob([oldContent], { type: mimeType });
    const newBlob = new Blob([newContent], { type: mimeType });

    setOldFile(new File([oldBlob], oldName, { type: mimeType }));
    setNewFile(new File([newBlob], newName, { type: mimeType }));
  };

  // Execute Comparison
  const handleCompare = async () => {
    if (!oldFile || !newFile) {
      setErrorMessage('Please choose both the Old Document and the New Document before comparing.');
      return;
    }

    setErrorMessage('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('old_file', oldFile);
      formData.append('new_file', newFile);
      formData.append('strategy', strategy);

      const response = await fetch(`${API_BASE}/api/compare`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || errorData.message || `Server responded with code ${response.status}`);
      }

      const data = await response.json();
      setComparisonResult(data);
      setActiveFilter('All');
      setCurrentScreen('results');
    } catch (err) {
      console.error('Comparison request failed:', err);
      setErrorMessage(err.message || 'Failed to compare documents. Check server connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // PDF Report Download
  const handleDownloadPdf = async () => {
    if (!comparisonResult) return;

    setIsDownloadingPdf(true);
    try {
      const response = await fetch(`${API_BASE}/api/report/pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(comparisonResult),
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF report from server.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Comparison_Report_${comparisonResult.summary.old_filename}_vs_${comparisonResult.summary.new_filename}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Error downloading PDF report: ' + err.message);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  // Filter changes
  const getFilteredChanges = () => {
    if (!comparisonResult || !comparisonResult.changes) return [];
    const allChanges = comparisonResult.changes;

    switch (activeFilter) {
      case 'Added':
        return allChanges.filter((c) => c.change_type === 'ADDED');
      case 'Deleted':
        return allChanges.filter((c) => c.change_type === 'DELETED');
      case 'Modified':
        return allChanges.filter((c) => c.change_type === 'MODIFIED');
      case 'High':
        return allChanges.filter((c) => c.importance === 'HIGH');
      case 'Medium':
        return allChanges.filter((c) => c.importance === 'MEDIUM');
      case 'Low':
        return allChanges.filter((c) => c.importance === 'LOW');
      case 'All':
      default:
        return allChanges;
    }
  };

  // Helper to format simplified explanations in student-friendly English
  const formatSimpleExplanation = (explanation) => {
    if (!explanation) return 'This sentence was updated between versions.';
    if (explanation.includes('without altering obligations or terms') || explanation.includes('clarified or restated')) {
      return 'The wording changed, but the meaning stayed the same.';
    }
    return explanation.replace(/^\[Text Diff\]\s*/i, '');
  };

  // Helper to render practical impact as readable bullet points
  const renderImpactBullets = (impactText) => {
    if (!impactText) {
      return <p className="meta-block-text">No specific impact noted.</p>;
    }

    const lines = impactText
      .split(/\n|•/)
      .map((line) => line.trim().replace(/^[-*•]\s*/, ''))
      .filter(Boolean);

    if (lines.length === 0) {
      return <p className="meta-block-text">{impactText}</p>;
    }

    return (
      <ul className="impact-bullet-list">
        {lines.map((line, idx) => (
          <li key={idx}>{line}</li>
        ))}
      </ul>
    );
  };

  const filteredChanges = getFilteredChanges();

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-icon">
            <FileText size={22} />
          </div>
          <div>
            <div className="brand-title">AI Document Comparison System</div>
          </div>
        </div>

        {currentScreen === 'results' && (
          <div className="results-actions">
            <button
              className="btn-secondary"
              onClick={() => setCurrentScreen('upload')}
            >
              <ArrowLeft size={16} /> Return to Upload
            </button>
            <button
              className="btn-primary"
              onClick={handleDownloadPdf}
              disabled={isDownloadingPdf}
              style={{ padding: '8px 18px', fontSize: '0.88rem' }}
            >
              <Download size={16} />
              {isDownloadingPdf ? 'Generating PDF...' : 'Download PDF Report'}
            </button>
          </div>
        )}
      </header>

      {/* Main Container */}
      <main className="main-content">
        {/* ========================================================= */}
        {/* SCREEN 1: UPLOAD DOCUMENTS                                */}
        {/* ========================================================= */}
        {currentScreen === 'upload' && (
          <div>
            <div className="upload-screen-hero">
              <h1 className="hero-title">Compare Documents & Analyze Changes</h1>
              <p className="hero-subtitle">
                Upload your old and new documents to see what was added, removed, or modified — and understand whether the actual meaning changed.
              </p>
              <div className="tech-pills">
                <span className="tech-pill">Supported Formats: PDF, DOCX, TXT</span>
              </div>
            </div>

            {errorMessage && (
              <div className="alert-error">
                <AlertCircle size={20} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Optional Quick Sample Box */}
            <div className="sample-box">
              <div className="sample-box-text">
                <strong>Want to try a quick test?</strong> Load sample files showing an attendance rule change from 75% to 80%.
              </div>
              <button
                type="button"
                className="btn-sample"
                onClick={handleLoadSample}
              >
                Load Attendance Sample (75% → 80%)
              </button>
            </div>

            {/* Upload Two File Cards */}
            <div className="upload-grid">
              {/* OLD DOCUMENT UPLOAD */}
              <label className={`dropzone-card ${oldFile ? 'has-file' : ''}`}>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  style={{ display: 'none' }}
                  onChange={handleOldFileChange}
                />
                <div className="dropzone-header old-doc">
                  <FileText size={18} /> Old Document (Baseline / Original)
                </div>
                <div className="dropzone-icon">
                  <Upload size={24} />
                </div>
                <div className="dropzone-title">
                  {oldFile ? oldFile.name : 'Choose Old Document'}
                </div>
                <div className="dropzone-hint">
                  {oldFile ? `${(oldFile.size / 1024).toFixed(1)} KB` : 'Click or drop PDF, DOCX, or TXT file'}
                </div>
                {oldFile && (
                  <div className="file-info-badge">
                    <CheckCircle2 size={16} color="#16a34a" /> Baseline Document Ready
                  </div>
                )}
              </label>

              {/* NEW DOCUMENT UPLOAD */}
              <label className={`dropzone-card ${newFile ? 'has-file' : ''}`}>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  style={{ display: 'none' }}
                  onChange={handleNewFileChange}
                />
                <div className="dropzone-header new-doc">
                  <FileText size={18} /> New Document (Updated / Revised)
                </div>
                <div className="dropzone-icon">
                  <Upload size={24} />
                </div>
                <div className="dropzone-title">
                  {newFile ? newFile.name : 'Choose New Document'}
                </div>
                <div className="dropzone-hint">
                  {newFile ? `${(newFile.size / 1024).toFixed(1)} KB` : 'Click or drop PDF, DOCX, or TXT file'}
                </div>
                {newFile && (
                  <div className="file-info-badge">
                    <CheckCircle2 size={16} color="#16a34a" /> Updated Document Ready
                  </div>
                )}
              </label>
            </div>

            {/* Action Button */}
            <div className="action-wrapper">
              <button
                className="btn-primary"
                onClick={handleCompare}
                disabled={isLoading || !oldFile || !newFile}
              >
                {isLoading ? (
                  <>
                    <RefreshCw size={18} className="animate-spin" />
                    Comparing documents and analyzing changes...
                  </>
                ) : (
                  <>
                    Compare Documents <ArrowRight size={18} />
                  </>
                )}
              </button>
            </div>

            {/* Loading Indicator */}
            {isLoading && (
              <div className="loading-box">
                <div className="spinner"></div>
                <h3>Comparing Documents</h3>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '6px' }}>
                  Reading text, detecting sections, and evaluating meaning changes...
                </p>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* SCREEN 2: COMPARISON RESULTS                              */}
        {/* ========================================================= */}
        {currentScreen === 'results' && comparisonResult && (
          <div>
            {/* Top Bar Details */}
            <div className="results-header-bar">
              <div>
                <h2 className="results-meta-title">Comparison Results</h2>
                <div className="results-docs-subtitle">
                  <span>Baseline: <b>{comparisonResult.summary.old_filename}</b></span>
                  <span>vs</span>
                  <span>Revised: <b>{comparisonResult.summary.new_filename}</b></span>
                </div>
              </div>
            </div>

            {/* Summary Metrics Bar with Clear Explanations */}
            <div className="metrics-grid">
              <div className="metric-card">
                <div>
                  <div className="metric-label">Total Changes</div>
                  <div className="metric-value">{comparisonResult.summary.total_changes}</div>
                </div>
                <div className="metric-desc">Total number of detected changes.</div>
              </div>

              <div className="metric-card">
                <div>
                  <div className="metric-label">Added</div>
                  <div className="metric-value highlight-added">{comparisonResult.summary.added_count}</div>
                </div>
                <div className="metric-desc">New content present in the new document but not in the old document.</div>
              </div>

              <div className="metric-card">
                <div>
                  <div className="metric-label">Deleted</div>
                  <div className="metric-value highlight-deleted">{comparisonResult.summary.deleted_count}</div>
                </div>
                <div className="metric-desc">Content present in the old document but removed from the new document.</div>
              </div>

              <div className="metric-card">
                <div>
                  <div className="metric-label">Modified</div>
                  <div className="metric-value highlight-modified">{comparisonResult.summary.modified_count}</div>
                </div>
                <div className="metric-desc">Existing content that has been changed.</div>
              </div>

              <div className="metric-card">
                <div>
                  <div className="metric-label">High Importance</div>
                  <div className="metric-value highlight-high">{comparisonResult.summary.high_importance_count}</div>
                </div>
                <div className="metric-desc">Significant requirement or rule changes.</div>
              </div>

              <div className="metric-card">
                <div>
                  <div className="metric-label">Med Importance</div>
                  <div className="metric-value highlight-med">{comparisonResult.summary.medium_importance_count}</div>
                </div>
                <div className="metric-desc">Moderate updates to details or process.</div>
              </div>

              <div className="metric-card">
                <div>
                  <div className="metric-label">Low Importance</div>
                  <div className="metric-value highlight-low">{comparisonResult.summary.low_importance_count}</div>
                </div>
                <div className="metric-desc">Minor wording or phrasing changes.</div>
              </div>
            </div>

            {/* Filter Tabs strictly matching requirements */}
            <div className="filter-container">
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#64748b', marginRight: '4px' }}>
                <Filter size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Filter:
              </span>
              {[
                { label: 'All', count: comparisonResult.changes.length },
                { label: 'Added', count: comparisonResult.summary.added_count },
                { label: 'Deleted', count: comparisonResult.summary.deleted_count },
                { label: 'Modified', count: comparisonResult.summary.modified_count },
                { label: 'High', count: comparisonResult.summary.high_importance_count },
                { label: 'Medium', count: comparisonResult.summary.medium_importance_count },
                { label: 'Low', count: comparisonResult.summary.low_importance_count },
              ].map((f) => (
                <button
                  key={f.label}
                  className={`filter-tab ${activeFilter === f.label ? 'active' : ''}`}
                  onClick={() => setActiveFilter(f.label)}
                >
                  {f.label}
                  <span className="filter-count">{f.count}</span>
                </button>
              ))}
            </div>

            {/* Individual Change Findings */}
            {filteredChanges.length === 0 ? (
              <div className="empty-state">
                <h3 className="empty-state-title">No changes match the selected filter</h3>
                <p className="empty-state-text">Select 'All' or a different filter to view other detected document changes.</p>
              </div>
            ) : (
              <div className="change-list">
                {filteredChanges.map((change, index) => {
                  const typeClass =
                    change.change_type === 'ADDED'
                      ? 'badge-type-added'
                      : change.change_type === 'DELETED'
                      ? 'badge-type-deleted'
                      : 'badge-type-modified';

                  const impClass =
                    change.importance === 'HIGH'
                      ? 'badge-imp-high'
                      : change.importance === 'MEDIUM'
                      ? 'badge-imp-med'
                      : 'badge-imp-low';

                  const confClass =
                    change.confidence === 'HIGH'
                      ? 'badge-conf-high'
                      : change.confidence === 'MEDIUM'
                      ? 'badge-conf-med'
                      : 'badge-conf-low';

                  return (
                    <div key={change.id || index} className="change-card">
                      {/* Card Header */}
                      <div className="change-card-header">
                        <div className="badges-group">
                          <span className={`badge ${typeClass}`}>
                            {change.change_type}
                          </span>
                          <span className="badge badge-category">
                            {change.category}
                          </span>
                          <span className={`badge ${impClass}`}>
                            Importance: {change.importance}
                          </span>
                          <span className={`badge ${confClass}`}>
                            AI Confidence: {change.confidence}
                          </span>
                          {change.is_meaningful ? (
                            <span className="badge badge-imp-high">
                              Meaningful Change
                            </span>
                          ) : (
                            <span className="badge badge-imp-low">
                              Wording Only
                            </span>
                          )}
                        </div>

                        <div className="location-info">
                          {change.section || 'General'}
                          {change.location && ` • ${change.location}`}
                        </div>
                      </div>

                      {/* Visual Diff: Old Text vs New Text */}
                      <div className="diff-container">
                        <div className="diff-box diff-old">
                          <div className="diff-box-label">
                            <ArrowLeft size={12} /> Previous Text (Old)
                          </div>
                          <div>{change.old_text || '— (No previous content; newly added) —'}</div>
                        </div>

                        <div className="diff-box diff-new">
                          <div className="diff-box-label">
                            <ArrowRight size={12} /> Revised Text (New)
                          </div>
                          <div>{change.new_text || '— (Content removed in revision) —'}</div>
                        </div>
                      </div>

                      {/* AI Explanation & Practical Impact */}
                      <div className="analysis-meta-container">
                        <div>
                          <div className="meta-block-title">
                            <Sparkles size={14} color="#2563eb" /> AI Explanation
                          </div>
                          <div className="meta-block-text">
                            {formatSimpleExplanation(change.explanation)}
                          </div>
                        </div>

                        <div>
                          <div className="meta-block-title">
                            <ShieldAlert size={14} color="#d97706" /> Practical Impact
                          </div>
                          <div className="meta-block-text">
                            {renderImpactBullets(change.impact)}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
