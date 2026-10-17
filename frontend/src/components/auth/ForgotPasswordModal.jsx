import React, { useState } from 'react';
import { Mail, ArrowLeft, CheckCircle2, AlertCircle, RefreshCw, KeyRound, X } from 'lucide-react';
import { api } from '../../services/api';

export const ForgotPasswordModal = ({ isOpen, onClose, onBackToLogin }) => {
  const [identifier, setIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setErrorMsg('Please enter your institution email or ID.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await api.forgotPassword(identifier.trim());
      setSuccessMsg(res.message || 'Password reset instructions have been sent to your registered email.');
    } catch (err) {
      setErrorMsg(err.message || 'Unable to process reset request. Please verify connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 99999,
      background: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      animation: 'fadeIn 0.2s ease-out',
    }}>
      <div style={{
        background: '#FFFFFF',
        borderRadius: '20px',
        maxWidth: '480px',
        width: '100%',
        boxShadow: '0 25px 50px -12px rgba(225, 29, 72, 0.15)',
        border: '1px solid #FCE7EC',
        overflow: 'hidden',
        animation: 'slideUp 0.25s ease-out',
        padding: '32px',
        position: 'relative',
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'transparent',
            border: 'none',
            color: '#94A3B8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '8px',
          }}
        >
          <X size={20} />
        </button>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '14px',
            background: '#FFF1F4',
            border: '1px solid #FFE4E8',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#E11D48',
            marginBottom: '14px',
          }}>
            <KeyRound size={26} />
          </div>
          <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0F172A', margin: '0 0 6px' }}>
            Reset Institution Password
          </h3>
          <p style={{ color: '#64748B', fontSize: '0.875rem', margin: 0, lineHeight: 1.5 }}>
            Enter your registered Official Institution Email or Institution ID to receive a secure recovery link.
          </p>
        </div>

        {successMsg ? (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div style={{
              background: '#ECFDF5',
              border: '1px solid #A7F3D0',
              borderRadius: '12px',
              padding: '16px',
              color: '#065F46',
              fontSize: '0.9rem',
              lineHeight: 1.5,
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              textAlign: 'left',
            }}>
              <CheckCircle2 size={20} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong>Instructions Dispatched</strong>
                <p style={{ margin: '4px 0 0', fontSize: '0.85rem' }}>{successMsg}</p>
              </div>
            </div>

            <button
              type="button"
              onClick={onBackToLogin}
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                fontWeight: 600,
                fontSize: '0.9rem',
              }}
            >
              Return to Login
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {errorMsg && (
              <div style={{
                background: '#FEF2F2',
                border: '1px solid #FECACA',
                borderRadius: '10px',
                padding: '10px 14px',
                color: '#991B1B',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <AlertCircle size={16} />
                <span>{errorMsg}</span>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>
                Institution Email or ID
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  placeholder="e.g. admin@cityhospital.org or city_hospital_01"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '11px 14px 11px 40px',
                    borderRadius: '10px',
                    border: '1px solid #CBD5E1',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'all 0.2s',
                  }}
                  autoFocus
                />
                <Mail size={18} color="#94A3B8" style={{ position: 'absolute', left: '13px', top: '13px' }} />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                fontWeight: 600,
                fontSize: '0.925rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, #10B981, #059669)',
                border: 'none',
                color: '#FFFFFF',
                boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Dispatching Instructions...
                </>
              ) : (
                'Send Reset Instructions'
              )}
            </button>

            <div style={{ textAlign: 'center', marginTop: '6px' }}>
              <button
                type="button"
                onClick={onBackToLogin}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#64748B',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <ArrowLeft size={14} />
                Back to Sign In
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
