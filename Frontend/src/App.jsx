import { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Polygon, Polyline, useMap } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

const API_BASE = 'http://localhost:5000';

/* ========================================
   CONTACT TYPE ICONS (SVG)
   ======================================== */
const CONTACT_ICONS = {
  submarine: '🔻',
  warship: '⚓',
  aircraft: '✈️',
  merchant: '🚢',
  fishing: '🎣',
  civilian: '⛵',
  unknown: '❓'
};

const THREAT_COLORS = {
  high: '#ff1744',
  medium: '#ff9100',
  low: '#00e676'
};

const TYPE_COLORS = {
  submarine: '#ff6d00',
  warship: '#448aff',
  aircraft: '#7c4dff',
  merchant: '#69f0ae',
  fishing: '#ffd740',
  civilian: '#e0e0e0',
  unknown: '#ff1744'
};

const ZONE_COLORS = {
  'Military Exercise Zone': '#ff174440',
  'Environmental Protection Zone': '#00e67640',
  'Fisheries Management': '#ffd74040',
  'Vessel Traffic Service Zone': '#448aff40',
  'Naval Training Zone': '#7c4dff40',
  'Resource Extraction Zone': '#ff6d0040'
};

const ZONE_BORDERS = {
  'Military Exercise Zone': '#ff1744',
  'Environmental Protection Zone': '#00e676',
  'Fisheries Management': '#ffd740',
  'Vessel Traffic Service Zone': '#448aff',
  'Naval Training Zone': '#7c4dff',
  'Resource Extraction Zone': '#ff6d00'
};

/* ========================================
   MAP FLY-TO COMPONENT
   ======================================== */
function MapFlyTo({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, 10, { duration: 1 });
    }
  }, [center, map]);
  return null;
}

/* ========================================
   MAIN APP COMPONENT
   ======================================== */
function App() {
  // State
  const [contacts, setContacts] = useState([]);
  const [mapContacts, setMapContacts] = useState([]);
  const [zones, setZones] = useState([]);
  const [shippingLanes, setShippingLanes] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [alertSummary, setAlertSummary] = useState({ total: 0, critical: 0, warning: 0 });
  const [stats, setStats] = useState(null);
  const [selectedContact, setSelectedContact] = useState(null);
  const [flyToCenter, setFlyToCenter] = useState(null);
  const [activeView, setActiveView] = useState('map');
  const [rightPanel, setRightPanel] = useState('details');
  const [filterType, setFilterType] = useState(null);
  const [filterThreat, setFilterThreat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [queryText, setQueryText] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [rawText, setRawText] = useState('');
  const [toast, setToast] = useState(null);
  const [crossRefs, setCrossRefs] = useState([]);
  const [serverOnline, setServerOnline] = useState(false);

  const fileInputRef = useRef(null);

  // Show toast notification
  const showToast = useCallback((title, message) => {
    setToast({ title, message });
    setTimeout(() => setToast(null), 5000);
  }, []);

  // Check server health
  const checkHealth = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/health`);
      setServerOnline(true);
      setAlertSummary(res.data.alert_summary);
      if (res.data.contacts_count > 0) {
        setDataLoaded(true);
      }
    } catch {
      setServerOnline(false);
    }
  }, []);

  // Fetch data
  const fetchContacts = useCallback(async () => {
    try {
      const params = {};
      if (filterType) params.type = filterType;
      if (filterThreat) params.threat = filterThreat;
      const res = await axios.get(`${API_BASE}/api/contacts`, { params });
      setContacts(res.data.contacts);
    } catch (err) {
      console.error('Failed to fetch contacts:', err);
    }
  }, [filterType, filterThreat]);

  const fetchMapContacts = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/contacts/map`);
      setMapContacts(res.data.contacts);
    } catch (err) {
      console.error('Failed to fetch map contacts:', err);
    }
  }, []);

  const fetchZones = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/zones`);
      setZones(res.data.zones);
      setShippingLanes(res.data.shipping_lanes);
    } catch (err) {
      console.error('Failed to fetch zones:', err);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/alerts`);
      setAlerts(res.data.alerts);
      setAlertSummary(res.data.summary);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/stats`);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  // Load data from backend
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/load-data`, {});
      if (res.data.success) {
        setDataLoaded(true);
        showToast('Data Loaded', `${res.data.contacts_loaded} contacts loaded, ${res.data.alerts_generated} alerts generated`);
        fetchContacts();
        fetchMapContacts();
        fetchAlerts();
        fetchStats();
      }
    } catch (err) {
      console.error('Failed to load data:', err);
      showToast('Error', err.response?.data?.error || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [fetchContacts, fetchMapContacts, fetchAlerts, fetchStats, showToast]);

  // Initial load
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  useEffect(() => {
    if (serverOnline) {
      fetchZones();
      if (dataLoaded) {
        fetchContacts();
        fetchMapContacts();
        fetchAlerts();
        fetchStats();
      }
    }
  }, [serverOnline, dataLoaded, fetchContacts, fetchMapContacts, fetchZones, fetchAlerts, fetchStats]);

  // Filter effect
  useEffect(() => {
    if (dataLoaded && serverOnline) {
      fetchContacts();
    }
  }, [filterType, filterThreat, dataLoaded, serverOnline, fetchContacts]);

  // Contact selection handler
  const selectContact = useCallback(async (contact) => {
    setSelectedContact(contact);
    setRightPanel('details');
    if (contact.coordinates && contact.coordinates.length > 0) {
      setFlyToCenter([contact.coordinates[0].lat, contact.coordinates[0].lon]);
    }
    // Fetch cross-references
    try {
      const res = await axios.get(`${API_BASE}/api/cross-reference/${contact.id}`);
      setCrossRefs(res.data.related_reports);
    } catch {
      setCrossRefs([]);
    }
  }, []);

  // Map contact click
  const selectMapContact = useCallback((mc) => {
    const full = contacts.find(c => c.id === mc.id);
    if (full) selectContact(full);
    else {
      setSelectedContact(mc);
      setRightPanel('details');
    }
  }, [contacts, selectContact]);

  // RAG Query
  const submitQuery = useCallback(async () => {
    if (!queryText.trim()) return;
    setQueryLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/query`, { query: queryText, k: 10 });
      setQueryResult(res.data);
    } catch (err) {
      console.error('Query failed:', err);
      showToast('Query Error', 'Failed to process query');
    } finally {
      setQueryLoading(false);
    }
  }, [queryText, showToast]);

  // Process raw text
  const processText = useCallback(async () => {
    if (!rawText.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/process-text`, { text: rawText });
      if (res.data.success) {
        showToast('Report Processed', `Contact "${res.data.contact.from}" added with ${res.data.alerts.length} alerts`);
        setRawText('');
        fetchContacts();
        fetchMapContacts();
        fetchAlerts();
        fetchStats();
      }
    } catch (err) {
      console.error('Text processing failed:', err);
      showToast('Error', 'Failed to process text');
    } finally {
      setLoading(false);
    }
  }, [rawText, fetchContacts, fetchMapContacts, fetchAlerts, fetchStats, showToast]);

  // File upload
  const handleFileUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_BASE}/api/scan`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.success) {
        showToast('Document Scanned', `Extracted text and created contact with ${res.data.alerts.length} alerts`);
        fetchContacts();
        fetchMapContacts();
        fetchAlerts();
        fetchStats();
      }
    } catch (err) {
      console.error('File upload failed:', err);
      showToast('Error', 'Failed to scan document');
    } finally {
      setLoading(false);
    }
  }, [fetchContacts, fetchMapContacts, fetchAlerts, fetchStats, showToast]);

  // Acknowledge alert
  const acknowledgeAlert = useCallback(async (alertId) => {
    try {
      await axios.post(`${API_BASE}/api/alerts/${alertId}/acknowledge`);
      fetchAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  }, [fetchAlerts]);

  /* ========================================
     RENDER FUNCTIONS
     ======================================== */

  // Render Contact Card
  const renderContactCard = (contact) => {
    const message = contact.message || contact.report || '';
    const preview = message.length > 100 ? message.substring(0, 100) + '...' : message;
    const priorityClass = contact.priority ?
      `priority-${contact.priority.toLowerCase().replace(' ', '-')}` : '';

    return (
      <div
        key={contact.id}
        className={`contact-card threat-${contact.threat_level} ${selectedContact?.id === contact.id ? 'selected' : ''} animate-fade-in`}
        onClick={() => selectContact(contact)}
      >
        <div className="contact-card-header">
          <span className={`contact-type-badge ${contact.contact_type}`}>
            {CONTACT_ICONS[contact.contact_type] || '❓'} {contact.contact_type}
          </span>
          <span className={`contact-priority ${priorityClass}`}>
            {contact.priority}
          </span>
        </div>
        <div className="contact-from">{contact.from || 'Unknown Source'}</div>
        <div className="contact-message-preview">{preview}</div>
        <div className="contact-meta">
          {contact.dtg && <span className="contact-meta-item">📅 {contact.dtg}</span>}
          {contact.speed && <span className="contact-meta-item">🚀 {contact.speed}kts</span>}
          {contact.bearing != null && <span className="contact-meta-item">🧭 {contact.bearing}°</span>}
          {contact.vessel_name && <span className="contact-meta-item">🚢 {contact.vessel_name}</span>}
        </div>
      </div>
    );
  };

  // Render Alert Card
  const renderAlertCard = (alert) => (
    <div key={alert.id} className={`alert-card ${alert.severity} animate-fade-in`}>
      <div className="alert-card-header">
        <span className={`alert-severity ${alert.severity}`}>
          {alert.severity === 'critical' ? '🔴' : '🟡'} {alert.severity}
        </span>
        {!alert.acknowledged && (
          <button className="alert-ack-btn" onClick={() => acknowledgeAlert(alert.id)}>
            ACK
          </button>
        )}
      </div>
      <div className="alert-message">{alert.message}</div>
      <div className="alert-time">{alert.type} • {alert.dtg || 'N/A'}</div>
    </div>
  );

  // Render Contact Detail Panel
  const renderDetailPanel = () => {
    if (!selectedContact) {
      return (
        <div className="empty-state">
          <div className="empty-icon">⚓</div>
          <p>Select a contact to view details</p>
        </div>
      );
    }

    const c = selectedContact;
    return (
      <div className="animate-fade-in">
        <div className="detail-section">
          <div className="detail-label">Source</div>
          <div className="detail-value">{c.from || c.location || 'Unknown'}</div>
        </div>

        {c.vessel_name && (
          <div className="detail-section">
            <div className="detail-label">Vessel</div>
            <div className="detail-value">{c.vessel_name}</div>
          </div>
        )}

        <div className="detail-grid">
          <div className="detail-section">
            <div className="detail-label">Type</div>
            <div className="detail-value">
              <span className={`contact-type-badge ${c.contact_type}`}>
                {CONTACT_ICONS[c.contact_type]} {c.contact_type}
              </span>
            </div>
          </div>
          <div className="detail-section">
            <div className="detail-label">Threat</div>
            <div className="detail-value" style={{ color: THREAT_COLORS[c.threat_level] }}>
              {c.threat_level?.toUpperCase()}
            </div>
          </div>
        </div>

        <div className="detail-grid">
          {c.speed && (
            <div className="detail-section">
              <div className="detail-label">Speed</div>
              <div className="detail-value mono">{c.speed} knots</div>
            </div>
          )}
          {c.bearing != null && (
            <div className="detail-section">
              <div className="detail-label">Bearing</div>
              <div className="detail-value mono">{c.bearing}°</div>
            </div>
          )}
        </div>

        {c.coordinates && c.coordinates.length > 0 && (
          <div className="detail-section">
            <div className="detail-label">Coordinates</div>
            <div className="detail-value mono">
              {c.coordinates.map((coord, i) => (
                <div key={i}>{coord.lat.toFixed(4)}°N, {Math.abs(coord.lon).toFixed(4)}°W</div>
              ))}
            </div>
          </div>
        )}

        {c.zone && (
          <div className="detail-section">
            <div className="detail-label">Zone</div>
            <div className="detail-value">{c.zone}</div>
          </div>
        )}

        {(c.dtg || c.date) && (
          <div className="detail-section">
            <div className="detail-label">Date-Time Group</div>
            <div className="detail-value mono">{c.dtg || `${c.date} ${c.time || ''}`}</div>
          </div>
        )}

        <div className="detail-section">
          <div className="detail-label">Full Report</div>
          <div className="detail-value" style={{ fontSize: '11px', lineHeight: '1.6' }}>
            {c.message || c.report || c.raw_text || 'No message content'}
          </div>
        </div>

        {/* Cross References */}
        {crossRefs.length > 0 && (
          <div className="detail-section">
            <div className="detail-label">Cross-Referenced Reports ({crossRefs.length})</div>
            {crossRefs.map((ref, i) => (
              <div key={i} className="cross-ref-card">
                <div style={{ fontWeight: 600, marginBottom: 4, color: '#e0e6ed' }}>
                  {ref.from || ref.location || 'Unknown'}
                </div>
                <div style={{ color: '#8899aa', marginBottom: 4 }}>
                  {(ref.message || ref.report || '').substring(0, 80)}...
                </div>
                <div className="cross-ref-score">
                  Relevance: {(ref.relevance_score * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  /* ========================================
     MAIN RENDER
     ======================================== */
  return (
    <div className="app-container">
      {/* TOP BAR */}
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="logo">
            <div className="logo-icon">🛡️</div>
            <div>
              <div className="logo-text">VARUNNETRA</div>
              <div className="logo-subtitle">Maritime Situational Awareness</div>
            </div>
          </div>
        </div>

        <div className="top-bar-center">
          <button
            className={`nav-tab ${activeView === 'map' ? 'active' : ''}`}
            onClick={() => setActiveView('map')}
          >
            🗺️ Tactical Map
          </button>
          <button
            className={`nav-tab ${activeView === 'intel' ? 'active' : ''}`}
            onClick={() => setActiveView('intel')}
          >
            🔍 Intel Query
          </button>
          <button
            className={`nav-tab ${activeView === 'scan' ? 'active' : ''}`}
            onClick={() => setActiveView('scan')}
          >
            📡 Scan Report
          </button>
        </div>

        <div className="top-bar-right">
          <div className="status-indicator">
            <div className={`status-dot ${serverOnline ? '' : 'offline'}`}></div>
            {serverOnline ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </div>

          {alertSummary.total > 0 && (
            <div className="alert-badge" onClick={() => { setActiveView('map'); setRightPanel('alerts'); }}>
              🚨 ALERTS
              <span className="alert-count">{alertSummary.total}</span>
            </div>
          )}

          {!dataLoaded && serverOnline && (
            <button className="btn btn-primary" onClick={loadData} disabled={loading}>
              {loading ? '⏳ Loading...' : '📥 Load Data'}
            </button>
          )}
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="main-content">
        {/* LEFT SIDEBAR - Contact List */}
        <aside className="sidebar-left">
          <div className="sidebar-header">
            <div className="sidebar-title">
              Contacts ({contacts.length})
            </div>
            <div className="filter-bar">
              <button
                className={`filter-chip ${!filterType ? 'active' : ''}`}
                onClick={() => setFilterType(null)}
              >All</button>
              {['submarine', 'warship', 'aircraft', 'merchant', 'unknown'].map(t => (
                <button
                  key={t}
                  className={`filter-chip ${filterType === t ? 'active' : ''}`}
                  onClick={() => setFilterType(filterType === t ? null : t)}
                >
                  {CONTACT_ICONS[t]} {t}
                </button>
              ))}
            </div>
            <div className="filter-bar" style={{ marginTop: 6 }}>
              <button
                className={`filter-chip ${!filterThreat ? 'active' : ''}`}
                onClick={() => setFilterThreat(null)}
              >All Threats</button>
              {['high', 'medium', 'low'].map(t => (
                <button
                  key={t}
                  className={`filter-chip ${filterThreat === t ? 'active' : ''}`}
                  onClick={() => setFilterThreat(filterThreat === t ? null : t)}
                  style={{ color: THREAT_COLORS[t] }}
                >
                  {t === 'high' ? '🔴' : t === 'medium' ? '🟡' : '🟢'} {t}
                </button>
              ))}
            </div>
          </div>

          <div className="contact-list">
            {!dataLoaded ? (
              <div className="empty-state">
                <div className="empty-icon">📡</div>
                <p>No data loaded</p>
                <p style={{ fontSize: 11, marginTop: 8 }}>
                  {serverOnline
                    ? 'Click "Load Data" to import maritime reports'
                    : 'Start the backend server first'}
                </p>
              </div>
            ) : contacts.length === 0 ? (
              <div className="empty-state">
                <div className="loading-spinner"></div>
                <p>Loading contacts...</p>
              </div>
            ) : (
              contacts.map(c => renderContactCard(c))
            )}
          </div>
        </aside>

        {/* CENTER - Map / Intel / Scan */}
        <main className="map-container">
          {activeView === 'map' && (
            <>
              <MapContainer
                center={[13.0, -71.0]}
                zoom={8}
                style={{ width: '100%', height: '100%' }}
                zoomControl={true}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapFlyTo center={flyToCenter} />

                {/* Maritime Zones */}
                {zones.map((zone, i) => {
                  if (!zone.coordinates || zone.coordinates.length < 3) return null;
                  const positions = zone.coordinates.map(c => [c.lat, c.lon]);
                  return (
                    <Polygon
                      key={`zone-${i}`}
                      positions={positions}
                      pathOptions={{
                        color: ZONE_BORDERS[zone.type] || '#ffffff',
                        fillColor: ZONE_COLORS[zone.type] || '#ffffff20',
                        fillOpacity: 0.3,
                        weight: 1,
                        dashArray: '5,5'
                      }}
                    >
                      <Popup>
                        <div className="popup-content">
                          <div className="popup-title">{zone.name}</div>
                          <div className="popup-row">
                            <span className="popup-label">Type</span>
                            <span className="popup-value">{zone.type}</span>
                          </div>
                        </div>
                      </Popup>
                    </Polygon>
                  );
                })}

                {/* Shipping Lanes */}
                {shippingLanes.map((lane, i) => {
                  const positions = lane.coordinates.map(c => [c.lat, c.lon]);
                  return (
                    <Polyline
                      key={`lane-${i}`}
                      positions={positions}
                      pathOptions={{
                        color: '#26c6da60',
                        weight: 2,
                        dashArray: '10,10'
                      }}
                    >
                      <Popup>
                        <div className="popup-content">
                          <div className="popup-title">{lane.name}</div>
                          <div className="popup-row">
                            <span className="popup-label">Type</span>
                            <span className="popup-value">{lane.type}</span>
                          </div>
                        </div>
                      </Popup>
                    </Polyline>
                  );
                })}

                {/* Contact Markers */}
                {mapContacts.map((mc, i) => (
                  <CircleMarker
                    key={`contact-${i}`}
                    center={[mc.lat, mc.lon]}
                    radius={mc.threat_level === 'high' ? 8 : mc.threat_level === 'medium' ? 6 : 5}
                    pathOptions={{
                      color: TYPE_COLORS[mc.type] || '#ffffff',
                      fillColor: THREAT_COLORS[mc.threat_level] || '#69f0ae',
                      fillOpacity: 0.8,
                      weight: 2,
                    }}
                    eventHandlers={{
                      click: () => selectMapContact(mc)
                    }}
                  >
                    <Popup>
                      <div className="popup-content">
                        <div className="popup-title">
                          {CONTACT_ICONS[mc.type]} {mc.from}
                        </div>
                        {mc.vessel_name && (
                          <div className="popup-row">
                            <span className="popup-label">Vessel</span>
                            <span className="popup-value">{mc.vessel_name}</span>
                          </div>
                        )}
                        <div className="popup-row">
                          <span className="popup-label">Type</span>
                          <span className="popup-value">{mc.type}</span>
                        </div>
                        <div className="popup-row">
                          <span className="popup-label">Threat</span>
                          <span className="popup-value" style={{ color: THREAT_COLORS[mc.threat_level] }}>
                            {mc.threat_level?.toUpperCase()}
                          </span>
                        </div>
                        {mc.speed && (
                          <div className="popup-row">
                            <span className="popup-label">Speed</span>
                            <span className="popup-value">{mc.speed} kts</span>
                          </div>
                        )}
                        {mc.bearing != null && (
                          <div className="popup-row">
                            <span className="popup-label">Bearing</span>
                            <span className="popup-value">{mc.bearing}°</span>
                          </div>
                        )}
                        <div className="popup-row">
                          <span className="popup-label">DTG</span>
                          <span className="popup-value">{mc.dtg}</span>
                        </div>
                        {mc.zone && (
                          <div className="popup-row">
                            <span className="popup-label">Zone</span>
                            <span className="popup-value">{mc.zone}</span>
                          </div>
                        )}
                        <div style={{ marginTop: 8, fontSize: 10, color: '#8899aa' }}>
                          {mc.message_preview}
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>

              {/* Map Overlay - Stats */}
              <div className="map-overlay map-overlay-top-left">
                <div className="stats-panel">
                  <div className="stat-card">
                    <div className="stat-value">{mapContacts.length}</div>
                    <div className="stat-label">Plotted</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value" style={{ color: '#ff1744' }}>
                      {stats?.threat_distribution?.high || 0}
                    </div>
                    <div className="stat-label">High Threat</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value" style={{ color: '#ff9100' }}>
                      {alertSummary.total}
                    </div>
                    <div className="stat-label">Alerts</div>
                  </div>
                </div>
              </div>

              {/* Map Legend */}
              <div className="map-overlay map-overlay-bottom-right">
                <div className="map-legend">
                  <div className="legend-title">Contact Types</div>
                  {Object.entries(TYPE_COLORS).map(([type, color]) => (
                    <div key={type} className="legend-item">
                      <div className="legend-dot" style={{ background: color }}></div>
                      {type}
                    </div>
                  ))}
                  <div className="legend-title" style={{ marginTop: 8 }}>Threat Level</div>
                  {Object.entries(THREAT_COLORS).map(([level, color]) => (
                    <div key={level} className="legend-item">
                      <div className="legend-dot" style={{ background: color }}></div>
                      {level}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {activeView === 'intel' && (
            <div style={{ padding: 32, maxWidth: 900, margin: '0 auto', overflowY: 'auto', height: '100%' }}>
              <h2 style={{ color: '#00e5ff', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
                🔍 Intelligence Query (RAG)
              </h2>
              <p style={{ color: '#8899aa', fontSize: 13, marginBottom: 24 }}>
                Query the maritime intelligence database using natural language.
                The RAG system will search relevant reports and provide cross-referenced analysis.
              </p>
              <div className="query-input-group">
                <input
                  className="query-input"
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="e.g. 'hostile submarine activity near 13°N, 71°W'"
                  onKeyDown={(e) => e.key === 'Enter' && submitQuery()}
                />
                <button className="query-btn" onClick={submitQuery} disabled={queryLoading || !queryText.trim()}>
                  {queryLoading ? '⏳ Analyzing...' : '🔎 Analyze'}
                </button>
              </div>

              <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                {[
                  'submarine activity', 'piracy threats', 'distress signals',
                  'unidentified vessels', 'environmental hazards', 'suspicious activity near restricted zones'
                ].map(q => (
                  <button
                    key={q}
                    className="filter-chip"
                    onClick={() => { setQueryText(q); }}
                    style={{ fontSize: 11 }}
                  >
                    {q}
                  </button>
                ))}
              </div>

              {queryResult && (
                <div className="animate-fade-in" style={{ marginTop: 24 }}>
                  <div className="analysis-result">
                    <div className="detail-label" style={{ marginBottom: 12 }}>AI Analysis</div>
                    <div className="analysis-text">{queryResult.analysis}</div>
                  </div>

                  {queryResult.results && queryResult.results.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <div className="detail-label" style={{ marginBottom: 8 }}>
                        Relevant Reports ({queryResult.total_results})
                      </div>
                      {queryResult.results.map((r, i) => (
                        <div key={i} className="cross-ref-card" style={{ cursor: 'pointer' }}
                          onClick={() => selectContact(r)}>
                          <div style={{ fontWeight: 600, color: '#e0e6ed', marginBottom: 4 }}>
                            {CONTACT_ICONS[r.contact_type]} {r.from || r.location}
                          </div>
                          <div style={{ color: '#8899aa', fontSize: 11, marginBottom: 4 }}>
                            {(r.message || r.report || '').substring(0, 120)}...
                          </div>
                          <div className="cross-ref-score">
                            Relevance: {(r.relevance_score * 100).toFixed(1)}% • Threat: {r.threat_level}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeView === 'scan' && (
            <div style={{ padding: 32, maxWidth: 700, margin: '0 auto', overflowY: 'auto', height: '100%' }}>
              <h2 style={{ color: '#00e5ff', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
                📡 Scan New Report
              </h2>
              <p style={{ color: '#8899aa', fontSize: 13, marginBottom: 24 }}>
                Upload a document (image/PDF/DOCX) or paste raw communication text.
                The system will extract intelligence and update the tactical map.
              </p>

              {/* File Upload */}
              <div className="scan-section" style={{ padding: 0, border: 'none' }}>
                <div
                  className="scan-dropzone"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div style={{ fontSize: 36, marginBottom: 8 }}>📄</div>
                  <div className="scan-dropzone-text">Click to upload a document</div>
                  <div className="scan-dropzone-hint">Supports: PNG, JPG, PDF, DOCX, TXT, MD</div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".png,.jpg,.jpeg,.pdf,.docx,.txt,.md"
                  style={{ display: 'none' }}
                  onChange={handleFileUpload}
                />
              </div>

              <div style={{ textAlign: 'center', color: '#556677', margin: '16px 0', fontSize: 12 }}>— OR —</div>

              {/* Raw Text Input */}
              <div className="text-input-area" style={{ padding: 0 }}>
                <textarea
                  className="text-input"
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  placeholder={`Paste a communication message, e.g.:\n\nFROM: PATROL BOAT BRAVO\nTO: COMMAND CENTER\nPRIORITY: URGENT\nDTG: 201700Z OCT 24\n1. DETECTED SUBMARINE PERISCOPE AT 13°45'N, 71°23'W AT 1645Z.\n2. BEARING 270°, SPEED UNKNOWN.\n...`}
                />
                <button
                  className="btn btn-primary"
                  onClick={processText}
                  disabled={loading || !rawText.trim()}
                  style={{ marginTop: 12, width: '100%', justifyContent: 'center', padding: '12px' }}
                >
                  {loading ? '⏳ Processing...' : '⚡ Process Report'}
                </button>
              </div>
            </div>
          )}
        </main>

        {/* RIGHT PANEL */}
        <aside className="panel-right">
          <div className="panel-right-header">
            <div className="panel-tabs">
              <button
                className={`panel-tab ${rightPanel === 'details' ? 'active' : ''}`}
                onClick={() => setRightPanel('details')}
              >Details</button>
              <button
                className={`panel-tab ${rightPanel === 'alerts' ? 'active' : ''}`}
                onClick={() => setRightPanel('alerts')}
              >
                Alerts {alertSummary.total > 0 && `(${alertSummary.total})`}
              </button>
            </div>
          </div>

          <div className="panel-content">
            {rightPanel === 'details' && renderDetailPanel()}

            {rightPanel === 'alerts' && (
              <>
                {alerts.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">✅</div>
                    <p>No alerts</p>
                  </div>
                ) : (
                  <>
                    <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
                      <div className="stat-card" style={{ flex: 1, textAlign: 'center' }}>
                        <div className="stat-value" style={{ color: '#ff1744', fontSize: 18 }}>
                          {alertSummary.critical}
                        </div>
                        <div className="stat-label">Critical</div>
                      </div>
                      <div className="stat-card" style={{ flex: 1, textAlign: 'center' }}>
                        <div className="stat-value" style={{ color: '#ff9100', fontSize: 18 }}>
                          {alertSummary.warning}
                        </div>
                        <div className="stat-label">Warning</div>
                      </div>
                    </div>
                    {alerts.filter(a => !a.acknowledged).map(a => renderAlertCard(a))}
                    {alerts.filter(a => a.acknowledged).length > 0 && (
                      <>
                        <div className="detail-label" style={{ marginTop: 16, marginBottom: 8 }}>
                          Acknowledged
                        </div>
                        {alerts.filter(a => a.acknowledged).map(a => (
                          <div key={a.id} className="alert-card info" style={{ opacity: 0.5 }}>
                            <div className="alert-message">{a.message}</div>
                            <div className="alert-time">{a.type}</div>
                          </div>
                        ))}
                      </>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        </aside>
      </div>

      {/* TOAST NOTIFICATION */}
      {toast && (
        <div className="scan-result-toast">
          <div className="toast-title">{toast.title}</div>
          <div className="toast-message">{toast.message}</div>
        </div>
      )}
    </div>
  );
}

export default App;
