import React, { useState } from 'react';
import { 
  Activity, CheckCircle2, XCircle, AlertTriangle, 
  ArrowLeft, Clock, Eye, BarChart2, Plus, HeartPulse,
  Info, Cpu, ShieldAlert, Stethoscope, Layers
} from 'lucide-react';

/**
 * Formats timestamps into Indian standard date and time format:
 * DD/MM/YYYY, hh:mm:ss A IST
 */
const formatIndianTimestamp = (rawTs) => {
  if (!rawTs) return '—';
  try {
    const match = String(rawTs).match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2}))?/);
    if (match) {
      const [_, y, m, d, hh, mm, ss] = match;
      let h = parseInt(hh, 10);
      const ampm = h >= 12 ? 'PM' : 'AM';
      h = h % 12 || 12;
      const hhStr = String(h).padStart(2, '0');
      const ssStr = ss ? String(ss).padStart(2, '0') : '00';
      return `${d}/${m}/${y}, ${hhStr}:${mm}:${ssStr} ${ampm} IST`;
    }
    const date = new Date(rawTs);
    if (!isNaN(date.getTime())) {
      const d = String(date.getDate()).padStart(2, '0');
      const m = String(date.getMonth() + 1).padStart(2, '0');
      const y = date.getFullYear();
      let hours = date.getHours();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      const hhStr = String(hours).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');
      return `${d}/${m}/${y}, ${hhStr}:${minutes}:${seconds} ${ampm} IST`;
    }
  } catch {
    // Graceful fallback
  }
  return `${rawTs} IST`;
};

export const ResultPage = ({
  assessment,
  onBackToQueue,
  onGoToTimeline,
}) => {
  const [xrayView, setXrayView] = useState('overlay');
  const [showAllShapFeatures, setShowAllShapFeatures] = useState(false);

  const getPriorityStyle = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return {
          color: '#DC2626',
          border: '#DC2626',
          bg: '#FEF2F2',
          glow: '0 4px 16px rgba(220, 38, 38, 0.18)',
          label: 'LEVEL 1 • CRITICAL (Immediate Resuscitation)',
        };
      case 'HIGH':
        return {
          color: '#EA580C',
          border: '#EA580C',
          bg: '#FFF7ED',
          glow: '0 4px 14px rgba(234, 88, 12, 0.18)',
          label: 'LEVEL 2 • HIGH EMERGENT (< 15 min)',
        };
      case 'MODERATE':
        return {
          color: '#D97706',
          border: '#D97706',
          bg: '#FEFCE8',
          glow: '0 4px 14px rgba(217, 119, 6, 0.18)',
          label: 'LEVEL 3 • MODERATE URGENT (< 30 min)',
        };
      case 'LESS_URGENT':
        return {
          color: '#0284C7',
          border: '#0284C7',
          bg: '#F0F9FF',
          glow: 'none',
          label: 'LEVEL 4 • LOW RISK (< 60 min)',
        };
      default:
        return {
          color: '#059669',
          border: '#059669',
          bg: '#ECFDF5',
          glow: '0 4px 14px rgba(5, 150, 105, 0.18)',
          label: 'LEVEL 5 • NON-URGENT / ROUTINE (< 120 min)',
        };
    }
  };

  const priorityStyle = getPriorityStyle(assessment.priority);
  const mods = assessment.modalities_used;
  const hasSafetyOverrides = Array.isArray(assessment.safety_overrides) && assessment.safety_overrides.length > 0;
  const decisionBasis = hasSafetyOverrides ? 'ML Prediction + Safety Escalation' : 'ML Prediction';
  const formattedTimestamp = formatIndianTimestamp(assessment.timestamp);

  // Derive specific scan type if medical imaging was processed
  const imagingScanType = assessment.xray_analysis?.modality || 
    (assessment.xray_analysis?.detected_findings && assessment.xray_analysis.detected_findings.length > 0 ? 'Radiography' : null);

  // Exact confirmed count of successfully processed data sources
  const dataSourcesCount = mods?.count || (2 + (mods?.ecg ? 1 : 0) + (mods?.xray ? 1 : 0));

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '36px 24px 80px' }}>
      {/* TOP NAVIGATION & ACTIONS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <button onClick={onBackToQueue} className="btn btn-ghost" style={{ padding: '8px 12px' }}>
          <ArrowLeft size={16} />
          Back to Triage Queue
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => onGoToTimeline(assessment.patient_id)} 
            className="btn btn-secondary"
          >
            <Clock size={16} />
            View Patient Timeline
          </button>
          <button 
            onClick={() => onGoToTimeline(assessment.patient_id)} 
            className="btn btn-primary"
          >
            <Plus size={16} />
            Add New Observation (Dynamic Update)
          </button>
        </div>
      </div>

      {/* MASTER DECISION CARD: RISK & PRIORITY GAUGE */}
      <div className="glass-panel" style={{
        padding: '32px 36px',
        marginBottom: '28px',
        borderLeft: `6px solid ${priorityStyle.color}`,
        boxShadow: priorityStyle.glow,
        background: 'linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)'
      }}>
        {/* CARD HEADER: METADATA & METRICS */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '24px', marginBottom: '24px' }}>
          
          {/* LEFT: SUBTITLE, DECISION BASIS, HEADING & PATIENT INFO */}
          <div style={{ flex: '1 1 500px', minWidth: '280px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
                AI-Assisted Emergency Triage Assessment
              </div>
              
              {/* Decision Basis Indicator */}
              <div 
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '3px 9px',
                  borderRadius: '6px',
                  background: hasSafetyOverrides ? 'rgba(220, 38, 38, 0.08)' : 'rgba(16, 185, 129, 0.08)',
                  border: hasSafetyOverrides ? '1px solid rgba(220, 38, 38, 0.25)' : '1px solid rgba(16, 185, 129, 0.25)',
                  color: hasSafetyOverrides ? '#B91C1C' : '#047857',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'help'
                }}
                title={hasSafetyOverrides 
                  ? 'Triage priority determined by multimodal ML models with clinical safety rule override due to acute physiological risk.'
                  : 'Triage priority determined directly by multimodal machine learning predictive inference.'}
              >
                <Cpu size={13} />
                <span>Decision Basis: {decisionBasis}</span>
              </div>
            </div>

            {/* Dynamic Acuity Heading - wraps naturally while preserving color and acuity emphasis */}
            <h1 style={{ 
              fontSize: 'clamp(1.65rem, 3.2vw, 2.25rem)', 
              fontWeight: 800, 
              color: priorityStyle.color, 
              letterSpacing: '-0.02em', 
              lineHeight: 1.25,
              margin: '4px 0 10px',
              wordBreak: 'break-word',
              overflowWrap: 'break-word',
              maxWidth: '100%'
            }}>
              {priorityStyle.label}
            </h1>

            {/* Comprehensive Patient Metadata */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              flexWrap: 'wrap', 
              gap: '8px 14px', 
              fontSize: '0.925rem', 
              color: 'var(--text-secondary)' 
            }}>
              <div>
                Patient: <strong style={{ color: 'var(--text-primary)' }}>{assessment.patient_name || 'Anonymous Patient'}</strong>
              </div>
              <span style={{ color: 'var(--border-medium)' }}>•</span>
              <div>
                Patient ID: <code style={{ 
                  fontFamily: 'var(--font-mono)', 
                  background: '#F1F5F9', 
                  padding: '2px 6px', 
                  borderRadius: '4px',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem'
                }}>{assessment.patient_id}</code>
              </div>
              {assessment.assessment_id && (
                <>
                  <span style={{ color: 'var(--border-medium)' }}>•</span>
                  <div>
                    Assessment ID: <code style={{ 
                      fontFamily: 'var(--font-mono)', 
                      background: '#F1F5F9', 
                      padding: '2px 6px', 
                      borderRadius: '4px',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem'
                    }}>{assessment.assessment_id}</code>
                  </div>
                </>
              )}
              <span style={{ color: 'var(--border-medium)' }}>•</span>
              <div>
                Time: <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{formattedTimestamp}</span>
              </div>
            </div>
          </div>

          {/* RIGHT: RISK METRICS & TARGET RESPONSE */}
          <div style={{ 
            display: 'flex', 
            gap: '24px', 
            alignItems: 'center', 
            flexWrap: 'wrap',
            flexShrink: 0,
            background: 'rgba(248, 250, 252, 0.8)',
            padding: '14px 22px',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 1px 3px rgba(15, 23, 42, 0.03)'
          }}>
            
            {/* Multimodal Composite Risk Score */}
            <div style={{ textAlign: 'right' }}>
              <div 
                style={{ 
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.8rem', 
                  color: 'var(--text-muted)', 
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  cursor: 'help'
                }}
                title="Composite clinical risk score (0–100%) calculated by weighting the XGBoost KTAS classification probability distribution (55%) with available ECG (22%) and medical imaging (23%) abnormality scores, bounded by physiological safety overrides. Represents composite clinical severity, not an empirical outcome probability."
              >
                <span>Composite Risk Score</span>
                <Info size={13} color="var(--text-muted)" />
              </div>
              <div style={{ 
                fontSize: 'clamp(2.4rem, 4vw, 3.2rem)', 
                fontWeight: 800, 
                lineHeight: 1.05, 
                color: priorityStyle.color,
                marginTop: '2px'
              }}>
                {assessment.risk_score}%
              </div>
            </div>

            {/* Target Response & Confidence */}
            <div style={{ textAlign: 'right', borderLeft: '1px solid var(--border-medium)', paddingLeft: '24px' }}>
              <div 
                style={{ 
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.8rem', 
                  color: 'var(--text-muted)', 
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  cursor: 'help'
                }}
                title="Standard emergency triage target response window (KTAS protocol) assigned to this priority level. Provides department prioritization guidance, not a prediction of actual bedside physician arrival time."
              >
                <span>Target Response</span>
                <Info size={13} color="var(--text-muted)" />
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                {assessment.target_time}
              </div>
              <div 
                style={{ 
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.8rem', 
                  color: 'var(--text-muted)', 
                  marginTop: '4px',
                  cursor: 'help'
                }}
                title="Heuristic confidence index (60–96%) calculated directly as: 65% base + (20% × top XGBoost classification probability) + (15% × diagnostic data completeness ratio). Reflects classifier certainty and diagnostic data availability."
              >
                <span>Confidence: <strong style={{ color: 'var(--text-secondary)' }}>{assessment.confidence}%</strong></span>
                <Info size={12} color="var(--text-muted)" />
              </div>
            </div>
          </div>
        </div>

        {/* EMERGENCY ACUITY ESCALATION ALERT CONTAINER */}
        {hasSafetyOverrides && (
          <div style={{
            padding: '16px 20px',
            borderRadius: '10px',
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            color: '#991B1B',
            marginBottom: '20px',
            boxShadow: '0 1px 3px rgba(220, 38, 38, 0.06)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '0.9rem', color: '#991B1B' }}>
                <AlertTriangle size={18} color="#DC2626" style={{ flexShrink: 0 }} />
                <span>Emergency Acuity Escalation Triggered</span>
              </div>
              <span 
                style={{
                  fontSize: '0.725rem',
                  fontWeight: 600,
                  background: '#FEE2E2',
                  color: '#B91C1C',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '1px solid #FCA5A5'
                }}
                title="Deterministic clinical rule override applied to prevent undertriage of critically unstable patients."
              >
                Deterministic Clinical Safety Rule
              </span>
            </div>
            
            {/* Itemized Clinical Warning Factors */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {assessment.safety_overrides.map((override, idx) => (
                <div key={idx} style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  background: '#FFFFFF',
                  border: '1px solid #FCA5A5',
                  color: '#991B1B',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
                }}>
                  <span style={{ color: '#DC2626', fontSize: '0.7rem' }}>●</span>
                  <span>{override}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* DATA SOURCES USED SECTION */}
        <div style={{
          padding: '14px 20px',
          borderRadius: '10px',
          background: '#F8FAFC',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', gap: '16px 20px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 700 }}>
              Data Sources Used:
            </span>
            
            {/* 1. Clinical Demographics */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
              <CheckCircle2 size={16} color="#059669" />
              <span>
                Clinical Demographics <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>(Available & Processed)</span>
              </span>
            </div>

            {/* 2. Vital Signs */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
              <CheckCircle2 size={16} color="#059669" />
              <span>
                Vital Signs <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>(Available & Processed)</span>
              </span>
            </div>

            {/* 3. ECG Analysis */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
              {mods?.ecg ? (
                <>
                  <CheckCircle2 size={16} color="#059669" />
                  <span>
                    ECG Analysis <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>(Available & Processed)</span>
                  </span>
                </>
              ) : (
                <>
                  <XCircle size={16} color="var(--text-muted)" />
                  <span style={{ color: 'var(--text-muted)' }}>
                    ECG Analysis <span style={{ fontSize: '0.75rem' }}>(Not Provided)</span>
                  </span>
                </>
              )}
            </div>

            {/* 4. Medical Imaging */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
              {mods?.xray ? (
                <>
                  <CheckCircle2 size={16} color="#059669" />
                  <span>
                    Medical Imaging {imagingScanType ? `(${imagingScanType})` : ''} <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>(Available & Processed)</span>
                  </span>
                </>
              ) : (
                <>
                  <XCircle size={16} color="var(--text-muted)" />
                  <span style={{ color: 'var(--text-muted)' }}>
                    Medical Imaging <span style={{ fontSize: '0.75rem' }}>(Not Provided)</span>
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Dynamic Available Count Summary */}
          <div style={{ fontSize: '0.8rem', color: '#059669', fontWeight: 600 }}>
            {`Assessment generated using ${dataSourcesCount} available data sources.`}
          </div>
        </div>
      </div>

      {/* TWO COLUMN WORKFLOW: EXPLAINABILITY & DETAILS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', marginBottom: '28px' }}>
        
        {/* COLUMN 1: EXPLAINABILITY — SHAP CONTRIBUTION ANALYSIS */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <h2 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <BarChart2 size={20} color="#059669" />
              Explainability: Contributing Factors
            </h2>
            <span style={{ fontSize: '0.75rem', padding: '3px 8px', borderRadius: '4px', background: '#ECFDF5', color: '#059669', fontWeight: 600 }}>
              TreeSHAP
            </span>
          </div>

          {/* Model Output Explanation */}
          {assessment.shap_factors && typeof assessment.shap_factors === 'object' && assessment.shap_factors.explained_class_label ? (
            <>
              <div style={{ 
                padding: '10px 14px', 
                borderRadius: '8px', 
                background: '#F0F9FF', 
                border: '1px solid #BAE6FD', 
                marginBottom: '16px',
                fontSize: '0.825rem',
                color: '#0C4A6E',
                lineHeight: 1.5
              }}>
                <strong>Explaining:</strong> {assessment.shap_factors.explained_class_label}
                <span style={{ color: '#64748B', marginLeft: '8px' }}>
                  (Output scale: {assessment.shap_factors.output_scale || 'raw margin'})
                </span>
                {assessment.shap_factors.base_value != null && (
                  <span style={{ display: 'block', marginTop: '3px', fontSize: '0.775rem', color: '#64748B' }}>
                    Baseline value: {assessment.shap_factors.base_value}
                    {assessment.shap_factors.model_output != null && (
                      <> → Model output: {assessment.shap_factors.model_output}</>
                    )}
                  </span>
                )}
              </div>

              {/* HORIZONTAL SHAP CONTRIBUTION CHART */}
              {(() => {
                const allFeatures = assessment.shap_factors.features || [];
                const topK = assessment.shap_factors.top_k || 6;
                const [showAllFeatures, setShowAllFeatures] = [
                  showAllShapFeatures, setShowAllShapFeatures
                ];
                const displayFeatures = showAllFeatures ? allFeatures : allFeatures.slice(0, topK);
                const maxAbsValue = Math.max(...allFeatures.map(f => Math.abs(f.shap_value)), 0.001);

                if (allFeatures.length === 0) {
                  return (
                    <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      No SHAP feature contributions available for this assessment.
                    </div>
                  );
                }

                return (
                  <>
                    {/* SVG Horizontal Bar Chart */}
                    <div style={{ marginBottom: '16px' }}>
                      <svg
                        viewBox={`0 0 560 ${displayFeatures.length * 36 + 28}`}
                        style={{ width: '100%', height: `${displayFeatures.length * 36 + 28}px`, display: 'block', overflow: 'visible' }}
                      >
                        {/* Chart Background */}
                        <rect x="0" y="0" width="560" height={displayFeatures.length * 36 + 28} fill="#F8FAFC" rx="6" />
                        
                        {/* Axis Labels */}
                        <text x="280" y={displayFeatures.length * 36 + 20} textAnchor="middle" fontSize="9" fill="#94A3B8" fontFamily="inherit">
                          ← Decreases prediction | Increases prediction →
                        </text>

                        {/* Zero Reference Line */}
                        <line x1="280" y1="4" x2="280" y2={displayFeatures.length * 36} stroke="#CBD5E1" strokeWidth="1" strokeDasharray="3,3" />

                        {displayFeatures.map((f, i) => {
                          const barMaxWidth = 240;
                          const barWidth = (Math.abs(f.shap_value) / maxAbsValue) * barMaxWidth;
                          const isPositive = f.shap_value > 0;
                          const barColor = isPositive ? '#EF4444' : '#10B981';
                          const barX = isPositive ? 280 : 280 - barWidth;
                          const y = i * 36 + 12;

                          // Truncate label for chart
                          const chartLabel = f.label.length > 28 ? f.label.substring(0, 26) + '…' : f.label;
                          const valueText = f.shap_value > 0 ? `+${f.shap_value.toFixed(4)}` : f.shap_value.toFixed(4);

                          return (
                            <g key={i}>
                              {/* Hover highlight background */}
                              <rect
                                x="2" y={y - 6} width="556" height="30" rx="4"
                                fill="transparent"
                                style={{ cursor: 'pointer' }}
                              >
                                <title>{`${f.label}\nPatient value: ${f.patient_value != null ? `${f.patient_value}${f.unit ? ' ' + f.unit : ''}` : 'N/A'}\nSHAP contribution: ${valueText}\nDirection: ${f.direction === 'increases_risk' ? 'Increases' : f.direction === 'decreases_risk' ? 'Decreases' : 'Neutral'} prediction for this class`}</title>
                              </rect>

                              {/* Feature Label (left side) */}
                              <text
                                x={isPositive ? 275 : 275}
                                y={y + 10}
                                textAnchor="end"
                                fontSize="10"
                                fill="#334155"
                                fontFamily="inherit"
                                fontWeight="500"
                              >
                                {chartLabel}
                              </text>

                              {/* Bar */}
                              <rect
                                x={barX}
                                y={y + 1}
                                width={Math.max(barWidth, 2)}
                                height="16"
                                rx="3"
                                fill={barColor}
                                opacity="0.8"
                              />

                              {/* Value Label */}
                              <text
                                x={isPositive ? barX + barWidth + 4 : barX - 4}
                                y={y + 12}
                                textAnchor={isPositive ? 'start' : 'end'}
                                fontSize="9"
                                fill={barColor}
                                fontWeight="600"
                                fontFamily="inherit"
                              >
                                {valueText}
                              </text>
                            </g>
                          );
                        })}
                      </svg>
                    </div>

                    {/* Show More / Show Less Toggle */}
                    {allFeatures.length > topK && (
                      <button
                        type="button"
                        onClick={() => setShowAllShapFeatures(!showAllShapFeatures)}
                        style={{
                          display: 'block',
                          margin: '0 auto 16px',
                          padding: '5px 14px',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '6px',
                          background: '#FFFFFF',
                          color: '#059669',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {showAllShapFeatures 
                          ? `Show Top ${topK} Features` 
                          : `Show All ${allFeatures.length} Features`}
                      </button>
                    )}

                    {/* DETAILED FEATURE CONTRIBUTION LIST */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                        Feature Contributions — {assessment.shap_factors.explained_class_label}
                      </div>
                      {displayFeatures.map((f, i) => (
                        <div key={i} style={{
                          padding: '10px 14px',
                          borderRadius: '8px',
                          background: '#F8FAFC',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          gap: '12px'
                        }}>
                          <div style={{ flex: '1 1 auto', minWidth: 0 }}>
                            <div style={{ fontWeight: 600, fontSize: '0.875rem', lineHeight: 1.3 }}>{f.label}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                              {f.feature}
                              {f.patient_value != null && (
                                <span style={{ 
                                  marginLeft: '8px', 
                                  color: '#0F172A', 
                                  fontWeight: 600,
                                  background: '#E2E8F0',
                                  padding: '1px 6px',
                                  borderRadius: '3px'
                                }}>
                                  Value: {typeof f.patient_value === 'number' ? f.patient_value : String(f.patient_value)}
                                  {f.unit ? ` ${f.unit}` : ''}
                                </span>
                              )}
                            </div>
                          </div>
                          <div style={{ textAlign: 'right', flexShrink: 0 }}>
                            <span style={{
                              display: 'inline-block',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              fontSize: '0.8rem',
                              fontWeight: 700,
                              fontFamily: 'var(--font-mono, monospace)',
                              background: f.direction === 'increases_risk' ? '#FEF2F2' : f.direction === 'decreases_risk' ? '#ECFDF5' : '#F1F5F9',
                              color: f.direction === 'increases_risk' ? '#DC2626' : f.direction === 'decreases_risk' ? '#059669' : '#64748B',
                            }}>
                              {f.shap_value > 0 ? '+' : ''}{f.shap_value.toFixed(4)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                );
              })()}
            </>
          ) : (
            /* Fallback for legacy/unavailable SHAP format */
            <>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '16px' }}>
                Feature attribution data is not available for this assessment.
              </p>
              {/* Render legacy format if present as array */}
              {Array.isArray(assessment.shap_factors) && assessment.shap_factors.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
                  {assessment.shap_factors.map((f, i) => (
                    <div key={i} style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: '#F8FAFC',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{f.label}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{f.feature}</div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                          fontWeight: 700,
                          background: f.direction === 'increases_risk' ? '#FEF2F2' : '#ECFDF5',
                          color: f.direction === 'increases_risk' ? '#DC2626' : '#059669',
                        }}>
                          SHAP: {f.shap_value > 0 ? `+${f.shap_value}` : f.shap_value}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* CLINICAL SAFETY ALERTS — Rule-Based (Separate from SHAP) */}
          <div style={{ padding: '14px', borderRadius: '8px', background: '#FFF7ED', border: '1px solid #FED7AA', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              <AlertTriangle size={14} color="#C2410C" />
              <span style={{ fontSize: '0.8rem', color: '#9A3412', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Clinical Safety Alerts
              </span>
              <span style={{ fontSize: '0.675rem', color: '#C2410C', fontWeight: 500, marginLeft: '4px' }}>
                (Rule-Based — Not SHAP)
              </span>
            </div>
            <ul style={{ paddingLeft: '18px', fontSize: '0.825rem', color: '#7C2D12', lineHeight: 1.7, margin: 0 }}>
              {assessment.contributing_factors && assessment.contributing_factors.map((cf, idx) => (
                <li key={idx} style={{ 
                  color: cf.includes('Hypoxemia') || cf.includes('Tachycardia') || cf.includes('Shock') || cf.includes('Hypotension')
                    ? '#DC2626' : '#7C2D12',
                  fontWeight: cf.includes('Hypoxemia') || cf.includes('Tachycardia') || cf.includes('Shock') ? 600 : 400
                }}>
                  {cf}
                </li>
              ))}
            </ul>
            <div style={{ fontSize: '0.7rem', color: '#C2410C', marginTop: '6px', fontStyle: 'italic' }}>
              Generated by deterministic clinical safety rules from observed vital signs.
            </div>
          </div>

          {/* INTERPRETATION GUIDANCE PANEL */}
          <div style={{
            padding: '12px 14px',
            borderRadius: '8px',
            background: '#F8FAFC',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            lineHeight: 1.55
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '6px' }}>
              <Info size={13} color="var(--text-muted)" />
              <span style={{ fontWeight: 700, fontSize: '0.775rem', color: 'var(--text-secondary)' }}>How to Read SHAP Values</span>
            </div>
            <ul style={{ paddingLeft: '16px', margin: 0 }}>
              <li><strong style={{ color: '#DC2626' }}>Positive</strong> values push the model's output <strong>higher</strong> for this triage class (towards predicting it).</li>
              <li><strong style={{ color: '#059669' }}>Negative</strong> values push the model's output <strong>lower</strong> for this class (away from predicting it).</li>
              <li>SHAP values represent the model's internal log-odds contributions — <strong>they are not percentages of clinical risk</strong>.</li>
              <li>These explanations describe <strong>model behaviour</strong>, not proven medical causation.</li>
              <li>All clinical decisions should be made by qualified healthcare professionals.</li>
            </ul>
          </div>
        </div>

        {/* COLUMN 2: CLINICAL INDICES & CONTEXTUAL CONDITIONS */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <HeartPulse size={20} color="#059669" />
              Calculated Hemodynamics
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              <div style={{ padding: '12px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Shock Index</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 800, color: (assessment.clinical_indices?.shock_index ?? 0) > 0.9 ? '#DC2626' : '#059669' }}>
                  {assessment.clinical_indices?.shock_index ?? '—'}
                </span>
                <span style={{ fontSize: '0.675rem', color: 'var(--text-dim)', display: 'block' }}>HR/SBP ratio</span>
              </div>

              <div style={{ padding: '12px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>MAP</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 800 }}>
                  {assessment.clinical_indices?.map ?? '—'} <span style={{ fontSize: '0.7rem' }}>mmHg</span>
                </span>
                <span style={{ fontSize: '0.675rem', color: 'var(--text-dim)', display: 'block' }}>Mean Arterial</span>
              </div>

              <div style={{ padding: '12px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Pulse Pressure</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 800 }}>
                  {assessment.clinical_indices?.pulse_pressure ?? '—'} <span style={{ fontSize: '0.7rem' }}>mmHg</span>
                </span>
                <span style={{ fontSize: '0.675rem', color: 'var(--text-dim)', display: 'block' }}>SBP - DBP</span>
              </div>
            </div>
          </div>

          {/* EVIDENCE-GROUNDED MULTIMODAL CLINICAL DIFFERENTIAL */}
          <div>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Stethoscope size={18} color="#059669" />
                  Potential Clinical Conditions
                </h3>
                <span style={{ 
                  fontSize: '0.675rem', 
                  fontWeight: 700, 
                  padding: '3px 8px', 
                  borderRadius: '12px',
                  background: assessment.clinical_differential?.urgent_action_required ? '#FEE2E2' : '#F1F5F9',
                  color: assessment.clinical_differential?.urgent_action_required ? '#DC2626' : 'var(--text-secondary)',
                  border: `1px solid ${assessment.clinical_differential?.urgent_action_required ? '#FCA5A5' : 'var(--border-subtle)'}`
                }}>
                  {assessment.clinical_differential?.urgent_action_required ? 'Urgent Action Required' : 'Triage Decision Support'}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>
                AI-assisted clinical differential based on available assessment data. Not a confirmed diagnosis.
              </p>

              {/* Modality Consultation Chips */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                <span style={{ fontSize: '0.65rem', padding: '2px 7px', borderRadius: '4px', background: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0', fontWeight: 600 }}>
                  ✓ Symptoms
                </span>
                <span style={{ fontSize: '0.65rem', padding: '2px 7px', borderRadius: '4px', background: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0', fontWeight: 600 }}>
                  ✓ Vitals & Hemodynamics
                </span>
                <span style={{ 
                  fontSize: '0.65rem', 
                  padding: '2px 7px', 
                  borderRadius: '4px', 
                  background: assessment.ecg_analysis ? '#ECFDF5' : '#F1F5F9', 
                  color: assessment.ecg_analysis ? '#059669' : 'var(--text-dim)', 
                  border: `1px solid ${assessment.ecg_analysis ? '#A7F3D0' : '#E2E8F0'}`, 
                  fontWeight: 600 
                }}>
                  {assessment.ecg_analysis ? '✓ ECG Analyzed' : '○ ECG Not Provided'}
                </span>
                <span style={{ 
                  fontSize: '0.65rem', 
                  padding: '2px 7px', 
                  borderRadius: '4px', 
                  background: assessment.xray_analysis ? '#ECFDF5' : '#F1F5F9', 
                  color: assessment.xray_analysis ? '#059669' : 'var(--text-dim)', 
                  border: `1px solid ${assessment.xray_analysis ? '#A7F3D0' : '#E2E8F0'}`, 
                  fontWeight: 600 
                }}>
                  {assessment.xray_analysis ? '✓ Imaging Analyzed' : '○ Imaging Not Performed'}
                </span>
              </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {assessment.potential_conditions && assessment.potential_conditions.length > 0 ? (
                assessment.potential_conditions.map((c, i) => {
                  const concern = c.concern_level || (c.urgent_exclusion ? 'Urgent Exclusion' : 'Consider');
                  const isUrgent = concern === 'Urgent Exclusion' || c.urgent_exclusion;
                  
                  // Palette for qualitative concern levels (no fabricated percentages)
                  const badgeStyles = {
                    'Urgent Exclusion': { bg: '#FEE2E2', text: '#DC2626', border: '#FCA5A5' },
                    'High Concern': { bg: '#FFEDD5', text: '#C2410C', border: '#FDBA74' },
                    'Consider': { bg: '#EFF6FF', text: '#1D4ED8', border: '#BFDBFE' },
                    'Lower Concern': { bg: '#F1F5F9', text: '#475569', border: '#CBD5E1' }
                  }[concern] || { bg: '#F1F5F9', text: '#475569', border: '#CBD5E1' };

                  return (
                    <div key={i} style={{
                      padding: '14px 16px',
                      borderRadius: '10px',
                      background: isUrgent ? '#FFFDFD' : '#F8FAFC',
                      border: `1px solid ${isUrgent ? '#FECACA' : 'var(--border-subtle)'}`,
                      borderLeft: isUrgent ? '4px solid #DC2626' : '1px solid var(--border-subtle)',
                      boxShadow: isUrgent ? '0 1px 3px rgba(220, 38, 38, 0.08)' : 'none'
                    }}>
                      {/* Card Header: Condition Name & Qualitative Concern Badge */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                            <strong style={{ fontSize: '0.95rem', color: isUrgent ? '#991B1B' : 'var(--text-primary)', fontWeight: 700 }}>
                              {c.condition_name || c.condition}
                            </strong>
                            {c.clinical_category && (
                              <span style={{ fontSize: '0.675rem', padding: '1px 6px', borderRadius: '4px', background: '#E2E8F0', color: '#475569', fontWeight: 600 }}>
                                {c.clinical_category}
                              </span>
                            )}
                          </div>
                        </div>
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: badgeStyles.bg,
                          color: badgeStyles.text,
                          border: `1px solid ${badgeStyles.border}`,
                          whiteSpace: 'nowrap',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          {isUrgent && <AlertTriangle size={12} color="#DC2626" />}
                          {concern}
                        </span>
                      </div>

                      {/* Clinical Rationale */}
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.45, marginBottom: '8px' }}>
                        {c.reason_for_consideration || c.description || 'Clinical correlation recommended.'}
                      </p>

                      {/* Supporting Evidence Chips / Points */}
                      {c.supporting_evidence && c.supporting_evidence.length > 0 && (
                        <div style={{ marginBottom: '6px' }}>
                          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#065F46', display: 'block', marginBottom: '2px' }}>
                            Supporting Findings:
                          </span>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {c.supporting_evidence.map((ev, idx) => (
                              <span key={idx} style={{
                                fontSize: '0.7rem',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                background: '#ECFDF5',
                                color: '#065F46',
                                border: '1px solid #D1FAE5'
                              }}>
                                • {ev}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Missing Information / Essential Differentiators */}
                      {c.missing_information && c.missing_information.length > 0 && (
                        <div style={{ marginBottom: '6px' }}>
                          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#92400E', display: 'block', marginBottom: '2px' }}>
                            To Confirm or Rule Out:
                          </span>
                          <span style={{ fontSize: '0.725rem', color: '#78350F' }}>
                            {c.missing_information.join(' • ')}
                          </span>
                        </div>
                      )}

                      {/* Evidence Sources Pills */}
                      {c.evidence_sources && c.evidence_sources.length > 0 && (
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '8px', paddingTop: '6px', borderTop: '1px dashed var(--border-subtle)' }}>
                          <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', alignSelf: 'center' }}>Sources:</span>
                          {c.evidence_sources.map((src, idx) => (
                            <span key={idx} style={{
                              fontSize: '0.625rem',
                              padding: '1px 5px',
                              borderRadius: '3px',
                              background: '#F1F5F9',
                              color: '#64748B',
                              border: '1px solid #E2E8F0'
                            }}>
                              {src}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div style={{
                  padding: '16px',
                  borderRadius: '8px',
                  background: '#FEF3C7',
                  border: '1px solid #FDE68A',
                  display: 'flex',
                  gap: '12px',
                  alignItems: 'flex-start'
                }}>
                  <AlertTriangle size={18} color="#D97706" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#92400E' }}>
                      Clinical differential currently unavailable. Emergency triage assessment remains available.
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#B45309', marginTop: '2px' }}>
                      Deterministic clinical triage, vital signs monitoring, and emergency safety escalations remain active and fully operational.
                    </div>
                  </div>
                </div>
              )}

              {/* Recommended Bedside / Diagnostic Investigations */}
              {assessment.clinical_differential?.recommended_investigations && assessment.clinical_differential.recommended_investigations.length > 0 && (
                <div style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: '#F0FDF4',
                  border: '1px solid #BBF7D0',
                  marginTop: '4px'
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Activity size={14} color="#166534" />
                    Recommended Emergent Investigations:
                  </span>
                  <div style={{ fontSize: '0.75rem', color: '#14532D', marginTop: '4px', lineHeight: 1.4 }}>
                    {assessment.clinical_differential.recommended_investigations.join(' • ')}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* DIAGNOSTIC MODALITY DEEP DIVES: ECG & GRAD-CAM */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '28px' }}>
        
        {/* ECG WAVEFORM & RHYTHM CARD */}
        {assessment.ecg_analysis ? (
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Activity size={20} color="#059669" />
                ECG Rhythm Analysis
              </h2>
              <span style={{
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.8rem',
                fontWeight: 700,
                background: assessment.ecg_analysis.is_abnormal ? '#FEF2F2' : '#ECFDF5',
                color: assessment.ecg_analysis.is_abnormal ? '#DC2626' : '#059669',
                border: assessment.ecg_analysis.is_abnormal ? '1px solid #FECACA' : '1px solid #A7F3D0'
              }}>
                {assessment.ecg_analysis.predicted_class}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '18px', marginBottom: '14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <div>Heart Rate: <strong style={{ color: 'var(--text-primary)' }}>{assessment.ecg_analysis.estimated_heart_rate} bpm</strong></div>
              <div>QRS Duration: <strong style={{ color: 'var(--text-primary)' }}>{assessment.ecg_analysis.qrs_duration_ms} ms</strong></div>
              <div>Abnormality Score: <strong style={{ color: assessment.ecg_analysis.abnormality_score > 0.4 ? '#DC2626' : '#059669' }}>{Math.round(assessment.ecg_analysis.abnormality_score * 100)}%</strong></div>
            </div>

            {/* Waveform SVG Display - Hospital Paper Style */}
            {assessment.ecg_analysis.waveform && (
              <div style={{
                background: '#F0FDF4',
                border: '1px solid #A7F3D0',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '12px'
              }}>
                <svg viewBox="0 0 560 120" style={{ width: '100%', height: '110px', display: 'block' }}>
                  {/* Grid lines */}
                  <defs>
                    <pattern id="ecg-grid" width="20" height="20" patternUnits="userSpaceOnUse">
                      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(16, 185, 129, 0.25)" strokeWidth="0.75" />
                    </pattern>
                  </defs>
                  <rect width="560" height="120" fill="url(#ecg-grid)" />
                  
                  {/* Waveform polyline */}
                  <polyline
                    fill="none"
                    stroke="#059669"
                    strokeWidth="2"
                    points={assessment.ecg_analysis.waveform.map((val, idx) => {
                      const x = (idx / (assessment.ecg_analysis.waveform.length - 1)) * 550 + 5;
                      const y = 110 - (val * 90 + 10);
                      return `${x},${y}`;
                    }).join(' ')}
                  />
                </svg>
                <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', textAlign: 'right', marginTop: '4px' }}>
                  Lead II Standardization (125 Hz • 187 samples)
                </div>
              </div>
            )}

            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {assessment.ecg_analysis.interpretation_summary}
            </div>
          </div>
        ) : (
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <Activity size={36} color="var(--text-dim)" style={{ marginBottom: '12px' }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ECG Modality Not Provided</div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '300px', marginTop: '6px' }}>
              The system formulated this assessment without inventing or hallucinating cardiac lead data.
            </p>
          </div>
        )}

        {/* EMERGENCY DIAGNOSTIC IMAGING & GRAD-CAM VISUALIZER */}
        {assessment.xray_analysis ? (
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Eye size={20} color="#D97706" />
                {assessment.xray_analysis.modality || 'Emergency Diagnostic Imaging'}
              </h2>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                {assessment.xray_analysis.emergency_severity && (
                  <span style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    background: assessment.xray_analysis.emergency_severity === 'CRITICAL' ? '#FEF2F2' : (assessment.xray_analysis.emergency_severity === 'HIGH' ? '#FFF7ED' : '#FEFCE8'),
                    color: assessment.xray_analysis.emergency_severity === 'CRITICAL' ? '#DC2626' : (assessment.xray_analysis.emergency_severity === 'HIGH' ? '#EA580C' : '#D97706'),
                    border: '1px solid currentColor'
                  }}>
                    {assessment.xray_analysis.emergency_severity}
                  </span>
                )}
                <span style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  background: assessment.xray_analysis.is_abnormal ? '#FEF2F2' : '#ECFDF5',
                  color: assessment.xray_analysis.is_abnormal ? '#DC2626' : '#059669',
                  border: assessment.xray_analysis.is_abnormal ? '1px solid #FECACA' : '1px solid #A7F3D0'
                }}>
                  {assessment.xray_analysis.top_condition}
                </span>
              </div>
            </div>

            {/* Modality & Anatomic Body Region Metadata */}
            {assessment.xray_analysis.anatomical_region && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Region: <strong>{assessment.xray_analysis.anatomical_region}</strong>
                {assessment.xray_analysis.ai_engine && (
                  <span> • Engine: <strong style={{ color: '#059669' }}>{assessment.xray_analysis.ai_engine}</strong></span>
                )}
              </div>
            )}

            {/* View Selector Tabs (Overlay, Heatmap, Original Scan) */}
            {(assessment.xray_analysis.overlay_b64 || assessment.xray_analysis.heatmap_b64 || assessment.xray_analysis.original_image_b64) && (
              <>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                  <button 
                    type="button"
                    onClick={() => setXrayView('overlay')}
                    className={`btn ${xrayView === 'overlay' ? 'btn-primary' : 'btn-ghost'}`}
                    style={{ padding: '4px 12px', fontSize: '0.785rem' }}
                  >
                    Model Overlay
                  </button>
                  <button 
                    type="button"
                    onClick={() => setXrayView('heatmap')}
                    className={`btn ${xrayView === 'heatmap' ? 'btn-primary' : 'btn-ghost'}`}
                    style={{ padding: '4px 12px', fontSize: '0.785rem' }}
                  >
                    Attention Heatmap
                  </button>
                  <button 
                    type="button"
                    onClick={() => setXrayView('original')}
                    className={`btn ${xrayView === 'original' ? 'btn-primary' : 'btn-ghost'}`}
                    style={{ padding: '4px 12px', fontSize: '0.785rem' }}
                  >
                    Original Scan
                  </button>
                </div>

                {/* Visualizer Frame */}
                <div style={{
                  borderRadius: '8px',
                  overflow: 'hidden',
                  background: '#0F172A',
                  textAlign: 'center',
                  marginBottom: '12px'
                }}>
                  {xrayView === 'overlay' && assessment.xray_analysis.overlay_b64 && (
                    <img src={assessment.xray_analysis.overlay_b64} alt="Grad-CAM Overlay" style={{ width: '100%', maxHeight: '240px', objectFit: 'contain' }} />
                  )}
                  {xrayView === 'heatmap' && assessment.xray_analysis.heatmap_b64 && (
                    <img src={assessment.xray_analysis.heatmap_b64} alt="Grad-CAM Heatmap" style={{ width: '100%', maxHeight: '240px', objectFit: 'contain' }} />
                  )}
                  {xrayView === 'original' && assessment.xray_analysis.original_image_b64 && (
                    <img src={assessment.xray_analysis.original_image_b64} alt="Original Scan" style={{ width: '100%', maxHeight: '240px', objectFit: 'contain' }} />
                  )}
                </div>
              </>
            )}

            {/* Clinical Radiologist Rationale */}
            {assessment.xray_analysis.clinical_rationale && (
              <div style={{
                padding: '12px 14px',
                borderRadius: '8px',
                background: '#F8FAFC',
                border: '1px solid var(--border-subtle)',
                marginBottom: '10px',
                fontSize: '0.825rem',
                lineHeight: 1.5,
                color: 'var(--text-secondary)'
              }}>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '3px' }}>Diagnostic Rationale:</div>
                {assessment.xray_analysis.clinical_rationale}
              </div>
            )}

            {/* Actionable Triage Recommendation */}
            {assessment.xray_analysis.triage_recommendations && (
              <div style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: '#FEF3C7',
                border: '1px solid #FDE68A',
                marginBottom: '10px',
                fontSize: '0.825rem',
                color: '#92400E'
              }}>
                <strong>Clinical Action:</strong> {assessment.xray_analysis.triage_recommendations}
              </div>
            )}

            <div style={{ fontSize: '0.725rem', color: '#D97706', fontStyle: 'italic', marginBottom: '8px' }}>
              {assessment.xray_analysis.disclaimer}
            </div>

            {/* Detected Findings Badges */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {(assessment.xray_analysis.primary_findings || []).map((finding, i) => (
                <span key={i} style={{
                  fontSize: '0.75rem',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  background: '#FEF2F2',
                  color: '#DC2626',
                  border: '1px solid #FECACA',
                  fontWeight: 600
                }}>
                  {finding}
                </span>
              ))}
              {(assessment.xray_analysis.findings || assessment.xray_analysis.detected_findings || []).slice(0, 4).map((fd, i) => (
                <span key={i} style={{
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: fd.is_positive ? '#FEF2F2' : '#F1F5F9',
                  color: fd.is_positive ? '#DC2626' : 'var(--text-secondary)',
                  border: fd.is_positive ? '1px solid #FECACA' : '1px solid var(--border-subtle)',
                  fontWeight: 600
                }}>
                  {fd.condition}: {Math.round(fd.probability * 100)}%
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <Eye size={36} color="var(--text-dim)" style={{ marginBottom: '12px' }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Diagnostic Imaging Not Attached</div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '300px', marginTop: '6px' }}>
              The system formulated this triage assessment strictly from presenting vitals and symptoms without inventing radiographic findings.
            </p>
          </div>
        )}

      </div>
    </div>
  );
};
