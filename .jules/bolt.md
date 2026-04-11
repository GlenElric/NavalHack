## 2026-04-11 - [RAG Indexing Inefficiency]
**Learning:** Rebuilding a FAISS index from scratch for every single document addition is an O(N^2) bottleneck over time because each addition triggers re-encoding of the entire existing corpus using heavy transformer models.
**Action:** Implement incremental indexing by encoding only the new document and appending it to the existing FAISS index, keeping metadata in sync.

## 2026-04-11 - [OCR Model Reload Overhead]
**Learning:** Initializing heavy ML models (like EasyOCR) inside function calls causes massive latency spikes due to repeated disk I/O and memory allocation for model weights.
**Action:** Move model initialization to the module level or a singleton pattern to ensure models are loaded once.
