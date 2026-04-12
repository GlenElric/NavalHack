## 2026-04-11 - [RAG Indexing Inefficiency]
**Learning:** Rebuilding a FAISS index from scratch for every single document addition is an O(N^2) bottleneck over time because each addition triggers re-encoding of the entire existing corpus using heavy transformer models.
**Action:** Implement incremental indexing by encoding only the new document and appending it to the existing FAISS index, keeping metadata in sync.

## 2026-04-11 - [OCR Model Reload Overhead]
**Learning:** Initializing heavy ML models (like EasyOCR) inside function calls causes massive latency spikes due to repeated disk I/O and memory allocation for model weights.
**Action:** Move model initialization to the module level or a singleton pattern to ensure models are loaded once.

## 2026-04-12 - [Redundant Bounding Box Calculations]
**Learning:** Recalculating the bounding box (min/max lat/lon) for maritime zones on every `determine_zone` call is an O(N*M) bottleneck, where N is the number of contacts and M is the number of zones.
**Action:** Implement lazy bounding box caching on the zone objects to achieve O(1) coordinate-to-box checks after the first calculation, resulting in a ~4.5x speedup.
