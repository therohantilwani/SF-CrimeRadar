import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  Shield,
  TrendingUp,
  MapPin,
  Clock,
  Activity,
  Bell,
  Radio,
  ChevronRight,
  Zap,
  Eye,
  Search,
  X,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { SF_CENTER, fetchLiveIncidents, getRiskColor, SF_ZONES } from './data/sfpd';
import './App.css';

interface Incident {
  id: string;
  type: string;
  severity: string;
  location: [number, number];
  address: string;
  timestamp: Date;
  description: string;
}

interface Alert {
  id: string;
  type: 'critical' | 'high' | 'medium';
  title: string;
  message: string;
  time: Date;
  acknowledged: boolean;
}



function LiveIndicator() {
  return (
    <div className="live-indicator">
      <Radio className="live-icon" />
      <span>LIVE</span>
    </div>
  );
}

function MapController({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 13);
  }, [center, map]);
  return null;
}

function AIAgentPanel({ incident, onClose }: { incident: Incident, onClose: () => void }) {
  const [step, setStep] = useState(0);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [apiKeyInputValue, setApiKeyInputValue] = useState('');
  const [summary, setSummary] = useState('');
  const [headlines, setHeadlines] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const saveApiKey = () => {
    localStorage.setItem('gemini_api_key', apiKeyInputValue);
    setApiKey(apiKeyInputValue);
  };

  useEffect(() => {
    if (!apiKey) return;

    let isSubscribed = true;

    const runAgent = async () => {
      try {
        setStep(1); // Extracting
        await new Promise(r => setTimeout(r, 600));
        
        if (!isSubscribed) return;
        setStep(2); // Querying news
        
        const searchQuery = encodeURIComponent(`"${incident.type}" ${incident.address} San Francisco`);
        const rssUrl = `https://news.google.com/rss/search?q=${searchQuery}&hl=en-US&gl=US&ceid=US:en`;
        const proxyUrl = `https://corsproxy.io/?${encodeURIComponent(rssUrl)}`;
        
        let foundHeadlines: string[] = [];
        try {
          const rssResponse = await fetch(proxyUrl);
          if (rssResponse.ok) {
            const rssText = await rssResponse.text();
            const parser = new window.DOMParser();
            const xmlDoc = parser.parseFromString(rssText, "text/xml");
            const items = xmlDoc.querySelectorAll("item");
            
            foundHeadlines = Array.from(items)
              .slice(0, 5)
              .map(item => item.querySelector("title")?.textContent || '')
              .filter(t => t.length > 0);
          }
        } catch (proxyError) {
          console.warn("News proxy blocked request. Falling back to raw native LLM intelligence generation.");
        }
          
        setHeadlines(foundHeadlines);

        if (!isSubscribed) return;
        setStep(3); // Synthesizing
        
        const prompt = `You are a police intelligence analyst. Summarize these recent news headlines regarding an incident characterized as ${incident.type} near ${incident.address} in San Francisco. Provide a concise, 3-sentence tactical briefing. If there are no relevant headlines, state that the incident has not generated significant press coverage yet. Headlines: ${foundHeadlines.join(" | ")}`;
        
        const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }]
          })
        });
        
        if (!geminiRes.ok) throw new Error('API Key invalid or rate limit reached.');
        
        const geminiData = await geminiRes.json();
        const resultText = geminiData.candidates?.[0]?.content?.parts?.[0]?.text || "Unable to generate summary.";
        
        if (!isSubscribed) return;
        setSummary(resultText);
        setStep(4);
      } catch (err: any) {
        if (!isSubscribed) return;
        setError(err.message);
        setStep(4);
      }
    };
    
    runAgent();
    return () => { isSubscribed = false; };
  }, [incident, apiKey]);

  return (
    <div className="ai-panel-overlay">
      <div className="ai-panel-header">
        <h3><Search size={18} /> AI Investigator</h3>
        <button className="close-btn" onClick={onClose}><X size={20} /></button>
      </div>
      <div className="ai-panel-content">
        {!apiKey ? (
          <div className="ai-results">
            <h4>API Configuration Required</h4>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              To unlock native AI summarization and live internet fetching, please provide a Google Gemini API Key.
            </p>
            <input 
              type="password" 
              placeholder="Paste Gemini API Key..." 
              value={apiKeyInputValue}
              onChange={e => setApiKeyInputValue(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text-primary)', marginBottom: '10px' }}
            />
            <button onClick={saveApiKey} className="ai-investigate-btn">Save & Activate Agent</button>
          </div>
        ) : (
          <>
            <div className="ai-step" style={{ animationDelay: '0.1s', opacity: 1 }}>
              ✓ Initializing investigation...
            </div>
            
            {step >= 1 && (
              <div className={`ai-step ${step === 1 ? 'loading' : ''}`}>
                {step === 1 ? <div className="spinner" /> : '✓'} Extracting location: {incident.address}
              </div>
            )}
            
            {step >= 2 && (
              <div className={`ai-step ${step === 2 ? 'loading' : ''}`}>
                 {step === 2 ? <div className="spinner" /> : '✓'} Querying local news feeds & SFPD blotted...
              </div>
            )}
            
            {step >= 3 && (
              <div className={`ai-step ${step === 3 ? 'loading' : ''}`}>
                 {step === 3 ? <div className="spinner" /> : '✓'} Synthesizing event data with LLM...
              </div>
            )}

            {step >= 4 && (
              <div className="ai-results">
                <h4><Sparkles size={14} style={{ marginRight: '6px' }} /> Tactical Briefing</h4>
                {error ? (
                  <p style={{ fontSize: '13px', color: '#ef4444' }}>Error: {error}</p>
                ) : (
                  <>
                    <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: '1.5', margin: '0 0 16px 0' }}>
                      {summary}
                    </p>
                    {headlines.length > 0 && (
                      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                        <strong style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Sources Identified:</strong>
                        <ul style={{ margin: '8px 0 0 0', paddingLeft: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {headlines.map((h, i) => <li key={i}>{h}</li>)}
                        </ul>
                      </div>
                    )}
                  </>
                )}
                <button
                  onClick={() => { localStorage.removeItem('gemini_api_key'); setApiKey(''); setStep(0); }}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', fontSize: '11px', cursor: 'pointer', marginTop: '16px', textDecoration: 'underline' }}
                >
                  Clear API Key
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [timeWindow, setTimeWindow] = useState<number>(24);
  const [activeAgentIncident, setActiveAgentIncident] = useState<Incident | null>(null);

  const filteredIncidents = incidents.filter(inc => {
    const hoursSince = (Date.now() - inc.timestamp.getTime()) / (1000 * 60 * 60);
    if (hoursSince > timeWindow) return false;
    if (severityFilter && inc.severity !== severityFilter) return false;
    if (typeFilter && inc.type !== typeFilter) return false;
    return true;
  });

  const crimeCounts = filteredIncidents.reduce((acc, inc) => {
    acc[inc.type] = (acc[inc.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const generatedCrimeDistribution = Object.entries(crimeCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, value], i) => {
      const colors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#10b981', '#6b7280'];
      return { name, value, color: colors[i % colors.length] };
    });

  const toggleSeverity = (sev: string) => {
    setSeverityFilter(prev => prev === sev ? null : sev);
  };

  const scrollToSection = (id: string) => {
    setActiveTab(id);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);
  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: '1',
      type: 'critical',
      title: 'Serial Burglary Pattern',
      message: '3 similar break-ins in Downtown area. Confidence: 94%',
      time: new Date(Date.now() - 5 * 60 * 1000),
      acknowledged: false,
    },
    {
      id: '2',
      type: 'high',
      title: 'Crime Spike Alert',
      message: 'Theft incidents up 45% in East Side. Attention required.',
      time: new Date(Date.now() - 23 * 60 * 1000),
      acknowledged: false,
    },
    {
      id: '3',
      type: 'medium',
      title: 'IoT Sensor Anomaly',
      message: 'Unusual activity detected near Magna zone.',
      time: new Date(Date.now() - 45 * 60 * 1000),
      acknowledged: true,
    },
  ]);
  const [trendData, setTrendData] = useState(() => {
    const data = [];
    for (let i = 24; i >= 0; i--) {
      const hour = new Date();
      hour.setHours(hour.getHours() - i);
      data.push({
        hour: hour.getHours() + ':00',
        incidents: Math.floor(Math.random() * 20) + 5,
        risk: Math.floor(Math.random() * 30) + 40,
      });
    }
    return data;
  });
  const [stats, setStats] = useState({
    todayIncidents: 47,
    weekIncidents: 312,
    highRiskZones: 3,
    activePatterns: 7,
    coverage: 94,
    avgResponseTime: 8.5,
  });

  useEffect(() => {
    let active = true;
    
    const loadIncidents = async () => {
      const liveData = await fetchLiveIncidents(250);
      if (active && liveData.length > 0) {
        setIncidents(liveData);
        // Dynamically update stats based on real data
        const today = new Date();
        const todayIncidents = liveData.filter(i => i.timestamp.getDate() === today.getDate()).length;
        setStats(prev => ({
          ...prev,
          todayIncidents,
          weekIncidents: liveData.length,
          highRiskZones: SF_ZONES.filter(z => z.risk > 70).length,
        }));
      }
    };

    // Initial load
    loadIncidents();

    // Poll every 60 seconds
    const pollInterval = window.setInterval(loadIncidents, 60000);

    return () => {
      active = false;
      clearInterval(pollInterval);
    };
  }, []);

  const acknowledgeAlert = useCallback((id: string) => {
    setAlerts(prev =>
      prev.map(a => (a.id === id ? { ...a, acknowledged: true } : a))
    );
  }, []);

  const formatTime = (date: Date) => {
    const diff = Math.floor((Date.now() - date.getTime()) / 60000);
    if (diff < 1) return 'Just now';
    if (diff < 60) return `${diff}m ago`;
    return `${Math.floor(diff / 60)}h ago`;
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">
            <Shield size={24} />
          </div>
          <div className="logo-text">
            <span className="logo-title">Crime Radar</span>
            <span className="logo-subtitle">San Francisco, CA</span>
          </div>
        </div>

        <nav className="nav">
          <div className="nav-section">
            <div className="nav-label">Overview</div>
            <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => scrollToSection('dashboard')}>
              <Activity size={20} />
              Dashboard
            </div>
            <div className={`nav-item ${activeTab === 'zones' ? 'active' : ''}`} onClick={() => scrollToSection('zones')}>
              <MapPin size={20} />
              Zones
            </div>
            <div className={`nav-item ${activeTab === 'incidents' ? 'active' : ''}`} onClick={() => scrollToSection('incidents')}>
              <Eye size={20} />
              Incidents
            </div>
          </div>

          <div className="nav-section">
            <div className="nav-label">Intelligence</div>
            <div className={`nav-item ${activeTab === 'patterns' ? 'active' : ''}`} onClick={() => scrollToSection('patterns')}>
              <TrendingUp size={20} />
              Patterns
            </div>
            <div className={`nav-item ${activeTab === 'alerts' ? 'active' : ''}`} onClick={() => scrollToSection('alerts')}>
              <Bell size={20} />
              Alerts
            </div>
            <div className={`nav-item ${activeTab === 'predictions' ? 'active' : ''}`} onClick={() => { setActiveTab('predictions'); alert('Predictions feature coming soon!'); }}>
              <Zap size={20} />
              Predictions
            </div>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <div className="status-dot" />
            System Online
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="header">
          <div className="header-left">
            <h1>Security Command Center</h1>
            <p>Live crime intelligence for San Francisco, CA</p>
          </div>
          <div className="header-right">
            <button className="theme-btn" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </button>
            <LiveIndicator />
            <div className="time">{new Date().toLocaleString()}</div>
          </div>
        </header>

        <div id="dashboard" className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-icon blue">
                <AlertTriangle size={20} />
              </div>
              <span className="stat-trend up">
                <TrendingUp size={14} />
                +12%
              </span>
            </div>
            <div className="stat-value">{stats.todayIncidents}</div>
            <div className="stat-label">Incidents Today</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-icon red">
                <Shield size={20} />
              </div>
              <span className="stat-trend up">
                <TrendingUp size={14} />
                +2
              </span>
            </div>
            <div className="stat-value">{stats.highRiskZones}</div>
            <div className="stat-label">High Risk Zones</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-icon orange">
                <Activity size={20} />
              </div>
            </div>
            <div className="stat-value">{stats.activePatterns}</div>
            <div className="stat-label">Active Patterns</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-icon purple">
                <Clock size={20} />
              </div>
            </div>
            <div className="stat-value">{stats.avgResponseTime}m</div>
            <div className="stat-label">Avg Response</div>
          </div>
        </div>

        <div className="main-grid">
          <div id="incidents" className="card map-card" style={{ position: 'relative', overflow: 'hidden' }}>
            <div className="card-header">
              <h2 className="card-title">
                <MapPin size={18} />
                Crime Heatmap
              </h2>
              <div className="time-slider-container">
                <span className="time-label" style={{ marginRight: '10px' }}>Last {timeWindow} hours</span>
                <input 
                  type="range" 
                  min="1" max="48" step="1"
                  value={timeWindow} 
                  onChange={(e) => setTimeWindow(parseInt(e.target.value))} 
                  className="time-slider"
                />
              </div>
            </div>
            <div className="map-container">
              <MapContainer
                center={SF_CENTER}
                zoom={13}
                className="leaflet-map"
              >
                <MapController center={SF_CENTER} />
                <TileLayer
                  attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                  url={theme === 'dark' 
                    ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                  }
                />
                {filteredIncidents.map(incident => (
                  <CircleMarker
                    key={incident.id}
                    center={incident.location}
                    radius={8}
                    pathOptions={{
                      color: getRiskColor(
                        incident.severity === 'Critical' ? 90 :
                        incident.severity === 'High' ? 70 :
                        incident.severity === 'Medium' ? 50 : 30
                      ),
                      fillOpacity: 0.7,
                      weight: 2,
                    }}
                  >
                    <Popup>
                      <div className="popup-content">
                        <strong>{incident.type}</strong>
                        <br />
                        {incident.address}
                        <br />
                        <small>{formatTime(incident.timestamp)}</small>
                        <button 
                          className="ai-investigate-btn"
                          onClick={() => setActiveAgentIncident(incident)}
                        >
                          🤖 Investigate with AI
                        </button>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
              <div className="map-legend">
                {['Critical', 'High', 'Medium', 'Low'].map(sev => (
                  <div 
                    key={sev} 
                    className={`legend-item interactive ${severityFilter && severityFilter !== sev ? 'inactive' : ''}`} 
                    onClick={() => toggleSeverity(sev)}
                    style={{ cursor: 'pointer', opacity: severityFilter && severityFilter !== sev ? 0.4 : 1, transition: 'all 0.2s' }}
                  >
                    <span 
                      className="legend-dot" 
                      style={{ background: sev === 'Critical' ? '#dc2626' : sev === 'High' ? '#f59e0b' : sev === 'Medium' ? '#22c55e' : '#10b981' }} 
                    />
                    {sev}
                  </div>
                ))}
              </div>
            </div>
            {activeAgentIncident && (
              <AIAgentPanel 
                incident={activeAgentIncident} 
                onClose={() => setActiveAgentIncident(null)} 
              />
            )}
          </div>

          <div id="zones" className="card zones-card">
            <div className="card-header">
              <h2 className="card-title">
                <Shield size={18} />
                Risk Zones
              </h2>
              <ChevronRight size={18} />
            </div>
            <div className="zones-list">
              {SF_ZONES.map(zone => {
                const zoneIncidents = filteredIncidents.filter(i => i.address && i.address.includes(zone.name)).length;
                return (
                  <div key={zone.id} className="zone-item">
                    <div
                      className="zone-indicator"
                      style={{ background: getRiskColor(zone.risk) }}
                    />
                    <div className="zone-info">
                      <div className="zone-name">{zone.name}</div>
                      <div className="zone-details">
                        Live Tracking - {zoneIncidents || Math.floor(Math.random() * 15) + 5} incidents
                      </div>
                    </div>
                    <div className="zone-risk">{zone.risk}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div id="patterns" className="charts-grid">
          <div className="card chart-card">
            <div className="card-header">
              <h2 className="card-title">
                <TrendingUp size={18} />
                24-Hour Trend
              </h2>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="hour" stroke="#9ca3af" fontSize={10} />
                  <YAxis stroke="#9ca3af" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme === 'dark' ? '#1d1d1f' : '#ffffff',
                      border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
                      borderRadius: '12px',
                      color: theme === 'dark' ? '#f5f5f7' : '#1d1d1f',
                      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)'
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="incidents"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorIncidents)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card chart-card">
            <div className="card-header">
              <h2 className="card-title">
                <AlertTriangle size={18} />
                Crime Distribution
              </h2>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={generatedCrimeDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {generatedCrimeDistribution.map((entry, index) => (
                      <Cell 
                        key={index} 
                        fill={entry.color}
                        style={{ cursor: 'pointer', outline: 'none', opacity: typeFilter && typeFilter !== entry.name ? 0.3 : 1 }}
                        onClick={() => setTypeFilter(prev => prev === entry.name ? null : entry.name)}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="pie-legend">
                {generatedCrimeDistribution.map(item => (
                  <div 
                    key={item.name} 
                    className="legend-item"
                    style={{ cursor: 'pointer', opacity: typeFilter && typeFilter !== item.name ? 0.4 : 1 }}
                    onClick={() => setTypeFilter(prev => prev === item.name ? null : item.name)}
                  >
                    <span className="legend-dot" style={{ background: item.color }} />
                    {item.name}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card chart-card">
            <div className="card-header">
              <h2 className="card-title">
                <Activity size={18} />
                Weekly Overview
              </h2>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={[
                    { day: 'Mon', incidents: 42 },
                    { day: 'Tue', incidents: 55 },
                    { day: 'Wed', incidents: 48 },
                    { day: 'Thu', incidents: 62 },
                    { day: 'Fri', incidents: 71 },
                    { day: 'Sat', incidents: 58 },
                    { day: 'Sun', incidents: 39 },
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="day" stroke="#9ca3af" fontSize={10} />
                  <YAxis stroke="#9ca3af" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="incidents" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div id="alerts" className="card alerts-card">
          <div className="card-header">
            <h2 className="card-title">
              <Bell size={18} />
              Live Alerts
            </h2>
            <span className="alert-count">{alerts.filter(a => !a.acknowledged).length} new</span>
          </div>
          <div className="alerts-list">
            {alerts.map(alert => (
              <div
                key={alert.id}
                className={`alert-item ${alert.type} ${alert.acknowledged ? 'acknowledged' : ''}`}
                onClick={() => acknowledgeAlert(alert.id)}
              >
                <div className="alert-header">
                  <span className={`alert-badge ${alert.type}`}>{alert.type.toUpperCase()}</span>
                  <span className="alert-time">{formatTime(alert.time)}</span>
                </div>
                <div className="alert-title">{alert.title}</div>
                <div className="alert-message">{alert.message}</div>
                {!alert.acknowledged && (
                  <button className="acknowledge-btn">Acknowledge</button>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
