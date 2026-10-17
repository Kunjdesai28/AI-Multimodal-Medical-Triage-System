import React, { useState, useEffect } from 'react';
import { HeartPulse, Shield } from 'lucide-react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { ForgotPasswordModal } from './ForgotPasswordModal';

export const AuthLanding = () => {
  // First, the login page pops up directly (not the registration page)
  const [view, setView] = useState('login'); // 'login' | 'register'
  const [registeredInfo, setRegisteredInfo] = useState(null);
  const [isForgotOpen, setIsForgotOpen] = useState(false);

  const handleProceedToLogin = (info) => {
    if (info && info.identifier) {
      setRegisteredInfo(info);
    }
    setView('login');
  };

  // Check URL query parameters for Google OAuth redirection
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const action = params.get('action');
    if (action === 'complete_registration') {
      setView('register');
    }
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflowX: 'hidden',
    }}>
      {/* High-Resolution Hospital Background Image with Professional Subtle Backdrop */}
      <div style={{
        position: 'fixed',
        inset: 0,
        backgroundImage: 'linear-gradient(135deg, rgba(248, 250, 252, 0.78) 0%, rgba(255, 241, 244, 0.82) 50%, rgba(240, 253, 250, 0.82) 100%), url("/auth_bg.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        zIndex: 0,
        pointerEvents: 'none',
      }} />

      {/* Subtle Depth Vignette */}
      <div style={{
        position: 'fixed',
        inset: 0,
        background: 'radial-gradient(ellipse at center, transparent 40%, rgba(15, 23, 42, 0.10) 100%)',
        zIndex: 0,
        pointerEvents: 'none',
      }} />

      {/* TOP COMPACT BRAND HEADER */}
      <header style={{
        padding: '24px 36px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 10,
      }}>
        <div 
          onClick={() => setView('login')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #10B981, #059669)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
          }}>
            <HeartPulse size={24} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.1, color: '#0F172A' }}>
              TRIAGE<span style={{ color: '#10B981' }}>AI</span>
            </div>
            <div style={{ fontSize: '0.675rem', color: '#64748B', fontWeight: 600, letterSpacing: '0.06em' }}>
              MULTIMODAL EMERGENCY TRIAGE
            </div>
          </div>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(8px)',
          padding: '6px 14px',
          borderRadius: '9999px',
          border: '1px solid #FFE4E8',
          fontSize: '0.785rem',
          color: '#475569',
          fontWeight: 600,
        }}>
          <Shield size={14} color="#059669" />
          <span>Hospital Data Partitioning Active</span>
        </div>
      </header>

      {/* MAIN AUTHENTICATION CONTAINER: Login opens by default */}
      <main style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        zIndex: 10,
      }}>
        <div style={{
          width: '100%',
          maxWidth: view === 'register' ? '800px' : '460px',
          transition: 'max-width 0.3s ease',
        }}>
          {view === 'register' ? (
            <RegisterForm 
              onSwitchToLogin={handleProceedToLogin}
            />
          ) : (
            <LoginForm 
              onSwitchToRegister={() => {
                setRegisteredInfo(null);
                setView('register');
              }}
              onBackToLanding={null}
              onForgotPassword={() => setIsForgotOpen(true)}
              initialIdentifier={registeredInfo?.identifier || ''}
              registrationBanner={registeredInfo}
            />
          )}
        </div>
      </main>

      {/* Forgot Password Modal */}
      <ForgotPasswordModal 
        isOpen={isForgotOpen} 
        onClose={() => setIsForgotOpen(false)} 
        onBackToLogin={() => {
          setIsForgotOpen(false);
          setView('login');
        }}
      />
    </div>
  );
};
