import { useState, useEffect, type FormEvent } from 'react';
import { useAuth } from '../AuthContext';
import {
  LogIn, UserPlus, KeyRound, Mail, Lock, User, ArrowLeft,
  Eye, EyeOff, Dna, Shield, Sparkles, Check, AlertCircle
} from 'lucide-react';

type AuthView = 'login' | 'register' | 'forgot' | 'reset';

export function AuthPage() {
  const { login, register, forgotPassword, resetPassword } = useAuth();
  const [view, setView] = useState<AuthView>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Particle animation
  const [particles] = useState(() =>
    Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 20 + 10,
      delay: Math.random() * 5,
      opacity: Math.random() * 0.4 + 0.1,
    }))
  );

  useEffect(() => {
    setError('');
    setSuccess('');
  }, [view]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setIsLoading(true);
    try {
      await register(username, email, password, fullName);
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const result = await forgotPassword(email);
      if (result.reset_code) {
        setResetCode(result.reset_code);
      }
      setSuccess('Reset code generated! Check below or your email.');
      setView('reset');
    } catch (err: any) {
      setError(err.message || 'Failed to send reset code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setIsLoading(true);
    try {
      await resetPassword(resetCode, newPassword);
      setSuccess('Password reset successfully! You can now log in.');
      setTimeout(() => setView('login'), 2000);
    } catch (err: any) {
      setError(err.message || 'Password reset failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Animated background particles */}
      <div style={styles.particleField}>
        {particles.map((p) => (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              background: p.id % 3 === 0
                ? 'var(--color-gene)'
                : p.id % 3 === 1
                ? 'var(--color-protein)'
                : 'var(--color-pathway)',
              opacity: p.opacity,
              animation: `floatParticle ${p.speed}s ease-in-out ${p.delay}s infinite alternate`,
            }}
          />
        ))}
      </div>

      {/* DNA helix lines */}
      <div style={styles.helixLeft} />
      <div style={styles.helixRight} />

      {/* Left branding panel */}
      <div style={styles.brandPanel}>
        <div style={styles.brandContent}>
          <div style={styles.logoContainer}>
            <div style={styles.logoGlow} />
            <Dna size={48} color="var(--color-gene)" strokeWidth={1.5} />
          </div>
          <h1 style={styles.brandTitle}>GeneGraph</h1>
          <p style={styles.brandSubtitle}>
            AI-Powered Gene-Disease-Protein<br />Knowledge Graph Explorer
          </p>

          <div style={styles.featureList}>
            <FeatureItem icon={<Sparkles size={16} />} text="NL-to-Cypher AI Queries" />
            <FeatureItem icon={<Shield size={16} />} text="Graph ML Link Prediction" />
            <FeatureItem icon={<Dna size={16} />} text="Biological Pathway Exploration" />
          </div>

          <div style={styles.disclaimer}>
            ⚠️ For research use only. Not medical advice.
          </div>
        </div>
      </div>

      {/* Right auth card */}
      <div style={styles.formPanel}>
        <div style={styles.card}>
          {/* Card top accent */}
          <div style={styles.cardAccent} />

          {/* Tab switcher for Login / Register */}
          {(view === 'login' || view === 'register') && (
            <div style={styles.tabContainer}>
              <button
                style={{
                  ...styles.tab,
                  ...(view === 'login' ? styles.tabActive : {}),
                }}
                onClick={() => setView('login')}
              >
                <LogIn size={15} />
                Sign In
              </button>
              <button
                style={{
                  ...styles.tab,
                  ...(view === 'register' ? styles.tabActive : {}),
                }}
                onClick={() => setView('register')}
              >
                <UserPlus size={15} />
                Sign Up
              </button>
            </div>
          )}

          {/* Back button for forgot/reset */}
          {(view === 'forgot' || view === 'reset') && (
            <button style={styles.backButton} onClick={() => setView('login')}>
              <ArrowLeft size={16} />
              Back to Sign In
            </button>
          )}

          {/* Error / Success messages */}
          {error && (
            <div style={styles.alert}>
              <AlertCircle size={16} />
              {error}
            </div>
          )}
          {success && (
            <div style={styles.alertSuccess}>
              <Check size={16} />
              {success}
            </div>
          )}

          {/* ─── LOGIN FORM ─── */}
          {view === 'login' && (
            <form onSubmit={handleLogin} style={styles.form}>
              <h2 style={styles.formTitle}>Welcome Back</h2>
              <p style={styles.formSubtitle}>Sign in to explore the knowledge graph</p>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Email</label>
                <div style={styles.inputWrapper}>
                  <Mail size={16} style={styles.inputIcon} />
                  <input
                    type="email"
                    style={styles.input}
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Password</label>
                <div style={styles.inputWrapper}>
                  <Lock size={16} style={styles.inputIcon} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    style={styles.input}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    style={styles.eyeButton}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="button"
                style={styles.forgotLink}
                onClick={() => setView('forgot')}
              >
                Forgot your password?
              </button>

              <button
                type="submit"
                style={styles.submitButton}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span style={styles.spinner} />
                ) : (
                  <>
                    <LogIn size={16} />
                    Sign In
                  </>
                )}
              </button>
            </form>
          )}

          {/* ─── REGISTER FORM ─── */}
          {view === 'register' && (
            <form onSubmit={handleRegister} style={styles.form}>
              <h2 style={styles.formTitle}>Create Account</h2>
              <p style={styles.formSubtitle}>Join GeneGraph to start exploring</p>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Username</label>
                <div style={styles.inputWrapper}>
                  <User size={16} style={styles.inputIcon} />
                  <input
                    type="text"
                    style={styles.input}
                    placeholder="researcher_123"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    minLength={3}
                    required
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Full Name</label>
                <div style={styles.inputWrapper}>
                  <User size={16} style={styles.inputIcon} />
                  <input
                    type="text"
                    style={styles.input}
                    placeholder="Dr. Jane Smith"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Email</label>
                <div style={styles.inputWrapper}>
                  <Mail size={16} style={styles.inputIcon} />
                  <input
                    type="email"
                    style={styles.input}
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Password</label>
                <div style={styles.inputWrapper}>
                  <Lock size={16} style={styles.inputIcon} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    style={styles.input}
                    placeholder="Min. 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    minLength={6}
                    required
                  />
                  <button
                    type="button"
                    style={styles.eyeButton}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Confirm Password</label>
                <div style={styles.inputWrapper}>
                  <Lock size={16} style={styles.inputIcon} />
                  <input
                    type="password"
                    style={styles.input}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    minLength={6}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                style={styles.submitButton}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span style={styles.spinner} />
                ) : (
                  <>
                    <UserPlus size={16} />
                    Create Account
                  </>
                )}
              </button>
            </form>
          )}

          {/* ─── FORGOT PASSWORD ─── */}
          {view === 'forgot' && (
            <form onSubmit={handleForgotPassword} style={styles.form}>
              <div style={styles.iconCircle}>
                <KeyRound size={28} color="var(--color-gene)" />
              </div>
              <h2 style={styles.formTitle}>Forgot Password?</h2>
              <p style={styles.formSubtitle}>
                Enter your email address and we'll generate a reset code for you.
              </p>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Email Address</label>
                <div style={styles.inputWrapper}>
                  <Mail size={16} style={styles.inputIcon} />
                  <input
                    type="email"
                    style={styles.input}
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                style={styles.submitButton}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span style={styles.spinner} />
                ) : (
                  <>
                    <Mail size={16} />
                    Send Reset Code
                  </>
                )}
              </button>
            </form>
          )}

          {/* ─── RESET PASSWORD ─── */}
          {view === 'reset' && (
            <form onSubmit={handleResetPassword} style={styles.form}>
              <div style={styles.iconCircle}>
                <Shield size={28} color="var(--color-protein)" />
              </div>
              <h2 style={styles.formTitle}>Reset Password</h2>
              <p style={styles.formSubtitle}>
                Enter the reset code and your new password.
              </p>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Reset Code</label>
                <div style={styles.inputWrapper}>
                  <KeyRound size={16} style={styles.inputIcon} />
                  <input
                    type="text"
                    style={styles.input}
                    placeholder="6-digit code"
                    value={resetCode}
                    onChange={(e) => setResetCode(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>New Password</label>
                <div style={styles.inputWrapper}>
                  <Lock size={16} style={styles.inputIcon} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    style={styles.input}
                    placeholder="Min. 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    minLength={6}
                    required
                  />
                  <button
                    type="button"
                    style={styles.eyeButton}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                style={styles.submitButton}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span style={styles.spinner} />
                ) : (
                  <>
                    <Shield size={16} />
                    Reset Password
                  </>
                )}
              </button>
            </form>
          )}

          {/* Footer */}
          <div style={styles.footer}>
            <Dna size={14} color="var(--text-muted)" />
            <span>GeneGraph v0.1.0 — Research Use Only</span>
          </div>
        </div>
      </div>

      {/* Keyframe styles injected once */}
      <style>{`
        @keyframes floatParticle {
          0% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(${Math.random() > 0.5 ? '' : '-'}${Math.random() * 30 + 10}px, ${Math.random() > 0.5 ? '' : '-'}${Math.random() * 30 + 10}px) scale(1.3); }
          100% { transform: translate(${Math.random() > 0.5 ? '' : '-'}${Math.random() * 20 + 5}px, ${Math.random() > 0.5 ? '' : '-'}${Math.random() * 20 + 5}px) scale(0.8); }
        }
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 20px rgba(129, 140, 248, 0.3); }
          50% { box-shadow: 0 0 40px rgba(129, 140, 248, 0.6), 0 0 60px rgba(139, 92, 246, 0.2); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes gradientShift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>
    </div>
  );
}


function FeatureItem({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '10px 16px',
      background: 'rgba(129, 140, 248, 0.06)',
      borderRadius: 10,
      border: '1px solid rgba(129, 140, 248, 0.1)',
    }}>
      <div style={{
        color: 'var(--color-gene)',
        display: 'flex',
        alignItems: 'center',
      }}>
        {icon}
      </div>
      <span style={{
        color: 'var(--text-secondary)',
        fontSize: 13,
        fontWeight: 500,
      }}>
        {text}
      </span>
    </div>
  );
}


// ─── Inline Styles ────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    background: 'var(--bg-primary)',
    position: 'relative',
    overflow: 'hidden',
    fontFamily: "'Inter', sans-serif",
  },
  particleField: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    zIndex: 0,
  },
  helixLeft: {
    position: 'absolute',
    left: -100,
    top: '20%',
    width: 200,
    height: '60%',
    background: 'linear-gradient(180deg, transparent, rgba(129, 140, 248, 0.03), rgba(52, 211, 153, 0.03), transparent)',
    borderRadius: '50%',
    filter: 'blur(40px)',
    zIndex: 0,
  },
  helixRight: {
    position: 'absolute',
    right: -100,
    top: '10%',
    width: 300,
    height: '80%',
    background: 'linear-gradient(180deg, transparent, rgba(139, 92, 246, 0.04), rgba(56, 189, 248, 0.03), transparent)',
    borderRadius: '50%',
    filter: 'blur(60px)',
    zIndex: 0,
  },

  // Brand panel (left)
  brandPanel: {
    flex: '0 0 45%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    zIndex: 1,
    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(30, 27, 75, 0.4))',
    borderRight: '1px solid rgba(99, 102, 241, 0.1)',
  },
  brandContent: {
    maxWidth: 380,
    animation: 'slideUp 0.8s ease-out',
  },
  logoContainer: {
    position: 'relative',
    width: 80,
    height: 80,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
    background: 'rgba(129, 140, 248, 0.08)',
    border: '1px solid rgba(129, 140, 248, 0.2)',
    marginBottom: 24,
    animation: 'pulseGlow 4s ease-in-out infinite',
  },
  logoGlow: {
    position: 'absolute',
    inset: -4,
    borderRadius: 24,
    background: 'radial-gradient(circle, rgba(129, 140, 248, 0.15), transparent 70%)',
    zIndex: -1,
  },
  brandTitle: {
    fontSize: 36,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #818cf8, #a78bfa, #34d399)',
    backgroundSize: '200% 200%',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    animation: 'gradientShift 6s ease infinite',
    margin: '0 0 8px',
    letterSpacing: '-0.5px',
  },
  brandSubtitle: {
    fontSize: 15,
    color: 'var(--text-secondary)',
    lineHeight: 1.6,
    margin: '0 0 32px',
  },
  featureList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    marginBottom: 32,
  },
  disclaimer: {
    fontSize: 11,
    color: 'var(--text-muted)',
    padding: '8px 12px',
    background: 'rgba(251, 191, 36, 0.06)',
    border: '1px solid rgba(251, 191, 36, 0.15)',
    borderRadius: 8,
  },

  // Form panel (right)
  formPanel: {
    flex: '0 0 55%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    zIndex: 1,
    padding: 40,
  },
  card: {
    width: '100%',
    maxWidth: 440,
    background: 'rgba(17, 24, 39, 0.65)',
    backdropFilter: 'blur(24px)',
    border: '1px solid rgba(99, 102, 241, 0.12)',
    borderRadius: 20,
    overflow: 'hidden',
    animation: 'slideUp 0.6s ease-out 0.2s both',
  },
  cardAccent: {
    height: 3,
    background: 'linear-gradient(90deg, #6366f1, #8b5cf6, #34d399, #38bdf8)',
    backgroundSize: '300% 100%',
    animation: 'gradientShift 4s ease infinite',
  },

  // Tabs
  tabContainer: {
    display: 'flex',
    borderBottom: '1px solid rgba(99, 102, 241, 0.1)',
  },
  tab: {
    flex: 1,
    padding: '14px 0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-muted)',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    borderBottom: '2px solid transparent',
    fontFamily: "'Inter', sans-serif",
  },
  tabActive: {
    color: 'var(--text-accent)',
    borderBottomColor: 'var(--color-gene)',
    background: 'rgba(99, 102, 241, 0.05)',
  },

  // Form
  form: {
    padding: '28px 32px',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  formTitle: {
    fontSize: 22,
    fontWeight: 700,
    color: 'var(--text-primary)',
    margin: 0,
  },
  formSubtitle: {
    fontSize: 13,
    color: 'var(--text-muted)',
    margin: '-4px 0 8px',
    lineHeight: 1.5,
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-secondary)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: 14,
    color: 'var(--text-muted)',
    pointerEvents: 'none',
    zIndex: 1,
  },
  input: {
    width: '100%',
    padding: '12px 14px 12px 42px',
    fontSize: 14,
    color: 'var(--text-primary)',
    background: 'rgba(10, 14, 23, 0.6)',
    border: '1px solid rgba(99, 102, 241, 0.15)',
    borderRadius: 10,
    outline: 'none',
    transition: 'all 0.3s ease',
    fontFamily: "'Inter', sans-serif",
  },
  eyeButton: {
    position: 'absolute',
    right: 12,
    background: 'none',
    border: 'none',
    color: 'var(--text-muted)',
    cursor: 'pointer',
    padding: 4,
    display: 'flex',
    alignItems: 'center',
    zIndex: 1,
  },
  forgotLink: {
    alignSelf: 'flex-end',
    background: 'none',
    border: 'none',
    color: 'var(--text-accent)',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    padding: 0,
    marginTop: -8,
    fontFamily: "'Inter', sans-serif",
  },
  submitButton: {
    padding: '13px 24px',
    fontSize: 14,
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    border: 'none',
    borderRadius: 10,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 4,
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)',
    fontFamily: "'Inter', sans-serif",
  },

  // Back button
  backButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '12px 24px',
    fontSize: 13,
    fontWeight: 500,
    color: 'var(--text-secondary)',
    background: 'transparent',
    border: 'none',
    borderBottom: '1px solid rgba(99, 102, 241, 0.1)',
    cursor: 'pointer',
    width: '100%',
    fontFamily: "'Inter', sans-serif",
  },

  // Alerts
  alert: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 16px',
    margin: '12px 24px 0',
    fontSize: 13,
    color: '#f87171',
    background: 'rgba(248, 113, 113, 0.08)',
    border: '1px solid rgba(248, 113, 113, 0.2)',
    borderRadius: 10,
  },
  alertSuccess: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 16px',
    margin: '12px 24px 0',
    fontSize: 13,
    color: '#34d399',
    background: 'rgba(52, 211, 153, 0.08)',
    border: '1px solid rgba(52, 211, 153, 0.2)',
    borderRadius: 10,
  },

  // Icon circle (forgot/reset)
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 16,
    background: 'rgba(129, 140, 248, 0.08)',
    border: '1px solid rgba(129, 140, 248, 0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },

  // Spinner
  spinner: {
    width: 18,
    height: 18,
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.6s linear infinite',
    display: 'inline-block',
  },

  // Footer
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: '14px 24px',
    borderTop: '1px solid rgba(99, 102, 241, 0.08)',
    fontSize: 11,
    color: 'var(--text-muted)',
  },
};
