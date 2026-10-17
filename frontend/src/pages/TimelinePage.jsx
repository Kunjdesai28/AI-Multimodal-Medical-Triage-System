import React, { useState, useEffect } from 'react';
import { 
  LineChart, Clock, TrendingUp, TrendingDown, Minus, 
  Plus, AlertCircle, CheckCircle2, ArrowRight, RefreshCw, Heart 
} from 'lucide-react';
import { api } from '../services/api';


export const TimelinePage = ({ initialPatientId, onViewAssessment }) => {
  const [patientId, setPatientId] = useState(initialPatientId || 'PAT-DEMO');
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // New Observation Form State
  const [obsVitals, setObsVitals] = useState({
    age: 58,
    sex: 'Male',
    arrival_mode: 2,
    injury: 1,
    chief_complaint: 'Follow-up evaluation in emergency bay',
    symptoms: 'Increasing shortness of breath, diaphoretic',
    mental: 1,
    pain: 1,
    nrs_pain: 8,
    sbp: 86,
    dbp: 54,
    hr: 128,
    rr: 28,
    bt: 37.2,
    saturation: 88,
  });

  const fetchTimeline = async (id) => {
    setLoading(true);
    try {
      const data = await api.getTimeline(id);
      setTimeline(data);
    } catch {
      // If no timeline exists yet for this ID, initialize a demonstration trajectory
      const dummyTraj = {
        patient_id: id,
        patient_name: 'Patient ' + id,
        total_observations: 3,
        overall_trend: 'Deteriorating',
        latest_risk: 84.5,
        latest_priority: 'CRITICAL',
        trajectory: [
          {
            observation_id: 'OBS-001',
            assessment_id: 'ASM-INIT',
            timestamp: '10:00:00',
            risk_score: 32.0,
            priority: 'LESS_URGENT',
            priority_color: 'blue',
            delta_risk: 0.0,
            delta_direction: 'initial',
            vitals_summary: { hr: 78, sbp: 124, spo2: 98, shock_index: 0.63 },
            modalities_count: 2,
          },
          {
            observation_id: 'OBS-002',
            assessment_id: 'ASM-MID',
            timestamp: '10:45:00',
            risk_score: 58.5,
            priority: 'HIGH',
            priority_color: 'orange',
            delta_risk: 26.5,
            delta_direction: 'increased',
            vitals_summary: { hr: 106, sbp: 102, spo2: 93, shock_index: 1.04 },
            modalities_count: 3,
          },
          {
            observation_id: 'OBS-003',
            assessment_id: 'ASM-ACUTE',
            timestamp: '11:30:00',
            risk_score: 84.5,
            priority: 'CRITICAL',
            priority_color: 'red',
            delta_risk: 26.0,
            delta_direction: 'increased',
            vitals_summary: { hr: 128, sbp: 86, spo2: 88, shock_index: 1.49 },
            modalities_count: 4,
          }
        ]
      };
      setTimeline(dummyTraj);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline(patientId);
  }, [patientId]);

  const handleAddObservation = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('patient_data', JSON.stringify({
        patient_id: patientId,
        vitals: obsVitals
      }));
      const updated = await api.addObservation(patientId, formData);
      setShowAddModal(false);
      await fetchTimeline(patientId);
      onViewAssessment(updated);
    } catch (err) {
      alert("Failed to add observation: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const traj = timeline?.trajectory || [];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '36px 24px 80px' }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '6px' }}>
            Dynamic & Adaptive Triage Timeline
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Triage is continuous. Track longitudinal patient trajectory across observation time points (T1 → T2 → T3).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Patient ID:</span>
            <input 
              type="text" 
              value={patientId} 
              onChange={(e) => setPatientId(e.target.value)} 
              className="form-input" 
              style={{ width: '130px', padding: '6px 10px' }} 
            />
          </div>
          <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
            <Plus size={16} />
            Add Observation
          </button>
        </div>
      </div>

      {/* TIMELINE OVERVIEW CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '18px',
        marginBottom: '32px'
      }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Risk Acuity</span>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: (timeline?.latest_risk ?? 0) >= 78 ? '#DC2626' : '#EA580C' }}>
            {timeline?.latest_risk ?? 0}%
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Priority: <strong>{timeline?.latest_priority}</strong></div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Clinical Trend Direction</span>
          <div style={{
            fontSize: '1.8rem',
            fontWeight: 800,
            color: timeline?.overall_trend === 'Deteriorating' ? '#DC2626' : (timeline?.overall_trend === 'Improving' ? '#059669' : '#D97706'),
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            {timeline?.overall_trend === 'Deteriorating' && <TrendingUp size={28} color="#DC2626" />}
            {timeline?.overall_trend === 'Improving' && <TrendingDown size={28} color="#059669" />}
            {timeline?.overall_trend === 'Stabilizing' && <Minus size={28} color="#D97706" />}
            {timeline?.overall_trend}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Evaluated over {traj.length} time points</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Latest Net Risk Change</span>
          {traj.length >= 2 ? (
            <div>
              <div style={{
                fontSize: '2rem',
                fontWeight: 800,
                color: (traj[traj.length - 1].delta_risk ?? 0) > 0 ? '#DC2626' : '#059669'
              }}>
                {(traj[traj.length - 1].delta_risk ?? 0) > 0 ? `+${traj[traj.length - 1].delta_risk}%` : `${traj[traj.length - 1].delta_risk}%`}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Shift from previous check
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-muted)', marginTop: '8px' }}>
              Baseline established
            </div>
          )}
        </div>
      </div>

      {/* INTERACTIVE TRAJECTORY CHART */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '20px' }}>Longitudinal Acuity Trajectory</h2>
        
        {traj.length > 0 ? (
          <div style={{ background: '#FFFFFF', border: '1px solid var(--border-medium)', borderRadius: '12px', padding: '24px 20px 16px', boxShadow: '0 1px 4px rgba(0,0,0,0.03)' }}>
            <svg viewBox="0 0 800 240" style={{ width: '100%', height: '220px', display: 'block' }}>
              {/* Horizontal Acuity Zones */}
              <rect x="50" y="20" width="730" height="40" fill="rgba(220, 38, 38, 0.08)" />
              <text x="56" y="44" fill="#DC2626" fontSize="11" fontWeight="700">CRITICAL ZONE (&gt; 78%)</text>

              <rect x="50" y="60" width="730" height="50" fill="rgba(234, 88, 12, 0.06)" />
              <text x="56" y="88" fill="#EA580C" fontSize="11" fontWeight="700">HIGH / EMERGENT (58-78%)</text>

              <rect x="50" y="110" width="730" height="50" fill="rgba(217, 119, 6, 0.06)" />
              <text x="56" y="138" fill="#D97706" fontSize="11" fontWeight="700">MODERATE URGENT (38-58%)</text>

              <rect x="50" y="160" width="730" height="50" fill="rgba(5, 150, 105, 0.06)" />
              <text x="56" y="188" fill="#059669" fontSize="11" fontWeight="700">STABLE / LOW (&lt; 38%)</text>

              {/* Grid Lines */}
              <line x1="50" y1="20" x2="780" y2="20" stroke="#E2E8F0" />
              <line x1="50" y1="60" x2="780" y2="60" stroke="#E2E8F0" />
              <line x1="50" y1="110" x2="780" y2="110" stroke="#E2E8F0" />
              <line x1="50" y1="160" x2="780" y2="160" stroke="#E2E8F0" />
              <line x1="50" y1="210" x2="780" y2="210" stroke="#E2E8F0" />

              {/* Trajectory Polyline */}
              {traj.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="3.5"
                  points={traj.map((pt, idx) => {
                    const x = 70 + (idx / (traj.length - 1)) * 680;
                    const y = 210 - (pt.risk_score / 100) * 190;
                    return `${x},${y}`;
                  }).join(' ')}
                />
              )}

              {/* Data points & labels */}
              {traj.map((pt, idx) => {
                const x = traj.length === 1 ? 400 : 70 + (idx / (traj.length - 1)) * 680;
                const y = 210 - (pt.risk_score / 100) * 190;
                const ptColor = pt.risk_score >= 78 ? '#DC2626' : (pt.risk_score >= 58 ? '#EA580C' : (pt.risk_score >= 38 ? '#D97706' : '#059669'));

                return (
                  <g key={idx}>
                    <circle cx={x} cy={y} r="7" fill={ptColor} stroke="#FFFFFF" strokeWidth="2.5" />
                    <text x={x} y={y - 12} fill="var(--text-primary)" fontSize="12" fontWeight="800" textAnchor="middle">
                      {pt.risk_score}%
                    </text>
                    <text x={x} y={230} fill="var(--text-muted)" fontSize="11" textAnchor="middle">
                      T{idx + 1} ({pt.timestamp.slice(11, 16) || pt.timestamp})
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No observations recorded yet. Click "Add Observation" to start trajectory.
          </div>
        )}
      </div>

      {/* DETAILED OBSERVATION LOG */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>Observation Event Log</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {traj.map((pt, idx) => (
            <div key={idx} style={{
              padding: '16px 20px',
              borderRadius: '10px',
              background: '#F8FAFC',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: '#ECFDF5',
                  color: '#059669',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: '0.9rem'
                }}>
                  T{idx + 1}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{pt.observation_id} • Time: {pt.timestamp}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    HR: {pt.vitals_summary?.hr ?? '—'} bpm • BP: {pt.vitals_summary?.sbp ?? '—'} mmHg • SpO2: {pt.vitals_summary?.spo2 ?? '—'}% • Shock Index: {pt.vitals_summary?.shock_index ?? '—'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                {pt.delta_risk !== undefined && pt.delta_direction !== 'initial' && (
                  <span style={{
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    color: pt.delta_risk > 0 ? '#DC2626' : '#059669',
                  }}>
                    {pt.delta_risk > 0 ? `+${pt.delta_risk}%` : `${pt.delta_risk}%`}
                  </span>
                )}
                <span className={`priority-badge priority-${pt.priority.toLowerCase().replace('_', '-')}`}>
                  {pt.priority}
                </span>
                <span style={{ fontWeight: 800, fontSize: '1.2rem' }}>
                  {pt.risk_score}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ADD OBSERVATION MODAL */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(15, 23, 42, 0.45)',
          backdropFilter: 'blur(6px)',
          zIndex: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div className="glass-panel" style={{ background: '#FFFFFF', maxWidth: '580px', width: '100%', padding: '28px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h2 style={{ fontSize: '1.4rem', marginBottom: '8px' }}>Add Observation: {patientId}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '20px' }}>
              Input updated vital signs to trigger real model re-assessment and calculate delta progression.
            </p>

            <form onSubmit={handleAddObservation}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div className="input-group">
                  <label className="input-label">Systolic BP (mmHg)</label>
                  <input 
                    type="number" 
                    min="20"
                    max="300"
                    value={obsVitals.sbp} 
                    onChange={(e) => setObsVitals({ ...obsVitals, sbp: parseFloat(e.target.value) || 0 })} 
                    className="form-input" 
                    required 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Heart Rate (bpm)</label>
                  <input 
                    type="number" 
                    min="20"
                    max="350"
                    value={obsVitals.hr} 
                    onChange={(e) => setObsVitals({ ...obsVitals, hr: parseFloat(e.target.value) || 0 })} 
                    className="form-input" 
                    required 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">SpO2 (%)</label>
                  <input 
                    type="number" 
                    min="10"
                    max="100"
                    value={obsVitals.saturation} 
                    onChange={(e) => setObsVitals({ ...obsVitals, saturation: parseFloat(e.target.value) || 0 })} 
                    className="form-input" 
                    required 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Respiratory Rate (/min)</label>
                  <input 
                    type="number" 
                    min="0"
                    max="150"
                    value={obsVitals.rr} 
                    onChange={(e) => setObsVitals({ ...obsVitals, rr: parseFloat(e.target.value) || 0 })} 
                    className="form-input" 
                    required 
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn btn-primary">
                  {submitting ? 'Recalculating...' : 'Recalculate Dynamic Risk'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
