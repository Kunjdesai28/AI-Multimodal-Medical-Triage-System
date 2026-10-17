import React, { useState, useMemo, useEffect } from 'react';
import { 
  Heart, Activity, FileText, Upload, ArrowRight, 
  AlertTriangle, CheckCircle2, RefreshCw, Sparkles, FileSpreadsheet, Eye 
} from 'lucide-react';
import { api } from '../services/api';


export const AssessmentPage = ({ onAssessmentCompleted }) => {
  const [patientName, setPatientName] = useState('');
  const [patientId, setPatientId] = useState('');

  // Automatically fetch next sequential patient ID starting from 01 (PAT-01, PAT-02, ...)
  useEffect(() => {
    let active = true;
    api.getNextPatientId().then((nextId) => {
      if (active && nextId) {
        setPatientId(nextId);
      }
    });
    return () => { active = false; };
  }, []);
  
  // Vitals State - starts completely empty with clean placeholders
  const [vitals, setVitals] = useState({
    age: '',
    sex: 'Male',
    arrival_mode: 1, // Walking / Self
    injury: 1, // Non-trauma
    chief_complaint: '',
    symptoms: '',
    mental: 1, // Alert
    pain: 0,
    nrs_pain: '',
    sbp: '',
    dbp: '',
    hr: '',
    rr: '',
    bt: '',
    saturation: '',
  });

  // Uploaded Files
  const [ecgFile, setEcgFile] = useState(null);
  const [ecgFileName, setEcgFileName] = useState('');
  const [xrayFile, setXrayFile] = useState(null);
  const [xrayPreview, setXrayPreview] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Real-time calculated hemodynamic indices (clean fallback '—' when inputs are empty, clamped to Universal Limits)
  const shockIndex = useMemo(() => {
    const sbp = typeof vitals.sbp === 'number' ? vitals.sbp : parseFloat(vitals.sbp);
    const hr = typeof vitals.hr === 'number' ? vitals.hr : parseFloat(vitals.hr);
    if (!isNaN(sbp) && !isNaN(hr) && sbp > 0 && hr > 0) {
      const si = hr / sbp;
      return Math.min(Math.max(si, 0.1), 6.0).toFixed(2);
    }
    return '—';
  }, [vitals.hr, vitals.sbp]);

  const mapValue = useMemo(() => {
    const sbp = typeof vitals.sbp === 'number' ? vitals.sbp : parseFloat(vitals.sbp);
    const dbp = typeof vitals.dbp === 'number' ? vitals.dbp : parseFloat(vitals.dbp);
    if (!isNaN(sbp) && !isNaN(dbp) && sbp > 0 && dbp > 0) {
      const map = (2 * dbp + sbp) / 3;
      const clampedMap = Math.min(Math.max(map, 10), 250);
      return `${clampedMap.toFixed(1)} mmHg`;
    }
    return '—';
  }, [vitals.sbp, vitals.dbp]);

  const pulsePressure = useMemo(() => {
    const sbp = typeof vitals.sbp === 'number' ? vitals.sbp : parseFloat(vitals.sbp);
    const dbp = typeof vitals.dbp === 'number' ? vitals.dbp : parseFloat(vitals.dbp);
    if (!isNaN(sbp) && !isNaN(dbp) && sbp > 0 && dbp > 0) {
      const pp = sbp - dbp;
      const clampedPp = Math.min(Math.max(pp, 5), 200);
      return `${clampedPp.toFixed(0)} mmHg`;
    }
    return '—';
  }, [vitals.sbp, vitals.dbp]);

  const isShockAlert = shockIndex !== '—' && Number(shockIndex) >= 0.9;
  const isNormalShock = shockIndex !== '—' && Number(shockIndex) < 0.9;

  // Clear all form inputs back to empty and refresh sequential ID
  const clearForm = async () => {
    setPatientName('');
    try {
      const nextId = await api.getNextPatientId();
      setPatientId(nextId || 'PAT-01');
    } catch {
      setPatientId('PAT-01');
    }
    setVitals({
      age: '',
      sex: 'Male',
      arrival_mode: 1,
      injury: 1,
      chief_complaint: '',
      symptoms: '',
      mental: 1,
      pain: 0,
      nrs_pain: '',
      sbp: '',
      dbp: '',
      hr: '',
      rr: '',
      bt: '',
      saturation: '',
    });
    setEcgFile(null);
    setEcgFileName('');
    setXrayFile(null);
    setXrayPreview(null);
  };




  const removeEcg = () => {
    setEcgFile(null);
    setEcgFileName('');
  };

  const removeXray = () => {
    setXrayFile(null);
    setXrayPreview(null);
  };

  const handleEcgUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setEcgFile(file);
      setEcgFileName(file.name);
    }
  };

  const handleXRayUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setXrayFile(file);
      const reader = new FileReader();
      reader.onload = () => setXrayPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);

    try {
      let finalPatientId = patientId.trim();
      if (!finalPatientId) {
        try {
          finalPatientId = await api.getNextPatientId();
        } catch {
          finalPatientId = 'PAT-01';
        }
      }
      const finalPatientName = patientName.trim() || 'Anonymous Patient';

      const sbpVal = vitals.sbp !== '' ? Number(vitals.sbp) : 120;
      const dbpVal = vitals.dbp !== '' ? Number(vitals.dbp) : 80;
      const hrVal = vitals.hr !== '' ? Number(vitals.hr) : 75;
      const rrVal = vitals.rr !== '' ? Number(vitals.rr) : 18;
      const btVal = vitals.bt !== '' ? Number(vitals.bt) : 36.8;
      const ageVal = vitals.age !== '' ? Number(vitals.age) : 45;
      const satVal = vitals.saturation !== '' && vitals.saturation !== undefined ? Number(vitals.saturation) : undefined;

      // Universal Physiological Entry Limits validation
      if (hrVal < 20 || hrVal > 350) {
        setErrorMsg('Heart Rate must be within universal physiological limits: 20 – 350 bpm');
        setSubmitting(false);
        return;
      }
      if (rrVal < 0 || rrVal > 150) {
        setErrorMsg('Respiration Rate must be within universal physiological limits: 0 – 150 /min');
        setSubmitting(false);
        return;
      }
      if (sbpVal < 20 || sbpVal > 300) {
        setErrorMsg('Systolic BP must be within universal physiological limits: 20 – 300 mmHg');
        setSubmitting(false);
        return;
      }
      if (dbpVal < 5 || dbpVal > 200) {
        setErrorMsg('Diastolic BP must be within universal physiological limits: 5 – 200 mmHg');
        setSubmitting(false);
        return;
      }
      if (btVal < 20.0 || btVal > 45.0) {
        setErrorMsg('Body Temperature must be within universal physiological limits: 20.0 – 45.0 °C');
        setSubmitting(false);
        return;
      }
      if (satVal !== undefined && (satVal < 10 || satVal > 100)) {
        setErrorMsg('Oxygen Saturation (SpO2) must be within universal limits: 10 – 100%');
        setSubmitting(false);
        return;
      }
      if (ageVal < 0 || ageVal > 125) {
        setErrorMsg('Age must be between 0 and 125 years');
        setSubmitting(false);
        return;
      }

      const numericVitals = {
        age: ageVal,
        sex: vitals.sex || 'Male',
        arrival_mode: Number(vitals.arrival_mode) || 1,
        injury: Number(vitals.injury) || 1,
        chief_complaint: vitals.chief_complaint.trim() || 'General Emergency Evaluation',
        symptoms: vitals.symptoms ? vitals.symptoms.trim() : '',
        mental: Number(vitals.mental) || 1,
        pain: Number(vitals.nrs_pain) > 0 ? 1 : 0,
        nrs_pain: vitals.nrs_pain === '' ? 0 : Number(vitals.nrs_pain),
        sbp: sbpVal,
        dbp: dbpVal,
        hr: hrVal,
        rr: rrVal,
        bt: btVal,
        saturation: satVal,
      };

      const formData = new FormData();
      formData.append('patient_data', JSON.stringify({
        patient_id: finalPatientId,
        patient_name: finalPatientName,
        vitals: numericVitals
      }));

      if (ecgFile) {
        formData.append('ecg_file', ecgFile);
      }
      if (xrayFile) {
        formData.append('xray_file', xrayFile);
      }

      const assessment = await api.createAssessment(formData);
      onAssessmentCompleted(assessment);
    } catch (err) {
      setErrorMsg(err.message || 'Assessment submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '1360px', margin: '0 auto', padding: '36px 24px 80px' }}>
      {/* HEADER */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>
          New Patient Triage Assessment
        </h1>
      </div>

      {errorMsg && (
        <div style={{
          padding: '16px 20px',
          background: '#FEF2F2',
          border: '1px solid #FECACA',
          borderRadius: '10px',
          color: '#991B1B',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertTriangle size={20} color="#DC2626" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '28px', marginBottom: '28px' }}>
          
          {/* CARD 1: PATIENT DEMOGRAPHICS & PRESENTATION */}
          <div className="glass-panel" style={{ padding: '28px 30px' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FileSpreadsheet size={20} color="#059669" />
              Patient Information
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="input-group">
                  <label className="input-label">Patient Name</label>
                  <input 
                    type="text" 
                    value={patientName} 
                    onChange={(e) => setPatientName(e.target.value)} 
                    className="form-input" 
                    placeholder="e.g. Jane Doe"
                    required 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Patient ID</label>
                  <input 
                    type="text" 
                    value={patientId} 
                    onChange={(e) => setPatientId(e.target.value)} 
                    className="form-input" 
                    placeholder="e.g. PAT-01"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="input-group">
                  <label className="input-label">Age <span className="unit">Years</span></label>
                  <input 
                    type="number" 
                    value={vitals.age !== '' ? vitals.age : ''} 
                    onChange={(e) => setVitals({ ...vitals, age: e.target.value === '' ? '' : parseInt(e.target.value) })} 
                    className="form-input" 
                    min="0" 
                    max="125" 
                    placeholder="e.g. 58 (0 for infant)"
                    required 
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Sex</label>
                  <select 
                    value={vitals.sex} 
                    onChange={(e) => setVitals({ ...vitals, sex: e.target.value })} 
                    className="form-select"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="input-group">
                  <label className="input-label">Arrival Transport</label>
                  <select 
                    value={vitals.arrival_mode} 
                    onChange={(e) => setVitals({ ...vitals, arrival_mode: parseInt(e.target.value) })} 
                    className="form-select"
                  >
                    <option value={1}>Walking / Self</option>
                    <option value={2}>119 Emergency Ambulance</option>
                    <option value={3}>Private Vehicle</option>
                    <option value={4}>Other / Transfer</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">Injury Classification</label>
                  <select 
                    value={vitals.injury} 
                    onChange={(e) => setVitals({ ...vitals, injury: parseInt(e.target.value) })} 
                    className="form-select"
                  >
                    <option value={1}>Non-Trauma / Medical</option>
                    <option value={2}>Trauma / Physical Injury</option>
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Chief Presenting Complaint</label>
                <input 
                  type="text" 
                  value={vitals.chief_complaint} 
                  onChange={(e) => setVitals({ ...vitals, chief_complaint: e.target.value })} 
                  className="form-input" 
                  placeholder="e.g. Acute chest pain with shortness of breath"
                  required 
                />
              </div>

              <div className="input-group">
                <label className="input-label">Associated Symptoms</label>
                <textarea 
                  value={vitals.symptoms || ''} 
                  onChange={(e) => setVitals({ ...vitals, symptoms: e.target.value })} 
                  className="form-textarea" 
                  rows={2} 
                  placeholder="e.g. Diaphoresis, radiating left arm pain, dizziness, nausea (optional)"
                />
              </div>
            </div>
          </div>

          {/* CARD 2: VITAL SIGNS & HEMODYNAMIC INDICES */}
          <div className="glass-panel" style={{ padding: '28px 30px' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Activity size={20} color="#10B981" />
              Vital Signs & Hemodynamics
            </h2>

            {/* Live Shock Index Banner */}
            <div style={{
              padding: '14px 18px',
              borderRadius: '8px',
              background: isShockAlert ? '#FEF2F2' : isNormalShock ? '#ECFDF5' : '#F8FAFC',
              border: isShockAlert ? '1px solid #FECACA' : isNormalShock ? '1px solid #A7F3D0' : '1px solid var(--border-subtle)',
              marginBottom: '18px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <span style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', display: 'block' }}>Shock Index (HR/SBP)</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: isShockAlert ? '#DC2626' : isNormalShock ? '#059669' : 'var(--text-muted)' }}>
                  {shockIndex}
                </span>
              </div>
              <div>
                <span style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', display: 'block' }}>MAP</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: mapValue !== '—' ? 'inherit' : 'var(--text-muted)' }}>{mapValue}</span>
              </div>
              <div>
                <span style={{ fontSize: '0.785rem', color: 'var(--text-secondary)', display: 'block' }}>Pulse Pressure</span>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: pulsePressure !== '—' ? 'inherit' : 'var(--text-muted)' }}>{pulsePressure}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="input-group">
                <label className="input-label">Systolic BP <span className="unit">mmHg</span></label>
                <input 
                  type="number" 
                  value={vitals.sbp !== '' ? vitals.sbp : ''} 
                  onChange={(e) => setVitals({ ...vitals, sbp: e.target.value === '' ? '' : parseFloat(e.target.value) })} 
                  className="form-input" 
                  min="20" 
                  max="300" 
                  placeholder="e.g. 120"
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Diastolic BP <span className="unit">mmHg</span></label>
                <input 
                  type="number" 
                  value={vitals.dbp !== '' ? vitals.dbp : ''} 
                  onChange={(e) => setVitals({ ...vitals, dbp: e.target.value === '' ? '' : parseFloat(e.target.value) })} 
                  className="form-input" 
                  min="5" 
                  max="200" 
                  placeholder="e.g. 80"
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Heart Rate <span className="unit">bpm</span></label>
                <input 
                  type="number" 
                  value={vitals.hr !== '' ? vitals.hr : ''} 
                  onChange={(e) => setVitals({ ...vitals, hr: e.target.value === '' ? '' : parseFloat(e.target.value) })} 
                  className="form-input" 
                  min="20" 
                  max="350" 
                  placeholder="e.g. 75"
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Respiration <span className="unit">/min</span></label>
                <input 
                  type="number" 
                  value={vitals.rr !== '' ? vitals.rr : ''} 
                  onChange={(e) => setVitals({ ...vitals, rr: e.target.value === '' ? '' : parseFloat(e.target.value) })} 
                  className="form-input" 
                  min="0" 
                  max="150" 
                  placeholder="e.g. 18"
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Body Temp <span className="unit">°C</span></label>
                <input 
                  type="number" 
                  step="0.1" 
                  value={vitals.bt !== '' ? vitals.bt : ''} 
                  onChange={(e) => setVitals({ ...vitals, bt: e.target.value === '' ? '' : parseFloat(e.target.value) })} 
                  className="form-input" 
                  min="20.0" 
                  max="45.0" 
                  placeholder="e.g. 36.8"
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Oxygen (SpO2) <span className="unit">%</span></label>
                <input 
                  type="number" 
                  value={vitals.saturation !== '' && vitals.saturation !== undefined ? vitals.saturation : ''} 
                  onChange={(e) => setVitals({ ...vitals, saturation: e.target.value === '' ? '' : parseFloat(e.target.value) })} 
                  className="form-input" 
                  min="10" 
                  max="100" 
                  placeholder="e.g. 98"
                />
              </div>
              <div className="input-group">
                <label className="input-label">Pain Intensity <span className="unit">NRS 0-10</span></label>
                <input 
                  type="number" 
                  value={vitals.nrs_pain !== '' ? vitals.nrs_pain : ''} 
                  onChange={(e) => {
                    const val = e.target.value === '' ? '' : parseInt(e.target.value);
                    setVitals({ 
                      ...vitals, 
                      nrs_pain: val,
                      pain: typeof val === 'number' && val > 0 ? 1 : 0
                    });
                  }} 
                  className="form-input" 
                  min="0" 
                  max="10" 
                  placeholder="0 - 10"
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Mental Status (AVPU)</label>
                <select 
                  value={vitals.mental} 
                  onChange={(e) => setVitals({ ...vitals, mental: parseInt(e.target.value) })} 
                  className="form-select"
                >
                  <option value={1}>Alert (Normal)</option>
                  <option value={2}>Responds to Verbal</option>
                  <option value={3}>Responds to Pain</option>
                  <option value={4}>Unresponsive (Coma)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* MODALITIES ROW: ECG & CHEST X-RAY */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '28px', marginBottom: '32px' }}>
          
          {/* ECG UPLOADER */}
          <div className="glass-panel" style={{ padding: '28px 30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h2 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Activity size={20} color="#059669" />
                ECG Cardiac Lead (Optional)
              </h2>
              <span style={{ fontSize: '0.75rem', padding: '3px 8px', borderRadius: '4px', background: '#F1F5F9', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Cardiac AI
              </span>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '12px' }}>
              Upload a 187-point sampled ECG lead CSV file (MIT-BIH / PTB-DB benchmark format).
            </p>

            {ecgFile && (
              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <button 
                  type="button" 
                  onClick={removeEcg} 
                  className="btn btn-ghost" 
                  style={{ fontSize: '0.785rem', padding: '5px 10px', color: '#DC2626' }}
                >
                  ✕ Clear ECG
                </button>
              </div>
            )}

            <div style={{
              border: '2px dashed var(--border-medium)',
              borderRadius: '12px',
              padding: '20px',
              textAlign: 'center',
              background: '#F8FAFC',
              cursor: 'pointer',
              position: 'relative'
            }}>
              <input 
                type="file" 
                accept=".csv,.txt"
                onChange={handleEcgUpload} 
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }} 
              />
              <Upload size={26} color="#059669" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                {ecgFileName ? `Selected: ${ecgFileName}` : 'Drag & drop ECG CSV or click to browse'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Optional • Supported: .csv, .txt (187 lead samples)
              </div>
            </div>
          </div>

          {/* EMERGENCY DIAGNOSTIC IMAGING UPLOADER */}
          <div className="glass-panel" style={{ padding: '28px 30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Eye size={20} color="#D97706" />
                Emergency Diagnostic Imaging (Optional)
              </h2>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '12px', lineHeight: 1.45 }}>
              Upload any emergency scan (Head CT, Bone / Orthopedic X-ray, Chest Radiography, FAST Ultrasound, or Trauma Bedside Photo).
            </p>

            {xrayFile && (
              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <button 
                  type="button" 
                  onClick={removeXray} 
                  className="btn btn-ghost" 
                  style={{ fontSize: '0.785rem', padding: '5px 10px', color: '#DC2626' }}
                >
                  ✕ Clear Scan
                </button>
              </div>
            )}

            <div style={{
              border: '2px dashed var(--border-medium)',
              borderRadius: '12px',
              padding: '20px',
              textAlign: 'center',
              background: '#F8FAFC',
              cursor: 'pointer',
              position: 'relative',
              minHeight: '120px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <input 
                type="file" 
                accept="image/*"
                onChange={handleXRayUpload} 
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }} 
              />
              {xrayPreview ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <img src={xrayPreview} alt="Scan Preview" style={{ width: '64px', height: '64px', borderRadius: '8px', objectFit: 'cover' }} />
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{xrayFile?.name}</div>
                    <div style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>Diagnostic scan loaded ✓ (Click to change)</div>
                  </div>
                </div>
              ) : (
                <>
                  <Upload size={26} color="#D97706" style={{ margin: '0 auto 8px' }} />
                  <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>Drag & drop emergency scan or click to browse</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Supported: CT, X-ray, Ultrasound, Trauma Photos (PNG, JPG, JPEG, WebP)
                  </div>
                </>
              )}
            </div>
          </div>

        </div>

        {/* SUBMISSION FOOTER */}
        <div className="glass-panel" style={{ padding: '20px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>Synthesizing Available Modalities</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Clinical + Vitals {ecgFile ? '+ ECG' : ''} {xrayFile ? '+ Diagnostic Imaging' : ''} (Adaptive Multimodal Fusion)
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button 
              type="button" 
              onClick={clearForm} 
              className="btn btn-secondary"
              style={{ padding: '12px 20px', fontSize: '0.95rem', borderRadius: '10px' }}
            >
              <RefreshCw size={16} />
              Clear Form
            </button>
            <button 
              type="submit" 
              disabled={submitting} 
              className="btn btn-primary"
              style={{ padding: '12px 32px', fontSize: '1rem', borderRadius: '10px' }}
            >
              {submitting ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Running Multimodal AI Assessment...
                </>
              ) : (
                <>
                  Run AI Assessment
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
