import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, HeartPulse, LineChart, HelpCircle, Building2, LogOut } from 'lucide-react';
import { api } from '../services/api';
import { HelpModal } from './HelpModal';
import { useAuth } from '../context/AuthContext';

export const Navbar = ({ activePage, setActivePage }) => {
  const { institution, logout } = useAuth();
  const [systemOnline, setSystemOnline] = useState(null);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        await api.checkHealth();
        setSystemOnline(true);
      } catch {
        setSystemOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'landing', label: 'Home', icon: Activity },
    { id: 'dashboard', label: 'Triage Queue', icon: ShieldAlert },
    { id: 'assessment', label: 'New Assessment', icon: HeartPulse },
    { id: 'timeline', label: 'Risk Timeline', icon: LineChart },
  ];

  return (
    <>
      <nav style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        boxShadow: '0 2px 10px rgba(15, 23, 42, 0.04)',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        minHeight: '64px',
      }}>
        {/* Brand */}
        <div 
          onClick={() => setActivePage('landing')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', flexShrink: 0 }}
        >
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #10B981, #059669)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
            flexShrink: 0,
          }}>
            <HeartPulse size={22} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.1, color: 'var(--text-primary)' }}>
              TRIAGE<span style={{ color: '#10B981' }}>AI</span>
            </div>
            <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.04em' }}>
              MULTIMODAL EMERGENCY TRIAGE
            </div>
          </div>
        </div>

        {/* Nav Links Segmented Group */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '6px',
          background: '#F8FAFC',
          padding: '4px 6px',
          borderRadius: '12px',
          border: '2px solid #10B981',
        }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '7px',
                  padding: '7px 14px',
                  borderRadius: '8px',
                  background: isActive ? '#FFFFFF' : 'transparent',
                  border: isActive ? '2px solid #059669' : '2px solid transparent',
                  color: isActive ? '#059669' : 'var(--text-secondary)',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  boxShadow: isActive ? '0 1px 4px rgba(16, 185, 129, 0.18)' : 'none',
                  whiteSpace: 'nowrap',
                  height: '34px',
                  boxSizing: 'border-box',
                }}
              >
                <Icon size={15} color={isActive ? '#059669' : '#64748B'} />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Database & System Status Indicator + Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '7px',
            background: '#F1F5F9',
            padding: '6px 12px',
            borderRadius: '8px',
            border: '2px solid #10B981',
            fontSize: '0.785rem',
            height: '36px',
            boxSizing: 'border-box',
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: systemOnline === true ? '#10B981' : (systemOnline === false ? '#EF4444' : '#F59E0B'),
              boxShadow: systemOnline === true ? '0 0 6px rgba(16, 185, 129, 0.5)' : 'none',
              flexShrink: 0,
            }} />
            <span style={{ color: 'var(--text-secondary)', fontWeight: 500, whiteSpace: 'nowrap' }}>
              {systemOnline === true ? 'MongoDB: Connected (triageai)' : (systemOnline === false ? 'Database Offline' : 'Connecting...')}
            </span>
          </div>

          {/* Authenticated Institution & Logout */}
          {institution && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
              justifyContent: 'center',
              gap: '3px',
              borderLeft: '2px solid #10B981',
              paddingLeft: '14px',
            }}>
              <div 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  lineHeight: 1.2,
                }}
                title={`Logged in institution: ${institution.institutionName} (${institution.institutionId})`}
              >
                <Building2 size={13} color="#059669" />
                <span style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {institution.institutionName}
                </span>
              </div>

              <button
                type="button"
                onClick={logout}
                style={{
                  background: '#FFFFFF',
                  border: '2px solid #10B981',
                  color: '#065F46',
                  borderRadius: '6px',
                  padding: '2px 8px',
                  fontSize: '0.725rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  height: '24px',
                  boxSizing: 'border-box',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#FECDD3';
                  e.currentTarget.style.color = '#E11D48';
                  e.currentTarget.style.background = '#FFF1F4';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#10B981';
                  e.currentTarget.style.color = '#065F46';
                  e.currentTarget.style.background = '#FFFFFF';
                }}
                title="Sign out of this institution workspace"
              >
                <LogOut size={11} />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </nav>

      {/* Floating Help & Guide Action Button in Bottom Right */}
      <button 
        onClick={() => setIsHelpOpen(true)}
        style={{ 
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 99,
          padding: '10px 18px', 
          fontSize: '0.85rem', 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          borderRadius: '50px',
          border: '2px solid #10B981',
          color: '#065F46',
          background: '#ECFDF5',
          fontWeight: 700,
          boxShadow: '0 4px 14px rgba(16, 185, 129, 0.22), 0 1px 3px rgba(0, 0, 0, 0.05)',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(16, 185, 129, 0.35)';
          e.currentTarget.style.background = '#D1FAE5';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 4px 14px rgba(16, 185, 129, 0.22), 0 1px 3px rgba(0, 0, 0, 0.05)';
          e.currentTarget.style.background = '#ECFDF5';
        }}
        title="Step-by-step instructions for completing patient assessment"
      >
        <HelpCircle size={18} color="#059669" />
        Help & Guide
      </button>


      {/* Triage Assessment Step-by-Step Walkthrough Modal */}
      <HelpModal 
        isOpen={isHelpOpen} 
        onClose={() => setIsHelpOpen(false)} 
        onGoToAssessment={() => setActivePage('assessment')}
      />
    </>
  );
};

