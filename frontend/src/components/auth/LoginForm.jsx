import React, { useState, useEffect } from 'react';
import { 
  Building2, Lock, Eye, EyeOff, ArrowRight, ArrowLeft, 
  AlertCircle, CheckCircle2, Sparkles, RefreshCw, HeartPulse 
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export const LoginForm = ({ 
  onSwitchToRegister, 
  onBackToLanding, 
  onForgotPassword, 
  initialIdentifier = '', 
  registrationBanner = null 
}) => {
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState(initialIdentifier || '');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (initialIdentifier) {
      setIdentifier(initialIdentifier);
    }
  }, [initialIdentifier]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanIdent = identifier.trim();
    if (!cleanIdent || !password) {
      setErrorMsg('Please enter both your Institution ID/Email and Password.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await api.loginInstitution({
        identifier: cleanIdent,
        password: password,
        rememberMe: rememberMe,
      });

      if (res.success && res.token && res.institution) {
        login(res.token, res.institution, rememberMe);
      } else {
        setErrorMsg('Authentication failed. Please check credentials.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      width: '100%',
      maxWidth: '440px',
      margin: '0 auto',
      animation: 'fadeIn 0.3s ease-out',
    }}>
      {/* Back button */}
      {onBackToLanding && (
        <div style={{ marginBottom: '16px' }}>
          <button
            type="button"
            onClick={onBackToLanding}
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
              padding: '4px 0',
              transition: 'color 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#0F172A'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = '#64748B'; }}
          >
            <ArrowLeft size={16} />
            Back to Options
          </button>
        </div>
      )}


      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderRadius: '24px',
        padding: '38px 32px',
        boxShadow: '0 20px 45px -10px rgba(15, 23, 42, 0.12), 0 4px 16px rgba(15, 23, 42, 0.04)',
        border: '1px solid rgba(255, 255, 255, 0.9)',
      }}>
        {/* TRIAGEAI Logo Header (Centered) */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          marginBottom: '20px',
        }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #10B981, #059669)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.28)',
          }}>
            <HeartPulse size={24} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#0F172A', lineHeight: 1.1 }}>
              TRIAGE<span style={{ color: '#10B981' }}>AI</span>
            </div>
            <div style={{ fontSize: '0.675rem', color: '#94A3B8', fontWeight: 700, letterSpacing: '0.06em' }}>
              CLINICAL PORTAL
            </div>
          </div>
        </div>

        {/* Title (Centered) */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0F172A', margin: '0 0 6px', letterSpacing: '-0.02em' }}>
            Welcome
          </h2>
          <p style={{ color: '#64748B', fontSize: '0.9rem', margin: 0, lineHeight: 1.5 }}>
            Sign in to your TRIAGEAI institution account.
          </p>
        </div>

        {/* Registration Success Banner */}
        {registrationBanner && (
          <div style={{
            background: 'linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)',
            border: '1px solid #A7F3D0',
            borderRadius: '12px',
            padding: '14px 16px',
            color: '#065F46',
            fontSize: '0.85rem',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            lineHeight: 1.45,
            boxShadow: '0 4px 14px rgba(16, 185, 129, 0.12)',
          }}>
            <CheckCircle2 size={18} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 700, marginBottom: '2px', color: '#064E3B' }}>
                Registration Confirmed!
              </div>
              <div style={{ color: '#047857' }}>
                Confirmation email sent to <strong>{registrationBanner.identifier}</strong>. Sign in using your registered credentials.
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div style={{
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: '10px',
            padding: '12px 14px',
            color: '#991B1B',
            fontSize: '0.85rem',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            lineHeight: 1.4,
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Standard Form: Username & Password */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

          {/* Official Email / Clinic Name / Institution ID */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>
                Official Email or Institution ID
              </label>
              <span style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 600 }}>
                Not case-sensitive
              </span>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                required
                placeholder="Enter email, clinic name, or ID"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                style={{
                  width: '100%',
                  padding: '11px 14px 11px 40px',
                  borderRadius: '10px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.925rem',
                  outline: 'none',
                  transition: 'all 0.15s ease',
                  background: '#FFFFFF',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#10B981';
                  e.target.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.12)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#CBD5E1';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <Building2 size={18} color="#94A3B8" style={{ position: 'absolute', left: '13px', top: '13px' }} />
            </div>
          </div>

          {/* Password */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>
                Password
              </label>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '11px 42px 11px 40px',
                  borderRadius: '10px',
                  border: '1px solid #CBD5E1',
                  fontSize: '0.925rem',
                  outline: 'none',
                  transition: 'all 0.15s ease',
                  background: '#FFFFFF',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#10B981';
                  e.target.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.12)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#CBD5E1';
                  e.target.style.boxShadow = 'none';
                }}
              />
              <Lock size={18} color="#94A3B8" style={{ position: 'absolute', left: '13px', top: '13px' }} />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '12px',
                  background: 'transparent',
                  border: 'none',
                  color: '#94A3B8',
                  cursor: 'pointer',
                  padding: '2px',
                }}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Remember Me */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: '#475569' }}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: '#10B981', cursor: 'pointer' }}
              />
              Remember Me
            </label>
          </div>

          {/* [ Sign In ] Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '13px',
              borderRadius: '11px',
              fontWeight: 700,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              background: 'linear-gradient(135deg, #10B981, #059669)',
              border: 'none',
              color: '#FFFFFF',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '4px',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 6px 18px rgba(16, 185, 129, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 14px rgba(16, 185, 129, 0.3)';
            }}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                Authenticating...
              </>
            ) : (
              <>
                Sign In
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Forgot Password? Link */}
        <div style={{ textAlign: 'center', marginTop: '16px' }}>
          <button
            type="button"
            onClick={onForgotPassword}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#059669',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              padding: '4px 8px',
              transition: 'color 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#047857'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = '#059669'; }}
          >
            Forgot Password?
          </button>
        </div>

        {/* Register Prompt */}
        <div style={{
          marginTop: '20px',
          paddingTop: '18px',
          borderTop: '1px solid #F1F5F9',
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#64748B',
        }}>
          New user?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#059669',
              fontWeight: 700,
              cursor: 'pointer',
              padding: 0,
              transition: 'color 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#047857'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = '#059669'; }}
          >
            Sign Up / Register Here
          </button>
        </div>
      </div>
    </div>
  );
};
