import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [institution, setInstitution] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Detect OAuth token redirected from Google callback
        const urlParams = new URLSearchParams(window.location.search);
        const urlToken = urlParams.get('token');
        if (urlToken) {
          localStorage.setItem('triageai_token', urlToken);
          window.history.replaceState({}, document.title, window.location.pathname);
        }

        const storedToken = localStorage.getItem('triageai_token') || sessionStorage.getItem('triageai_token');
        const storedInst = localStorage.getItem('triageai_institution') || sessionStorage.getItem('triageai_institution');

        if (storedToken) {
          setToken(storedToken);
          if (storedInst) {
            try {
              setInstitution(JSON.parse(storedInst));
            } catch (e) {
              // Ignore parse error
            }
          }

          // Verify with live backend
          try {
            const verified = await api.getMe();
            if (verified) {
              setInstitution(verified);
              // Update storage with latest verified profile
              if (localStorage.getItem('triageai_token')) {
                localStorage.setItem('triageai_institution', JSON.stringify(verified));
              } else {
                sessionStorage.setItem('triageai_institution', JSON.stringify(verified));
              }
            }
          } catch (e) {
            console.warn('[Auth] Stored session expired or invalid:', e.message);
            // Session expired
            localStorage.removeItem('triageai_token');
            localStorage.removeItem('triageai_institution');
            sessionStorage.removeItem('triageai_token');
            sessionStorage.removeItem('triageai_institution');
            setToken(null);
            setInstitution(null);
          }
        }
      } catch (err) {
        console.error('[Auth] Failed to initialize auth state:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = (authToken, instData, rememberMe = true) => {
    setToken(authToken);
    setInstitution(instData);

    const storage = rememberMe ? localStorage : sessionStorage;
    const otherStorage = rememberMe ? sessionStorage : localStorage;

    // Clean other storage to prevent conflicts
    otherStorage.removeItem('triageai_token');
    otherStorage.removeItem('triageai_institution');

    storage.setItem('triageai_token', authToken);
    storage.setItem('triageai_institution', JSON.stringify(instData));
  };

  const logout = () => {
    localStorage.removeItem('triageai_token');
    localStorage.removeItem('triageai_institution');
    sessionStorage.removeItem('triageai_token');
    sessionStorage.removeItem('triageai_institution');
    setToken(null);
    setInstitution(null);
  };

  return (
    <AuthContext.Provider value={{
      institution,
      token,
      isAuthenticated: !!token && !!institution,
      isLoading,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
