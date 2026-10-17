import React, { useState, useMemo } from 'react';
import { 
  Building2, ArrowRight, ArrowLeft, Eye, EyeOff,
  CheckCircle2, AlertCircle, RefreshCw, Sparkles 
} from 'lucide-react';
import { api } from '../../services/api';
import { INDIAN_STATES } from '../../data/indianStates';

export const RegisterForm = ({ onSwitchToLogin, onRegistrationSuccess }) => {
  // Organization details + password & confirm password
  const [formData, setFormData] = useState({
    hospitalName: '',
    organizationType: 'Hospital',
    registrationNumber: '',
    country: 'India',
    state: '',
    city: '',
    address: '',
    pincode: '',
    contactNumber: '',
    officialEmail: '',
    website: '',
    password: '',
    confirmPassword: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [touched, setTouched] = useState({});
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successModalData, setSuccessModalData] = useState(null);
  const [countdown, setCountdown] = useState(5);

  // Auto-redirect timer for registration success popup
  React.useEffect(() => {
    if (!successModalData) return;
    setCountdown(5);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleProceedToLogin();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [successModalData]);

  const handleProceedToLogin = () => {
    if (successModalData && onSwitchToLogin) {
      onSwitchToLogin({
        identifier: successModalData.officialEmail,
        hospitalName: successModalData.hospitalName,
      });
    }
  };

  // Field change handler: restrict contact number strictly to 10 digits
  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'contactNumber') {
      const digitsOnly = value.replace(/\D/g, '').slice(0, 10);
      setFormData(prev => ({
        ...prev,
        [name]: digitsOnly
      }));
      return;
    }
    if (name === 'pincode') {
      const pinDigits = value.replace(/\D/g, '').slice(0, 6);
      setFormData(prev => ({
        ...prev,
        [name]: pinDigits
      }));
      return;
    }
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
  };

  // Comprehensive Inline Validation
  const errors = useMemo(() => {
    const errs = {};

    // 1. Hospital / Clinic Name (Required)
    if (!formData.hospitalName.trim()) {
      errs.hospitalName = 'Hospital / Clinic Name is required.';
    }

    // 2. Organization Type (Required)
    if (!formData.organizationType.trim()) {
      errs.organizationType = 'Please select an Organization Type.';
    }

    // 3. Registration / License Number (Required)
    if (!formData.registrationNumber.trim()) {
      errs.registrationNumber = 'Registration / License Number is required.';
    }

    // 4. Country (Required)
    if (!formData.country.trim()) {
      errs.country = 'Country is required.';
    }

    // 5. State (Required)
    if (!formData.state.trim()) {
      errs.state = 'Please select a State.';
    }

    // 6. City (Required)
    if (!formData.city.trim()) {
      errs.city = 'City is required.';
    }

    // 7. Full Address (Required)
    if (!formData.address.trim()) {
      errs.address = 'Full Address is required.';
    }

    // 8. Pincode (Required, 6-digit Indian pincode)
    const pin = formData.pincode.trim();
    if (!pin) {
      errs.pincode = 'Pincode is required.';
    } else if (!/^[1-9][0-9]{5}$/.test(pin)) {
      errs.pincode = 'Please enter a valid 6-digit Indian pincode (e.g. 400001).';
    }

    // 9. Contact Number (Required, exactly 10 digits only)
    const phone = formData.contactNumber.trim();
    if (!phone) {
      errs.contactNumber = 'Contact phone number is required.';
    } else if (!/^\d{10}$/.test(phone)) {
      errs.contactNumber = 'Phone number must be exactly 10 digits.';
    }

    // 10. Official Email (Required, valid email address)
    const email = formData.officialEmail.trim();
    if (!email) {
      errs.officialEmail = 'Official Email is required.';
    } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) {
      errs.officialEmail = 'Please enter a valid email address (e.g. info@hospital.org).';
    }

    // 11. Website (Optional, valid URL if provided)
    const web = formData.website.trim();
    if (web) {
      const isValidUrl = /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{2,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)$/i.test(web);
      if (!isValidUrl) {
        errs.website = 'Please enter a valid website URL (e.g. https://www.example.com).';
      }
    }

    // 12. Password (Required, min 6 characters)
    const pw = formData.password;
    if (!pw) {
      errs.password = 'Password is required.';
    } else if (pw.length < 6) {
      errs.password = 'Password must be at least 6 characters long.';
    }

    // 13. Confirm Password (Required, must match password)
    const cpw = formData.confirmPassword;
    if (!cpw) {
      errs.confirmPassword = 'Please confirm your password.';
    } else if (pw !== cpw) {
      errs.confirmPassword = 'Passwords do not match.';
    }

    return errs;
  }, [formData]);

  const isFormValid = useMemo(() => {
    return Object.keys(errors).length === 0;
  }, [errors]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Mark all required fields as touched
    const allTouched = {
      hospitalName: true,
      organizationType: true,
      registrationNumber: true,
      country: true,
      state: true,
      city: true,
      address: true,
      pincode: true,
      contactNumber: true,
      officialEmail: true,
      website: Boolean(formData.website),
      password: true,
      confirmPassword: true,
    };
    setTouched(allTouched);

    if (!isFormValid) {
      setErrorMsg('Please correct the highlighted validation errors before submitting.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const payload = {
        hospitalName: formData.hospitalName.trim(),
        organizationType: formData.organizationType,
        registrationNumber: formData.registrationNumber.trim(),
        country: formData.country.trim(),
        state: formData.state.trim(),
        city: formData.city.trim(),
        address: formData.address.trim(),
        pincode: formData.pincode.trim(),
        contactNumber: formData.contactNumber.trim(),
        officialEmail: formData.officialEmail.trim().toLowerCase(),
        website: formData.website.trim() || null,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
      };

      const res = await api.registerInstitution(payload);
      if (res.success) {
        setSuccessModalData({
          hospitalName: formData.hospitalName.trim(),
          organizationType: formData.organizationType,
          officialEmail: formData.officialEmail.trim().toLowerCase(),
          contactNumber: formData.contactNumber.trim(),
        });
      } else {
        setErrorMsg(res.message || 'Registration could not be completed.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Registration request failed. Please check network connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      maxWidth: '740px',
      margin: '0 auto',
      animation: 'fadeIn 0.3s ease-out',
    }}>
      {/* Back to Sign In button */}
      <div style={{ marginBottom: '16px' }}>
        <button
          type="button"
          onClick={onSwitchToLogin}
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
          }}
        >
          <ArrowLeft size={16} />
          Back to Sign In
        </button>
      </div>

      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderRadius: '24px',
        padding: '36px 32px',
        boxShadow: '0 20px 45px -10px rgba(15, 23, 42, 0.12), 0 4px 16px rgba(15, 23, 42, 0.04)',
        border: '1px solid rgba(255, 255, 255, 0.9)',
      }}>
        {/* Header */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: '9999px',
            background: '#FFF1F4',
            border: '1px solid #FFE4E8',
            color: '#E11D48',
            fontSize: '0.75rem',
            fontWeight: 700,
            marginBottom: '10px',
          }}>
            <Sparkles size={13} />
            Institutional Onboarding
          </div>
          <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0F172A', margin: '0 0 6px', letterSpacing: '-0.02em' }}>
            Hospital / Clinic Registration
          </h2>
          <p style={{ color: '#64748B', fontSize: '0.925rem', margin: 0, lineHeight: 1.5 }}>
            Enter your healthcare organization details and password below to create your isolated emergency triage workspace.
          </p>
        </div>

        {/* Global Error Banner */}
        {errorMsg && (
          <div style={{
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: '12px',
            padding: '12px 16px',
            color: '#991B1B',
            fontSize: '0.875rem',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Section Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #F1E4E8', paddingBottom: '8px' }}>
            <Building2 size={20} color="#059669" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1E293B', margin: 0 }}>
              Organization Details
            </h3>
          </div>

          {/* Form Grid: Two-column on desktop, single-column on smaller screens */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '18px 20px',
          }}>

            {/* 1. Hospital / Clinic Name */}
            <div className="input-group">
              <label style={labelStyle}>
                Hospital / Clinic Name <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <input
                type="text"
                name="hospitalName"
                required
                placeholder="Enter hospital or clinic name"
                value={formData.hospitalName}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.hospitalName && errors.hospitalName ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.hospitalName && errors.hospitalName && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.hospitalName}
                </span>
              )}
            </div>

            {/* 2. Organization Type */}
            <div className="input-group">
              <label style={labelStyle}>
                Organization Type <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <select
                name="organizationType"
                required
                value={formData.organizationType}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.organizationType && errors.organizationType ? '#EF4444' : '#CBD5E1',
                }}
              >
                <option value="Hospital">Hospital</option>
                <option value="Clinic">Clinic</option>
                <option value="Diagnostic Center">Diagnostic Center</option>
              </select>
              {touched.organizationType && errors.organizationType && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.organizationType}
                </span>
              )}
            </div>

            {/* 3. Registration / License Number */}
            <div className="input-group">
              <label style={labelStyle}>
                Registration / License Number <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <input
                type="text"
                name="registrationNumber"
                required
                placeholder="Enter registration or license number"
                value={formData.registrationNumber}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.registrationNumber && errors.registrationNumber ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.registrationNumber && errors.registrationNumber && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.registrationNumber}
                </span>
              )}
            </div>

            {/* 4. Country */}
            <div className="input-group">
              <label style={labelStyle}>
                Country <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <select
                name="country"
                required
                value={formData.country}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.country && errors.country ? '#EF4444' : '#CBD5E1',
                }}
              >
                <option value="India">India</option>
              </select>
              {touched.country && errors.country && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.country}
                </span>
              )}
            </div>

            {/* 5. State */}
            <div className="input-group">
              <label style={labelStyle}>
                State <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <select
                name="state"
                required
                value={formData.state}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.state && errors.state ? '#EF4444' : '#CBD5E1',
                }}
              >
                <option value="">Select State</option>
                {INDIAN_STATES.map((stateName) => (
                  <option key={stateName} value={stateName}>
                    {stateName}
                  </option>
                ))}
              </select>
              {touched.state && errors.state && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.state}
                </span>
              )}
            </div>

            {/* 6. City */}
            <div className="input-group">
              <label style={labelStyle}>
                City <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <input
                type="text"
                name="city"
                required
                placeholder="Enter city"
                value={formData.city}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.city && errors.city ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.city && errors.city && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.city}
                </span>
              )}
            </div>

            {/* 7. Full Address (Spans Full Available Width) */}
            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label style={labelStyle}>
                Full Address <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <textarea
                name="address"
                required
                rows={3}
                placeholder="Enter complete hospital or clinic address"
                value={formData.address}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  resize: 'vertical',
                  minHeight: '84px',
                  borderColor: touched.address && errors.address ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.address && errors.address && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.address}
                </span>
              )}
            </div>

            {/* 8. Pincode */}
            <div className="input-group">
              <label style={labelStyle}>
                Pincode <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <input
                type="text"
                name="pincode"
                required
                maxLength={6}
                placeholder="Enter pincode"
                value={formData.pincode}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.pincode && errors.pincode ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.pincode && errors.pincode && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.pincode}
                </span>
              )}
            </div>

            {/* 9. Contact Number (10 digits only) */}
            <div className="input-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ ...labelStyle, marginBottom: 0 }}>
                  Contact Number <span style={{ color: '#EF4444' }}>*</span>
                </label>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: formData.contactNumber.length === 10 ? '#059669' : '#64748B'
                }}>
                  {formData.contactNumber.length}/10 digits
                </span>
              </div>
              <input
                type="tel"
                name="contactNumber"
                required
                maxLength={10}
                placeholder="Enter 10-digit phone number (e.g. 9876543210)"
                value={formData.contactNumber}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.contactNumber && errors.contactNumber 
                    ? '#EF4444' 
                    : (formData.contactNumber.length === 10 ? '#10B981' : '#CBD5E1'),
                }}
              />
              {touched.contactNumber && errors.contactNumber && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.contactNumber}
                </span>
              )}
            </div>

            {/* 10. Official Email */}
            <div className="input-group">
              <label style={labelStyle}>
                Official Email <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <input
                type="email"
                name="officialEmail"
                required
                placeholder="Enter official email address"
                value={formData.officialEmail}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.officialEmail && errors.officialEmail ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.officialEmail && errors.officialEmail && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.officialEmail}
                </span>
              )}
            </div>

            {/* 11. Website (Optional) */}
            <div className="input-group">
              <label style={labelStyle}>
                Website <span style={{ color: '#64748B', fontWeight: 400 }}>(Optional)</span>
              </label>
              <input
                type="url"
                name="website"
                placeholder="https://www.example.com"
                value={formData.website}
                onChange={handleChange}
                onBlur={handleBlur}
                style={{
                  ...inputStyle,
                  borderColor: touched.website && errors.website ? '#EF4444' : '#CBD5E1',
                }}
              />
              {touched.website && errors.website && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.website}
                </span>
              )}
            </div>

            {/* 12. Password */}
            <div className="input-group">
              <label style={labelStyle}>
                Password <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  required
                  placeholder="Enter password (min 6 characters)"
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  style={{
                    ...inputStyle,
                    paddingRight: '40px',
                    borderColor: touched.password && errors.password ? '#EF4444' : '#CBD5E1',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={eyeToggleButtonStyle}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {touched.password && errors.password && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.password}
                </span>
              )}
            </div>

            {/* 13. Confirm Password */}
            <div className="input-group">
              <label style={labelStyle}>
                Confirm Password <span style={{ color: '#EF4444' }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  required
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  style={{
                    ...inputStyle,
                    paddingRight: '40px',
                    borderColor: touched.confirmPassword && errors.confirmPassword ? '#EF4444' : '#CBD5E1',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={eyeToggleButtonStyle}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {touched.confirmPassword && errors.confirmPassword && (
                <span style={errorTextStyle}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  {errors.confirmPassword}
                </span>
              )}
            </div>

          </div>

          {/* Submit Action Button */}
          <div style={{ marginTop: '8px' }}>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '15px',
                borderRadius: '12px',
                fontWeight: 700,
                fontSize: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                background: 'linear-gradient(135deg, #10B981, #059669)',
                border: 'none',
                color: '#FFFFFF',
                boxShadow: '0 4px 16px rgba(16, 185, 129, 0.35)',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              {loading ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Registering Healthcare Organization...
                </>
              ) : (
                <>
                  Register Healthcare Organization
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Existing login link */}
        <div style={{
          marginTop: '28px',
          paddingTop: '20px',
          borderTop: '1px solid #F1F5F9',
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#64748B',
        }}>
          Already registered?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#059669',
              fontWeight: 700,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            Sign In Here
          </button>
        </div>
      </div>

      {/* REGISTRATION SUCCESS POPUP MODAL */}
      {successModalData && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 99999,
          background: 'rgba(15, 23, 42, 0.72)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
          animation: 'fadeIn 0.25s ease-out',
        }}>
          <div style={{
            background: '#FFFFFF',
            borderRadius: '24px',
            maxWidth: '520px',
            width: '100%',
            boxShadow: '0 25px 60px -15px rgba(16, 185, 129, 0.3), 0 0 0 1px rgba(16, 185, 129, 0.15)',
            border: '1px solid #D1FAE5',
            overflow: 'hidden',
            padding: '36px 30px',
            textAlign: 'center',
            position: 'relative',
            animation: 'slideUp 0.3s ease-out',
          }}>
            {/* Top Success Badge */}
            <div style={{
              width: '76px',
              height: '76px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)',
              border: '2px solid #A7F3D0',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px',
              boxShadow: '0 8px 24px rgba(16, 185, 129, 0.25)',
            }}>
              <CheckCircle2 size={44} color="#059669" />
            </div>

            <h2 style={{
              fontSize: '1.75rem',
              fontWeight: 800,
              color: '#0F172A',
              margin: '0 0 8px',
              letterSpacing: '-0.02em',
            }}>
              Registration Successful!
            </h2>
            <p style={{
              color: '#059669',
              fontWeight: 700,
              fontSize: '1.1rem',
              margin: '0 0 20px',
            }}>
              {successModalData.hospitalName}
            </p>

            {/* Email confirmation dispatch banner */}
            <div style={{
              background: '#F0FDF4',
              border: '1px solid #BBF7D0',
              borderRadius: '14px',
              padding: '16px',
              marginBottom: '20px',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}>
              <div style={{
                background: '#DCFCE7',
                borderRadius: '8px',
                padding: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '2px'
              }}>
                <Sparkles size={18} color="#16A34A" />
              </div>
              <div style={{ fontSize: '0.875rem', color: '#166534', lineHeight: 1.5 }}>
                <div style={{ fontWeight: 700, marginBottom: '2px', color: '#14532D' }}>
                  Confirmation Email Dispatched
                </div>
                An official confirmation email has been dispatched to <strong>{successModalData.officialEmail}</strong>.
              </div>
            </div>

            {/* Credentials summary */}
            <div style={{
              background: '#F8FAFC',
              borderRadius: '12px',
              border: '1px solid #E2E8F0',
              padding: '14px 18px',
              marginBottom: '24px',
              textAlign: 'left',
              fontSize: '0.85rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: '#64748B', fontWeight: 600 }}>Login ID:</span>
                <span style={{ color: '#0F172A', fontWeight: 700 }}>{successModalData.officialEmail}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: '#64748B', fontWeight: 600 }}>Contact Phone:</span>
                <span style={{ color: '#0F172A', fontWeight: 600 }}>{successModalData.contactNumber}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748B', fontWeight: 600 }}>Organization Type:</span>
                <span style={{ color: '#0F172A', fontWeight: 600 }}>{successModalData.organizationType}</span>
              </div>
            </div>

            {/* Proceed to Sign In CTA button */}
            <button
              type="button"
              onClick={handleProceedToLogin}
              style={{
                width: '100%',
                padding: '14px',
                borderRadius: '12px',
                fontWeight: 700,
                fontSize: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, #10B981, #059669)',
                border: 'none',
                color: '#FFFFFF',
                boxShadow: '0 4px 16px rgba(16, 185, 129, 0.35)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              Proceed to Sign In Now
              <ArrowRight size={18} />
            </button>

            <div style={{ marginTop: '14px', fontSize: '0.8rem', color: '#94A3B8' }}>
              Redirecting to Sign In in <strong style={{ color: '#10B981' }}>{countdown}s</strong>...
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const labelStyle = {
  display: 'block',
  fontSize: '0.825rem',
  fontWeight: 600,
  color: '#334155',
  marginBottom: '6px',
};

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  borderRadius: '10px',
  border: '1px solid #CBD5E1',
  fontSize: '0.9rem',
  outline: 'none',
  background: '#FFFFFF',
  color: '#0F172A',
  boxSizing: 'border-box',
  transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
};

const eyeToggleButtonStyle = {
  position: 'absolute',
  right: '12px',
  top: '50%',
  transform: 'translateY(-50%)',
  background: 'transparent',
  border: 'none',
  color: '#94A3B8',
  cursor: 'pointer',
  padding: '2px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const errorTextStyle = {
  fontSize: '0.75rem',
  color: '#EF4444',
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  marginTop: '5px',
  fontWeight: 500,
};
