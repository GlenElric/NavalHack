"""
Alert Engine Module
Monitors contacts and generates automated alerts for potential threats.
"""
import json
import os
from datetime import datetime
from config import ALERTS_DB_PATH, MARITIME_ZONES, THREAT_KEYWORDS


class AlertEngine:
    """Automated alert system for maritime threat detection."""

    def __init__(self):
        self.alerts = []
        self._load_alerts()

    def _load_alerts(self):
        """Load existing alerts from disk."""
        if os.path.exists(ALERTS_DB_PATH):
            with open(ALERTS_DB_PATH, 'r') as f:
                self.alerts = json.load(f)

    def _save_alerts(self):
        """Save alerts to disk."""
        with open(ALERTS_DB_PATH, 'w') as f:
            json.dump(self.alerts, f, indent=2, default=str)

    def evaluate_contact(self, contact):
        """Evaluate a contact and generate alerts if needed."""
        new_alerts = []

        # Check for high threat level
        if contact.get("threat_level") == "high":
            alert = self._create_alert(
                contact,
                "HIGH_THREAT",
                f"High threat contact detected: {contact.get('from', 'Unknown source')}",
                "critical"
            )
            new_alerts.append(alert)

        # Check for unidentified contacts
        text = (contact.get("message", "") + " " + contact.get("report", "")).lower()
        if "unidentified" in text:
            obj_type = "object"
            if "aircraft" in text:
                obj_type = "aircraft"
            elif "vessel" in text or "ship" in text:
                obj_type = "vessel"
            elif "submarine" in text or "submersible" in text:
                obj_type = "submarine"
            elif "underwater" in text:
                obj_type = "underwater contact"

            alert = self._create_alert(
                contact,
                "UNIDENTIFIED_CONTACT",
                f"Unidentified {obj_type} detected by {contact.get('from', 'Unknown')}",
                "critical"
            )
            new_alerts.append(alert)

        # Check for vessels in restricted waters
        if contact.get("zone"):
            zone_info = None
            for z in MARITIME_ZONES:
                if z["name"] == contact["zone"]:
                    zone_info = z
                    break
            if zone_info and zone_info["type"] in ["Military Exercise Zone", "Environmental Protection Zone", "Naval Training Zone"]:
                # Check if the contact is not a military/authorized entity
                from_lower = contact.get("from", "").lower()
                authorized = any(kw in from_lower for kw in [
                    "naval", "coast guard", "patrol", "military", "submarine"
                ])
                if not authorized:
                    alert = self._create_alert(
                        contact,
                        "RESTRICTED_ZONE_VIOLATION",
                        f"Contact in restricted zone: {contact['zone']} - {contact.get('from', 'Unknown')}",
                        "warning"
                    )
                    new_alerts.append(alert)

        # Check for distress situations
        if any(kw in text for kw in ["mayday", "distress", "taking on water", "fire", "explosion", "sinking"]):
            alert = self._create_alert(
                contact,
                "DISTRESS",
                f"Distress situation reported by {contact.get('from', 'Unknown')}",
                "critical"
            )
            new_alerts.append(alert)

        # Check for non-responsive vessels
        if "not responding" in text or "uncooperative" in text:
            alert = self._create_alert(
                contact,
                "NON_RESPONSIVE",
                f"Non-responsive contact detected by {contact.get('from', 'Unknown')}",
                "warning"
            )
            new_alerts.append(alert)

        # Check for hostile activity
        if any(kw in text for kw in ["hostile", "piracy", "attack", "armed", "smuggling", "drug"]):
            alert = self._create_alert(
                contact,
                "HOSTILE_ACTIVITY",
                f"Potential hostile activity: {contact.get('from', 'Unknown')}",
                "critical"
            )
            new_alerts.append(alert)

        # Check for environmental hazards
        if any(kw in text for kw in ["oil spill", "pollution", "toxic", "hazardous material", "debris field"]):
            alert = self._create_alert(
                contact,
                "ENVIRONMENTAL_HAZARD",
                f"Environmental hazard reported: {contact.get('from', 'Unknown')}",
                "warning"
            )
            new_alerts.append(alert)

        # Save new alerts
        for alert in new_alerts:
            self.alerts.append(alert)

        self._save_alerts()
        return new_alerts

    def _create_alert(self, contact, alert_type, message, severity):
        """Create an alert object."""
        return {
            "id": len(self.alerts) + 1,
            "type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "contact_id": contact.get("id"),
            "coordinates": contact.get("coordinates", []),
            "from": contact.get("from", "Unknown"),
            "dtg": contact.get("dtg", contact.get("date", "")),
            "acknowledged": False
        }

    def get_active_alerts(self):
        """Get all unacknowledged alerts."""
        return [a for a in self.alerts if not a.get("acknowledged", False)]

    def get_all_alerts(self):
        """Get all alerts."""
        return self.alerts

    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                self._save_alerts()
                return True
        return False

    def get_alert_summary(self):
        """Get summary of alert counts by severity."""
        active = self.get_active_alerts()
        return {
            "total": len(active),
            "critical": len([a for a in active if a["severity"] == "critical"]),
            "warning": len([a for a in active if a["severity"] == "warning"]),
            "info": len([a for a in active if a["severity"] == "info"])
        }

    def clear_alerts(self):
        """Clear all alerts (for reprocessing)."""
        self.alerts = []
        self._save_alerts()


# Global alert engine instance
alert_engine = AlertEngine()
