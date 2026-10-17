const API_BASE = 'http://localhost:8000/api';

const getStoredToken = () => {
  return localStorage.getItem('triageai_token') || sessionStorage.getItem('triageai_token');
};

const getStoredInstitution = () => {
  const raw = localStorage.getItem('triageai_institution') || sessionStorage.getItem('triageai_institution');
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const getAuthHeaders = () => {
  const token = getStoredToken();
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  // Authentication & Institution Onboarding
  async registerInstitution(data) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = Array.isArray(result.detail) 
        ? result.detail.map(d => d.msg).join(', ') 
        : (result.detail || 'Registration failed');
      throw new Error(msg);
    }
    return result;
  },

  async loginInstitution(credentials) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    const result = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(result.detail || 'Invalid Institution credentials');
    }
    return result;
  },

  async getMe() {
    const token = getStoredToken();
    if (!token) return null;
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Session invalid or expired');
    return res.json();
  },

  async forgotPassword(identifier) {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier }),
    });
    const result = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(result.detail || 'Password reset request failed');
    return result;
  },

  async checkHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async createAssessment(formData) {
    // Automatically inject institution ID from authenticated session if available
    const inst = getStoredInstitution();
    if (inst?.institutionId && formData.has('patient_data')) {
      try {
        const raw = formData.get('patient_data');
        const parsed = JSON.parse(raw);
        if (!parsed.institution_id) {
          parsed.institution_id = inst.institutionId;
          parsed.institution_name = inst.institutionName;
          formData.set('patient_data', JSON.stringify(parsed));
        }
      } catch (e) {
        // Fallback gracefully
      }
    }

    const res = await fetch(`${API_BASE}/assessment`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Assessment failed' }));
      throw new Error(err.detail || 'Assessment request failed');
    }
    return res.json();
  },

  async createJsonAssessment(vitals, patientName = 'Patient', patientId) {
    const inst = getStoredInstitution();
    const res = await fetch(`${API_BASE}/assessment/json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        patient_id: patientId,
        patient_name: patientName,
        institution_id: inst?.institutionId,
        vitals: vitals,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Assessment failed' }));
      throw new Error(err.detail || 'Assessment request failed');
    }
    return res.json();
  },

  async getNextPatientId() {
    try {
      const res = await fetch(`${API_BASE}/assessment/next-patient-id`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) return 'PAT-01';
      const data = await res.json();
      return data.next_patient_id || 'PAT-01';
    } catch {
      return 'PAT-01';
    }
  },

  async getAssessment(id) {
    const res = await fetch(`${API_BASE}/assessment/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Assessment not found');
    return res.json();
  },

  async listAssessments(institutionId = null) {
    const inst = getStoredInstitution();
    const targetInstId = institutionId || inst?.institutionId;
    const url = targetInstId 
      ? `${API_BASE}/assessment?institution_id=${encodeURIComponent(targetInstId)}`
      : `${API_BASE}/assessment`;

    const res = await fetch(url, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to list assessments');
    return res.json();
  },


  async getTimeline(patientId) {
    const res = await fetch(`${API_BASE}/timeline/${patientId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Timeline not found');
    return res.json();
  },

  async addObservation(patientId, formData) {
    const res = await fetch(`${API_BASE}/timeline/${patientId}/observation`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Observation update failed' }));
      throw new Error(err.detail || 'Observation update failed');
    }
    return res.json();
  },

  async getModelMetrics() {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error('Failed to load model metrics');
    return res.json();
  },

  async analyzeECG(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/ecg/analyze`, {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) throw new Error('ECG file analysis failed');
    return res.json();
  },

  async analyzeXRay(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/xray/analyze`, {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) throw new Error('Chest X-ray analysis failed');
    return res.json();
  },

  async clearAssessments() {
    const res = await fetch(`${API_BASE}/assessment`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to clear assessments');
    return res.json();
  },

  async getDatabaseInfo() {
    const res = await fetch(`${API_BASE}/assessment/database/info`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load database info');
    return res.json();
  },

  async logout() {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
    } catch (e) {
      // Ignore network errors during logout
    }
    localStorage.removeItem('triageai_token');
    localStorage.removeItem('triageai_institution');
    sessionStorage.removeItem('triageai_token');
    sessionStorage.removeItem('triageai_institution');
  },
};
