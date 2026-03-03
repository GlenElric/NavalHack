# 🛡️ VarunNetra — Maritime Situational Awareness System

> **Advanced Naval Intelligence Platform** | Real-time Maritime Surveillance | AI-Powered Analysis

A comprehensive naval intelligence platform that uses **RAG (Retrieval-Augmented Generation)** to extract, structure, and visualize maritime communication data in real-time on an interactive tactical map. VarunNetra enables maritime commanders to monitor vessel activity, detect threats, analyze communications, and maintain situational awareness across dynamic ocean environments.

### 🎯 Key Capabilities
- **Real-time Contact Tracking**: Plot vessel positions and track maritime activity
- **Intelligent Language Analysis**: RAG-powered queries for cross-referencing contacts and communications
- **Automated Threat Detection**: AI-driven alerts for unauthorized vessels, restricted zone violations, and distress situations
- **Full-Stack Intelligence**: Seamlessly integrated backend analytics with interactive tactical visualization

---

## 🏗️ Architecture

```
NavalHack/
├── Backend/                    # Flask API Server
│   ├── app.py                 # Main REST API + WebSocket server
│   ├── config.py              # Configuration, zones, threat classifications
│   ├── data_parser.py         # Maritime comm/surveillance message parser
│   ├── rag_engine.py          # RAG engine (Sentence-Transformers + FAISS + Gemini)
│   ├── alert_engine.py        # Automated threat detection & alert system
│   ├── text_extractor.py      # OCR/PDF/DOCX text extraction
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # API keys (not committed)
│
├── Frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx            # Main application (Map, Intel, Scan views)
│   │   ├── index.css          # Design system (Navy dark theme)
│   │   └── main.jsx           # Entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── README.md
```

## ✨ Features

### (a) RAG for Information Retrieval
- **Sentence-Transformers** (`all-MiniLM-L6-v2`) for local embedding generation
- **FAISS** vector store for fast similarity search
- **Google Gemini** for intelligent cross-referencing and analysis
- Extracts: locations, time of sighting, vessel names, bearings, speeds, contact types
- Natural language query interface for naval intelligence analysis

### (b) Contact Mapping
- **Interactive Leaflet map** with dark, tactical theme
- Contacts plotted with color-coded markers by type and threat level
- Maritime zones (military, environmental, fishing) displayed as overlays
- Shipping lanes visualized
- Click-to-inspect contact details
- Real-time updates via WebSocket

### (c) User Interface
- **Premium dark navy theme** with cyan accent colors
- Three main views: Tactical Map, Intel Query, Scan Report
- Left sidebar: Contact list with filtering by type & threat level
- Right panel: Contact details, cross-references, and alerts
- Map legend with contact types and threat levels
- Toast notifications for real-time updates

### (d) Automated Alerts
- **Threat detection engine** evaluates every contact for:
  - Unidentified objects (vessels, aircraft, submarines)
  - Restricted zone violations
  - Distress situations (MAYDAY, fire, sinking)
  - Hostile activity (piracy, smuggling, armed threats)
  - Environmental hazards (oil spills, toxic materials)
- Alert acknowledgment workflow
- Critical/Warning severity classification

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
```bash
cd Backend
pip install -r requirements.txt
# Add your Gemini API key to .env
python app.py
```
Server starts at `http://localhost:5000`

### Frontend Setup
```bash
cd Frontend
npm install --legacy-peer-deps
npm run dev
```
App available at `http://localhost:3000`

### Loading Data
1. Open `http://localhost:3000`
2. Click **"Load Data"** in the top bar
3. The system automatically finds and parses the Maritime Situational Awareness dataset
4. 134 contacts are parsed, indexed in FAISS, and plotted on the map

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/api/contacts` | Get all contacts (with filter params) |
| GET | `/api/contacts/map` | Get contacts for map plotting |
| GET | `/api/zones` | Get maritime zones & shipping lanes |
| GET | `/api/alerts` | Get all alerts |
| POST | `/api/alerts/:id/acknowledge` | Acknowledge an alert |
| POST | `/api/load-data` | Load & parse maritime data |
| POST | `/api/scan` | Upload & scan a document |
| POST | `/api/process-text` | Process raw comm text |
| POST | `/api/query` | RAG intelligence query |
| GET | `/api/cross-reference/:id` | Cross-reference a contact |
| GET | `/api/stats` | System statistics |

---

## 📊 Test Data

The system is tested with the Maritime Situational Awareness dataset containing:
- **100 communication messages** (FROM/TO/PRIORITY/DTG format)
- **15 surveillance logs** (Date/Time/Location/Report format)
- **Maritime zones** and **shipping lanes**
- Covering areas around 12°N-14°N, 70°W-72°W
