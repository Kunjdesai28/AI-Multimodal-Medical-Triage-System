import React, { useEffect, useState } from 'react';
import { HeartPulse, Sparkles } from 'lucide-react';

export const SplashScreen = ({ onFinish }) => {
  const [fadingOut, setFadingOut] = useState(false);

  useEffect(() => {
    // Shutter animation duration: 1.9s show, 0.4s fade-out
    const timer = setTimeout(() => {
      setFadingOut(true);
      const finishTimer = setTimeout(() => {
        onFinish();
      }, 400);
      return () => clearTimeout(finishTimer);
    }, 1900);

    return () => clearTimeout(timer);
  }, [onFinish]);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 99999,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at center, #FFFFFF 0%, #FFF5F7 50%, #FFE8ED 100%)',
      transition: 'opacity 0.4s ease-out, transform 0.4s ease-out',
      opacity: fadingOut ? 0 : 1,
      transform: fadingOut ? 'scale(1.02)' : 'scale(1)',
      pointerEvents: fadingOut ? 'none' : 'auto',
      padding: '24px',
    }}>
      {/* Background Soft Glow Rings */}
      <div style={{
        position: 'absolute',
        width: '380px',
        height: '380px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(244, 63, 94, 0.08) 0%, rgba(16, 185, 129, 0.05) 50%, transparent 70%)',
        filter: 'blur(30px)',
        animation: 'pulseGlow 2.5s infinite ease-in-out',
        pointerEvents: 'none',
      }} />

      {/* Main Animated Branding Capsule */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        position: 'relative',
        animation: 'splashEntrance 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }}>
        {/* Animated Medical Icon Badge */}
        <div style={{
          width: '72px',
          height: '72px',
          borderRadius: '20px',
          background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 12px 30px rgba(16, 185, 129, 0.35), 0 0 0 8px rgba(16, 185, 129, 0.1)',
          marginBottom: '20px',
          animation: 'logoPop 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        }}>
          <HeartPulse size={40} color="#FFFFFF" />
        </div>

        {/* Brand Name */}
        <h1 style={{
          fontSize: 'clamp(2.2rem, 5vw, 3.2rem)',
          fontWeight: 800,
          letterSpacing: '-0.04em',
          margin: '0 0 6px',
          color: '#0F172A',
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
        }}>
          TRIAGE<span style={{ color: '#10B981' }}>AI</span>
        </h1>

        {/* Subtitle */}
        <div style={{
          fontSize: '0.85rem',
          fontWeight: 700,
          letterSpacing: '0.18em',
          color: '#64748B',
          textTransform: 'uppercase',
          marginBottom: '24px',
        }}>
          MULTIMODAL EMERGENCY TRIAGE
        </div>

        {/* Medical Heartbeat (EKG) SVG Pulse Line */}
        <div style={{
          width: '240px',
          height: '42px',
          position: 'relative',
          overflow: 'hidden',
          marginBottom: '16px',
        }}>
          <svg
            width="240"
            height="42"
            viewBox="0 0 240 42"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ width: '100%', height: '100%' }}
          >
            {/* Guide line */}
            <path
              d="M 0 21 L 240 21"
              stroke="rgba(244, 63, 94, 0.15)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
            {/* Animated EKG pulse */}
            <path
              d="M 0 21 L 70 21 L 80 10 L 90 32 L 100 4 L 112 38 L 122 21 L 135 21 L 142 16 L 150 21 L 240 21"
              stroke="url(#ekgGradient)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                strokeDasharray: 300,
                strokeDashoffset: 300,
                animation: 'ekgDraw 1.6s ease-in-out infinite',
              }}
            />
            <defs>
              <linearGradient id="ekgGradient" x1="0" y1="0" x2="240" y2="0" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F43F5E" />
                <stop offset="0.5" stopColor="#10B981" />
                <stop offset="1" stopColor="#059669" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Clinical Enterprise Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '7px',
          padding: '6px 14px',
          borderRadius: '9999px',
          background: 'rgba(255, 255, 255, 0.85)',
          border: '1px solid rgba(244, 63, 94, 0.2)',
          boxShadow: '0 2px 8px rgba(244, 63, 94, 0.06)',
          fontSize: '0.785rem',
          color: '#475569',
          fontWeight: 600,
        }}>
          <span style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: '#10B981',
            boxShadow: '0 0 6px #10B981',
          }} />
          Enterprise Clinical Decision Support
        </div>
      </div>
    </div>
  );
};
