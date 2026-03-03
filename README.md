# 🛡️ VarunNetra — Maritime Situational Awareness System

> **Advanced Naval Intelligence Platform** | Real-time Maritime Surveillance | AI-Powered Analysis

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Node.js Version](https://img.shields.io/badge/node.js-18%2B-green)](https://nodejs.org/)
[![React Version](https://img.shields.io/badge/react-18.x-cyan)](https://react.dev/)
[![Flask Version](https://img.shields.io/badge/flask-latest-lightgrey)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive naval intelligence platform that uses **RAG (Retrieval-Augmented Generation)** to extract, structure, and visualize maritime communication data in real-time on an interactive tactical map. VarunNetra enables maritime commanders to monitor vessel activity, detect threats, analyze communications, and maintain situational awareness across dynamic ocean environments.

## 🎯 Key Capabilities

- **Real-time Contact Tracking**: Plot vessel positions and track maritime activity visually.
- **Intelligent Language Analysis**: RAG-powered queries for cross-referencing contacts and communications.
- **Automated Threat Detection**: AI-driven alerts for unauthorized vessels, restricted zone violations, and distress situations using a robust rule engine.
- **Full-Stack Intelligence**: Seamlessly integrated Flask backend analytics with an interactive React SPA visualization.
- **Document Scanning**: Upload and scan images, PDFs, or DOCX files for maritime intelligence extraction.

## 📸 Screenshots

Here is a glimpse of the VarunNetra interface in action:

<p align="center">
  <img src="preview/Screenshot%202026-03-02%20230526.png" alt="VarunNetra Tactical Map" width="800" />
</p>
<p align="center">
  <img src="preview/Screenshot%202026-03-02%20230554.png" alt="Intelligence Analysis View" width="800" />
</p>
<p align="center">
  <img src="preview/Screenshot%202026-03-02%20230618.png" alt="VarunNetra Dashboard" width="800" />
</p>

---

## 🏗️ Architecture

The project is split into a robust Python back-end and a sleek React front-end, designed for scalability and real-time updates using WebSockets.

```text
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
│   ├── index.html             # Application HTML template
│   ├── vite.config.js         # Vite configuration
│   └── package.json           # Node.js dependencies
│
└── README.md                  # Project documentation
```

## ✨ Features

### 🔍 RAG for Information Retrieval
- **Sentence-Transformers** (`all-MiniLM-L6-v2`) for local, private embedding generation.
- **FAISS** vector store for fast, scalable semantic similarity search.
- **Google Gemini** integration for intelligent cross-referencing and contextual analysis.
- Extracts entity specifics: locations, time of sighting, vessel names, bearings, speeds, and contact types.
- Natural language query interface tailored for naval intelligence.

### 🗺️ Contact Mapping & Visualization
- **Interactive Leaflet Map** featuring a dark, tactical naval theme.
- Contacts are plotted with color-coded markers distinguishing by type and threat level.
- Maritime zones (military, environmental, fishing) displayed as vector overlays.
- Real-time updates pushed seamlessly via **Socket.IO** connections.
- Deep-dive into contact specifics with a click-to-inspect feature.

### 💻 Threat & Alert Management
- **Automated Threat Evaluation** for every new contact against a robust set of rules:
  - Unidentified objects (vessels, aircraft, submarines).
  - Infractions within restricted operational zones.
  - Distress situations (MAYDAY broadcasts, fire, sinking).
  - Hostile activity patterns (piracy, smuggling, armed threats).
- Clear, actionable alert acknowledgment workflows.
- Granular severity classifications to prioritize critical threats.

### 🎨 Premium User Interface
- **Navy Dark Theme** accented with tactical cyan styles.
- Left sidebar includes a responsive contact list filtering by type & threat level.
- Right action panel provides intelligence deep-dives, cross-references, and active alerts.
- Dedicated tabs for Tactical Map, Intel Query, and Document Scan workflows.

---

## 🚀 Getting Started

Follow these steps to deploy VarunNetra to your local development environment.

### Prerequisites

Ensure you have the following installed on your system:
- **Python 3.10+**
- **Node.js 18+**

### 1. Backend Setup

Launch the Flask REST API and WebSocket Server:

```bash
cd Backend
# Install python dependencies
pip install -r requirements.txt

# Create your .env file and add your Gemini API Key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Start the Flask Server
python app.py
```
> **Note:** The backend server will start at `http://localhost:5000`

### 2. Frontend Setup

Launch the React SPA using Vite:

```bash
cd Frontend
# Install frontend dependencies (legacy-peer-deps recommended for older react-leaflet compatibility)
npm install --legacy-peer-deps

# Start the development server
npm run dev
```

### 3. Loading Initial Data

1. Open your browser to the Frontend URL (usually `http://localhost:5173`).
2. Click **"Load Data"** in the top navigation bar.
3. The system will automatically scan, parse, and ingest standard Maritime Situational Awareness datasets.
4. Contacts and surveillance logs will be indexed in FAISS and instantaneously plotted on your tactical map.

---

## 🔌 Core API Endpoints

The backend provides a comprehensive set of RESTful endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check and status |
| `GET` | `/api/contacts` | Retrieve all contacts (supports filtering) |
| `GET` | `/api/contacts/map` | Dedicated subset payload for map plotting |
| `GET` | `/api/zones` | Fetch configured maritime zones & shipping lanes |
| `GET` | `/api/alerts` | Query active and historical threat alerts |
| `POST` | `/api/alerts/<id>/acknowledge`| Acknowledge and silence a specific alert |
| `POST` | `/api/load-data` | Trigger bulk ingestion of maritime data |
| `POST` | `/api/scan` | Upload document for OCR/Text extraction |
| `POST` | `/api/query` | Submit a RAG natural language intelligence query |
| `GET` | `/api/stats` | Retrieve holistic system metrics and statistics |

*(Real-time pushes are handled simultaneously via WebSocket events like `new_contact` and `new_alert`)*

---

## 📊 Test Data Composition

The platform is built to natively process standard Maritime Situational Awareness structures, including:
- **100+ Communication Messages** formatted with standard headers (`FROM`, `TO`, `PRIORITY`, `DTG`).
- **Surveillance Logs** detailing localized reports, date/times, and raw unstructured notes.
- Covers geolocation boundaries centered around the Caribbean and vital shipping lanes.

---

<p align="center">
  Built with ❤️ for Maritime Security.
</p>
