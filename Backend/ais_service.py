"""
AIS Data Service
Connects to aisstream.io to pull real-time maritime data.
"""
import asyncio
import json
import threading
import websockets
from datetime import datetime

class AISService:
    def __init__(self, api_key=None, callback=None):
        self.api_key = api_key
        self.callback = callback
        self.running = False
        self.thread = None
        self.loop = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_ais_stream())

    async def _connect_ais_stream(self):
        if not self.api_key:
            print("AIS Stream: No API Key provided. Real-time data will not be available.")
            # Use simulation if no API key
            await self._run_simulation()
            return

        url = "wss://stream.aisstream.io/v0/stream"
        while self.running:
            try:
                async with websockets.connect(url) as websocket:
                    subscribe_message = {
                        "APIKey": self.api_key,
                        "BoundingBoxes": [[[-15, -75], [20, -65]]], # Caribbean region as per project context
                    }
                    await websocket.send(json.dumps(subscribe_message))

                    async for message in websocket:
                        if not self.running:
                            break

                        data = json.loads(message)
                        if self.callback:
                            self.callback(self._parse_ais_message(data))
            except Exception as e:
                print(f"AIS Stream Error: {e}")
                await asyncio.sleep(10) # Wait before reconnecting

    def _parse_ais_message(self, data):
        """Standardize AIS message format for the application."""
        # This is a placeholder, will need to be refined based on actual aisstream.io output
        message_type = data.get("MessageType")
        meta = data.get("MetaData", {})
        payload = data.get("Message", {}).get(message_type, {})

        mmsi = meta.get("MMSI")
        ship_name = meta.get("ShipName", "").strip() or f"MMSI {mmsi}"

        lat = meta.get("latitude")
        lon = meta.get("longitude")

        # Determine threat level and type (basic for now)
        from data_parser import classify_contact_type, classify_threat_level

        text_for_classification = f"{ship_name} {message_type}"
        contact_type = classify_contact_type(text_for_classification)
        threat_level = classify_threat_level(text_for_classification)

        return {
            "id": f"ais-{mmsi}-{datetime.now().timestamp()}",
            "from": ship_name,
            "mmsi": mmsi,
            "contact_type": contact_type,
            "threat_level": threat_level,
            "coordinates": [{"lat": lat, "lon": lon}] if lat and lon else [],
            "dtg": datetime.now().strftime("%Y%m%d%H%M%S"),
            "message": f"AIS {message_type} received for {ship_name}",
            "type": "ais_update",
            "speed": payload.get("Sog"),
            "bearing": payload.get("Cog")
        }

    async def _run_simulation(self):
        """Simulate AIS data if no API key is provided."""
        import random
        print("AIS Stream: Running in simulation mode.")

        vessels = [
            {"mmsi": "211476060", "name": "CARGO EXPLORER", "type": "merchant"},
            {"mmsi": "368207620", "name": "SEA PATROL 7", "type": "warship"},
            {"mmsi": "367719770", "name": "BLUEFIN", "type": "fishing"},
            {"mmsi": "123456789", "name": "MYSTERY VESSEL", "type": "unknown"}
        ]

        # Base coordinates in Caribbean
        base_lat = 13.0
        base_lon = -71.0

        for v in vessels:
            v["lat"] = base_lat + random.uniform(-1, 1)
            v["lon"] = base_lon + random.uniform(-1, 1)

        while self.running:
            for v in vessels:
                # Move slightly
                v["lat"] += random.uniform(-0.01, 0.01)
                v["lon"] += random.uniform(-0.01, 0.01)

                # Randomize speed/bearing
                v["speed"] = random.randint(5, 25)
                v["bearing"] = random.randint(0, 359)

                update = {
                    "id": f"ais-sim-{v['mmsi']}-{int(datetime.now().timestamp())}",
                    "from": v["name"],
                    "mmsi": v["mmsi"],
                    "contact_type": v["type"],
                    "threat_level": "high" if v["type"] == "unknown" else "low",
                    "coordinates": [{"lat": v["lat"], "lon": v["lon"]}],
                    "dtg": datetime.now().strftime("%d%H%MZ %b %y").upper(),
                    "message": f"Simulated AIS update for {v['name']}",
                    "type": "ais_update",
                    "speed": v["speed"],
                    "bearing": v["bearing"]
                }

                if self.callback:
                    self.callback(update)

                await asyncio.sleep(2) # Send update every 2 seconds
            await asyncio.sleep(5)
