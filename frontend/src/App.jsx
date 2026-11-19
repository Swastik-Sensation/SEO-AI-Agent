import { useState, useEffect, useRef } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import {
  Search, Globe, BarChart2, Zap, FileText, Settings,
  ArrowRight, CheckCircle2, XCircle, AlertTriangle, Info,
  Download, RefreshCw, X, ChevronRight, Cpu, TrendingUp,
  Shield, Link2, Clock, Loader2, Layers, Target, Activity,
  Copy, Check, ExternalLink, Filter, BookOpen, Bot, Sparkles,
  HelpCircle, Award, ListChecks, User, UserCheck,
  Mail, Phone, MapPin, Share2
} from 'lucide-react';
import {
  apiDetectNiche, apiStartAudit, apiGetStatus,
  apiGetResult, getDownloadUrl, getOpportunityDownloadUrl, getOpportunityXlsxDownloadUrl, apiHealth, apiStartOpportunitySearch,
  apiGetOpportunityStatus, apiGetOpportunityResult,
  apiStartBlogCheck, apiGetBlogStatus, apiGetBlogResult, getBlogDownloadUrl,
  apiStartProfileCheck, apiGetProfileStatus, apiGetProfileResult, getProfileDownloadUrl,
  apiStartPublisherSearch, apiGetPublisherStatus, apiGetPublisherResult, getPublisherXlsxDownloadUrl, getPublisherCsvDownloadUrl
} from './api';

/* ═══════════════════════════════════════════════════════════════════════════
   TASK DEFINITIONS
═══════════════════════════════════════════════════════════════════════════ */
const TASKS = [
  {
    id: 'seo-audit',
    number: 1,
    icon: '🔍',
    gradient: 'linear-gradient(135deg, #1e40af, #4f46e5)',
    name: 'On-Page SEO Audit',
    subtitle: 'Meta Tags, Headings & Descriptions',
    description:
      'Deep-crawl your website to audit meta titles, descriptions, heading hierarchy, ' +
      'keyword density, broken links, and technical SEO health. Get AI-powered fixes and a prioritised action plan.',
    features: [
      'Meta title & description analysis',
      'H1–H6 heading structure audit',
      'Technical checks (robots, sitemap, HTTPS)',
      'AI-generated metadata rewrites',
      'CSV issues export + full PDF report',
    ],
    active: true,
    aiPowered: true,
    path: '/audit',
  },
  {
    id: 'opportunity-finder',
    number: 2,
    icon: '🎯',
    gradient: 'linear-gradient(135deg, #065f46, #0f766e)',
    name: 'Off-Page Opportunity Finder',
    subtitle: 'Free publishing & local SEO leads',
    description: 'Find public, relevant places to publish, list, or promote your business across off-page and local SEO categories.',
    features: ['Keyword volume & difficulty', 'Competitor gap analysis', 'Long-tail discovery', 'SERP feature analysis'],
    active: true,
    aiPowered: false,
  },
  {
    id: 'blog-checker',
    number: 3,
    icon: '📝',
    gradient: 'linear-gradient(135deg, #0e7490, #0369a1)',
    name: 'Blog & Article AI Auditor',
    subtitle: 'Search Intent & Google AI Overviews',
    description:
      'Audit your blog posts, articles or guides against your project niche. Evaluates link anchors, ' +
      'classifies 4-way search intent (Informational, Commercial, etc.), verifies keyword-intent alignment, and audits Google AI Search Bot (GEO) readiness.',
    features: [
      'Project link & Niche context detection',
      '4-Way Search Intent (Commercial, Informational...)',
      'Keyword-to-Intent alignment matrix',
      'Links & generic anchor text audit',
      'Google AI Search Bot (GEO) readiness score',
      'Direct answer snippet recommendations',
    ],
    active: true,
    aiPowered: true,
  },
  {
    id: 'profile-checker',
    number: 4,
    icon: '👤',
    gradient: 'linear-gradient(135deg, #7c2d12, #c2410c)',
    name: 'Business Profile Auditor',
    subtitle: 'Bio Correctness & Website Backlink Verification',
    description:
      'Audit public business & citation profiles (Medium, Substack, Dev.to, GitHub, Crunchbase, About.me, Yelp, Directories, etc.). ' +
      'Verifies that your official website link is present and active in the bio/profile, and validates whether the bio content is correct and aligned with your business niche.',
    features: [
      'Website backlink verification in bio & profile',
      'Bio content correctness & brand alignment check',
      'Niche relevance & core service keyword coverage',
      'Call-to-action (CTA) & character limit validation',
      'Actionable checklist & Profile Health Score',
      'AI-powered bio evaluation & ready-to-use rewrites',
    ],
    active: true,
    aiPowered: true,
  },
  {
    id: 'publisher-finder',
    number: 5,
    icon: '📰',
    gradient: 'linear-gradient(135deg, #1e3a8a, #2563eb)',
    name: 'Publisher & Blogger Outreach Finder',
    subtitle: 'Local & Niche Publisher Contacts (Emails & Phones)',
    description:
      'Find blogs, publishers, and media outlets in your niche and location (e.g. Event Planning in Mohali / Chandigarh / Tricity). ' +
      'Extracts verified editorial emails, phone/WhatsApp numbers, editor details, and contributor guidelines with 1-click Excel export.',
    features: [
      'Niche & hyper-local search (e.g. Chandigarh, Mohali, Tricity)',
      'Scrapes direct editorial emails & verified phone numbers',
      'Identifies publication bio, domain DA & editor links',
      'Extracts contact forms & guest post guidelines',
      'Professional Excel (.xlsx) and CSV export for outreach',
    ],
    active: true,
    aiPowered: true,
  },
  {
    id: 'competitor',
    number: 6,
    icon: '🏆',
    gradient: 'linear-gradient(135deg, #134e4a, #0f766e)',
    name: 'Competitor Analysis',
    subtitle: 'Competitor Intelligence',
    description: 'Benchmark your SEO performance against top competitors, uncover their strategies, and find quick wins.',
    features: ['Competitor keyword overlap', 'Content strategy analysis', 'Ranking opportunity finder', 'Traffic estimation'],
    active: false,
    aiPowered: false,
  },
];

/* ═══════════════════════════════════════════════════════════════════════════
   UTILITY COMPONENTS
═══════════════════════════════════════════════════════════════════════════ */
function Spinner({ className = '' }) {
  return <div className={`spinner ${className}`} />;
}

function Alert({ type = 'info', children }) {
  const icons = { error: <XCircle size={16} />, success: <CheckCircle2 size={16} />, info: <Info size={16} /> };
  return (
    <div className={`alert alert-${type}`}>
      {icons[type]}
      <span>{children}</span>
    </div>
  );
}

function SeverityBadge({ sev }) {
  return <span className={`sev-badge ${sev}`}>{sev}</span>;
}

/* ═══════════════════════════════════════════════════════════════════════════
   NAVBAR
═══════════════════════════════════════════════════════════════════════════ */
function Navbar({ apiOnline }) {
  const navigate = useNavigate();
  return (
    <nav className="navbar">
      <button className="navbar-brand" onClick={() => navigate('/')} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
        <div className="navbar-logo">S</div>
        <span>SEO<span className="navbar-logo-text"> AI Agent</span></span>
      </button>
      <div className="navbar-nav">
        <div className="navbar-status" style={apiOnline === false ? {
          background: 'var(--accent-red-bg)', borderColor: 'var(--accent-red-bd)', color: 'var(--accent-red)'
        } : {}}>
          <div className="status-dot" style={apiOnline === false ? { background: 'var(--accent-red-lt)' } : {}} />
          {apiOnline === null ? 'Connecting…' : apiOnline ? 'API Online' : 'API Offline'}
        </div>
      </div>
    </nav>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   AUDIT MODAL – STEP 1: URL Input + Niche Detection
═══════════════════════════════════════════════════════════════════════════ */
function AuditModal({ onClose, onLaunch }) {
  const [step, setStep] = useState('url');
  const [url, setUrl] = useState('');
  const [maxPages, setMaxPages] = useState(25);
  const [useAi, setUseAi] = useState(true);
  const [nicheData, setNicheData] = useState(null);
  const [customNiche, setCustomNiche] = useState('');
  const [editingNiche, setEditingNiche] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleDetect() {
    if (!url.trim()) { setError('Please enter a website URL'); return; }
    setError(''); setLoading(true); setStep('detecting');
    try {
      const data = await apiDetectNiche(url.trim(), 5);
      setNicheData(data);
      setCustomNiche(data.niche);
      setStep('niche');
    } catch (e) {
      setError(`Could not reach website: ${e.message}`);
      setStep('url');
    } finally {
      setLoading(false);
    }
  }

  function handleLaunch() {
    onLaunch({ url: url.trim(), niche: customNiche || nicheData?.niche, maxPages, useAi });
  }

  const STEP_LABELS = { url: 'Enter URL', detecting: 'Detecting', niche: 'Confirm Niche' };
  const isStepActive = (s, i) =>
    step === s || (step === 'detecting' && s === 'url') || (step === 'niche' && i < 2);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <h2>🔍 On-Page SEO Audit</h2>
            <p>Crawl, analyse, and generate a complete SEO report</p>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Step Indicators */}
        <div className="step-indicators">
          {['url', 'niche', 'config'].map((s, i) => (
            <div key={s} className="step-ind-item">
              <div className={`step-ind-circle ${isStepActive(s, i) ? 'active' : ''}`}>{i + 1}</div>
              <span className="step-ind-label">{STEP_LABELS[s] || 'Configure'}</span>
              {i < 2 && <span className="step-ind-sep">›</span>}
            </div>
          ))}
        </div>

        <div className="modal-body">
          {error && <Alert type="error">{error}</Alert>}

          {/* ── Step: URL ── */}
          {(step === 'url' || step === 'detecting') && (
            <>
              <div className="form-group">
                <label className="form-label">Website URL</label>
                <div className="input-group">
                  <input
                    className="form-input"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !loading && handleDetect()}
                    disabled={loading}
                    autoFocus
                    id="audit-url-input"
                  />
                </div>
                <p className="form-hint">We'll crawl up to 5 pages to detect your site's niche</p>
              </div>
              {step === 'detecting' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: '0.75rem',
                  background: 'var(--accent-blue-bg)', border: '1px solid var(--accent-blue-bd)', borderRadius: 'var(--radius-sm)', padding: '0.75rem 1rem' }}>
                  <Loader2 size={16} color="var(--accent-blue-lt)" style={{ animation: 'spin 1s linear infinite', flexShrink: 0 }} />
                  <span style={{ color: 'var(--accent-blue)', fontWeight: 500, fontSize: '0.84rem' }}>Crawling website to detect niche…</span>
                </div>
              )}
            </>
          )}

          {/* ── Step: Niche Confirmation ── */}
          {step === 'niche' && nicheData && (
            <>
              <div className="niche-card">
                <div className="niche-card-header">
                  <div>
                    <div className="niche-label">🤖 Detected Niche</div>
                    {!editingNiche
                      ? <div className="niche-value">{customNiche}</div>
                      : <input className="form-input" style={{ marginTop: 6 }} value={customNiche}
                          onChange={(e) => setCustomNiche(e.target.value)} autoFocus />
                    }
                  </div>
                  <button className="btn btn-sm btn-secondary" onClick={() => setEditingNiche(!editingNiche)}>
                    {editingNiche ? 'Save' : '✏️ Edit'}
                  </button>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '0.5rem' }}>
                  Crawled {nicheData.pages_crawled} pages · Top keywords detected:
                </div>
                <div className="niche-keywords">
                  {nicheData.keywords?.map((kw) => <span key={kw} className="niche-kw-tag">{kw}</span>)}
                </div>
              </div>
              <Alert type="info">
                Is this niche correct? Click "Edit" to change it if needed, then continue.
              </Alert>
            </>
          )}

          {/* ── Step: Config (shown after niche confirmed) ── */}
          {step === 'niche' && (
            <>
              <div className="form-group">
                <label className="form-label">Max Pages to Crawl</label>
                <input className="form-input" type="number" min={1} max={200} value={maxPages}
                  onChange={(e) => setMaxPages(Number(e.target.value))} id="max-pages-input" />
                <p className="form-hint">More pages = more accurate report but slower (default: 25)</p>
              </div>
              <div className="toggle-row">
                <span className="toggle-label">🤖 AI-powered metadata rewrites & action plan</span>
                <label className="toggle">
                  <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
                  <div className="toggle-track" />
                  <div className="toggle-thumb" />
                </label>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          {step === 'url' && (
            <button className="btn btn-primary" onClick={handleDetect} disabled={loading || !url.trim()} id="detect-niche-btn">
              {loading ? <Spinner className="spinner-sm" /> : <Globe size={15} />}
              Detect Niche
            </button>
          )}
          {step === 'detecting' && (
            <button className="btn btn-primary" disabled>
              <Spinner className="spinner-sm" /> Detecting...
            </button>
          )}
          {step === 'niche' && (
            <button className="btn btn-primary" onClick={handleLaunch} id="start-audit-btn">
              <Zap size={15} /> Start Full Audit
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   AUDIT PROGRESS PAGE
═══════════════════════════════════════════════════════════════════════════ */
const AUDIT_STEPS = [
  { icon: '🌐', name: 'Web Crawl', desc: 'Discovering all pages on the site' },
  { icon: '🛠️', name: 'Technical Checks', desc: 'HTTPS, robots.txt, sitemap, PageSpeed' },
  { icon: '📋', name: 'On-Page Audit', desc: 'Meta tags, headings, duplicate content' },
  { icon: '🔑', name: 'Keyword Extraction', desc: 'Identifying top keyword themes' },
  { icon: '🤖', name: 'AI Analysis', desc: 'Generating fixes and action plan' },
  { icon: '📄', name: 'Report Generation', desc: 'Creating CSV + PDF reports' },
];

/* ── Step Percentage Indicator ─────────────────────────────────────────────── */
function StepPercentage({ isDone, isActive }) {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    if (!isActive) { setPct(0); return; }
    // Animate 0 → ~95% with easing: fast at start, slowing near the top
    const target = 95;
    let current = 0;
    const tick = () => {
      // Ease: increment shrinks as we approach target
      const remaining = target - current;
      const step = Math.max(0.4, remaining * 0.035);
      current = Math.min(target, current + step);
      setPct(Math.floor(current));
      if (current < target) raf = requestAnimationFrame(() => setTimeout(tick, 120));
    };
    let raf = requestAnimationFrame(() => setTimeout(tick, 80));
    return () => cancelAnimationFrame(raf);
  }, [isActive]);

  if (isDone) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0,
      }}>
        <div style={{
          fontSize: '0.8rem', fontWeight: 800, color: 'var(--accent-green)',
          background: 'var(--accent-green-bg)', border: '1px solid var(--accent-green-bd)',
          borderRadius: 6, padding: '2px 9px', letterSpacing: '-0.01em',
        }}>100%</div>
      </div>
    );
  }
  if (isActive) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
        {/* Mini circular progress ring */}
        <svg width="34" height="34" viewBox="0 0 34 34" style={{ transform: 'rotate(-90deg)', flexShrink: 0 }}>
          <circle cx="17" cy="17" r="14" fill="none" stroke="var(--bg-muted)" strokeWidth="3" />
          <circle
            cx="17" cy="17" r="14" fill="none"
            stroke="var(--accent-blue-lt)" strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 14}`}
            strokeDashoffset={`${2 * Math.PI * 14 * (1 - pct / 100)}`}
            style={{ transition: 'stroke-dashoffset 0.15s ease' }}
          />
        </svg>
        <div style={{
          fontSize: '0.82rem', fontWeight: 800,
          color: 'var(--accent-blue)',
          minWidth: 36, textAlign: 'left', letterSpacing: '-0.01em',
        }}>{pct}%</div>
      </div>
    );
  }
  // Pending step
  return (
    <div style={{
      fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-faint)',
      background: 'var(--bg-muted)', borderRadius: 6, padding: '2px 9px',
      flexShrink: 0,
    }}>0%</div>
  );
}


function AuditProgressPage({ jobId, url, onComplete }) {
  const [status, setStatus] = useState({ current_step: 0, total_steps: 6, log: [], status: 'queued' });
  const logRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!jobId) return;
    const poll = setInterval(async () => {
      try {
        const s = await apiGetStatus(jobId);
        setStatus(s);
        if (s.status === 'done') {
          clearInterval(poll);
          setTimeout(() => navigate(`/results/${jobId}`), 800);
        }
        if (s.status === 'error') clearInterval(poll);
      } catch (e) { console.error(e); }
    }, 1500);
    return () => clearInterval(poll);
  }, [jobId, navigate]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [status.log]);

  const progress = status.total_steps ? (status.current_step / status.total_steps) * 100 : 0;
  const isDone = status.status === 'done';
  const isError = status.status === 'error';

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Progress header card */}
      <div style={{ background: 'var(--bg-white)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)',
        padding: '1.5rem', marginBottom: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '0.5rem' }}>
          {isDone
            ? <CheckCircle2 size={22} color="var(--accent-green)" />
            : isError
              ? <XCircle size={22} color="var(--accent-red)" />
              : <Loader2 size={22} color="var(--accent-blue-lt)" style={{ animation: 'spin 1s linear infinite' }} />}
          <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            {isDone ? '✅ Audit Complete!' : isError ? 'Audit Failed' : 'Running SEO Audit…'}
          </h1>
        </div>
        <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>{url}</div>

        {isError && <Alert type="error">{status.error || 'An unexpected error occurred.'}</Alert>}

        <div className="progress-bar-wrap" style={{ marginBottom: '0.75rem' }}>
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'right', fontWeight: 500 }}>
        Step {status.current_step} of {status.total_steps}
          {status.score != null && <span> · Score: <strong style={{ color: 'var(--accent-green)' }}>{status.score}/100</strong></span>}
        </div>
      </div>  {/* end header card */}

      <div className="audit-steps">
        {AUDIT_STEPS.map((s, i) => {
          const stepNum = i + 1;
          const isDoneStep = status.current_step > stepNum || isDone;
          const isActiveStep = status.current_step === stepNum && !isDone;
          const cls = isDoneStep ? 'step-done' : isActiveStep ? 'step-active' : '';
          return (
            <div key={s.name} className={`audit-step ${cls}`}>
              <div className="step-icon">
                {isDoneStep ? <CheckCircle2 size={18} color="var(--accent-green)" />
                  : isActiveStep ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} color="var(--accent-blue)" />
                  : <span style={{ fontSize: '1rem', opacity: 0.5 }}>{s.icon}</span>}
              </div>
              <div className="step-info">
                <div className="step-name">{s.name}</div>
                <div className="step-desc">{s.desc}</div>
              </div>
              {/* Live percentage – keyed to stepNum so counter resets each new active step */}
              <StepPercentage
                key={`pct-${stepNum}-${isDoneStep}-${isActiveStep}`}
                isDone={isDoneStep}
                isActive={isActiveStep}
              />
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem',
        textTransform: 'uppercase', letterSpacing: '0.07em' }}>
        Live Log
      </div>
      <div className="audit-log" ref={logRef}>
        {status.log.length === 0
          ? <div className="log-entry">Waiting for agent to start...</div>
          : status.log.map((entry, i) => (
            <div key={i} className={`log-entry ${i === status.log.length - 1 ? 'log-entry-active' : ''}`}>
              <span className="log-timestamp">
                {new Date(entry.timestamp * 1000).toLocaleTimeString()}
              </span>
              {entry.message}
            </div>
          ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESULTS PAGE
═══════════════════════════════════════════════════════════════════════════ */
function ResultsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiGetResult(jobId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [jobId]);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 12 }}>
      <Spinner className="spinner-lg" /> <span style={{ color: 'var(--text-secondary)' }}>Loading results...</span>
    </div>
  );
  if (error) return <div style={{ padding: '2rem' }}><Alert type="error">{error}</Alert></div>;
  if (!data) return null;

  const scoreClass = data.score >= 70 ? 'score-high' : data.score >= 40 ? 'score-mid' : 'score-low';
  const maxIssues = Math.max(...Object.values(data.issues_by_severity || {}), 1);
  const tech = data.technical || {};
  const ps = tech.pagespeed || {};

  return (
    <div className="results-page" style={{ paddingTop: '2rem' }}>
      {/* Header */}
      <div className="results-header">
        <div>
          <div style={{ marginBottom: '0.75rem' }}>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/')}>← Back to Home</button>
          </div>
          <h1 className="results-title">SEO Audit Report</h1>
          <div className="results-url">{data.url}</div>
        </div>
        <div className="results-actions">
          <a className="btn btn-secondary" href={getDownloadUrl(jobId, 'csv')} download id="download-csv-btn">
            <Download size={15} /> Issues CSV
          </a>
          <a className="btn btn-primary" href={getDownloadUrl(jobId, 'pdf')} download id="download-pdf-btn">
            <FileText size={15} /> Full Report (PDF)
          </a>
        </div>
      </div>

      {/* Score Cards */}
      <div className="score-section">
        <div className="score-card" style={{ borderColor: 'var(--accent-blue-bd)', background: 'var(--accent-blue-bg)' }}>
          <div className={`score-big ${scoreClass}`}>{data.score}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.35rem', fontWeight: 600 }}>Health Score</div>
          <div style={{ height: 5, background: 'var(--bg-muted)', borderRadius: 3 }}>
            <div style={{ height: '100%', width: `${data.score}%`, background: 'var(--gradient-brand)', borderRadius: 3, transition: 'width 1s ease' }} />
          </div>
        </div>
        <div className="score-card">
          <div className="score-card-value" style={{ color: 'var(--accent-orange)' }}>{data.issues_count}</div>
          <div className="score-card-label">Total Issues</div>
        </div>
        <div className="score-card">
          <div className="score-card-value" style={{ color: 'var(--accent-cyan)' }}>{data.pages_count}</div>
          <div className="score-card-label">Pages Crawled</div>
        </div>
        <div className="score-card" style={{ borderColor: 'var(--accent-red-bd)', background: 'var(--accent-red-bg)' }}>
          <div className="score-card-value" style={{ color: 'var(--accent-red)' }}>{data.issues_by_severity?.critical || 0}</div>
          <div className="score-card-label">Critical Issues</div>
        </div>
      </div>

      {/* Severity Breakdown */}
      <div className="severity-breakdown">
        <div className="severity-title">Issues by Severity</div>
        <div className="severity-rows">
          {['critical', 'high', 'medium', 'low'].map((sev) => {
            const count = data.issues_by_severity?.[sev] || 0;
            return (
              <div key={sev} className="severity-row">
                <div className={`severity-row-label sev-${sev}`}>{sev.charAt(0).toUpperCase() + sev.slice(1)}</div>
                <div className="severity-bar">
                  <div className={`severity-bar-fill fill-${sev}`} style={{ width: `${(count / maxIssues) * 100}%` }} />
                </div>
                <div className={`severity-count sev-${sev}`}>{count}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Technical Checks */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Technical SEO</h3>
        <div className="tech-grid">
          <div className="tech-card">
            <div className={`tech-icon ${tech.https?.is_https ? 'ok' : 'fail'}`}>
              {tech.https?.is_https ? '🔒' : '⚠️'}
            </div>
            <div>
              <div className="tech-label">HTTPS</div>
              <div className="tech-value">{tech.https?.is_https ? 'Secure' : 'Not Secure'}</div>
            </div>
          </div>
          <div className="tech-card">
            <div className={`tech-icon ${tech.robots?.found ? 'ok' : 'warn'}`}>
              {tech.robots?.found ? '🤖' : '❌'}
            </div>
            <div>
              <div className="tech-label">robots.txt</div>
              <div className="tech-value">{tech.robots?.found ? 'Found' : 'Missing'}</div>
            </div>
          </div>
          <div className="tech-card">
            <div className={`tech-icon ${tech.sitemap?.found ? 'ok' : 'warn'}`}>
              {tech.sitemap?.found ? '🗺️' : '❌'}
            </div>
            <div>
              <div className="tech-label">Sitemap</div>
              <div className="tech-value">
                {tech.sitemap?.found ? `${tech.sitemap.url_count} URLs` : 'Missing'}
              </div>
            </div>
          </div>
          <div className="tech-card">
            <div className={`tech-icon ${(tech.broken_links_count || 0) === 0 ? 'ok' : 'fail'}`}>
              {(tech.broken_links_count || 0) === 0 ? '✅' : '🔗'}
            </div>
            <div>
              <div className="tech-label">Broken Links</div>
              <div className="tech-value">{tech.broken_links_count || 0}</div>
            </div>
          </div>
          {ps && !ps.error && ps.performance_score != null && (
            <div className="tech-card">
              <div className={`tech-icon ${ps.performance_score >= 70 ? 'ok' : ps.performance_score >= 40 ? 'warn' : 'fail'}`}>⚡</div>
              <div>
                <div className="tech-label">PageSpeed</div>
                <div className="tech-value">Score {ps.performance_score}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI Action Plan */}
      {data.ai_plan && (
        <div className="ai-plan-section">
          <div className="ai-plan-header">
            <div className="ai-plan-icon">🤖</div>
            <div className="ai-plan-title">AI-Generated Action Plan</div>
            <span className="badge badge-ai" style={{ marginLeft: 'auto' }}>AI Powered</span>
          </div>
          <div className="ai-plan-content">{data.ai_plan}</div>
        </div>
      )}

      {/* Keywords */}
      {(data.keywords?.top_terms?.length > 0 || data.keywords?.top_phrases?.length > 0) && (
        <div className="keywords-section">
          <div className="keywords-title">🔑 Keyword Themes Detected</div>
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>Top Terms</div>
            <div className="keywords-tags">
              {data.keywords.top_terms.map(([w, n]) => (
                <span key={w} className="kw-tag">{w} <span style={{ opacity: 0.6 }}>({n})</span></span>
              ))}
            </div>
          </div>
          {data.keywords?.top_phrases?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>Top Phrases</div>
              <div className="keywords-tags">
                {data.keywords.top_phrases.map(([w, n]) => (
                  <span key={w} className="kw-phrase-tag">{w} <span style={{ opacity: 0.6 }}>({n})</span></span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI Metadata Fixes */}
      {data.fixes?.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)' }}>🛠️ AI-Suggested Metadata Rewrites</h3>
          {data.fixes.map((fix, i) => (
            <div key={i} className="panel" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem', wordBreak: 'break-all', fontWeight: 500 }}>{fix.url}</div>
              <div style={{ marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)' }}>New Title</span>
                <div style={{ marginTop: 5, fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600 }}>{fix.new_title}
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: 6, fontWeight: 400 }}>({fix.new_title?.length} chars)</span>
                </div>
              </div>
              <div style={{ marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-purple)' }}>New Meta Description</span>
                <div style={{ marginTop: 5, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{fix.new_meta_description}
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: 6 }}>({fix.new_meta_description?.length} chars)</span>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-light)', paddingTop: '0.625rem', marginTop: '0.25rem' }}>
                💡 {fix.reasoning}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Issues Table */}
      {data.top_issues?.length > 0 && (
        <div className="issues-section">
          <div className="issues-header">
            <h3>Top Issues Found</h3>
            <a className="btn btn-sm btn-secondary" href={getDownloadUrl(jobId, 'csv')} download>
              <Download size={13} /> Download All
            </a>
          </div>
          <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
            <table className="issues-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Code</th>
                  <th>Issue</th>
                  <th>URL</th>
                </tr>
              </thead>
              <tbody>
                {data.top_issues.map((issue, i) => (
                  <tr key={i}>
                    <td><SeverityBadge sev={issue.severity} /></td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--accent-cyan)' }}>{issue.code}</td>
                    <td style={{ maxWidth: 300, color: 'var(--text-secondary)' }}>{issue.issue}</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <a href={issue.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)', textDecoration: 'none', fontWeight: 500 }}>
                        {issue.url?.replace(/^https?:\/\//, '')}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   HOME PAGE
═══════════════════════════════════════════════════════════════════════════ */
function OpportunityModal({ onClose, onLaunch }) {
  const [url, setUrl] = useState('');
  const [projectName, setProjectName] = useState('');
  const [location, setLocation] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [niche, setNiche] = useState('');
  const [linkSuffix, setLinkSuffix] = useState('');
  const [linksPerCategory, setLinksPerCategory] = useState(50);
  const [detecting, setDetecting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function handleUrlChange(newUrl) {
    setUrl(newUrl);
    if (!linkSuffix.trim() && newUrl.trim()) {
      try {
        const u = newUrl.startsWith('http') ? newUrl : 'https://' + newUrl;
        const host = new URL(u).hostname.replace(/^www\./, '');
        const slug = host.split('.')[0];
        if (slug && slug.length >= 2) {
          const capitalized = slug.charAt(0).toUpperCase() + slug.slice(1);
          setLinkSuffix(`/${slug}, /${capitalized}, /${slug}1`);
        }
      } catch (_) {}
    }
  }

  async function handleDetectNiche() {
    if (!url.trim()) { setError('Enter your website URL first.'); return; }
    setDetecting(true);
    setError('');
    try {
      const result = await apiDetectNiche(url.trim(), 5);
      if (result.niche && result.niche !== 'Unknown') {
        setNiche(result.niche);
      } else {
        setNiche('General Business');
      }
    } catch (err) {
      setError(`Could not automatically detect niche: ${err.message}. You can enter it manually below.`);
      if (!niche) setNiche('General Business');
    } finally {
      setDetecting(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!url.trim()) { setError('Please enter your website URL.'); return; }
    setSubmitting(true);
    setError('');
    const finalNiche = (niche || 'General Business').trim();
    const suffixList = linkSuffix.split(/[,;\n]+/).map((s) => s.trim()).filter(Boolean);
    try {
      const job = await apiStartOpportunitySearch({
        url: url.trim(),
        projectName: projectName.trim(),
        niche: finalNiche,
        location: location.trim(),
        targetAudience: targetAudience.trim(),
        linksPerCategory: Number(linksPerCategory) || 50,
        linkSuffix: linkSuffix.trim(),
        linkSuffixes: suffixList,
      });
      onLaunch(job);
    } catch (err) {
      setError(`Could not start opportunity search: ${err.message}`);
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onMouseDown={onClose}>
      <form className="modal opportunity-modal" onSubmit={handleSubmit} onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>🎯 Off-Page Publishing & Citation Finder</h2>
            <p>Find high-authority publishing opportunities, directory listings, and local citations for your business</p>
          </div>
          <button type="button" className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="modal-body">
          {error && <Alert type="error">{error}</Alert>}

          <div className="form-group">
            <label className="form-label">Your Website URL *</label>
            <div className="input-group" style={{ display: 'flex', gap: '8px' }}>
              <input
                className="form-input"
                type="text"
                value={url}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="https://example.com"
                required
                autoFocus
              />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleDetectNiche}
                disabled={detecting || !url.trim()}
                style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
              >
                {detecting ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Globe size={14} />}
                {detecting ? 'Detecting…' : 'Detect Niche'}
              </button>
            </div>
            <p className="form-hint">Enter your website to tailor publishing platforms to your industry</p>
          </div>

          <div className="form-group">
            <label className="form-label">Profile Link Suffixes / Brand Handles (Check Multiple Variations)</label>
            <input
              className="form-input"
              type="text"
              value={linkSuffix}
              onChange={(e) => setLinkSuffix(e.target.value)}
              placeholder="e.g. /tracevenue, /Tracevenue, /tracevenue1"
            />
            <p className="form-hint">
              Enter one or multiple suffixes separated by commas (e.g. <code>/tracevenue, /Tracevenue, /tracevenue1</code>). The presence checker will test all variations across every website.
            </p>
          </div>

          <div className="form-group">
            <label className="form-label">Industry / Niche</label>
            <input
              className="form-input"
              type="text"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="e.g. Event Management, SaaS, E-commerce, Real Estate"
            />
            <p className="form-hint">Click 'Detect Niche' above or type your exact industry directly</p>
          </div>

          <div className="form-group">
            <label className="form-label">Business / Project Name (Optional)</label>
            <input
              className="form-input"
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g. Trace Venue"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Target Location</label>
              <input
                className="form-input"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Mumbai, India or Worldwide"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Target Audience</label>
              <input
                className="form-input"
                type="text"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="e.g. Corporate Event Planners"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Websites Per Category</label>
            <select
              className="form-input"
              value={linksPerCategory}
              onChange={(e) => setLinksPerCategory(Number(e.target.value))}
            >
              <option value={50}>Up to 50 websites per category (Recommended)</option>
              <option value={30}>Up to 30 websites per category</option>
              <option value={20}>Up to 20 websites per category</option>
              <option value={10}>Up to 10 websites per category</option>
            </select>
            <p className="form-hint">Discovers, verifies reachability, and ranks submission platforms per category</p>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" type="submit" disabled={submitting || !url.trim()} id="find-opportunities-btn">
            {submitting ? (
              <>
                <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                Starting Search…
              </>
            ) : (
              <>
                <Target size={14} />
                Find Opportunities
                <ArrowRight size={14} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

function OpportunityResultsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchFilter, setSearchFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [copiedUrl, setCopiedUrl] = useState('');
  const [activeCategoryModal, setActiveCategoryModal] = useState(null);
  const logContainerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function poll() {
      try {
        const next = await apiGetOpportunityStatus(jobId);
        if (cancelled) return;
        setStatus(next);
        if (next.status === 'done') {
          const result = await apiGetOpportunityResult(jobId);
          if (!cancelled) setData(result);
          return;
        }
        if (next.status === 'error') {
          setError(next.error || 'The search could not be completed.');
          return;
        }
        timer = setTimeout(poll, 1200);
      } catch (err) {
        if (cancelled) return;
        const message = String(err.message || err);
        setError(/not found|404/i.test(message)
          ? 'This search is no longer available on the server (it may have restarted). Retry or start a new search.'
          : `Could not reach the server: ${message}`);
      }
    }
    poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [jobId, attempt]);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [status?.log?.length]);

  function retry() {
    setError('');
    setStatus(null);
    setAttempt((n) => n + 1);
  }

  function handleCopy(url) {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(url);
      setCopiedUrl(url);
      setTimeout(() => setCopiedUrl(''), 2000);
    }
  }

  if (error) {
    return (
      <div className="opportunity-loading-box">
        <Alert type="error">{error}</Alert>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={retry}>Retry Search</button>
          <button className="btn btn-primary" onClick={() => navigate('/')}>Back to Workspace</button>
        </div>
      </div>
    );
  }

  if (!data) {
    const logs = status?.log || [];
    let doneCategories = 0;
    const totalCategories = 19;
    for (let i = logs.length - 1; i >= 0; i--) {
      const m = logs[i]?.message?.match(/\[(\d+)\/(\d+)\]/);
      if (m) {
        doneCategories = parseInt(m[1], 10);
        break;
      }
    }
    const progressPercent = Math.max(8, Math.min(96, Math.round((doneCategories / totalCategories) * 90) + (logs.length > 2 ? 5 : 0)));
    const latestMessage = logs.at(-1)?.message || 'Initializing category engines & authentic browser sessions…';

    return (
      <div className="opportunity-loading-box enhanced">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 12, background: 'var(--accent-blue-bg)',
              border: '2px solid var(--accent-blue-bd)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0
            }}>
              <Loader2 size={22} color="var(--accent-blue)" style={{ animation: 'spin 1.2s linear infinite' }} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                Finding Public Publishing & Citation Leads
              </h2>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 2 }}>
                Scanning 19 SEO categories with authentic browser sessions & Playwright rendering
              </div>
            </div>
          </div>
          <div style={{
            fontSize: '0.8rem', fontWeight: 700, padding: '4px 10px', borderRadius: 999,
            background: 'var(--accent-blue-bg)', color: 'var(--accent-blue)', border: '1px solid var(--accent-blue-bd)',
            whiteSpace: 'nowrap'
          }}>
            {doneCategories} / {totalCategories} Done ({progressPercent}%)
          </div>
        </div>

        {/* Dynamic Progress Bar */}
        <div className="progress-bar-wrap" style={{ height: 8, borderRadius: 6, marginBottom: '1rem', background: 'var(--border-light)' }}>
          <div
            className="progress-bar-fill"
            style={{
              width: `${progressPercent}%`,
              transition: 'width 0.4s ease-out',
              background: 'linear-gradient(90deg, #4f46e5, #06b6d4)'
            }}
          />
        </div>

        {/* Current Step Active Card */}
        <div style={{
          background: 'var(--bg-card, #ffffff)', border: '1px solid var(--accent-blue-bd)',
          borderRadius: 10, padding: '0.85rem 1rem', marginBottom: '1rem',
          display: 'flex', alignItems: 'center', gap: 10
        }}>
          <span style={{
            display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
            background: 'var(--accent-green, #10b981)', boxShadow: '0 0 0 3px rgba(16, 185, 129, 0.2)',
            animation: 'pulse 1.5s ease-in-out infinite', flexShrink: 0
          }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', fontWeight: 700 }}>
              Current Step Execution
            </div>
            <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {latestMessage}
            </div>
          </div>
        </div>

        {/* Live Step-by-Step Execution Feed */}
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>LIVE STEP-BY-STEP ACTIVITY LOG ({logs.length} events)</span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 500 }}>Real-time execution</span>
        </div>
        <div className="execution-log-container" ref={logContainerRef}>
          {logs.length === 0 ? (
            <div style={{ color: '#94a3b8', fontStyle: 'italic', padding: '0.5rem 0' }}>
              Preparing search seeds and starting multi-category background workers...
            </div>
          ) : (
            logs.map((entry, idx) => {
              const isDone = /Completed|Finished|sites ready/i.test(entry.message);
              const isLatest = idx === logs.length - 1;
              const timeStr = entry.timestamp ? new Date(entry.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';

              return (
                <div key={idx} className={`execution-log-item ${isLatest ? 'active' : isDone ? 'done' : ''}`}>
                  <span style={{ color: '#64748b', fontSize: '0.72rem', minWidth: 60, flexShrink: 0 }}>
                    {timeStr}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', flexShrink: 0, marginTop: 2 }}>
                    {isDone ? (
                      <CheckCircle2 size={13} color="#10b981" />
                    ) : isLatest ? (
                      <Loader2 size={13} color="#38bdf8" style={{ animation: 'spin 1.2s linear infinite' }} />
                    ) : (
                      <Activity size={13} color="#64748b" />
                    )}
                  </span>
                  <span style={{ flex: 1, wordBreak: 'break-word' }}>
                    {entry.message}
                  </span>
                </div>
              );
            })
          )}
        </div>

        {/* Security & Reliability Badges */}
        <div style={{
          display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: '0.74rem', color: 'var(--text-secondary)',
          marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid var(--border-light)'
        }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 8px', borderRadius: 6, background: 'var(--bg-page)' }}>
            <Shield size={12} color="#10b981" /> Genuine Browser Headers
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 8px', borderRadius: 6, background: 'var(--bg-page)' }}>
            <Cpu size={12} color="#6366f1" /> Chromium Playwright Engine
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 8px', borderRadius: 6, background: 'var(--bg-page)' }}>
            <Zap size={12} color="#f59e0b" /> 4 Parallel Workers
          </span>
        </div>
      </div>
    );
  }

  // Extract all categories
  const categoriesList = data.categories || [];
  const allCategoryNames = ['All', ...categoriesList.map((c) => c.category)];

  // Flatten all links for stats and CSV export
  const allLeads = [];
  categoriesList.forEach((cat) => {
    (cat.links || []).forEach((link) => {
      allLeads.push({ ...link, category: cat.category, task_type: cat.task_type });
    });
  });

  // Filter categories for the small boxes grid
  const filteredCategories = categoriesList.filter((cat) => {
    if (selectedCategory !== 'All' && cat.category !== selectedCategory) {
      return false;
    }
    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase();
      const catMatch =
        cat.category.toLowerCase().includes(q) ||
        (cat.description && cat.description.toLowerCase().includes(q)) ||
        (cat.task_type && cat.task_type.toLowerCase().includes(q));
      const linkMatch = (cat.links || []).some(
        (l) =>
          l.name?.toLowerCase().includes(q) ||
          l.title?.toLowerCase().includes(q) ||
          l.domain?.toLowerCase().includes(q) ||
          l.action?.toLowerCase().includes(q)
      );
      if (!catMatch && !linkMatch) return false;
    }
    return true;
  });

  const highDaCount = allLeads.filter((l) => (l.da_score || 0) >= (data.min_da || 80)).length;
  const hasRealScores = allLeads.some((l) => l.da_score !== null && l.da_score !== undefined);

  function handleDownloadCSV() {
    if (!allLeads.length) return;
    const headers = [
      'Category', 'Task Type', 'Website Name', 'Domain', 'URL', 'Link Suffix', 'DA Authority',
      'DA Source', 'Listing Source', 'Registered', 'Cost', 'Action', 'How to Perform'
    ];
    const rows = allLeads.map((l) => [
      `"${(l.category || '').replace(/"/g, '""')}"`,
      `"${(l.task_type || '').replace(/"/g, '""')}"`,
      `"${(l.name || l.title || '').replace(/"/g, '""')}"`,
      `"${(l.domain || '').replace(/"/g, '""')}"`,
      `"${(l.url || '').replace(/"/g, '""')}"`,
      `"${(l.link_suffix || '').replace(/"/g, '""')}"`,
      `"${(l.da || 'DA unknown').replace(/"/g, '""')}"`,
      `"${(l.da_source || 'Unknown').replace(/"/g, '""')}"`,
      `"${(l.source || 'Seed platform').replace(/"/g, '""')}"`,
      `"${(l.registered || 'Not checked').replace(/"/g, '""')}"`,
      `"${(l.cost || '100% Free').replace(/"/g, '""')}"`,
      `"${(l.action || '').replace(/"/g, '""')}"`,
      `"${(l.how_to_perform || l.snippet || '').replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `seo_submission_websites_${(data.niche || 'leads').toLowerCase().replace(/[^a-z0-9]+/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <div className="opportunity-results">
      {/* Header */}
      <div className="opportunity-header">
        <div>
          <button className="btn btn-sm btn-secondary" onClick={() => navigate('/')} style={{ marginBottom: '0.75rem' }}>
            ← Back to Workspace
          </button>
          <h1 className="opportunity-title">🎯 SEO Publishing & Submission Portals</h1>
          <div className="opportunity-subtitle">
            Targeting <strong>{data.niche}</strong> {data.location ? `· ${data.location}` : ''} {data.target_audience ? `· ${data.target_audience}` : ''}
            {' '}· <span style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>{allLeads.length} Submission Opportunities across {categoriesList.length} Categories</span>
          </div>
        </div>
        <div className="opportunity-actions" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <a
            className="btn btn-secondary"
            href={getOpportunityXlsxDownloadUrl(jobId)}
            target="_blank"
            rel="noreferrer"
            id="download-opportunity-xlsx"
          >
            <Download size={14} /> Download Excel (.xlsx)
          </a>
          <button
            className="btn btn-secondary"
            onClick={handleDownloadCSV}
            id="download-opportunity-csv"
          >
            <Download size={14} /> Export CSV
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            <RefreshCw size={14} /> New Search
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="opportunity-metrics-grid">
        <div className="opportunity-metric-card" style={{ borderColor: 'var(--accent-blue-bd)', background: 'var(--accent-blue-bg)' }}>
          <div className="opportunity-metric-value">{allLeads.length}</div>
          <div className="opportunity-metric-label">Target Websites</div>
        </div>
        <div className="opportunity-metric-card">
          <div className="opportunity-metric-value" style={{ color: 'var(--accent-green)' }}>
            {categoriesList.length} Tasks
          </div>
          <div className="opportunity-metric-label">Categories Covered</div>
        </div>
        <div className="opportunity-metric-card">
          <div className="opportunity-metric-value" style={{ color: 'var(--accent-purple)' }}>
            {hasRealScores ? highDaCount : `${allLeads.length}`}
          </div>
          <div className="opportunity-metric-label">
            {hasRealScores ? `DA ≥ ${data.min_da || 80} Verified` : 'Curated Seed Portals'}
          </div>
        </div>
        <div className="opportunity-metric-card">
          <div className="opportunity-metric-value" style={{ color: 'var(--accent-cyan)' }}>
            {data.presence_enabled ? `${data.presence_summary?.registered || 0} Registered` : '100% Free'}
          </div>
          <div className="opportunity-metric-label">
            {data.presence_enabled ? 'Presence Tagged' : 'Submission Access'}
          </div>
        </div>
      </div>

      {/* Notice Banner */}
      <div style={{ marginBottom: '1.5rem' }}>
        <Alert type="info">
          {data.notice || 'Click any task box below to open the complete list of verified websites, direct portal links, and step-by-step instructions.'}
        </Alert>
      </div>

      {/* Search & Category Filter Controls */}
      <div className="opportunity-controls">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="opportunity-search-box" style={{ flexGrow: 1, minWidth: 260 }}>
            <Search size={16} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search tasks, platforms (e.g. PRLog, Medium, Yelp, Crunchbase)…"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
            {searchFilter && (
              <button
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                onClick={() => setSearchFilter('')}
              >
                <X size={14} color="var(--text-muted)" />
              </button>
            )}
          </div>
        </div>

        {/* Category Pills */}
        <div className="opportunity-pills">
          {allCategoryNames.map((catName) => {
            const count =
              catName === 'All'
                ? allLeads.length
                : allLeads.filter((l) => l.category === catName).length;
            return (
              <button
                key={catName}
                className={`opportunity-pill ${selectedCategory === catName ? 'active' : ''}`}
                onClick={() => setSelectedCategory(catName)}
              >
                {catName} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Small Boxes Grid */}
      {filteredCategories.length === 0 ? (
        <div className="opportunity-loading-box">
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            No task categories matched your search <strong>"{searchFilter}"</strong>.
          </p>
          <button className="btn btn-secondary btn-sm" onClick={() => { setSearchFilter(''); setSelectedCategory('All'); }}>
            Reset Filter
          </button>
        </div>
      ) : (
        <div className="opportunity-category-grid">
          {filteredCategories.map((cat) => (
            <div
              key={cat.category}
              className="opportunity-category-box"
              onClick={() => setActiveCategoryModal(cat)}
              title={`Click to open websites for ${cat.category}`}
            >
              <div>
                <div className="opportunity-box-top">
                  <span className="opportunity-box-icon">{cat.icon || '🎯'}</span>
                  <span className="opportunity-box-count">{cat.links.length} Websites</span>
                </div>
                <div className="opportunity-box-title">{cat.category}</div>
                <div className="opportunity-box-desc">{cat.description}</div>
              </div>
              <div className="opportunity-box-footer">
                <span>View Web Links</span>
                <ArrowRight size={13} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal for viewing the list of websites for a category */}
      {activeCategoryModal && (
        <div
          className="opportunity-modal-backdrop"
          onClick={() => setActiveCategoryModal(null)}
        >
          <div
            className="opportunity-links-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="opportunity-links-header">
              <div className="opportunity-links-title-group">
                <div className="opportunity-links-icon-wrap">
                  {activeCategoryModal.icon || '🎯'}
                </div>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                    {activeCategoryModal.category}
                  </h2>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                    {activeCategoryModal.description}
                  </p>
                </div>
              </div>
              <button
                className="modal-close"
                onClick={() => setActiveCategoryModal(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
              >
                <X size={20} />
              </button>
            </div>

            <div className="opportunity-links-body">
              {activeCategoryModal.links.map((link, idx) => (
                <div key={`${link.url}-${idx}`} className="opportunity-link-item">
                  <div className="opportunity-link-top">
                    <div>
                      <span className="opportunity-link-name">{link.name || link.title}</span>
                      <span style={{ marginLeft: 8, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        🌐 {link.domain}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                      <span
                        className="opportunity-da-badge"
                        style={{
                          background: (link.da_score || 0) >= 80 ? 'rgba(34,197,94,0.12)' : 'var(--bg-subtle)',
                          color: (link.da_score || 0) >= 80 ? '#16a34a' : 'var(--text-secondary)',
                          border: `1px solid ${(link.da_score || 0) >= 80 ? '#86efac' : 'var(--border-light)'}`,
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: 6,
                          fontSize: '0.75rem',
                        }}
                      >
                        {link.da || 'DA unknown'}
                      </span>
                      {link.source && (
                        <span
                          style={{
                            fontSize: '0.72rem',
                            padding: '3px 8px',
                            borderRadius: 6,
                            background: link.source === 'Seed platform' ? 'rgba(59,130,246,0.1)' : 'rgba(147,51,234,0.1)',
                            color: link.source === 'Seed platform' ? '#2563eb' : '#7e22ce',
                            border: `1px solid ${link.source === 'Seed platform' ? '#bfdbfe' : '#e9d5ff'}`,
                            fontWeight: 600,
                          }}
                        >
                          {link.source}
                        </span>
                      )}
                      {link.registered && link.registered !== 'Not checked' && (
                        <span
                          style={{
                            fontSize: '0.72rem',
                            padding: '3px 8px',
                            borderRadius: 6,
                            fontWeight: 700,
                            background: link.registered === 'Registered' ? '#dcfce7' : link.registered === 'Not Registered' ? '#ffedd5' : '#f1f5f9',
                            color: link.registered === 'Registered' ? '#166534' : link.registered === 'Not Registered' ? '#9a3412' : '#475569',
                            border: `1px solid ${link.registered === 'Registered' ? '#86efac' : link.registered === 'Not Registered' ? '#fed7aa' : '#cbd5e1'}`,
                          }}
                        >
                          {link.registered}
                        </span>
                      )}
                      {link.link_suffix && (
                        <span
                          style={{
                            fontSize: '0.72rem',
                            padding: '3px 8px',
                            borderRadius: 6,
                            background: link.registered === 'Registered' ? '#f0fdf4' : '#f8fafc',
                            color: link.registered === 'Registered' ? '#15803d' : '#475569',
                            border: `1px solid ${link.registered === 'Registered' ? '#bbf7d0' : '#cbd5e1'}`,
                            fontFamily: 'monospace',
                            fontWeight: 600,
                          }}
                          title={`Tested handle suffix(es): ${link.link_suffix}`}
                        >
                          {link.registered === 'Registered' ? `Matched: ${link.link_suffix}` : `Checked: ${link.link_suffix}`}
                        </span>
                      )}
                      <span className="opportunity-action-tag">{link.cost || '100% Free'}</span>
                    </div>
                  </div>

                  <div className="opportunity-link-guide">
                    <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: 3 }}>
                      📌 Task Action: {link.action || 'Publish / Submit'}
                    </strong>
                    {link.how_to_perform || link.snippet}
                  </div>

                  <div className="opportunity-link-actions">
                    <button
                      className="btn btn-xs btn-secondary"
                      onClick={() => handleCopy(link.url)}
                      style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px' }}
                    >
                      {copiedUrl === link.url ? (
                        <>
                          <Check size={12} color="var(--accent-green)" /> Copied!
                        </>
                      ) : (
                        <>
                          <Copy size={12} /> Copy Link
                        </>
                      )}
                    </button>
                    {link.registered === 'Registered' && link.evidence_url && (
                      <a
                        className="btn btn-xs"
                        href={link.evidence_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          padding: '4px 10px',
                          textDecoration: 'none',
                          background: '#dcfce7',
                          color: '#15803d',
                          border: '1px solid #86efac',
                          fontWeight: 600,
                        }}
                      >
                        View Profile <ExternalLink size={12} />
                      </a>
                    )}
                    <a
                      className="btn btn-xs btn-primary"
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px', textDecoration: 'none' }}
                    >
                      Visit Website <ExternalLink size={12} />
                    </a>
                  </div>
                </div>
              ))}
            </div>

            <div className="opportunity-links-footer">
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                {activeCategoryModal.links.length} submission websites available for {activeCategoryModal.category}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={() => setActiveCategoryModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MODULE 3: BLOG & ARTICLE AI AUDITOR MODAL & RESULTS
═══════════════════════════════════════════════════════════════════════════ */
function BlogCheckerModal({ onClose, onLaunch }) {
  const [projectUrl, setProjectUrl] = useState('');
  const [blogUrl, setBlogUrl] = useState('');
  const [niche, setNiche] = useState('');
  const [focusKeyword, setFocusKeyword] = useState('');
  const [checkLinks, setCheckLinks] = useState(false);
  const [loadingNiche, setLoadingNiche] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleDetectNiche() {
    if (!projectUrl.trim()) {
      setError('Please enter a Project Website URL first to detect its niche.');
      return;
    }
    setError('');
    setLoadingNiche(true);
    try {
      const res = await apiDetectNiche(projectUrl.trim(), 4);
      if (res.niche && res.niche !== 'Unknown') {
        setNiche(res.niche);
      } else {
        setNiche('General Business');
      }
    } catch {
      setError('Could not auto-detect niche; feel free to type it in manually.');
    } finally {
      setLoadingNiche(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!projectUrl.trim() || !blogUrl.trim()) {
      setError('Please provide both Project Website URL and Blog Post URL.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const job = await apiStartBlogCheck({
        projectUrl: projectUrl.trim(),
        blogUrl: blogUrl.trim(),
        niche: niche.trim(),
        focusKeyword: focusKeyword.trim(),
        checkLinks,
      });
      onLaunch(job);
    } catch (err) {
      setError(err.message || 'Failed to start blog audit');
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 620 }}>
        <div className="modal-header">
          <div>
            <div className="modal-tag" style={{ color: 'var(--accent-blue)', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: 4 }}>
              Module 3 · Content & Google AI Overviews
            </div>
            <h2>📝 Blog & Article AI Auditor</h2>
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Check search intent, link anchors, indexability gates, and Google AI Search Bot (GEO) readiness.
            </p>
          </div>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div style={{ marginBottom: '1rem' }}><Alert type="error">{error}</Alert></div>}

            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                Project / Business Website URL <span style={{ color: 'var(--accent-red)' }}>*</span>
              </label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  type="text"
                  placeholder="https://yourbrand.com"
                  value={projectUrl}
                  onChange={(e) => setProjectUrl(e.target.value)}
                  style={{ flex: 1 }}
                  required
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleDetectNiche}
                  disabled={loadingNiche || !projectUrl}
                  style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  {loadingNiche ? <Loader2 size={14} className="spin" /> : <Sparkles size={14} color="var(--accent-blue)" />}
                  {loadingNiche ? 'Detecting...' : 'Detect Niche'}
                </button>
              </div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.76rem', display: 'block', marginTop: 4 }}>
                The core domain of your business. Used to establish your topical niche.
              </small>
            </div>

            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                Blog / Article / Post URL <span style={{ color: 'var(--accent-red)' }}>*</span>
              </label>
              <input
                type="text"
                placeholder="https://yourbrand.com/blog/complete-seo-guide"
                value={blogUrl}
                onChange={(e) => setBlogUrl(e.target.value)}
                required
              />
              <small style={{ color: 'var(--text-muted)', fontSize: '0.76rem', display: 'block', marginTop: 4 }}>
                The live public URL of the blog, article, guide, or post you want to audit.
              </small>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: '1rem' }}>
              <div className="form-group">
                <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                  Project Niche (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Event Management"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                  Target Focus Keyword (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. best corporate venues"
                  value={focusKeyword}
                  onChange={(e) => setFocusKeyword(e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                id="check-links-checkbox"
                checked={checkLinks}
                onChange={(e) => setCheckLinks(e.target.checked)}
                style={{ width: 'auto', margin: 0, cursor: 'pointer' }}
              />
              <label htmlFor="check-links-checkbox" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', cursor: 'pointer', margin: 0 }}>
                Test outbound links for broken URLs (HTTP 404/5xx checks, takes ~5s longer)
              </label>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.85rem 1rem', display: 'flex', gap: 10, alignItems: 'center' }}>
              <Bot size={22} color="var(--accent-blue)" style={{ flexShrink: 0 }} />
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                <strong>Indexability Gate & GEO Analysis:</strong> Checks noindex, nosnippet, robots.txt, 4-way search intent, keyword-intent alignment, and direct-answer blocks for Google AI Overviews.
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {submitting ? <Loader2 size={15} className="spin" /> : <ArrowRight size={15} />}
              {submitting ? 'Auditing Blog...' : 'Start Blog Audit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function BlogCheckerResultsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [activeTab, setActiveTab] = useState('ai_bot');
  const [kwFilter, setKwFilter] = useState('');
  const [linkFilter, setLinkFilter] = useState('all');
  const [fixFilter, setFixFilter] = useState('all');
  const [copiedUrl, setCopiedUrl] = useState('');

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function poll() {
      try {
        const next = await apiGetBlogStatus(jobId);
        if (cancelled) return;
        setStatus(next);
        if (next.status === 'done') {
          const res = await apiGetBlogResult(jobId);
          if (!cancelled) setData(res);
          return;
        }
        if (next.status === 'error') {
          setError(next.error || 'The blog check could not be completed.');
          return;
        }
        timer = setTimeout(poll, 1200);
      } catch (err) {
        if (cancelled) return;
        setError(String(err.message || err));
      }
    }
    poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [jobId, attempt]);

  function handleCopy(url) {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(url);
      setCopiedUrl(url);
      setTimeout(() => setCopiedUrl(''), 2000);
    }
  }

  if (error) {
    return (
      <div className="opportunity-loading-box">
        <Alert type="error">{error}</Alert>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => { setError(''); setStatus(null); setAttempt((n) => n + 1); }}>
            Retry Audit
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/')}>Back to Workspace</button>
        </div>
      </div>
    );
  }

  if (!data) {
    const lastMsg = status?.log?.at(-1)?.message || 'Initiating blog analysis & search intent scan…';
    const steps = [
      'Project Website & Niche Context',
      'Article Content & Schema Extraction',
      'Indexability Gates & Links Quality',
      '4-Way Search Intent Classification',
      'Google AI Search Bot (GEO) Readiness',
      'Keyword Matrix & AI Recommendations',
    ];
    const currentStep = status?.current_step || 1;

    return (
      <div className="opportunity-loading-box" style={{ maxWidth: 640 }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.25rem' }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%', background: 'var(--accent-blue-bg)',
            border: '2px solid var(--accent-blue-bd)', display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Loader2 size={28} color="var(--accent-blue)" style={{ animation: 'spin 1.2s linear infinite' }} />
          </div>
        </div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
          Auditing Blog Post & Google AI Bot Readiness
        </h2>
        <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          {lastMsg}
        </p>

        {/* Step list */}
        <div style={{ textAlign: 'left', background: 'var(--bg-subtle)', borderRadius: 10, padding: '1rem 1.25rem', marginBottom: '1.25rem' }}>
          {steps.map((stepText, idx) => {
            const stepNum = idx + 1;
            const isDone = currentStep > stepNum || status?.status === 'done';
            const isActive = currentStep === stepNum && status?.status !== 'done';
            return (
              <div key={stepText} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', opacity: isDone || isActive ? 1 : 0.45 }}>
                {isDone ? (
                  <CheckCircle2 size={16} color="var(--accent-green)" />
                ) : isActive ? (
                  <Loader2 size={16} color="var(--accent-blue)" style={{ animation: 'spin 1s linear infinite' }} />
                ) : (
                  <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1.5px solid var(--text-muted)' }} />
                )}
                <span style={{ fontSize: '0.82rem', fontWeight: isActive ? 700 : 500, color: isActive ? 'var(--accent-blue)' : 'var(--text-primary)' }}>
                  {stepText}
                </span>
              </div>
            );
          })}
        </div>

        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Evaluating search intent (Commercial, Transactional, Informational, Navigational) and Google AI Overviews quotation parameters.
        </div>
      </div>
    );
  }

  // Extracted data helpers
  const intentClass = `intent-${(data.primary_intent || 'informational').toLowerCase()}`;
  const keywordsList = (data.keywords || []).filter((kw) => {
    if (!kwFilter.trim()) return true;
    const q = kwFilter.toLowerCase();
    return kw.keyword.toLowerCase().includes(q) || kw.intent.toLowerCase().includes(q) || kw.status.toLowerCase().includes(q);
  });

  const internalLinks = data.links_summary?.internal_links || [];
  const externalLinks = data.links_summary?.external_links || [];
  const shownLinks = linkFilter === 'internal' ? internalLinks : linkFilter === 'external' ? externalLinks : [...internalLinks, ...externalLinks];

  return (
    <div className="blog-results">
      {/* Header */}
      <div className="blog-header">
        <div>
          <button className="btn btn-sm btn-secondary" onClick={() => navigate('/')} style={{ marginBottom: '0.75rem' }}>
            ← Back to Workspace
          </button>
          <h1 className="blog-title">
            <span>📝 Blog & Article AI Search Audit</span>
          </h1>
          <div className="blog-meta-pills">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <strong>Article:</strong> <span style={{ color: 'var(--text-primary)' }}>{data.title || data.blog_url}</span>
            </span>
            <span>·</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <strong>Niche:</strong> <span style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>{data.project_niche}</span>
              {data.niche_alignment_score !== null && data.niche_alignment_score !== undefined
                ? ` (${data.niche_alignment_score}% match)`
                : data.niche_terms?.length ? ` (${data.niche_terms.slice(0, 3).join(', ')})` : ''}
            </span>
            <span>·</span>
            <span className={`intent-badge ${intentClass}`}>
              {data.primary_intent} Intent
            </span>
            {data.secondary_intent && (
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                (+{data.secondary_intent})
              </span>
            )}
            <span>·</span>
            {data.indexability?.indexable ? (
              <span style={{ color: 'var(--accent-green)', fontWeight: 600, fontSize: '0.75rem' }}>
                ✓ Indexable ({data.indexability?.http_status})
              </span>
            ) : (
              <span style={{ color: 'var(--accent-red)', fontWeight: 700, fontSize: '0.75rem' }}>
                ✕ Non-Indexable
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <a
            className="btn btn-secondary"
            href={getBlogDownloadUrl(jobId)}
            download
            id="download-blog-csv"
            style={{ textDecoration: 'none' }}
          >
            <Download size={14} /> Export CSV Report
          </a>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            <RefreshCw size={14} /> Audit Another Blog
          </button>
        </div>
      </div>

      {/* Indexability Blocker Banner */}
      {data.indexability && !data.indexability.indexable && (
        <div style={{ background: '#fef2f2', border: '1.5px solid #fecaca', borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <AlertTriangle size={22} color="#dc2626" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ color: '#991b1b', fontWeight: 800, fontSize: '0.94rem', marginBottom: 3 }}>
              🚨 Google Search & AI Overviews Blocked (Non-Indexable)
            </div>
            <div style={{ color: '#b91c1c', fontSize: '0.82rem', lineHeight: 1.45, marginBottom: 6 }}>
              This URL cannot be crawled, indexed, or cited by Google AI Overviews because of active indexability blockers:
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, color: '#991b1b', fontSize: '0.8rem' }}>
              {(data.indexability.reasons || []).map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* nosnippet Banner */}
      {data.indexability && (data.indexability.nosnippet_meta || data.indexability.nosnippet_header) && (
        <div style={{ background: '#fffbeb', border: '1px solid #fef3c7', borderRadius: 'var(--radius-md)', padding: '0.85rem 1.25rem', marginBottom: '1.5rem', display: 'flex', gap: 10, alignItems: 'center' }}>
          <AlertTriangle size={18} color="#d97706" style={{ flexShrink: 0 }} />
          <div style={{ color: '#92400e', fontSize: '0.82rem' }}>
            <strong>nosnippet directive active:</strong> Google AI Overviews are forbidden from displaying text snippets from this post.
          </div>
        </div>
      )}

      {/* Top 5 KPI Cards */}
      <div className="blog-kpi-grid">
        {/* Overall Health */}
        <div className="blog-kpi-card">
          <div className="blog-kpi-label">Overall Health Score</div>
          <div className="blog-kpi-value" style={{ color: data.overall_health_score >= 75 ? 'var(--accent-green)' : data.overall_health_score >= 50 ? 'var(--accent-amber)' : 'var(--accent-red)' }}>
            {data.overall_health_score}<span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div className="blog-kpi-sub">
            Composite score across GEO, intent, links & structure
          </div>
          {data.score_breakdown && (
            <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 8px', fontSize: '0.7rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-light)', paddingTop: 6 }}>
              <div>GEO: <strong style={{ color: 'var(--text-primary)' }}>{data.score_breakdown.ai_bot_readiness}</strong></div>
              <div>Keywords: <strong style={{ color: 'var(--text-primary)' }}>{data.score_breakdown.keyword_alignment}%</strong></div>
              <div>Links: <strong style={{ color: 'var(--text-primary)' }}>{data.score_breakdown.links_and_anchors}</strong></div>
              <div>Structure: <strong style={{ color: 'var(--text-primary)' }}>{data.score_breakdown.on_page_structure}</strong></div>
            </div>
          )}
        </div>

        {/* Google AI Bot Score */}
        <div className="blog-kpi-card" style={{ borderLeft: '3px solid #8b5cf6' }}>
          <div className="blog-kpi-label">Google AI Search Bot (GEO)</div>
          <div className="blog-kpi-value" style={{ color: '#7c3aed' }}>
            {data.ai_bot_readiness?.score}<span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div className="blog-kpi-sub" style={{ fontWeight: 650, color: '#6d28d9' }}>
            {data.ai_bot_readiness?.badge}
          </div>
        </div>

        {/* Primary Intent Card */}
        <div className="blog-kpi-card">
          <div className="blog-kpi-label">Primary Search Intent</div>
          <div style={{ margin: '0.25rem 0 0.5rem' }}>
            <span className={`intent-badge ${intentClass}`} style={{ fontSize: '0.85rem', padding: '4px 12px' }}>
              {data.primary_intent}
            </span>
          </div>
          <div className="blog-kpi-sub">
            {data.intent_confidence && <span style={{ fontWeight: 650, color: 'var(--text-primary)' }}>{data.intent_confidence} Confidence</span>}
            <div style={{ marginTop: 3 }}>
              {data.intent_breakdown?.Informational || 0}% Info · {data.intent_breakdown?.Commercial || 0}% Comm · {data.intent_breakdown?.Transactional || 0}% Trans
            </div>
          </div>
        </div>

        {/* Word Count & Readability */}
        <div className="blog-kpi-card">
          <div className="blog-kpi-label">Word Count & Reading Ease</div>
          <div className="blog-kpi-value">
            {data.word_count.toLocaleString()}<span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}> words</span>
          </div>
          <div className="blog-kpi-sub">
            {data.readability?.grade} (~{data.readability?.reading_time_min} min read)
          </div>
        </div>

        {/* Links & Anchor Warnings */}
        <div className="blog-kpi-card">
          <div className="blog-kpi-label">Links & Anchors Health</div>
          <div className="blog-kpi-value" style={{ color: (data.links_summary?.broken_links?.length || data.links_summary?.generic_anchor_count) ? 'var(--accent-amber)' : 'var(--accent-blue)' }}>
            {data.links_summary?.total_links}<span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}> links</span>
          </div>
          <div className="blog-kpi-sub">
            {data.links_summary?.broken_links?.length > 0 ? (
              <span style={{ color: 'var(--accent-red)', fontWeight: 700 }}>⚠️ {data.links_summary.broken_links.length} Broken Link(s)</span>
            ) : data.links_summary?.generic_anchor_count > 0 ? (
              `⚠️ ${data.links_summary.generic_anchor_count} generic anchor warnings`
            ) : data.links_summary?.off_topic_anchor_count > 0 ? (
              `⚠️ ${data.links_summary.off_topic_anchor_count} off-topic anchors`
            ) : (
              '✓ Descriptive anchor profile'
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="blog-tabs">
        <button
          className={`blog-tab-btn ${activeTab === 'ai_bot' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai_bot')}
        >
          <Bot size={16} /> Google AI Bot & Overviews (GEO)
        </button>
        <button
          className={`blog-tab-btn ${activeTab === 'intent' ? 'active' : ''}`}
          onClick={() => setActiveTab('intent')}
        >
          <Target size={16} /> Search Intent & Keyword Matrix ({data.keywords?.length || 0})
        </button>
        <button
          className={`blog-tab-btn ${activeTab === 'links' ? 'active' : ''}`}
          onClick={() => setActiveTab('links')}
        >
          <Link2 size={16} /> Links & Anchor Texts ({data.links_summary?.total_links || 0})
        </button>
        <button
          className={`blog-tab-btn ${activeTab === 'fixes' ? 'active' : ''}`}
          onClick={() => setActiveTab('fixes')}
        >
          <ListChecks size={16} /> Actionable Fixes ({data.recommendations?.length || 0})
        </button>
      </div>

      {/* TAB 1: Google AI Search Bot (GEO) */}
      {activeTab === 'ai_bot' && (
        <div>
          {/* Simulated Google AI Overview Snippet */}
          <div className="ai-overview-preview">
            <div className="ai-overview-header">
              <div className="ai-overview-title">
                <Sparkles size={18} color="#7c3aed" />
                <span>Google AI Overview Quotation Simulation</span>
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '3px 9px', borderRadius: 12, background: '#ede9fe', color: '#6d28d9' }}>
                {data.ai_bot_readiness?.badge}
              </span>
            </div>
            <div className="ai-overview-content">
              <div style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: 8, fontStyle: 'italic' }}>
                How Google's AI Search Bot (Gemini / SGE) synthesizes and cites this post in searches:
              </div>
              <div style={{ fontWeight: 500, color: '#1e293b' }}>
                "{data.ai_bot_readiness?.snippet_sample || data.title}"
              </div>
              <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.78rem', color: '#64748b', borderTop: '1px solid #e2e8f0', paddingTop: 8 }}>
                <Globe size={14} />
                <span>Source citation: <strong>{data.blog_url}</strong></span>
              </div>
            </div>
          </div>

          {/* 4 AI Bot Core Factors Grid */}
          <h3 style={{ fontSize: '1.05rem', fontWeight: 750, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
            Google AI Search Engine Ranking Parameters
          </h3>
          <div className="ai-factors-grid">
            {(data.ai_bot_readiness?.checks || []).map((check, i) => (
              <div className="ai-factor-card" key={i} style={{ borderTop: check.passed ? '3px solid var(--accent-green)' : '3px solid var(--accent-amber)' }}>
                <div className="ai-factor-head">
                  <span className="ai-factor-name">{check.aspect}</span>
                  <span style={{
                    fontSize: '0.75rem', fontWeight: 750, padding: '2px 8px', borderRadius: 8,
                    background: check.passed ? '#d1fae5' : '#fef3c7',
                    color: check.passed ? '#065f46' : '#92400e'
                  }}>
                    {check.points}
                  </span>
                </div>
                <div style={{ fontSize: '0.74rem', fontWeight: 700, color: check.passed ? 'var(--accent-green)' : 'var(--accent-amber)', marginBottom: 6 }}>
                  {check.status}
                </div>
                <div className="ai-factor-desc">{check.detail}</div>
              </div>
            ))}
          </div>

          {/* AI Search Optimization Advice */}
          <div style={{ background: 'var(--bg-white)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
            <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem', fontWeight: 750, color: 'var(--text-primary)' }}>
              🤖 Why Generative Engine Optimization (GEO) Matters for this Article
            </h4>
            <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {data.ai_bot_readiness?.summary} Google's AI search engine extracts self-contained definition sentences and structured bullet steps to answer user questions directly on the search results page. Optimizing these blocks ensures your website is chosen as the primary citation.
            </p>
            {data.ai_bot_readiness?.disclaimer && (
              <div style={{ marginTop: '0.85rem', fontSize: '0.76rem', color: 'var(--text-muted)', fontStyle: 'italic', background: 'var(--bg-subtle)', padding: '0.5rem 0.75rem', borderRadius: 6 }}>
                ℹ️ {data.ai_bot_readiness.disclaimer}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Intent & Keyword Matrix */}
      {activeTab === 'intent' && (
        <div>
          {/* Intent Breakdown Bar */}
          <div style={{ background: 'var(--bg-white)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div>
                <h4 style={{ margin: '0 0 4px', fontSize: '0.95rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                  Search Intent Classification: <span className={`intent-badge ${intentClass}`}>{data.primary_intent}</span>
                  {data.intent_confidence && <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: 8 }}>({data.intent_confidence})</span>}
                </h4>
                <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  {data.intent_explanation}
                </p>
              </div>
            </div>

            {/* Distribution Bar */}
            <div style={{ display: 'flex', height: 12, borderRadius: 6, overflow: 'hidden', background: '#e2e8f0', margin: '1rem 0 0.75rem' }}>
              <div style={{ width: `${data.intent_breakdown?.Informational || 0}%`, background: '#8b5cf6' }} title={`Informational: ${data.intent_breakdown?.Informational || 0}%`} />
              <div style={{ width: `${data.intent_breakdown?.Commercial || 0}%`, background: '#0284c7' }} title={`Commercial: ${data.intent_breakdown?.Commercial || 0}%`} />
              <div style={{ width: `${data.intent_breakdown?.Transactional || 0}%`, background: '#10b981' }} title={`Transactional: ${data.intent_breakdown?.Transactional || 0}%`} />
              <div style={{ width: `${data.intent_breakdown?.Navigational || 0}%`, background: '#f59e0b' }} title={`Navigational: ${data.intent_breakdown?.Navigational || 0}%`} />
            </div>

            {/* Legend */}
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#8b5cf6', display: 'inline-block' }} />
                Informational: {data.intent_breakdown?.Informational || 0}%
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#0284c7', display: 'inline-block' }} />
                Commercial: {data.intent_breakdown?.Commercial || 0}%
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#10b981', display: 'inline-block' }} />
                Transactional: {data.intent_breakdown?.Transactional || 0}%
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#f59e0b', display: 'inline-block' }} />
                Navigational: {data.intent_breakdown?.Navigational || 0}%
              </span>
            </div>
          </div>

          {/* Alignment Banner */}
          {data.keyword_alignment && (
            <div style={{ display: 'flex', gap: 16, alignItems: 'center', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.84rem', flexWrap: 'wrap' }}>
              <span>Alignment Rate: <strong style={{ color: data.keyword_alignment.aligned_pct >= 70 ? 'var(--accent-green)' : 'var(--accent-amber)' }}>{data.keyword_alignment.aligned_pct}%</strong></span>
              <span>·</span>
              <span>{data.keyword_alignment.aligned_keywords} of {data.keyword_alignment.total_keywords} keywords match intent & niche</span>
              {data.keyword_alignment.misaligned?.length > 0 && (
                <>
                  <span>·</span>
                  <span style={{ color: 'var(--accent-red)', fontWeight: 600 }}>{data.keyword_alignment.misaligned.length} off-target keywords</span>
                </>
              )}
            </div>
          )}

          {/* Keywords Table Header & Search */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', gap: 12, flexWrap: 'wrap' }}>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 750, color: 'var(--text-primary)' }}>
              Extracted Keywords vs Intent Alignment Matrix
            </h3>
            <div style={{ position: 'relative', width: 260 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Filter keywords..."
                value={kwFilter}
                onChange={(e) => setKwFilter(e.target.value)}
                style={{ width: '100%', paddingLeft: 32, fontSize: '0.82rem', height: 34 }}
              />
            </div>
          </div>

          {/* Keywords Table */}
          <div className="clean-table-wrap">
            <table className="clean-table">
              <thead>
                <tr>
                  <th>Keyword / Phrase</th>
                  <th>Type</th>
                  <th>Occurrences</th>
                  <th>Density</th>
                  <th>Position Signals</th>
                  <th>Inferred Intent</th>
                  <th>Intent Alignment</th>
                  <th>Niche Alignment</th>
                  <th>Status & Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {keywordsList.map((kw, i) => (
                  <tr key={i}>
                    <td>
                      <strong style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}>{kw.keyword}</strong>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{kw.type}</td>
                    <td>
                      <span style={{ fontWeight: 700 }}>{kw.count}</span>
                    </td>
                    <td>{kw.density}%</td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {kw.in_title && <span style={{ background: '#e0f2fe', color: '#0369a1', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>TITLE</span>}
                        {kw.in_h1 && <span style={{ background: '#ede9fe', color: '#6d28d9', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>H1</span>}
                        {kw.in_h2 && <span style={{ background: '#f1f5f9', color: '#475569', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>H2</span>}
                        {kw.in_first_100_words && <span style={{ background: '#fef3c7', color: '#b45309', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>100w</span>}
                        {kw.in_meta_description && <span style={{ background: '#dcfce7', color: '#15803d', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>META</span>}
                        {kw.in_url && <span style={{ background: '#f3e8ff', color: '#7e22ce', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>SLUG</span>}
                        {!kw.in_title && !kw.in_h1 && !kw.in_h2 && !kw.in_first_100_words && <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Body only</span>}
                      </div>
                    </td>
                    <td>
                      <span className={`intent-badge intent-${kw.intent.toLowerCase()}`}>
                        {kw.intent}
                      </span>
                    </td>
                    <td>
                      {kw.intent_aligned ? (
                        <span style={{ color: 'var(--accent-green)', fontWeight: 650, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <Check size={14} /> Aligned
                        </span>
                      ) : (
                        <span style={{ color: 'var(--accent-amber)', fontWeight: 650, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <AlertTriangle size={14} /> Mismatched
                        </span>
                      )}
                    </td>
                    <td>
                      {kw.niche_aligned ? (
                        <span style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>On-Niche</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Broad Term</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <span className={
                          kw.status === 'Optimal' ? 'status-badge-optimal' :
                          kw.status === 'Review Intent' ? 'status-badge-mismatch' :
                          'status-badge-warning'
                        } style={{ width: 'fit-content' }}>
                          {kw.status}
                        </span>
                        {kw.recommendation && (
                          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                            {kw.recommendation}
                          </span>
                        )}
                        {kw.suggested_replacement && (
                          <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Suggest:</span>
                            <span className="fix-pill-replacement" style={{ fontSize: '0.74rem', padding: '1px 6px' }}>
                              {kw.suggested_replacement}
                            </span>
                            <button
                              className="btn btn-sm"
                              style={{ padding: '2px 5px', fontSize: '0.7rem', height: 20 }}
                              onClick={() => handleCopy(kw.suggested_replacement)}
                              title="Copy replacement"
                            >
                              {copiedUrl === kw.suggested_replacement ? <Check size={10} color="var(--accent-green)" /> : <Copy size={10} />}
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Links & Anchor Texts */}
      {activeTab === 'links' && (
        <div>
          {/* Warning Banner if Generic Anchors exist */}
          {data.links_summary?.generic_anchor_count > 0 && (
            <div style={{ background: '#fffbeb', border: '1px solid #fef3c7', borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem', marginBottom: '1.25rem', display: 'flex', gap: 10, alignItems: 'center' }}>
              <AlertTriangle size={20} color="#d97706" style={{ flexShrink: 0 }} />
              <div style={{ fontSize: '0.84rem', color: '#92400e' }}>
                <strong>Anchor Text Warning:</strong> Found {data.links_summary.generic_anchor_count} generic anchor text links (e.g. "click here", "read more"). Replace them with descriptive keywords so Google AI bots and search spiders understand the target page context.
              </div>
            </div>
          )}

          {/* Broken Links Alert */}
          {data.links_summary?.broken_links?.length > 0 && (
            <div style={{ background: '#fef2f2', border: '1.5px solid #fecaca', borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem', marginBottom: '1.25rem', display: 'flex', gap: 10, alignItems: 'center' }}>
              <XCircle size={20} color="#dc2626" style={{ flexShrink: 0 }} />
              <div style={{ fontSize: '0.84rem', color: '#991b1b' }}>
                <strong>Broken Links Found:</strong> {data.links_summary.broken_links.length} link(s) returned HTTP errors ({data.links_summary.broken_links.map((b) => `${b.status} on ${b.url}`).join(', ')}).
              </div>
            </div>
          )}

          {/* Anchor Metrics Pills */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: '1rem', fontSize: '0.78rem' }}>
            <span style={{ padding: '4px 10px', background: '#f1f5f9', borderRadius: 12, color: 'var(--text-secondary)' }}>
              Total: <strong>{data.links_summary?.total_links || 0}</strong>
            </span>
            <span style={{ padding: '4px 10px', background: data.links_summary?.generic_anchor_count ? '#fee2e2' : '#f1f5f9', borderRadius: 12, color: data.links_summary?.generic_anchor_count ? '#991b1b' : 'var(--text-secondary)' }}>
              Generic: <strong>{data.links_summary?.generic_anchor_count || 0}</strong>
            </span>
            <span style={{ padding: '4px 10px', background: data.links_summary?.empty_anchor_count ? '#fee2e2' : '#f1f5f9', borderRadius: 12, color: data.links_summary?.empty_anchor_count ? '#991b1b' : 'var(--text-secondary)' }}>
              Empty: <strong>{data.links_summary?.empty_anchor_count || 0}</strong>
            </span>
            <span style={{ padding: '4px 10px', background: '#f1f5f9', borderRadius: 12, color: 'var(--text-secondary)' }}>
              Long (&gt;8 words): <strong>{data.links_summary?.long_anchor_count || 0}</strong>
            </span>
            <span style={{ padding: '4px 10px', background: '#f1f5f9', borderRadius: 12, color: 'var(--text-secondary)' }}>
              Exact Match: <strong>{data.links_summary?.exact_match_anchor_count || 0}</strong>
            </span>
            <span style={{ padding: '4px 10px', background: data.links_summary?.off_topic_anchor_count ? '#fef3c7' : '#f1f5f9', borderRadius: 12, color: data.links_summary?.off_topic_anchor_count ? '#92400e' : 'var(--text-secondary)' }}>
              Off-Topic: <strong>{data.links_summary?.off_topic_anchor_count || 0}</strong>
            </span>
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className={`btn btn-sm ${linkFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setLinkFilter('all')}
              >
                All Links ({data.links_summary?.total_links || 0})
              </button>
              <button
                className={`btn btn-sm ${linkFilter === 'internal' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setLinkFilter('internal')}
              >
                Internal Links ({data.links_summary?.internal_count || 0})
              </button>
              <button
                className={`btn btn-sm ${linkFilter === 'external' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setLinkFilter('external')}
              >
                External Citations ({data.links_summary?.external_count || 0})
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="clean-table-wrap">
            <table className="clean-table">
              <thead>
                <tr>
                  <th>Anchor Text</th>
                  <th>Destination Domain</th>
                  <th>Target URL</th>
                  <th>Anchor Quality</th>
                  <th>Type & Attributes</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {shownLinks.map((link, i) => (
                  <tr key={i}>
                    <td>
                      <span style={{ fontWeight: 650, color: (link.is_generic || link.is_empty) ? 'var(--accent-red)' : 'var(--text-primary)' }}>
                        {link.anchor}
                      </span>
                      {link.is_generic && (
                        <div style={{ fontSize: '0.72rem', color: 'var(--accent-red)', fontWeight: 600, marginTop: 2 }}>
                          ⚠️ Generic Anchor
                        </div>
                      )}
                      {link.is_empty && (
                        <div style={{ fontSize: '0.72rem', color: 'var(--accent-red)', fontWeight: 600, marginTop: 2 }}>
                          ⚠️ Empty / Image link without alt
                        </div>
                      )}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {link.domain}
                      </span>
                    </td>
                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <a href={link.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)', textDecoration: 'none', fontSize: '0.8rem' }}>
                        {link.url}
                      </a>
                    </td>
                    <td>
                      {link.is_generic || link.is_empty ? (
                        <span className="status-badge-mismatch">Needs Fix</span>
                      ) : (
                        <span className="status-badge-optimal">Descriptive</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {link.high_authority && (
                          <span style={{ background: '#ede9fe', color: '#6d28d9', fontSize: '0.68rem', fontWeight: 700, padding: '1px 5px', borderRadius: 4 }}>
                            High DA Citation
                          </span>
                        )}
                        {link.nofollow && (
                          <span style={{ background: '#f1f5f9', color: '#475569', fontSize: '0.68rem', fontWeight: 600, padding: '1px 5px', borderRadius: 4 }}>
                            nofollow
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleCopy(link.url)}
                        title="Copy link"
                        style={{ padding: '4px 8px' }}
                      >
                        {copiedUrl === link.url ? <Check size={12} color="var(--accent-green)" /> : <Copy size={12} />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: Actionable Recommendations */}
      {activeTab === 'fixes' && (() => {
        const allRecs = data.recommendations || [];
        const kwFixes = allRecs.filter((r) => r.type === 'keywords' || r.category === 'Keywords');
        const anchorFixes = allRecs.filter((r) => r.type === 'anchors' || (r.category === 'Links & Anchors' && r.type !== 'citations'));
        const citeFixes = allRecs.filter((r) => r.type === 'citations');
        const techFixes = allRecs.filter((r) => !['keywords', 'anchors', 'citations'].includes(r.type) && r.category !== 'Keywords' && r.category !== 'Links & Anchors');

        const displayedRecs = fixFilter === 'keywords' ? kwFixes
          : fixFilter === 'anchors' ? anchorFixes
          : fixFilter === 'citations' ? citeFixes
          : fixFilter === 'tech' ? techFixes
          : allRecs;

        const totalReplacements = allRecs.reduce((acc, r) => acc + (r.suggestions?.length || 0), 0);

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Header & Metric Banner */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h3 style={{ margin: '0 0 4px', fontSize: '1.1rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                  Actionable Fixes & Content Replacements
                </h3>
                <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  Prioritized checklist with AI-suggested replacement keywords, optimized link anchors, and authoritative citation sources.
                </p>
              </div>

              {totalReplacements > 0 && (
                <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '4px 12px', borderRadius: 8, fontSize: '0.8rem', color: '#065f46', fontWeight: 650 }}>
                  ✨ {totalReplacements} AI Replacement Suggestions Ready
                </div>
              )}
            </div>

            {/* Category Filter Chips */}
            <div className="fix-filter-bar">
              <button
                className={`fix-filter-chip ${fixFilter === 'all' ? 'active' : ''}`}
                onClick={() => setFixFilter('all')}
              >
                All Fixes ({allRecs.length})
              </button>
              <button
                className={`fix-filter-chip ${fixFilter === 'keywords' ? 'active' : ''}`}
                onClick={() => setFixFilter('keywords')}
              >
                Keywords ({kwFixes.length})
              </button>
              <button
                className={`fix-filter-chip ${fixFilter === 'anchors' ? 'active' : ''}`}
                onClick={() => setFixFilter('anchors')}
              >
                Anchors & Links ({anchorFixes.length})
              </button>
              <button
                className={`fix-filter-chip ${fixFilter === 'citations' ? 'active' : ''}`}
                onClick={() => setFixFilter('citations')}
              >
                Citations & Sources ({citeFixes.length})
              </button>
              <button
                className={`fix-filter-chip ${fixFilter === 'tech' ? 'active' : ''}`}
                onClick={() => setFixFilter('tech')}
              >
                On-Page & Structure ({techFixes.length})
              </button>
            </div>

            {/* Recommendations List */}
            {displayedRecs.map((rec, i) => (
              <div
                key={i}
                style={{
                  background: 'var(--bg-white)',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  gap: 14,
                  alignItems: 'flex-start'
                }}
              >
                {/* Priority Badge */}
                <div style={{
                  background: rec.priority === 'Critical' ? '#7f1d1d' : rec.priority === 'High' ? '#fee2e2' : rec.priority === 'Medium' ? '#fef3c7' : '#f1f5f9',
                  color: rec.priority === 'Critical' ? '#ffffff' : rec.priority === 'High' ? '#991b1b' : rec.priority === 'Medium' ? '#92400e' : '#475569',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  padding: '4px 8px',
                  borderRadius: 6,
                  textTransform: 'uppercase',
                  flexShrink: 0
                }}>
                  {rec.priority}
                </div>

                <div style={{ flex: 1 }}>
                  {/* Category */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--accent-blue)', textTransform: 'uppercase' }}>
                      {rec.category}
                    </span>
                    {rec.type && (
                      <span style={{ fontSize: '0.68rem', fontWeight: 650, background: '#f1f5f9', color: '#475569', padding: '1px 6px', borderRadius: 4 }}>
                        {rec.type === 'keywords' ? 'Keyword Replacements' : rec.type === 'anchors' ? 'Anchor Text' : rec.type === 'citations' ? 'Outbound Citations' : rec.type}
                      </span>
                    )}
                  </div>

                  {/* Title & Action */}
                  <h4 style={{ margin: '0 0 6px', fontSize: '0.98rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                    {rec.title}
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {rec.action}
                  </p>

                  {/* ── 1. Keyword Replacements Table ── */}
                  {rec.type === 'keywords' && rec.suggestions && rec.suggestions.length > 0 && (
                    <div className="fix-suggestions-box">
                      <div className="fix-suggestions-title">
                        <Sparkles size={14} color="#059669" />
                        <span>Wrong Keywords vs Recommended Replacements ({rec.suggestions.length}):</span>
                      </div>

                      <div className="clean-table-wrap" style={{ margin: 0, boxShadow: 'none' }}>
                        <table className="clean-table" style={{ fontSize: '0.82rem' }}>
                          <thead>
                            <tr>
                              <th style={{ width: '28%' }}>Wrong Keyword (Current)</th>
                              <th style={{ width: '32%' }}>Suggested Replacement</th>
                              <th style={{ width: '30%' }}>SEO Alignment Reason</th>
                              <th style={{ width: '10%', textAlign: 'center' }}>Copy</th>
                            </tr>
                          </thead>
                          <tbody>
                            {rec.suggestions.map((sug, sIdx) => (
                              <tr key={sIdx}>
                                <td>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3, alignItems: 'flex-start' }}>
                                    <span className="fix-pill-wrong">
                                      {sug.current}
                                    </span>
                                    <span style={{ fontSize: '0.7rem', color: '#dc2626', fontWeight: 600 }}>
                                      {sug.issue}
                                    </span>
                                  </div>
                                </td>
                                <td>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <span className="fix-pill-replacement">
                                      {sug.replacement}
                                    </span>
                                  </div>
                                </td>
                                <td>
                                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                                    {sug.reason}
                                  </span>
                                </td>
                                <td style={{ textAlign: 'center' }}>
                                  <button
                                    className="btn btn-sm btn-secondary"
                                    onClick={() => handleCopy(sug.replacement)}
                                    title="Copy suggested replacement keyword"
                                    style={{ padding: '3px 8px', fontSize: '0.74rem' }}
                                  >
                                    {copiedUrl === sug.replacement ? (
                                      <Check size={12} color="var(--accent-green)" />
                                    ) : (
                                      <Copy size={12} />
                                    )}
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* ── 2. Anchor Replacements Table ── */}
                  {rec.type === 'anchors' && rec.suggestions && rec.suggestions.length > 0 && (
                    <div className="fix-suggestions-box">
                      <div className="fix-suggestions-title">
                        <Link2 size={14} color="#0284c7" />
                        <span>Problematic Anchors vs Recommended Text ({rec.suggestions.length}):</span>
                      </div>

                      <div className="clean-table-wrap" style={{ margin: 0, boxShadow: 'none' }}>
                        <table className="clean-table" style={{ fontSize: '0.82rem' }}>
                          <thead>
                            <tr>
                              <th style={{ width: '32%' }}>Problematic Anchor & Destination</th>
                              <th style={{ width: '30%' }}>Recommended Anchor Text</th>
                              <th style={{ width: '28%' }}>Context & SEO Benefit</th>
                              <th style={{ width: '10%', textAlign: 'center' }}>Copy</th>
                            </tr>
                          </thead>
                          <tbody>
                            {rec.suggestions.map((sug, sIdx) => (
                              <tr key={sIdx}>
                                <td>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3, alignItems: 'flex-start' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                                      <span className="fix-pill-wrong">
                                        "{sug.current}"
                                      </span>
                                      <span className="fix-pill-issue">
                                        {sug.issue}
                                      </span>
                                    </div>
                                    {sug.url && (
                                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                                        Target: {sug.url}
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td>
                                  <span className="fix-pill-replacement">
                                    "{sug.replacement}"
                                  </span>
                                </td>
                                <td>
                                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                                    {sug.reason}
                                  </span>
                                </td>
                                <td style={{ textAlign: 'center' }}>
                                  <button
                                    className="btn btn-sm btn-secondary"
                                    onClick={() => handleCopy(sug.replacement)}
                                    title="Copy recommended anchor text"
                                    style={{ padding: '3px 8px', fontSize: '0.74rem' }}
                                  >
                                    {copiedUrl === sug.replacement ? (
                                      <Check size={12} color="var(--accent-green)" />
                                    ) : (
                                      <Copy size={12} />
                                    )}
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* ── 3. Citations Recommendation Grid ── */}
                  {rec.type === 'citations' && rec.suggestions && rec.suggestions.length > 0 && (
                    <div className="fix-suggestions-box">
                      <div className="fix-suggestions-title">
                        <BookOpen size={14} color="#7c3aed" />
                        <span>Recommended High-Authority Niche References to Cite ({rec.suggestions.length}):</span>
                      </div>

                      <div className="citation-grid">
                        {rec.suggestions.map((sug, sIdx) => (
                          <div key={sIdx} className="citation-card">
                            <div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                <strong style={{ color: 'var(--text-primary)', fontSize: '0.86rem' }}>
                                  {sug.source}
                                </strong>
                                <span style={{ background: '#e0f2fe', color: '#0369a1', fontSize: '0.7rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4 }}>
                                  {sug.domain}
                                </span>
                              </div>

                              <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>
                                Topic: <span style={{ fontWeight: 500 }}>{sug.topic}</span>
                              </div>

                              {sug.anchor && (
                                <div style={{ fontSize: '0.78rem', color: 'var(--accent-green)', fontWeight: 650, marginBottom: 6 }}>
                                  Suggested Anchor: <span style={{ textDecoration: 'underline' }}>"{sug.anchor}"</span>
                                </div>
                              )}

                              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                                {sug.reason}
                              </div>
                            </div>

                            <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                              <button
                                className="btn btn-sm btn-secondary"
                                onClick={() => handleCopy(sug.anchor || sug.topic)}
                                style={{ flex: 1, fontSize: '0.74rem', padding: '4px 8px' }}
                              >
                                {copiedUrl === (sug.anchor || sug.topic) ? (
                                  <>
                                    <Check size={12} color="var(--accent-green)" /> Copied
                                  </>
                                ) : (
                                  <>
                                    <Copy size={12} /> Copy Anchor Text
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        );
      })()}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════════════
   MODULE 4: PROFILE CHECKER MODAL & RESULTS
═══════════════════════════════════════════════════════════════════════════ */
function ProfileCheckerModal({ onClose, onLaunch }) {
  const [projectUrl, setProjectUrl] = useState('');
  const [profileUrl, setProfileUrl] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [niche, setNiche] = useState('');
  const [loadingNiche, setLoadingNiche] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleDetectNiche() {
    if (!projectUrl.trim()) {
      setError('Please enter a Project Website URL first to detect your niche.');
      return;
    }
    setError('');
    setLoadingNiche(true);
    try {
      const res = await apiDetectNiche(projectUrl.trim(), 4);
      if (res.niche && res.niche !== 'Unknown') {
        setNiche(res.niche);
      } else {
        setNiche('General Business');
      }
      try {
        const u = projectUrl.trim().startsWith('http') ? projectUrl.trim() : `https://${projectUrl.trim()}`;
        const domain = new URL(u).hostname.replace('www.', '');
        const brand = domain.split('.')[0];
        if (brand && !businessName) {
          setBusinessName(brand.charAt(0).toUpperCase() + brand.slice(1));
        }
      } catch {}
    } catch {
      setError('Could not auto-detect niche; you can type it manually.');
    } finally {
      setLoadingNiche(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!profileUrl.trim()) {
      setError('Please provide the Public Profile URL to audit.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const job = await apiStartProfileCheck({
        projectUrl: projectUrl.trim(),
        profileUrl: profileUrl.trim(),
        businessName: businessName.trim(),
        niche: niche.trim(),
        maxPosts: 5,
      });
      onLaunch(job);
    } catch (err) {
      setError(err.message || 'Failed to start profile audit');
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 620 }}>
        <div className="modal-header">
          <div>
            <div className="modal-tag" style={{ color: '#c2410c', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: 4 }}>
              Module 4 · Business Profile & Bio Audit
            </div>
            <h2>👤 Business Profile Auditor</h2>
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Verify website backlink presence in the bio and check if the bio content accurately reflects your business.
            </p>
          </div>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div style={{ marginBottom: '1rem' }}><Alert type="error">{error}</Alert></div>}

            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                Business / Target Website URL <span style={{ color: 'var(--accent-red)' }}>*</span>
              </label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  type="text"
                  placeholder="https://yourbrand.com"
                  value={projectUrl}
                  onChange={(e) => setProjectUrl(e.target.value)}
                  style={{ flex: 1 }}
                  required
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleDetectNiche}
                  disabled={loadingNiche || !projectUrl}
                  style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  {loadingNiche ? <Loader2 size={14} className="spin" /> : <Sparkles size={14} color="#c2410c" />}
                  {loadingNiche ? 'Detecting...' : 'Detect Niche'}
                </button>
              </div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.76rem', display: 'block', marginTop: 4 }}>
                The official business website that should be linked in the profile bio or website field.
              </small>
            </div>

            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                Public Profile URL to Audit <span style={{ color: 'var(--accent-red)' }}>*</span>
              </label>
              <input
                type="text"
                placeholder="https://medium.com/@yourbrand, Dev.to, Substack, GitHub, Crunchbase, Web Directory..."
                value={profileUrl}
                onChange={(e) => setProfileUrl(e.target.value)}
                required
              />
              <small style={{ color: 'var(--text-muted)', fontSize: '0.76rem', display: 'block', marginTop: 4 }}>
                Supports Medium, Substack, Dev.to, GitHub, Behance, About.me, Crunchbase, Dribbble, Gravatar, Yelp, or any web directory.
              </small>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: '1.25rem' }}>
              <div className="form-group">
                <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                  Business Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Acme Corp"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label style={{ display: 'block', fontWeight: 650, fontSize: '0.86rem', marginBottom: 6 }}>
                  Industry / Niche (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. SaaS / Cloud Security"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                />
              </div>
            </div>

            <div style={{ background: '#fff7ed', border: '1px solid #ffedd5', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.8rem', color: '#9a3412', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <Info size={16} style={{ flexShrink: 0, marginTop: 2 }} color="#ea580c" />
              <div>
                <strong>Focused Profile Audit:</strong> Verifies that your official website link is present and active in the profile bio/about, and validates whether the bio content is correct, factual, and aligned with your business niche.
              </div>
            </div>
          </div>

          <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
              style={{ background: 'linear-gradient(135deg, #c2410c, #ea580c)', borderColor: '#c2410c' }}
            >
              {submitting ? (
                <>
                  <Loader2 size={15} className="spin" /> Starting Audit...
                </>
              ) : (
                <>
                  <UserCheck size={15} /> Audit Business Profile
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


function ProfileCheckerResultsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('issues');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [copiedKey, setCopiedKey] = useState('');

  const PROFILE_STEPS = [
    { num: 1, label: 'Context', desc: 'Extracting business signals' },
    { num: 2, label: 'Connect', desc: 'Fetching public profile page' },
    { num: 3, label: 'Extract', desc: 'Auditing profile bio & metadata' },
    { num: 4, label: 'Backlink', desc: 'Verifying website link in bio' },
    { num: 5, label: 'Correctness', desc: 'Checking bio content & niche accuracy' },
    { num: 6, label: 'Scoring', desc: 'Computing Profile Health Score' },
    { num: 7, label: 'AI Rewrites', desc: 'Generating optimized bio variations' },
  ];

  useEffect(() => {
    let timer;
    let isCancelled = false;

    async function poll() {
      try {
        const s = await apiGetProfileStatus(jobId);
        if (isCancelled) return;
        setStatus(s);

        if (s.status === 'done') {
          const res = await apiGetProfileResult(jobId);
          if (isCancelled) return;
          setData(res);
        } else if (s.status === 'error') {
          setError(s.error || 'Profile audit failed');
        } else {
          timer = setTimeout(poll, 1500);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err.message || 'Error checking audit status');
        }
      }
    }

    poll();
    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [jobId]);

  function handleCopy(text, key) {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(''), 2200);
  }

  if (!data && !error) {
    const curStep = status?.current_step || 1;
    const logs = status?.log || [];
    return (
      <div style={{ maxWidth: 860, margin: '2rem auto', padding: '0 1rem' }}>
        <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#fff7ed', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
            <Loader2 size={28} className="spin" color="#ea580c" />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 8 }}>
            Auditing Business Profile...
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: 540, margin: '0 auto 2rem' }}>
            Extracting profile branding, validating website backlinks, and auditing all published articles for SEO and topical alignment.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8, marginBottom: '2rem' }}>
            {PROFILE_STEPS.map((st) => {
              const isDone = curStep > st.num || status?.status === 'done';
              const isCurrent = curStep === st.num && status?.status !== 'done';
              return (
                <div key={st.num} style={{ textAlign: 'center' }}>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    margin: '0 auto 6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    background: isDone ? 'var(--accent-green)' : isCurrent ? '#ea580c' : '#f1f5f9',
                    color: isDone || isCurrent ? '#fff' : 'var(--text-muted)',
                    boxShadow: isCurrent ? '0 0 0 4px #ffedd5' : 'none',
                    transition: 'all 0.2s',
                  }}>
                    {isDone ? <Check size={16} /> : st.num}
                  </div>
                  <div style={{ fontSize: '0.72rem', fontWeight: 650, color: isCurrent ? '#ea580c' : 'var(--text-secondary)' }}>
                    {st.label}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ background: '#0f172a', borderRadius: 'var(--radius-md)', padding: '1rem', textAlign: 'left', maxHeight: 180, overflowY: 'auto', fontFamily: 'monospace', fontSize: '0.76rem', color: '#94a3b8' }}>
            <div style={{ color: '#38bdf8', marginBottom: 6, fontWeight: 600 }}>[Audit Progress Stream]</div>
            {logs.map((l, i) => (
              <div key={i} style={{ color: i === logs.length - 1 ? '#4ade80' : '#cbd5e1', marginBottom: 2 }}>
                &gt; {l.message}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 700, margin: '3rem auto', padding: '0 1rem' }}>
        <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
          <XCircle size={44} color="var(--accent-red)" style={{ margin: '0 auto 1rem' }} />
          <h3>Profile Audit Failed</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '0.5rem 0 1.5rem' }}>{error}</p>
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const meta = data.profile_meta || {};
  const backlink = data.backlink_analysis || {};
  const bio = data.bio_analysis || {};
  const issues = data.issues || [];
  const filteredIssues = severityFilter === 'all'
    ? issues
    : issues.filter((i) => i.severity.toLowerCase() === severityFilter.toLowerCase());

  const score = data.score || 0;
  const scoreColor = score >= 85 ? 'var(--accent-green)' : score >= 70 ? 'var(--accent-blue)' : score >= 50 ? 'var(--accent-amber)' : 'var(--accent-red)';

  return (
    <div style={{ maxWidth: 1100, margin: '1.5rem auto 3rem', padding: '0 1rem' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/')}>
            ← Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>
                {meta.name || 'Business Profile'}
              </h1>
              <span style={{ background: '#ffedd5', color: '#c2410c', fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: 12 }}>
                {data.platform || 'Profile'}
              </span>
            </div>
            <a href={data.profile_url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
              {data.profile_url} <ExternalLink size={12} />
            </a>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <a
            href={getProfileDownloadUrl(jobId)}
            download
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Download size={14} /> Export CSV Report
          </a>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/')}>
            New Audit
          </button>
        </div>
      </div>

      {/* Hero Overview Card */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem', background: 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(254,243,199,0.25))' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flex: 1, minWidth: 280 }}>
            {meta.avatar_url ? (
              <img
                src={meta.avatar_url}
                alt={meta.name}
                style={{ width: 68, height: 68, borderRadius: '50%', objectFit: 'cover', border: '3px solid #ffedd5', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
              />
            ) : (
              <div style={{ width: 68, height: 68, borderRadius: '50%', background: '#ffedd5', color: '#ea580c', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
                <User size={32} />
              </div>
            )}
            <div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {meta.name}
              </div>
              <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', margin: '4px 0 6px', maxWidth: 540 }}>
                Target Business: <strong>{data.project_context?.name || data.project_context?.domain}</strong> &nbsp;·&nbsp;
                Niche: <strong>{data.project_context?.niche || 'General Business'}</strong>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', fontSize: '0.78rem' }}>
                {backlink.found ? (
                  <span style={{ color: 'var(--accent-green)', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 4, background: '#dcfce7', padding: '2px 8px', borderRadius: 4 }}>
                    <CheckCircle2 size={13} /> Clickable Link to {data.project_context?.domain} Verified
                  </span>
                ) : backlink.plain_text_in_bio ? (
                  <span style={{ color: '#b45309', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 4, background: '#fef3c7', padding: '2px 8px', borderRadius: 4 }}>
                    <AlertTriangle size={13} /> Domain Mentioned as Plain Text (Not Clickable)
                  </span>
                ) : (
                  <span style={{ color: '#991b1b', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 4, background: '#fee2e2', padding: '2px 8px', borderRadius: 4 }}>
                    <XCircle size={13} /> No Link to {data.project_context?.domain}
                  </span>
                )}
                <span style={{ color: 'var(--text-muted)' }}>•</span>
                <span style={{ color: 'var(--text-muted)' }}>
                  Platform: <strong>{data.platform}</strong>
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
                Profile Health Score
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: scoreColor }}>
                {data.badge || 'Audited'}
              </div>
            </div>
            <div style={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              background: `conic-gradient(${scoreColor} ${score * 3.6}deg, #e2e8f0 0deg)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(0,0,0,0.06)'
            }}>
              <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '1.25rem', color: scoreColor }}>
                {score}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── TWO PRIMARY AUDIT PANELS ───────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: '1.5rem' }}>
        
        {/* PANEL 1: Website Backlink in Bio */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Link2 size={18} color="#ea580c" />
              <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                1. Website Backlink in Bio
              </h3>
            </div>
            {backlink.found ? (
              <span style={{ background: '#dcfce7', color: '#15803d', fontSize: '0.72rem', fontWeight: 700, padding: '3px 8px', borderRadius: 999 }}>
                ● Link Verified
              </span>
            ) : backlink.plain_text_in_bio ? (
              <span style={{ background: '#fef3c7', color: '#b45309', fontSize: '0.72rem', fontWeight: 700, padding: '3px 8px', borderRadius: 999 }}>
                ⚠ Plain Text Only
              </span>
            ) : (
              <span style={{ background: '#fee2e2', color: '#991b1b', fontSize: '0.72rem', fontWeight: 700, padding: '3px 8px', borderRadius: 999 }}>
                ✗ Missing Link
              </span>
            )}
          </div>

          <div style={{
            background: backlink.found ? '#f0fdf4' : backlink.plain_text_in_bio ? '#fffbeb' : '#fef2f2',
            border: `1px solid ${backlink.found ? '#bbf7d0' : backlink.plain_text_in_bio ? '#fef08a' : '#fecaca'}`,
            borderRadius: 'var(--radius-sm)', padding: '0.85rem', marginBottom: 12, fontSize: '0.83rem', lineHeight: 1.45,
            color: backlink.found ? '#166534' : backlink.plain_text_in_bio ? '#854d0e' : '#991b1b'
          }}>
            {backlink.summary || 'Checking website backlink...'}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.8rem', flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Target Business Website:</span>
              <span style={{ fontWeight: 650, color: 'var(--text-primary)' }}>
                {data.project_context?.url || data.project_context?.domain}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Link Placement:</span>
              <span style={{ fontWeight: 650, color: 'var(--text-primary)' }}>
                {backlink.placement || 'None'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Security Protocol:</span>
              <span style={{ fontWeight: 650 }}>
                {backlink.found ? (backlink.is_https ? <span style={{ color: '#15803d' }}>HTTPS (Secure) ✓</span> : <span style={{ color: '#b91c1c' }}>HTTP (Insecure) ✗</span>) : '—'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Anchor Text on Profile:</span>
              <span style={{ fontWeight: 650, color: 'var(--text-primary)', maxWidth: 220, textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {backlink.anchor_text || '—'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Target Liveness Status:</span>
              <span style={{ fontWeight: 700, color: backlink.status_code === 200 ? 'var(--accent-green)' : 'var(--text-secondary)' }}>
                {backlink.status_code ? `HTTP ${backlink.status_code}` : 'Verified Domain'}
              </span>
            </div>
          </div>
        </div>

        {/* PANEL 2: Bio Content Correctness */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={18} color="#ea580c" />
              <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                2. Bio Content Correctness
              </h3>
            </div>
            <span style={{
              background: bio.niche_alignment_score >= 75 ? '#dcfce7' : bio.niche_alignment_score >= 50 ? '#fef3c7' : '#fee2e2',
              color: bio.niche_alignment_score >= 75 ? '#15803d' : bio.niche_alignment_score >= 50 ? '#b45309' : '#991b1b',
              fontSize: '0.72rem', fontWeight: 700, padding: '3px 8px', borderRadius: 999
            }}>
              {bio.correctness_verdict || 'Audited'}
            </span>
          </div>

          <div style={{
            background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)',
            padding: '0.85rem', marginBottom: 12, fontSize: '0.82rem', lineHeight: 1.5, color: '#334155', fontStyle: bio.bio_text ? 'normal' : 'italic'
          }}>
            {bio.bio_text ? `"${bio.bio_text}"` : 'No bio or about description was found on this profile.'}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.8rem', flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Business Name Match:</span>
              <span style={{ fontWeight: 650, color: bio.business_name_match ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                {bio.business_name_match ? 'Brand Name Present ✓' : `Missing '${data.project_context?.name}' ✗`}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Niche Alignment Score:</span>
              <span style={{ fontWeight: 700, color: bio.niche_alignment_score >= 75 ? 'var(--accent-green)' : bio.niche_alignment_score >= 50 ? '#b45309' : 'var(--accent-red)' }}>
                {bio.niche_alignment_score || 0}% ({bio.niche_alignment_verdict || 'Unaligned'})
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Call to Action (CTA):</span>
              <span style={{ fontWeight: 650, color: bio.has_cta ? 'var(--accent-green)' : '#b45309' }}>
                {bio.has_cta ? `Found ('${bio.cta_phrase}') ✓` : 'Missing CTA ✗'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Bio Character Limit:</span>
              <span style={{ fontWeight: 650, color: bio.is_within_limit ? 'var(--text-primary)' : 'var(--accent-red)' }}>
                {bio.char_count || 0} / {bio.platform_limit || 160} chars {bio.is_within_limit ? '✓' : '⚠ Exceeds limit'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--border-color)', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        <button
          className={`tab-btn ${activeTab === 'issues' ? 'active' : ''}`}
          onClick={() => setActiveTab('issues')}
          style={{ padding: '8px 16px', fontWeight: 650, fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <AlertTriangle size={15} color={activeTab === 'issues' ? '#ea580c' : undefined} />
          What's Not Right ({issues.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
          style={{ padding: '8px 16px', fontWeight: 650, fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Sparkles size={15} color={activeTab === 'ai' ? '#ea580c' : undefined} />
          AI Bio Rewrites (Copy-Paste)
        </button>
        <button
          className={`tab-btn ${activeTab === 'links' ? 'active' : ''}`}
          onClick={() => setActiveTab('links')}
          style={{ padding: '8px 16px', fontWeight: 650, fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <ExternalLink size={15} color={activeTab === 'links' ? '#ea580c' : undefined} />
          Profile Links & Discovered Posts ({meta.external_links?.length || 0})
        </button>
      </div>

      {/* ── ISSUES TAB ───────────────────────────────────────────────────── */}
      {activeTab === 'issues' && (
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: '1rem', flexWrap: 'wrap' }}>
            {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
              <button
                key={sev}
                className={`btn btn-sm ${severityFilter === sev ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSeverityFilter(sev)}
                style={{ textTransform: 'capitalize', fontSize: '0.78rem' }}
              >
                {sev}
              </button>
            ))}
          </div>

          {filteredIssues.length === 0 ? (
            <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <CheckCircle2 size={36} color="var(--accent-green)" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontWeight: 650 }}>No issues found for this filter!</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {filteredIssues.map((iss, idx) => {
                const sevBg = iss.severity === 'critical' ? '#fee2e2' : iss.severity === 'high' ? '#ffedd5' : iss.severity === 'medium' ? '#fef3c7' : '#f1f5f9';
                const sevColor = iss.severity === 'critical' ? '#991b1b' : iss.severity === 'high' ? '#c2410c' : iss.severity === 'medium' ? '#b45309' : '#475569';

                return (
                  <div key={idx} className="card" style={{ padding: '1.25rem', borderLeft: `4px solid ${sevColor}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8, marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ background: sevBg, color: sevColor, fontSize: '0.7rem', fontWeight: 800, padding: '2px 8px', borderRadius: 4, textTransform: 'uppercase' }}>
                          {iss.severity}
                        </span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                          {iss.category}
                        </span>
                        {iss.code && (
                          <span style={{ fontSize: '0.68rem', color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: 4, fontFamily: 'monospace', border: '1px solid #e2e8f0' }}>
                            {iss.code}
                          </span>
                        )}
                      </div>
                    </div>

                    <div style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
                      {iss.issue}
                    </div>

                    {iss.impact && (
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 8, lineHeight: 1.45 }}>
                        <strong>Impact:</strong> {iss.impact}
                      </div>
                    )}

                    {iss.recommendation && (
                      <div style={{ background: 'rgba(234, 88, 12, 0.06)', border: '1px solid rgba(234, 88, 12, 0.2)', borderRadius: 'var(--radius-sm)', padding: '8px 12px', fontSize: '0.82rem', color: '#9a3412', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                        <Zap size={14} style={{ flexShrink: 0, marginTop: 2 }} color="#ea580c" />
                        <div>
                          <strong>Fix Recommendation:</strong> {iss.recommendation}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── AI BIO REWRITES TAB ───────────────────────────────────────────── */}
      {activeTab === 'ai' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* AI Assessment Bar */}
          <div className="card" style={{ padding: '1.25rem', background: '#fffbeb', border: '1px solid #fef3c7' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Sparkles size={18} color="#d97706" />
              <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 750, color: '#92400e' }}>
                AI Bio Correctness Evaluation
              </h3>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#78350f', lineHeight: 1.5 }}>
              {data.ai_suggestions?.assessment || 'Bio evaluation completed. Review the optimized variations below with your official website link included.'}
            </p>
          </div>

          {/* Bio Variation 1: Short & Punchy */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#c2410c', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Option 1 · Concise & Platform-Compliant
                </span>
                <h4 style={{ margin: '2px 0 0', fontSize: '0.92rem', fontWeight: 750 }}>
                  Short Bio (Ideal for Medium, X, Dev.to)
                </h4>
              </div>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => handleCopy(data.ai_suggestions?.short_bio, 'short')}
                style={{ fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                {copiedKey === 'short' ? <Check size={13} color="var(--accent-green)" /> : <Copy size={13} />}
                {copiedKey === 'short' ? 'Copied!' : 'Copy Bio'}
              </button>
            </div>
            <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.85rem 1rem', fontSize: '0.86rem', color: '#1e293b', lineHeight: 1.5 }}>
              "{data.ai_suggestions?.short_bio}"
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 6 }}>
              <span>Character count: {data.ai_suggestions?.short_bio_length || data.ai_suggestions?.short_bio?.length} chars</span>
              <span>Website link included ✓</span>
            </div>
          </div>

          {/* Bio Variation 2: Value-Focused */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Option 2 · Value-Proposition Focused
                </span>
                <h4 style={{ margin: '2px 0 0', fontSize: '0.92rem', fontWeight: 750 }}>
                  Brand Authority & Conversion Bio
                </h4>
              </div>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => handleCopy(data.ai_suggestions?.value_bio, 'value')}
                style={{ fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                {copiedKey === 'value' ? <Check size={13} color="var(--accent-green)" /> : <Copy size={13} />}
                {copiedKey === 'value' ? 'Copied!' : 'Copy Bio'}
              </button>
            </div>
            <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.85rem 1rem', fontSize: '0.86rem', color: '#1e293b', lineHeight: 1.5 }}>
              "{data.ai_suggestions?.value_bio}"
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 6 }}>
              <span>Character count: {data.ai_suggestions?.value_bio_length || data.ai_suggestions?.value_bio?.length} chars</span>
              <span>Full URL & Actionable CTA included ✓</span>
            </div>
          </div>

          {/* Bio Variation 3: Keyword-Rich */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#15803d', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Option 3 · Search Engine Optimized
                </span>
                <h4 style={{ margin: '2px 0 0', fontSize: '0.92rem', fontWeight: 750 }}>
                  SEO Keyword-Rich Bio
                </h4>
              </div>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => handleCopy(data.ai_suggestions?.keyword_bio, 'keyword')}
                style={{ fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                {copiedKey === 'keyword' ? <Check size={13} color="var(--accent-green)" /> : <Copy size={13} />}
                {copiedKey === 'keyword' ? 'Copied!' : 'Copy Bio'}
              </button>
            </div>
            <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.85rem 1rem', fontSize: '0.86rem', color: '#1e293b', lineHeight: 1.5 }}>
              "{data.ai_suggestions?.keyword_bio}"
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 6 }}>
              <span>Character count: {data.ai_suggestions?.keyword_bio_length || data.ai_suggestions?.keyword_bio?.length} chars</span>
              <span>Industry keywords & Website link included ✓</span>
            </div>
          </div>
        </div>
      )}

      {/* ── PROFILE LINKS & DISCOVERED POSTS TAB ─────────────────────────── */}
      {activeTab === 'links' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* External Links on Profile */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <Link2 size={16} color="var(--accent-blue)" />
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                All External Links on Profile ({meta.external_links?.length || 0})
              </h3>
            </div>
            {(!meta.external_links || meta.external_links.length === 0) ? (
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No external links detected on this profile page.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {meta.external_links.map((lnk, i) => (
                  <div key={i} style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 4, padding: '7px 10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                    <a href={lnk.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
                      {lnk.url} <ExternalLink size={10} />
                    </a>
                    <div style={{ display: 'flex', gap: 6, fontSize: '0.7rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{lnk.domain}</span>
                      {lnk.is_in_bio && <span style={{ background: '#dcfce7', color: '#15803d', padding: '0 4px', borderRadius: 2 }}>In Bio</span>}
                      {lnk.nofollow && <span style={{ background: '#f1f5f9', color: '#64748b', padding: '0 4px', borderRadius: 2 }}>nofollow</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Optional Discovered Posts (if any) */}
          {data.posts?.length > 0 && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <FileText size={16} color="#c2410c" />
                <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 750, color: 'var(--text-primary)' }}>
                  Discovered Published Articles ({data.posts.length})
                </h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {data.posts.map((p, i) => (
                  <div key={i} style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 4, padding: '7px 10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{p.title}</span>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 3 }}>
                      View <ExternalLink size={10} />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════════════
   MODULE 5: PUBLISHER & BLOGGER OUTREACH FINDER
═══════════════════════════════════════════════════════════════════════════ */

function PublisherFinderModal({ onClose, onLaunch }) {
  const [niche, setNiche] = useState('Event Planning');
  const [location, setLocation] = useState('Mohali, Chandigarh, Tricity');
  const [keywords, setKeywords] = useState('');
  const [maxPublishers, setMaxPublishers] = useState(20);
  const [checkMx, setCheckMx] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const NICHE_SUGGESTIONS = [
    'Event Planning',
    'Wedding Planners & Decor',
    'Digital Marketing & Tech',
    'Food & Restaurants',
    'Real Estate & Construction',
    'Health & Wellness'
  ];

  const LOCATION_SUGGESTIONS = [
    'Mohali, Chandigarh, Tricity',
    'Chandigarh',
    'Mohali',
    'Punjab, India',
    'Delhi NCR',
    'India (National)'
  ];

  async function handleSubmit(e) {
    e.preventDefault();
    if (!niche.trim()) {
      setError('Please specify your industry niche or topic.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const job = await apiStartPublisherSearch({
        niche: niche.trim(),
        location: location.trim(),
        keywords: keywords.trim(),
        maxPublishers: Number(maxPublishers) || 20,
        checkMx: Boolean(checkMx),
      });
      onLaunch(job);
    } catch (err) {
      setError(err.message || 'Failed to start publisher discovery search');
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 640 }}>
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '1.4rem' }}>📰</span>
              <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 700 }}>Publisher & Blogger Outreach Finder</h2>
            </div>
            <p className="modal-sub" style={{ margin: 0 }}>
              Find blogs, local news & editorial publishers accepting guest content, with verified emails and phone numbers.
            </p>
          </div>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div>
            <label className="input-label" style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span>Niche / Industry</span>
              <span style={{ color: 'var(--accent-red)' }}>*</span>
            </label>
            <input
              type="text"
              className="text-input"
              placeholder="e.g. Event Planning, Wedding Planners, Catering"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              required
            />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
              {NICHE_SUGGESTIONS.map((tag) => (
                <button
                  type="button"
                  key={tag}
                  onClick={() => setNiche(tag)}
                  style={{
                    background: niche === tag ? '#dbeafe' : 'var(--bg-card)',
                    color: niche === tag ? '#1d4ed8' : 'var(--text-muted)',
                    border: '1px solid ' + (niche === tag ? '#93c5fd' : 'var(--border-color)'),
                    borderRadius: 14,
                    padding: '2px 10px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    fontWeight: 500,
                  }}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="input-label" style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
              <MapPin size={14} color="#2563eb" />
              <span>Target Location / Region</span>
            </label>
            <input
              type="text"
              className="text-input"
              placeholder="e.g. Mohali, Chandigarh, Tricity or Worldwide"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
              {LOCATION_SUGGESTIONS.map((loc) => (
                <button
                  type="button"
                  key={loc}
                  onClick={() => setLocation(loc)}
                  style={{
                    background: location === loc ? '#dbeafe' : 'var(--bg-card)',
                    color: location === loc ? '#1d4ed8' : 'var(--text-muted)',
                    border: '1px solid ' + (location === loc ? '#93c5fd' : 'var(--border-color)'),
                    borderRadius: 14,
                    padding: '2px 10px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    fontWeight: 500,
                  }}
                >
                  {loc}
                </button>
              ))}
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 4 }}>
              Tip: Including city names (e.g. Mohali, Chandigarh) extracts local landline (0172) and regional mobile outreach numbers.
            </div>
          </div>

          <div>
            <label className="input-label" style={{ fontWeight: 600 }}>
              Optional Keywords / Extra Focus
            </label>
            <input
              type="text"
              className="text-input"
              placeholder="e.g. corporate party, wedding decorator, guest post, pr"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <label className="input-label" style={{ fontWeight: 600 }}>Maximum Publishers to Deep-Crawl</label>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#2563eb' }}>{maxPublishers} Websites</span>
            </div>
            <input
              type="range"
              min="10"
              max="50"
              step="5"
              value={maxPublishers}
              onChange={(e) => setMaxPublishers(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#2563eb' }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.84rem', cursor: 'pointer', color: 'var(--text-primary)' }}>
              <input
                type="checkbox"
                checked={checkMx}
                onChange={(e) => setCheckMx(e.target.checked)}
                style={{ accentColor: '#2563eb', cursor: 'pointer' }}
              />
              <span style={{ fontWeight: 500 }}>Verify Email Domain MX Records (filters out invalid/inactive mail hosts)</span>
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={submitting}
              style={{ background: 'linear-gradient(135deg, #1e3a8a, #2563eb)', display: 'flex', alignItems: 'center', gap: 6 }}
            >
              {submitting ? (
                <>
                  <Loader2 size={16} className="spin" />
                  <span>Starting Discovery...</span>
                </>
              ) : (
                <>
                  <span>Start Outreach Discovery</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PublisherResultsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [copiedKey, setCopiedKey] = useState('');

  const PUBLISHER_STEPS = [
    { num: 1, label: 'Search Footprints', desc: 'Querying blogs, guest posts & local publishers' },
    { num: 2, label: 'Contact Scraper', desc: 'Crawling home, editorial & contact pages' },
    { num: 3, label: 'Enrichment', desc: 'Validating emails, phone/WhatsApp & DA scores' },
    { num: 4, label: 'Export Builder', desc: 'Building professional Excel & CSV workbooks' },
  ];

  useEffect(() => {
    let timer;
    let isCancelled = false;

    async function poll() {
      try {
        const s = await apiGetPublisherStatus(jobId);
        if (isCancelled) return;
        setStatus(s);

        if (s.status === 'done') {
          const res = await apiGetPublisherResult(jobId);
          if (isCancelled) return;
          setData(res);
        } else if (s.status === 'error') {
          setError(s.error || 'Publisher search failed');
        } else {
          timer = setTimeout(poll, 1500);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err.message || 'Error checking publisher search status');
        }
      }
    }

    poll();
    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [jobId]);

  function handleCopy(text, key) {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(''), 2200);
  }

  function handleCopyAllEmails() {
    if (!data?.publishers) return;
    const allEmails = [];
    data.publishers.forEach((p) => {
      if (p.emails && p.emails.length > 0) {
        p.emails.forEach((e) => {
          if (!allEmails.includes(e)) allEmails.push(e);
        });
      }
    });
    if (allEmails.length > 0) {
      handleCopy(allEmails.join(', '), 'all_emails');
    }
  }

  if (!data && !error) {
    const curStep = status?.current_step || 1;
    const logs = status?.log || [];
    return (
      <div style={{ maxWidth: 860, margin: '2rem auto', padding: '0 1rem' }}>
        <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
            <Loader2 size={28} className="spin" color="#2563eb" />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0 0 0.5rem' }}>
            Discovering Publishers & Blogger Contacts
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0 0 1.5rem' }}>
            Searching niche footprints and deep-scraping contact emails and phone numbers...
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: '2rem' }}>
            {PUBLISHER_STEPS.map((s) => {
              const isPast = curStep > s.num;
              const isCur = curStep === s.num;
              return (
                <div
                  key={s.num}
                  style={{
                    padding: '0.85rem 0.5rem',
                    borderRadius: 8,
                    border: '1px solid ' + (isCur ? '#2563eb' : isPast ? '#10b981' : 'var(--border-color)'),
                    background: isCur ? '#eff6ff' : isPast ? '#f0fdf4' : 'var(--bg-card)',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    {isPast ? <CheckCircle2 size={16} color="#10b981" /> : isCur ? <Loader2 size={16} className="spin" color="#2563eb" /> : <div style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--border-color)', fontSize: '0.65rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{s.num}</div>}
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: isCur ? '#1d4ed8' : isPast ? '#065f46' : 'var(--text-primary)' }}>{s.label}</span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>{s.desc}</div>
                </div>
              );
            })}
          </div>

          <div style={{ background: '#0f172a', borderRadius: 8, padding: '1rem', textAlign: 'left', maxHeight: 220, overflowY: 'auto', fontFamily: 'monospace', fontSize: '0.78rem', color: '#94a3b8' }}>
            <div style={{ color: '#38bdf8', marginBottom: 6 }}>● Live Extraction Console</div>
            {logs.length === 0 && <div>Connecting to crawler queue...</div>}
            {logs.map((l, i) => (
              <div key={i} style={{ marginBottom: 3 }}>
                <span style={{ color: '#64748b' }}>[{new Date(l.timestamp * 1000).toLocaleTimeString()}]</span> {l.message}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 800, margin: '2rem auto', padding: '0 1rem' }}>
        <Alert type="error">{error}</Alert>
        <button className="btn-secondary" onClick={() => navigate('/')} style={{ marginTop: '1rem' }}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  const publishers = data?.publishers || [];
  const summary = data?.summary || {};

  const filteredPublishers = publishers.filter((p) => {
    if (activeFilter === 'email' && (!p.emails || p.emails.length === 0)) return false;
    if (activeFilter === 'phone' && (!p.phones || p.phones.length === 0)) return false;
    if (activeFilter === 'people' && (!p.people || p.people.length === 0)) return false;
    if (activeFilter === 'high_da' && (!p.da_score || p.da_score < 25)) return false;
    if (activeFilter === 'guidelines' && !p.guidelines_url) return false;

    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      (p.name && p.name.toLowerCase().includes(q)) ||
      (p.domain && p.domain.toLowerCase().includes(q)) ||
      (p.description && p.description.toLowerCase().includes(q)) ||
      (p.address && p.address.toLowerCase().includes(q)) ||
      (p.people && p.people.some((pe) => pe.toLowerCase().includes(q))) ||
      (p.emails && p.emails.some((e) => e.toLowerCase().includes(q))) ||
      (p.phones && p.phones.some((ph) => ph.includes(q))) ||
      (p.location && p.location.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ maxWidth: 1200, margin: '2rem auto', padding: '0 1rem' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '1.6rem' }}>📰</span>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0 }}>Publisher & Blogger Outreach Sheet</h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            <span>Niche: <strong style={{ color: 'var(--text-primary)' }}>{data.niche}</strong></span>
            <span>•</span>
            <span>Location: <strong style={{ color: 'var(--text-primary)' }}>{data.location || 'Worldwide'}</strong></span>
            <span>•</span>
            <span>Found: <strong style={{ color: '#2563eb' }}>{publishers.length} Publishers</strong></span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={handleCopyAllEmails}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.84rem' }}
          >
            {copiedKey === 'all_emails' ? <Check size={15} color="#10b981" /> : <Copy size={15} />}
            <span>{copiedKey === 'all_emails' ? 'Emails Copied!' : 'Copy All Emails'}</span>
          </button>

          <a
            href={getPublisherCsvDownloadUrl(jobId)}
            className="btn-secondary"
            download
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.84rem', textDecoration: 'none' }}
          >
            <Download size={15} />
            <span>CSV Export</span>
          </a>

          <a
            href={getPublisherXlsxDownloadUrl(jobId)}
            download
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: '0.88rem',
              fontWeight: 600,
              color: '#ffffff',
              background: 'linear-gradient(135deg, #059669, #10b981)',
              padding: '0.55rem 1.1rem',
              borderRadius: 6,
              textDecoration: 'none',
              boxShadow: '0 2px 6px rgba(16, 185, 129, 0.25)',
            }}
          >
            <Download size={16} />
            <span>Download Excel Sheet (.xlsx)</span>
          </a>
        </div>
      </div>

      {data.notice && (
        <div style={{ marginBottom: '1.25rem' }}>
          <Alert type="info">{data.notice}</Alert>
        </div>
      )}

      {/* Summary Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '1.1rem 1.25rem', borderLeft: '4px solid #3b82f6' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Total Publishers</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 2, color: 'var(--text-primary)' }}>{publishers.length}</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 2 }}>Websites in {data.niche}</div>
        </div>

        <div className="card" style={{ padding: '1.1rem 1.25rem', borderLeft: '4px solid #10b981' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Editorial Emails</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 2, color: '#059669' }}>{summary.emails_found || 0}</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 2 }}>Ready for direct email pitching</div>
        </div>

        <div className="card" style={{ padding: '1.1rem 1.25rem', borderLeft: '4px solid #8b5cf6' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Phone / WhatsApp</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 2, color: '#7c3aed' }}>{summary.phones_found || 0}</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 2 }}>Verified calling & WhatsApp numbers</div>
        </div>

        <div className="card" style={{ padding: '1.1rem 1.25rem', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Guest Post Guides</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 2, color: '#d97706' }}>{summary.guidelines_found || 0}</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 2 }}>"Write for Us" / Contributor guidelines</div>
        </div>
      </div>

      {/* Search and Filter Section */}
      <div className="card" style={{ padding: '1rem', marginBottom: '1.25rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 260 }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            className="text-input"
            style={{ width: '100%', padding: '0.45rem 0.75rem', fontSize: '0.85rem' }}
            placeholder="Search publishers by name, domain, city or description..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          {[
            { id: 'all', label: `All (${publishers.length})` },
            { id: 'email', label: `With Email (${summary.emails_found || 0})` },
            { id: 'phone', label: `With Phone (${summary.phones_found || 0})` },
            { id: 'people', label: 'With People / Editors' },
            { id: 'guidelines', label: `Guest Posts (${summary.guidelines_found || 0})` },
            { id: 'high_da', label: 'DA ≥ 25' },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setActiveFilter(f.id)}
              style={{
                background: activeFilter === f.id ? '#2563eb' : 'var(--bg-page)',
                color: activeFilter === f.id ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid ' + (activeFilter === f.id ? '#2563eb' : 'var(--border-color)'),
                borderRadius: 20,
                padding: '4px 12px',
                fontSize: '0.78rem',
                cursor: 'pointer',
                fontWeight: activeFilter === f.id ? 600 : 500,
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Publishers List */}
      {filteredPublishers.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No publishers match the selected filters.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1rem' }}>
          {filteredPublishers.map((pub, idx) => {
            const hasContacts = (pub.emails && pub.emails.length > 0) || (pub.phones && pub.phones.length > 0);
            return (
              <div
                key={pub.domain || idx}
                className="card"
                style={{
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: 12,
                  border: hasContacts ? '1px solid #bfdbfe' : '1px solid var(--border-color)',
                  position: 'relative',
                }}
              >
                {/* Publisher Header */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
                    <div>
                      <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 2px', lineHeight: 1.3 }}>
                        {pub.name || pub.domain}
                      </h3>
                      <a
                        href={pub.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: '0.78rem', color: '#2563eb', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
                      >
                        {pub.domain} <ExternalLink size={11} />
                      </a>
                    </div>

                    {/* DA Score & Relevance badge */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 12,
                          background: (pub.da_score || 0) >= 30 ? '#dcfce7' : '#fef3c7',
                          color: (pub.da_score || 0) >= 30 ? '#15803d' : '#b45309',
                          border: '1px solid ' + ((pub.da_score || 0) >= 30 ? '#86efac' : '#fde68a'),
                        }}
                      >
                        DA {pub.da_score ?? 'N/A'}
                      </span>
                      {pub.score !== undefined && pub.score !== null && (
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 600,
                            padding: '1px 6px',
                            borderRadius: 10,
                            background: '#eff6ff',
                            color: '#1d4ed8',
                            border: '1px solid #bfdbfe',
                          }}
                          title={`Relevance score: ${pub.relevance || 0}`}
                        >
                          Score {pub.score}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Status Tag & Location */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        padding: '1px 6px',
                        borderRadius: 4,
                        background: hasContacts ? '#f0fdf4' : '#f8fafc',
                        color: hasContacts ? '#16a34a' : 'var(--text-muted)',
                        border: '1px solid ' + (hasContacts ? '#bbf7d0' : 'var(--border-color)'),
                      }}
                    >
                      {pub.outreach_status || 'Identified'}
                    </span>
                    {pub.location_mentioned && (
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          padding: '1px 6px',
                          borderRadius: 4,
                          background: '#fef2f2',
                          color: '#b91c1c',
                          border: '1px solid #fecaca',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 3,
                        }}
                      >
                        <MapPin size={10} /> Local Match
                      </span>
                    )}
                  </div>

                  {/* Description / Bio */}
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 8px', lineHeight: 1.4 }}>
                    {pub.description}
                  </p>

                  {/* Verified Address */}
                  {pub.address && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.74rem', color: '#475569', marginBottom: 8 }}>
                      <MapPin size={12} color="#dc2626" />
                      <span>{pub.address}</span>
                    </div>
                  )}
                </div>

                {/* Contacts Box */}
                <div style={{ background: '#f8fafc', borderRadius: 6, padding: '0.75rem', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {/* Emails */}
                  {pub.emails && pub.emails.length > 0 ? (
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Mail size={12} color="#059669" />
                        <span>Editorial Emails</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {pub.emails.map((email, eIdx) => (
                          <div key={eIdx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, fontSize: '0.78rem' }}>
                            <a href={`mailto:${email}`} style={{ color: '#059669', textDecoration: 'none', fontWeight: 600, wordBreak: 'break-all' }}>
                              {email}
                            </a>
                            <button
                              onClick={() => handleCopy(email, `email_${idx}_${eIdx}`)}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}
                              title="Copy Email"
                            >
                              {copiedKey === `email_${idx}_${eIdx}` ? <Check size={12} color="#10b981" /> : <Copy size={12} color="var(--text-muted)" />}
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      No direct email scraped from public pages
                    </div>
                  )}

                  {/* Phones / WhatsApp */}
                  {pub.phones && pub.phones.length > 0 && (
                    <div style={{ borderTop: '1px dashed var(--border-color)', paddingTop: 6 }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Phone size={12} color="#7c3aed" />
                        <span>Phone / WhatsApp</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {pub.phones.map((phone, pIdx) => {
                          const digitsOnly = phone.replace(/[^0-9]/g, '');
                          const isWhatsAppCandidate = digitsOnly.length >= 10;
                          return (
                            <div key={pIdx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, fontSize: '0.78rem' }}>
                              <a href={`tel:${phone}`} style={{ color: '#7c3aed', textDecoration: 'none', fontWeight: 600 }}>
                                {phone}
                              </a>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                {isWhatsAppCandidate && (
                                  <a
                                    href={`https://wa.me/${digitsOnly.startsWith('91') ? digitsOnly : '91' + digitsOnly.slice(-10)}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    style={{ fontSize: '0.68rem', background: '#dcfce7', color: '#15803d', border: '1px solid #86efac', borderRadius: 4, padding: '1px 5px', textDecoration: 'none', fontWeight: 600 }}
                                    title="Open WhatsApp chat"
                                  >
                                    WhatsApp
                                  </a>
                                )}
                                <button
                                  onClick={() => handleCopy(phone, `phone_${idx}_${pIdx}`)}
                                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}
                                  title="Copy Phone"
                                >
                                  {copiedKey === `phone_${idx}_${pIdx}` ? <Check size={12} color="#10b981" /> : <Copy size={12} color="var(--text-muted)" />}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* People / Editorial Team */}
                  {pub.people && pub.people.length > 0 && (
                    <div style={{ borderTop: '1px dashed var(--border-color)', paddingTop: 6 }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <UserCheck size={12} color="#2563eb" />
                        <span>Editorial Team / Key Persons</span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                        {pub.people.map((person, peIdx) => (
                          <span key={peIdx} style={{ fontSize: '0.74rem', background: '#f1f5f9', color: '#334155', borderRadius: 4, padding: '2px 7px', border: '1px solid #e2e8f0', fontWeight: 500 }}>
                            {person}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Useful Links: Contact Page, Guidelines & Socials */}
                  <div style={{ borderTop: '1px dashed var(--border-color)', paddingTop: 6, display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: '0.74rem' }}>
                    {pub.contact_page_url && (
                      <a href={pub.contact_page_url} target="_blank" rel="noreferrer" style={{ color: '#2563eb', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 3 }}>
                        Contact Page <ExternalLink size={10} />
                      </a>
                    )}
                    {pub.guidelines_url && (
                      <a href={pub.guidelines_url} target="_blank" rel="noreferrer" style={{ color: '#d97706', textDecoration: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 3 }}>
                        Write For Us <ExternalLink size={10} />
                      </a>
                    )}
                    {pub.linkedin && (
                      <a href={pub.linkedin} target="_blank" rel="noreferrer" style={{ color: '#0077b5', textDecoration: 'none' }}>
                        LinkedIn
                      </a>
                    )}
                    {pub.facebook && (
                      <a href={pub.facebook} target="_blank" rel="noreferrer" style={{ color: '#1877f2', textDecoration: 'none' }}>
                        Facebook
                      </a>
                    )}
                    {pub.instagram && (
                      <a href={pub.instagram} target="_blank" rel="noreferrer" style={{ color: '#e1306c', textDecoration: 'none' }}>
                        Instagram
                      </a>
                    )}
                    {pub.twitter && (
                      <a href={pub.twitter} target="_blank" rel="noreferrer" style={{ color: '#1da1f2', textDecoration: 'none' }}>
                        Twitter/X
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


function HomePage() {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [activeJob, setActiveJob] = useState(null);
  const [auditUrl, setAuditUrl] = useState('');
  const [error, setError] = useState('');

  async function handleLaunch({ url, niche, maxPages, useAi }) {
    setShowModal(false);
    setError('');
    try {
      const job = await apiStartAudit({ url, niche, maxPages, useAi });
      setActiveJob(job);
      setAuditUrl(url);
    } catch (e) {
      setError(`Failed to start audit: ${e.message}`);
    }
  }

  function launchTask(task) {
    if (!task.active) return;
    if (task.id === 'seo-audit') setShowModal('audit');
    if (task.id === 'opportunity-finder') setShowModal('opportunities');
    if (task.id === 'blog-checker') setShowModal('blog-checker');
    if (task.id === 'profile-checker') setShowModal('profile-checker');
    if (task.id === 'publisher-finder') setShowModal('publisher-finder');
  }

  if (activeJob) {
    return (
      <div className="page" style={{ background: 'var(--bg-page)' }}>
        <div style={{ paddingTop: '1.5rem' }}>
          <AuditProgressPage jobId={activeJob.job_id} url={auditUrl} />
        </div>
      </div>
    );
  }

  return (
    <div className="page" style={{ background: 'var(--bg-page)' }}>
      {/* Hero */}
      <section className="hero">
        <div className="hero-bg" />
        <div className="hero-orbs">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <Cpu size={12} /> AI-Powered SEO Intelligence
          </div>
          <h1>
            SEO{' '}
            <span className="gradient-text">Workspace</span>
          </h1>
          <p>
            Deep-crawl any website, audit every SEO signal, and get AI-generated
            fixes and prioritised action plans — all in one professional platform.
          </p>
          <div className="hero-stats">
            <div className="hero-stat"><div className="hero-stat-value">6+</div><div className="hero-stat-label">SEO Modules</div></div>
            <div className="hero-stat"><div className="hero-stat-value">AI</div><div className="hero-stat-label">Powered Fixes</div></div>
            <div className="hero-stat"><div className="hero-stat-value">2</div><div className="hero-stat-label">Report Formats</div></div>
          </div>
        </div>
      </section>

      {/* Tasks */}
      <section className="tasks-section">
        <div className="section-header">
          <h2 className="section-title">SEO Modules</h2>
          <p className="section-subtitle">Click on an active module to get started</p>
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <div className="tasks-grid">
          {TASKS.map((task) => (
            <div
              key={task.id}
              className={`task-card ${task.active ? 'active-card' : 'coming-soon'}`}
              onClick={() => launchTask(task)}
              id={`task-card-${task.id}`}
            >
              <div className="task-card-header">
                <div className="task-icon-wrap" style={{ background: task.gradient, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
                  {task.icon}
                </div>
                <div className="task-badges">
                  {task.active
                    ? <span className="badge badge-active">● Active</span>
                    : <span className="badge badge-soon">Coming Soon</span>}
                  {task.aiPowered && <span className="badge badge-ai">🤖 AI</span>}
                </div>
              </div>
              <h3>{task.name}</h3>
              <div className="task-subtitle-label">{task.subtitle}</div>
              <p>{task.description}</p>
              <ul className="task-features">
                {task.features.map((f) => (
                  <li key={f} className="task-feature">
                    <div className="task-feature-dot" style={{ background: task.active ? 'var(--accent-blue)' : 'var(--text-muted)' }} />
                    {f}
                  </li>
                ))}
              </ul>
              <div className="task-card-footer">
                {task.active
                  ? <button className="btn-launch" onClick={(e) => { e.stopPropagation(); launchTask(task); }} id={`launch-${task.id}`}>
                      Launch <ArrowRight size={13} />
                    </button>
                  : <span className="btn-launch-ghost">Coming Soon</span>}
                <span className="module-num">Module {task.number}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {showModal === 'audit' && <AuditModal onClose={() => setShowModal(false)} onLaunch={handleLaunch} />}
      {showModal === 'opportunities' && <OpportunityModal onClose={() => setShowModal(false)} onLaunch={(job) => navigate(`/opportunities/${job.job_id}`)} />}
      {showModal === 'blog-checker' && <BlogCheckerModal onClose={() => setShowModal(false)} onLaunch={(job) => navigate(`/blog-checker/${job.job_id}`)} />}
      {showModal === 'profile-checker' && <ProfileCheckerModal onClose={() => setShowModal(false)} onLaunch={(job) => navigate(`/profile-checker/${job.job_id}`)} />}
      {showModal === 'publisher-finder' && <PublisherFinderModal onClose={() => setShowModal(false)} onLaunch={(job) => navigate(`/publishers/${job.job_id}`)} />}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   ROOT APP
═══════════════════════════════════════════════════════════════════════════ */
export default function App() {
  const [apiOnline, setApiOnline] = useState(null);

  useEffect(() => {
    let timer;
    let cancelled = false;

    const checkHealth = () => {
      fetch('http://localhost:8000/api/health')
        .then((r) => {
          if (cancelled) return;
          if (r.ok) {
            setApiOnline(true);
            timer = setTimeout(checkHealth, 30000);
          } else {
            setApiOnline(false);
            timer = setTimeout(checkHealth, 4000);
          }
        })
        .catch(() => {
          if (cancelled) return;
          setApiOnline(false);
          timer = setTimeout(checkHealth, 4000);
        });
    };

    checkHealth();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  return (
    <div className="app">
      <Navbar apiOnline={apiOnline} />
      {apiOnline === false && (
        <div className="api-banner">
          ⚠️ Backend API is offline — run <code>uvicorn api:app --reload --port 8000</code> in the project root
        </div>
      )}
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/results/:jobId" element={
          <div className="page"><ResultsPage /></div>
        } />
        <Route path="/opportunities/:jobId" element={
          <div className="page"><OpportunityResultsPage /></div>
        } />
        <Route path="/blog-checker/:jobId" element={
          <div className="page"><BlogCheckerResultsPage /></div>
        } />
        <Route path="/profile-checker/:jobId" element={
          <div className="page"><ProfileCheckerResultsPage /></div>
        } />
        <Route path="/publishers/:jobId" element={
          <div className="page"><PublisherResultsPage /></div>
        } />
      </Routes>
    </div>
  );
}
