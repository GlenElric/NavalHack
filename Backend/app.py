"""
Maritime Situational Awareness - Backend API
Flask application with REST endpoints for the maritime intelligence system.
"""
import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman

from config import (
    DATA_DIR, CONTACTS_DB_PATH, MARITIME_ZONES,
    SHIPPING_LANES, RAW_DATA_DIR, AIS_STREAM_API_KEY
)
from data_parser import (
    parse_comm_message, parse_surveillance_log,
    load_all_data, load_extracted_json
)
from rag_engine import rag_engine
from alert_engine import alert_engine
from text_extractor import extract_text
from ais_service import AISService

# Initialize Flask
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Security headers with Talisman
csp = {
    'default-src': '\'self\'',
    'script-src': '\'self\' \'unsafe-inline\'',
    'style-src': '\'self\' \'unsafe-inline\' https://unpkg.com',
    'img-src': '\'self\' data: https://*.openstreetmap.org https://unpkg.com',
    'connect-src': '\'self\' ws: wss: http://localhost:5000'
}
Talisman(app, content_security_policy=csp, force_https=False)

socketio = SocketIO(app, cors_allowed_origins="*")

# Upload folder
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# In-memory contact storage
contacts_store = []
ais_service = None


def handle_ais_update(contact):
    """Callback for AIS service updates."""
    global contacts_store

    # Check if contact exists by MMSI
    mmsi = contact.get("mmsi")
    existing_idx = -1
    for i, c in enumerate(contacts_store):
        if c.get("mmsi") == mmsi:
            existing_idx = i
            break

    if existing_idx >= 0:
        # Update existing contact
        contacts_store[existing_idx].update(contact)
        contact = contacts_store[existing_idx]
    else:
        # Add new contact
        contacts_store.append(contact)

    # Evaluate for alerts
    new_alerts = alert_engine.evaluate_contact(contact)

    # Emit updates
    socketio.emit('new_contact', contact)
    for alert in new_alerts:
        socketio.emit('new_alert', alert)


def initialize_system():
    """Initialize the system with data from Maritime Situational Awareness directory."""
    global contacts_store, ais_service

    # Initialize AIS Service
    ais_service = AISService(api_key=AIS_STREAM_API_KEY, callback=handle_ais_update)
    ais_service.start()

    # Try to load existing contacts
    if os.path.exists(CONTACTS_DB_PATH):
        with open(CONTACTS_DB_PATH, 'r') as f:
            contacts_store = json.load(f)
        print(f"Loaded {len(contacts_store)} existing contacts")
    
    # Try to build/load RAG index
    if not rag_engine.load_index():
        print("No existing RAG index found. Will build on data load.")
    else:
        print("RAG index loaded successfully")


def save_contacts():
    """Save contacts to disk."""
    with open(CONTACTS_DB_PATH, 'w') as f:
        json.dump(contacts_store, f, indent=2, default=str)


# ========================
# API ROUTES
# ========================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "contacts_count": len(contacts_store),
        "rag_indexed": rag_engine.index is not None and rag_engine.index.ntotal > 0,
        "alert_summary": alert_engine.get_alert_summary()
    })


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts with optional filtering."""
    contact_type = request.args.get('type')
    threat_level = request.args.get('threat')
    has_coords = request.args.get('has_coords', 'false').lower() == 'true'

    filtered = contacts_store
    if contact_type:
        filtered = [c for c in filtered if c.get('contact_type') == contact_type]
    if threat_level:
        filtered = [c for c in filtered if c.get('threat_level') == threat_level]
    if has_coords:
        filtered = [c for c in filtered if c.get('coordinates')]

    return jsonify({
        "contacts": filtered,
        "total": len(filtered),
        "all_total": len(contacts_store)
    })


@app.route('/api/contacts/map', methods=['GET'])
def get_map_contacts():
    """Get contacts formatted for map plotting (only those with coordinates)."""
    map_contacts = []
    for contact in contacts_store:
        if contact.get("coordinates"):
            for coord in contact["coordinates"]:
                map_contacts.append({
                    "id": contact.get("id"),
                    "lat": coord["lat"],
                    "lon": coord["lon"],
                    "type": contact.get("contact_type", "unknown"),
                    "threat_level": contact.get("threat_level", "low"),
                    "from": contact.get("from", "Unknown"),
                    "vessel_name": contact.get("vessel_name"),
                    "bearing": contact.get("bearing"),
                    "speed": contact.get("speed"),
                    "priority": contact.get("priority", ""),
                    "dtg": contact.get("dtg", contact.get("date", "")),
                    "zone": contact.get("zone"),
                    "message_preview": (
                        contact.get("message", contact.get("report", ""))[:150]
                    )
                })

    return jsonify({
        "contacts": map_contacts,
        "total": len(map_contacts)
    })


@app.route('/api/zones', methods=['GET'])
def get_zones():
    """Get maritime zones for map display."""
    return jsonify({
        "zones": MARITIME_ZONES,
        "shipping_lanes": SHIPPING_LANES
    })


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts."""
    active_only = request.args.get('active', 'false').lower() == 'true'
    if active_only:
        alerts = alert_engine.get_active_alerts()
    else:
        alerts = alert_engine.get_all_alerts()
    return jsonify({
        "alerts": alerts,
        "summary": alert_engine.get_alert_summary()
    })


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    success = alert_engine.acknowledge_alert(alert_id)
    return jsonify({"success": success})


@app.route('/api/load-data', methods=['POST'])
def load_data():
    """Load data from the Maritime Situational Awareness directory."""
    global contacts_store

    data = request.get_json() or {}
    data_dir = data.get('directory', '')

    if not data_dir or not os.path.exists(data_dir):
        # Try default locations
        possible_dirs = [
            os.path.join(os.path.expanduser("~"), "Downloads",
                        "Maritime Situational Awareness", "Maritime Situational Awareness"),
            os.path.join(os.path.expanduser("~"), "Downloads",
                        "Maritime Situational Awareness"),
        ]
        data_dir = None
        for d in possible_dirs:
            if os.path.exists(d):
                data_dir = d
                break

    if not data_dir:
        return jsonify({"error": "Data directory not found. Please provide the correct path."}), 400

    try:
        # Clear existing data
        contacts_store = []
        alert_engine.clear_alerts()

        # Parse all markdown files
        contacts_store = load_all_data(data_dir)
        print(f"Parsed {len(contacts_store)} contacts from markdown files")

        # Generate alerts for all contacts
        all_alerts = []
        for contact in contacts_store:
            new_alerts = alert_engine.evaluate_contact(contact)
            all_alerts.extend(new_alerts)

        # Build RAG index
        rag_engine.build_index(contacts_store)

        # Save contacts
        save_contacts()

        return jsonify({
            "success": True,
            "contacts_loaded": len(contacts_store),
            "alerts_generated": len(all_alerts),
            "alert_summary": alert_engine.get_alert_summary(),
            "data_directory": data_dir
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/scan', methods=['POST'])
def scan_document():
    """Upload and scan a document (image/PDF/DOCX) for maritime intelligence."""
    global contacts_store

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Extract text
    extracted_text = extract_text(file_path)

    # Parse the extracted text as a comm message
    new_id = max([c.get("id", 0) for c in contacts_store], default=0) + 1
    contact = parse_comm_message(extracted_text, new_id)
    contacts_store.append(contact)

    # Generate alerts
    new_alerts = alert_engine.evaluate_contact(contact)

    # Add to RAG index incrementally (Bolt optimization)
    rag_engine.add_to_index(contact)

    # Save
    save_contacts()

    # Emit real-time update
    socketio.emit('new_contact', contact)
    for alert in new_alerts:
        socketio.emit('new_alert', alert)

    return jsonify({
        "success": True,
        "extracted_text": extracted_text,
        "contact": contact,
        "alerts": new_alerts
    })


@app.route('/api/process-text', methods=['POST'])
def process_text():
    """Process raw text input as a maritime communication."""
    global contacts_store

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    raw_text = data['text']

    # Parse the text
    new_id = max([c.get("id", 0) for c in contacts_store], default=0) + 1
    contact = parse_comm_message(raw_text, new_id)
    contacts_store.append(contact)

    # Generate alerts
    new_alerts = alert_engine.evaluate_contact(contact)

    # Add to RAG index incrementally (Bolt optimization)
    rag_engine.add_to_index(contact)

    # Save
    save_contacts()

    # Emit real-time update
    socketio.emit('new_contact', contact)
    for alert in new_alerts:
        socketio.emit('new_alert', alert)

    return jsonify({
        "success": True,
        "contact": contact,
        "alerts": new_alerts
    })


@app.route('/api/query', methods=['POST'])
def query_rag():
    """Query the RAG system for intelligence analysis."""
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400

    query = data['query']
    k = data.get('k', 10)

    # Search and analyze
    search_results = rag_engine.search(query, k=k)
    analysis = rag_engine.analyze_with_gemini(query, search_results)

    return jsonify({
        "query": query,
        "results": search_results,
        "analysis": analysis.get("analysis", ""),
        "total_results": len(search_results)
    })


@app.route('/api/cross-reference/<int:contact_id>', methods=['GET'])
def cross_reference(contact_id):
    """Cross-reference a specific contact with the knowledge base."""
    contact = None
    for c in contacts_store:
        if c.get("id") == contact_id:
            contact = c
            break

    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    related = rag_engine.cross_reference(contact)
    return jsonify({
        "contact": contact,
        "related_reports": related,
        "total_related": len(related)
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    type_counts = {}
    threat_counts = {"high": 0, "medium": 0, "low": 0}
    zone_counts = {}
    with_coords = 0

    for c in contacts_store:
        ct = c.get("contact_type", "unknown")
        type_counts[ct] = type_counts.get(ct, 0) + 1

        tl = c.get("threat_level", "low")
        threat_counts[tl] = threat_counts.get(tl, 0) + 1

        zone = c.get("zone")
        if zone:
            zone_counts[zone] = zone_counts.get(zone, 0) + 1

        if c.get("coordinates"):
            with_coords += 1

    return jsonify({
        "total_contacts": len(contacts_store),
        "contacts_with_coordinates": with_coords,
        "type_distribution": type_counts,
        "threat_distribution": threat_counts,
        "zone_distribution": zone_counts,
        "alert_summary": alert_engine.get_alert_summary()
    })


# ========================
# SOCKET.IO EVENTS
# ========================

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('connection_status', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")


# ========================
# MAIN
# ========================

if __name__ == '__main__':
    initialize_system()
    print("\n=== Maritime Situational Awareness System ===")
    print(f"Contacts loaded: {len(contacts_store)}")
    print(f"RAG indexed: {rag_engine.index is not None}")
    print(f"Active alerts: {alert_engine.get_alert_summary()}")
    print("Starting server on http://localhost:5000\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
