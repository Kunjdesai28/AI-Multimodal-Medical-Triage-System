import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SplashScreen } from './components/auth/SplashScreen';
import { AuthLanding } from './components/auth/AuthLanding';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { AssessmentPage } from './pages/AssessmentPage';
import { ResultPage } from './pages/ResultPage';
import { TimelinePage } from './pages/TimelinePage';

const MainAppContent = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [showSplash, setShowSplash] = useState(true);
  const [activePage, setActivePage] = useState('landing');
  const [currentAssessment, setCurrentAssessment] = useState(null);
  const [timelinePatientId, setTimelinePatientId] = useState('PAT-DEMO');

  const handleAssessmentCompleted = (assessment) => {
    setCurrentAssessment(assessment);
    setTimelinePatientId(assessment.patient_id);
    setActivePage('result');
  };

  const handleSelectAssessment = (assessment) => {
    setCurrentAssessment(assessment);
    setTimelinePatientId(assessment.patient_id);
    setActivePage('result');
  };

  const handleOpenTimeline = (patientId) => {
    setTimelinePatientId(patientId);
    setActivePage('timeline');
  };

  // 1. OPENING SPLASH / SHUTTER SCREEN (plays on initial load / reload)
  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  // 2. AUTHENTICATION PROTECTION: If not authenticated, show institutional auth flow
  if (!isAuthenticated && !isLoading) {
    return <AuthLanding />;
  }

  // 3. EXISTING TRIAGEAI MAIN APPLICATION (Preserved intact after authentication)
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Global Navigation Bar */}
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      {/* Main Content Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {activePage === 'landing' && (
          <LandingPage
            onStartAssessment={() => setActivePage('assessment')}
          />
        )}

        {activePage === 'dashboard' && (
          <DashboardPage
            onSelectAssessment={handleSelectAssessment}
            onNewAssessment={() => setActivePage('assessment')}
            onOpenTimeline={handleOpenTimeline}
          />
        )}

        {activePage === 'assessment' && (
          <AssessmentPage
            onAssessmentCompleted={handleAssessmentCompleted}
          />
        )}

        {activePage === 'result' && currentAssessment && (
          <ResultPage
            assessment={currentAssessment}
            onBackToQueue={() => setActivePage('dashboard')}
            onGoToTimeline={handleOpenTimeline}
          />
        )}

        {activePage === 'timeline' && (
          <TimelinePage
            initialPatientId={timelinePatientId}
            onViewAssessment={handleSelectAssessment}
          />
        )}
      </main>
    </div>
  );
};

export const App = () => {
  return (
    <AuthProvider>
      <MainAppContent />
    </AuthProvider>
  );
};

export default App;
