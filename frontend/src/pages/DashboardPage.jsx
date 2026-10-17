import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, UserCheck, AlertOctagon, Heart, Clock, 
  Search, Filter, ArrowUpRight, Plus, RefreshCw, Layers, Trash2 
} from 'lucide-react';
import { api } from '../services/api';

export const DashboardPage = ({
  onSelectAssessment,
  onNewAssessment,
  onOpenTimeline,
}) => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');

  const fetchAssessments = async () => {
    setLoading(true);
    try {
      const data = await api.listAssessments();
      setAssessments(data);
    } catch (e) {
      console.error("Failed to load assessments:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleClearQueue = async () => {
    if (window.confirm("Are you sure you want to clear all patient records from the queue and MongoDB database?")) {
      try {
        await api.clearAssessments();
        fetchAssessments();
      } catch (err) {
        console.error("Failed to clear queue", err);
      }
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

  const filteredAssessments = assessments.filter(a => {
    const matchesSearch = 
      a.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.patient_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.assessment_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPriority = priorityFilter === 'ALL' || a.priority === priorityFilter;
    return matchesSearch && matchesPriority;
  });

  const criticalCount = assessments.filter(a => a.priority === 'CRITICAL').length;
  const highCount = assessments.filter(a => a.priority === 'HIGH').length;
  const moderateCount = assessments.filter(a => a.priority === 'MODERATE').length;
  const avgRisk = assessments.length > 0 
    ? Math.round(assessments.reduce((sum, a) => sum + a.risk_score, 0) / assessments.length)
    : 0;

  const getBadgeClass = (priority) => {
    switch (priority) {
      case 'CRITICAL': return 'priority-critical';
      case 'HIGH': return 'priority-high';
      case 'MODERATE': return 'priority-moderate';
      case 'LESS_URGENT': return 'priority-less';
      default: return 'priority-low';
    }
  };

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '36px 24px' }}>
      {/* HEADER & ACTIONS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '6px' }}>
            Emergency Triage Queue
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Real-time patient prioritization • Database: <strong style={{ color: '#059669' }}>MongoDB (triageai)</strong>
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={fetchAssessments} className="btn btn-secondary">
            <RefreshCw size={15} />
            Refresh
          </button>
          {assessments.length > 0 && (
            <button 
              onClick={handleClearQueue} 
              className="btn btn-secondary"
              style={{ borderColor: '#FECACA', color: '#DC2626', background: '#FEF2F2' }}
            >
              <Trash2 size={15} />
              Clear Queue
            </button>
          )}
        </div>
      </div>

      {/* STATS OVERVIEW CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '18px',
        marginBottom: '32px',
      }}>
        {/* Total Queue */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Active Queue</span>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800 }}>{assessments.length}</div>
          <div style={{ fontSize: '0.785rem', color: 'var(--text-muted)' }}>Assessed triage records</div>
        </div>

        {/* Critical (Level 1) */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: '#DC2626', fontWeight: 700 }}>Critical (Level 1)</span>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#DC2626' }}>{criticalCount}</div>
          <div style={{ fontSize: '0.785rem', color: 'var(--text-muted)' }}>Immediate physician intervention</div>
        </div>

        {/* Emergent (Level 2) */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: '#EA580C', fontWeight: 700 }}>Emergent (Level 2)</span>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#EA580C' }}>{highCount}</div>
          <div style={{ fontSize: '0.785rem', color: 'var(--text-muted)' }}>Target time &lt; 15 minutes</div>
        </div>

        {/* Average Acuity */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Avg Emergency Risk</span>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800 }}>{avgRisk}%</div>
          <div style={{ fontSize: '0.785rem', color: 'var(--text-muted)' }}>Calibrated severity index</div>
        </div>
      </div>

      {/* FILTER & SEARCH CONTROLS */}
      <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
          <Search size={18} color="var(--text-muted)" />
          <input 
            type="text"
            placeholder="Search patient name, patient ID, or assessment ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-input"
            style={{ padding: '8px 12px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="var(--text-muted)" />
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Priority:</span>
          <select 
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="form-select"
            style={{ padding: '8px 12px', width: 'auto' }}
          >
            <option value="ALL">All Acuities</option>
            <option value="CRITICAL">Level 1 • Critical</option>
            <option value="HIGH">Level 2 • High Emergent</option>
            <option value="MODERATE">Level 3 • Moderate Urgent</option>
            <option value="LESS_URGENT">Level 4 • Low Risk</option>
            <option value="NON_URGENT">Level 5 • Non-Urgent</option>
          </select>
        </div>
      </div>

      {/* PATIENTS TRIAGE TABLE */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#F8FAFC', borderBottom: '1px solid var(--border-medium)' }}>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Patient</th>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Timestamp</th>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Key Vitals</th>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Triage Priority</th>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Risk Score</th>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Modalities</th>
              <th style={{ padding: '14px 20px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Loading emergency queue...
                </td>
              </tr>
            ) : filteredAssessments.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '56px 20px', textAlign: 'center' }}>
                  <div style={{ width: '52px', height: '52px', borderRadius: '14px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                    <ShieldAlert size={28} color="#059669" />
                  </div>
                  <div style={{ color: 'var(--text-primary)', fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
                    Emergency Triage Queue is Clear
                  </div>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '520px', margin: '0 auto 16px', lineHeight: 1.5 }}>
                    No patients are currently waiting. Use the <strong>"+ New Assessment"</strong> button in the top navigation bar to triage an incoming patient.
                  </p>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 16px', borderRadius: '20px', background: '#ECFDF5', border: '1px solid #A7F3D0', fontSize: '0.8rem', color: '#065F46' }}>
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#059669' }}></span>
                    Active Database: MongoDB (database: triageai • collections: patients, assessments, timelines)
                  </div>
                </td>
              </tr>
            ) : (
              filteredAssessments.map((a) => {
                const badgeCls = getBadgeClass(a.priority);
                const sbp = a.clinical_indices?.sbp ?? '—';
                const hr = a.clinical_indices?.hr ?? '—';
                const spo2 = a.clinical_indices?.spo2 ?? '—';
                const si = a.clinical_indices?.shock_index ?? '—';

                return (
                  <tr 
                    key={a.assessment_id}
                    style={{ 
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background 0.15s ease',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#F8FAFC')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    {/* Patient info */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{a.patient_name}</div>
                      <div style={{ fontSize: '0.775rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {a.patient_id} • {a.assessment_id}
                      </div>
                    </td>

                    {/* Timestamp */}
                    <td style={{ padding: '16px 20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {a.timestamp}
                    </td>

                    {/* Key Vitals */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ fontSize: '0.825rem', color: 'var(--text-primary)', display: 'flex', gap: '8px' }}>
                        <span>HR: <strong>{hr}</strong></span>
                        <span>BP: <strong>{sbp}</strong></span>
                        <span>SpO2: <strong>{spo2}%</strong></span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: si > 0.9 ? '#DC2626' : 'var(--text-muted)' }}>
                        Shock Index: <strong>{si}</strong>
                      </div>
                    </td>

                    {/* Priority */}
                    <td style={{ padding: '16px 20px' }}>
                      <span className={`priority-badge ${badgeCls}`}>
                        {a.priority_label || a.priority}
                      </span>
                    </td>

                    {/* Risk Score */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontWeight: 800, fontSize: '1rem', width: '42px' }}>{a.risk_score}%</span>
                        <div style={{ width: '80px', height: '6px', background: '#E2E8F0', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${Math.min(a.risk_score, 100)}%`,
                            height: '100%',
                            background: a.risk_score >= 78 ? '#DC2626' : (a.risk_score >= 58 ? '#EA580C' : (a.risk_score >= 38 ? '#D97706' : '#059669')),
                            borderRadius: '3px',
                          }} />
                        </div>
                      </div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Confidence: {a.confidence}%</div>
                    </td>

                    {/* Modalities */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span style={{
                          padding: '2px 7px',
                          borderRadius: '4px',
                          background: '#ECFDF5',
                          color: '#059669',
                          fontSize: '0.725rem',
                          fontWeight: 600
                        }}>
                          Vitals
                        </span>
                        {a.modalities_used?.ecg && (
                          <span style={{
                            padding: '2px 7px',
                            borderRadius: '4px',
                            background: '#ECFDF5',
                            color: '#059669',
                            fontSize: '0.725rem',
                            fontWeight: 600
                          }}>
                            ECG
                          </span>
                        )}
                        {a.modalities_used?.xray && (
                          <span style={{
                            padding: '2px 7px',
                            borderRadius: '4px',
                            background: '#FEFCE8',
                            color: '#D97706',
                            fontSize: '0.725rem',
                            fontWeight: 600
                          }}>
                            Imaging
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Actions */}
                    <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '8px' }}>
                        <button 
                          onClick={() => onSelectAssessment(a)}
                          className="btn btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '0.785rem' }}
                        >
                          View XAI
                          <ArrowUpRight size={14} />
                        </button>
                        <button 
                          onClick={() => onOpenTimeline(a.patient_id)}
                          className="btn btn-ghost"
                          style={{ padding: '6px 10px', fontSize: '0.785rem' }}
                          title="Patient Risk Timeline"
                        >
                          Timeline
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
