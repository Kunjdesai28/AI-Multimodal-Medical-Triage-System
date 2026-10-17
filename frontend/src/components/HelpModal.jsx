import React, { useState } from 'react';
import { 
  HelpCircle, X, ChevronRight, ChevronLeft, 
  CheckCircle2, ArrowRight, Sparkles, HeartPulse, 
  Activity, FileText, Upload, ShieldAlert, Info 
} from 'lucide-react';

export const HelpModal = ({ isOpen, onClose, onGoToAssessment }) => {
  const [currentStep, setCurrentStep] = useState(0);

  if (!isOpen) return null;

  const steps = [
    {
      id: 0,
      badge: 'Step 1 • Demographics',
      title: 'Patient Identity & Presenting Case',
      icon: FileText,
      color: '#10B981',
      summary: 'Record initial patient demographics, injury classification, and chief complaint.',
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', lineHeight: 1.6 }}>
            Start by entering the patient's administrative information and primary emergency complaint:
          </p>
          <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.7 }}>
            <li><strong>Patient ID & Name:</strong> Enter hospital tracking number (e.g. <code>PAT-01</code>, auto-generated in proper sequence) and full patient name.</li>
            <li><strong>Demographics:</strong> Specify biological sex and age (pediatric, adult, or geriatric cohorts).</li>
            <li><strong>Arrival Mode:</strong> Select whether the patient arrived walking, via private vehicle, or by 119 Ambulance.</li>
            <li><strong>Injury & Complaint:</strong> Specify whether the presenting issue is trauma-related or non-trauma, followed by the chief complaint.</li>
          </ul>

          <div style={{
            background: '#ECFDF5',
            border: '1px solid #A7F3D0',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}>
            <Sparkles size={18} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.85rem', color: '#065F46' }}>
              <strong>1-Click Quick Testing:</strong> Don't want to type manually? Use the 4 preset buttons at the top of the assessment page (<strong>🚨 Cardiac Emergency</strong>, <strong>🫁 Respiratory Distress</strong>, <strong>🩺 Fever & Abdominal</strong>, <strong>🩹 Minor Sprain</strong>) to populate complete clinical cases in 1 click!
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 1,
      badge: 'Step 2 • Physiological Vitals',
      title: 'Enter Presenting Clinical Vitals & Pain',
      icon: Activity,
      color: '#0284C7',
      summary: 'Input core physiological observations that power the Gradient Boosting triage model.',
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', lineHeight: 1.6 }}>
            Accurate vital signs provide the baseline physiological grounding for machine learning risk estimation:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            <div style={{ padding: '10px 14px', background: '#F8FAFC', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Blood Pressure</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>SBP & DBP (mmHg)</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Normal ~120/80 mmHg</div>
            </div>
            <div style={{ padding: '10px 14px', background: '#F8FAFC', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Heart Rate</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>Pulse (BPM)</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Normal 60–100 BPM</div>
            </div>
            <div style={{ padding: '10px 14px', background: '#F8FAFC', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Respiration & SpO2</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>RR (/min) & SpO2 (%)</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>SpO2 &gt; 95% is normal</div>
            </div>
            <div style={{ padding: '10px 14px', background: '#F8FAFC', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Pain & Neurological</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>NRS (0–10) & AVPU</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Alert, Verbal, Pain, Unresponsive</div>
            </div>
          </div>

          <div style={{
            background: '#F0F9FF',
            border: '1px solid #BAE6FD',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}>
            <Info size={18} color="#0284C7" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.85rem', color: '#0369A1' }}>
              <strong>Clinical Guardrail:</strong> Hypotension (SBP &lt; 90), tachypnea (RR &ge; 30), or hypoxia (SpO2 &lt; 90%) trigger critical clinical rule checks to ensure high-acuity patients are never undertriaged.
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 2,
      badge: 'Step 3 • Hemodynamics',
      title: 'Real-Time Hemodynamic Monitoring Bar',
      icon: HeartPulse,
      color: '#EA580C',
      summary: 'Watch calculated physiological indices update automatically as you type.',
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', lineHeight: 1.6 }}>
            Located directly below the vital signs inputs, the live Hemodynamic Bar calculates validated cardiovascular indices instantly without page reloading:
          </p>
          <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.7 }}>
            <li><strong>Shock Index (HR / SBP):</strong> Normal range is 0.5 to 0.7. Any value <strong>&ge; 0.90</strong> triggers an immediate amber warning indicating occult hypoperfusion or impending shock.</li>
            <li><strong>Mean Arterial Pressure (MAP):</strong> Calculated via <code>(2 &times; DBP + SBP) / 3</code>. Normal range is 70 to 105 mmHg to guarantee adequate organ perfusion.</li>
            <li><strong>Pulse Pressure (SBP - DBP):</strong> Identifies narrow pressure (&lt; 30 mmHg, hypovolemia) or widened pulse pressure (&gt; 60 mmHg, aortic insufficiency / sepsis).</li>
          </ul>

          <div style={{
            background: '#FFF7ED',
            border: '1px solid #FED7AA',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}>
            <ShieldAlert size={18} color="#EA580C" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.85rem', color: '#9A3412' }}>
              <strong>Early Warning System:</strong> If the patient's Shock Index exceeds 0.90, the indicator automatically flashes with a "SHOCK RISK ALERT" badge before model submission.
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 3,
      badge: 'Step 4 • Diagnostic Signals',
      title: 'Attach ECG Signals & Chest Radiographs (Optional)',
      icon: Upload,
      color: '#D97706',
      summary: 'Enhance clinical evaluation with cardiac signal analysis and thoracic imaging.',
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', lineHeight: 1.6 }}>
            Our platform supports multimodal fusion by incorporating raw diagnostic signals alongside clinical vitals:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
            <div style={{ padding: '14px', background: '#F8FAFC', border: '1px solid var(--border-subtle)', borderRadius: '10px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#059669', marginBottom: '4px' }}>
                ⚡ Cardiac Rhythm (ECG Signal)
              </div>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Upload a 12-lead or Lead-II CSV signal. Analyzed via 1D-CNN deep neural network for arrhythmia, ST elevation, and tachycardia.
              </div>
              <div style={{ fontSize: '0.75rem', color: '#065F46', fontWeight: 600 }}>
                💡 Click "Load Demo Lead" to test with built-in ECG!
              </div>
            </div>

            <div style={{ padding: '14px', background: '#F8FAFC', border: '1px solid var(--border-subtle)', borderRadius: '10px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#D97706', marginBottom: '4px' }}>
                🫁 Chest Radiograph (X-Ray)
              </div>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Upload frontal thoracic image (PNG/JPG). Processed by DenseNet-121 neural network to detect cardiomegaly, effusion, or pneumonia.
              </div>
              <div style={{ fontSize: '0.75rem', color: '#92400E', fontWeight: 600 }}>
                💡 Click "Load Demo X-ray" to test with built-in radiograph!
              </div>
            </div>
          </div>

          <div style={{
            background: '#FEFCE8',
            border: '1px solid #FEF08A',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}>
            <Sparkles size={18} color="#D97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.85rem', color: '#854D0E' }}>
              <strong>Availability-Aware Fusion:</strong> Diagnostic files are 100% optional! If ECG or X-ray files are unavailable, the model gracefully triages using clinical vitals with zero hallucinations or artificial defaults.
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 4,
      badge: 'Step 5 • AI Triage Output',
      title: 'Run AI Assessment & Review Clinical Explanations',
      icon: CheckCircle2,
      color: '#10B981',
      summary: 'Trigger multimodal ensemble inference and inspect calibrated acuity & SHAP drivers.',
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', lineHeight: 1.6 }}>
            Click the green <strong>"Run AI Multimodal Assessment"</strong> button. The system executes the full inference pipeline and opens the comprehensive Result Page:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            <div style={{ padding: '12px', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '8px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#DC2626' }}>Level 1 • Critical (Red)</div>
              <div style={{ fontSize: '0.75rem', color: '#7F1D1D' }}>Immediate resuscitation (&lt; 0 min)</div>
            </div>
            <div style={{ padding: '12px', background: '#FFF7ED', border: '1px solid #FED7AA', borderRadius: '8px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#EA580C' }}>Level 2 • Emergent (Orange)</div>
              <div style={{ fontSize: '0.75rem', color: '#7C2D12' }}>Physician exam &lt; 15 min</div>
            </div>
            <div style={{ padding: '12px', background: '#FEFCE8', border: '1px solid #FEF08A', borderRadius: '8px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#D97706' }}>Level 3 • Urgent (Yellow)</div>
              <div style={{ fontSize: '0.75rem', color: '#78350F' }}>Physician exam &lt; 30 min</div>
            </div>
            <div style={{ padding: '12px', background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: '8px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#0284C7' }}>Level 4 • Less Urgent (Blue)</div>
              <div style={{ fontSize: '0.75rem', color: '#075985' }}>Low risk care &lt; 60 min</div>
            </div>
            <div style={{ padding: '12px', background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: '8px' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#059669' }}>Level 5 • Non-Urgent (Green)</div>
              <div style={{ fontSize: '0.75rem', color: '#064E3B' }}>Routine evaluation &lt; 120 min</div>
            </div>
          </div>

          <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.885rem', lineHeight: 1.65 }}>
            <li><strong>TreeSHAP Explainability:</strong> View the top physiological factors driving the risk prediction.</li>
            <li><strong>Patient Timeline:</strong> Click "Add New Observation" to log dynamic patient vitals and track acuity trends over time.</li>
            <li><strong>Persistent Queue:</strong> The assessment is automatically synchronized to the live emergency queue.</li>
          </ul>
        </div>
      ),
    },
  ];

  const current = steps[currentStep];
  const Icon = current.icon;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  const handleNext = () => {
    if (!isLastStep) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleStart = () => {
    onClose();
    if (onGoToAssessment) {
      onGoToAssessment();
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        animation: 'fadeIn 0.2s ease-out',
      }}
      onClick={onClose}
    >
      <div 
        style={{
          background: '#FFFFFF',
          borderRadius: '18px',
          maxWidth: '780px',
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid var(--border-subtle)',
          overflow: 'hidden',
          animation: 'slideUp 0.25s ease-out',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* MODAL HEADER */}
        <div style={{
          padding: '20px 26px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#FAFAFA',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #10B981, #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(16, 185, 129, 0.25)'
            }}>
              <HelpCircle size={22} color="#FFFFFF" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                Triage Assessment User Guide
              </h2>
              <p style={{ margin: '2px 0 0', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                Step-by-step walkthrough for evaluating emergency patients on the assessment page
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '6px',
              borderRadius: '8px',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background 0.15s ease',
            }}
            title="Close Guide"
          >
            <X size={20} />
          </button>
        </div>

        {/* STEP PROGRESS TABS BAR */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle)',
          background: '#FFFFFF',
          overflowX: 'auto',
          padding: '0 16px',
        }}>
          {steps.map((s, index) => {
            const isCurrent = index === currentStep;
            const isCompleted = index < currentStep;
            return (
              <button
                key={s.id}
                onClick={() => setCurrentStep(index)}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px 10px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: isCurrent ? '2px solid #10B981' : '2px solid transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  color: isCurrent ? '#059669' : (isCompleted ? 'var(--text-primary)' : 'var(--text-muted)'),
                  fontWeight: isCurrent ? 700 : 500,
                  fontSize: '0.8rem',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                {isCompleted ? (
                  <CheckCircle2 size={14} color="#10B981" />
                ) : (
                  <span style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: isCurrent ? '#10B981' : '#E2E8F0',
                    color: isCurrent ? '#FFFFFF' : '#64748B',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {index + 1}
                  </span>
                )}
                <span>Step {index + 1}</span>
              </button>
            );
          })}
        </div>

        {/* STEP CONTENT BODY (Scrollable) */}
        <div style={{ padding: '24px 28px', overflowY: 'auto', flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <span style={{
              display: 'inline-block',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '3px 10px',
              borderRadius: '9999px',
              background: '#ECFDF5',
              color: '#059669',
              border: '1px solid #A7F3D0',
            }}>
              {current.badge}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>

          <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '0 0 16px', color: 'var(--text-primary)' }}>
            {current.title}
          </h3>

          {current.content}
        </div>

        {/* MODAL FOOTER CONTROLS */}
        <div style={{
          padding: '16px 26px',
          borderTop: '1px solid var(--border-subtle)',
          background: '#FAFAFA',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          <div>
            <button
              type="button"
              onClick={handlePrev}
              disabled={isFirstStep}
              className="btn btn-secondary"
              style={{
                padding: '8px 16px',
                fontSize: '0.85rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                opacity: isFirstStep ? 0.4 : 1,
                cursor: isFirstStep ? 'not-allowed' : 'pointer',
              }}
            >
              <ChevronLeft size={16} />
              Previous Step
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {!isLastStep ? (
              <button
                type="button"
                onClick={handleNext}
                className="btn btn-secondary"
                style={{
                  padding: '8px 18px',
                  fontSize: '0.85rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  borderColor: '#10B981',
                  color: '#059669',
                  background: '#ECFDF5',
                  fontWeight: 600,
                }}
              >
                Next Step
                <ChevronRight size={16} />
              </button>
            ) : null}

            <button
              type="button"
              onClick={handleStart}
              className="btn btn-primary"
              style={{
                padding: '8px 20px',
                fontSize: '0.85rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 2px 10px rgba(16, 185, 129, 0.3)',
              }}
            >
              Go to Assessment Page
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
