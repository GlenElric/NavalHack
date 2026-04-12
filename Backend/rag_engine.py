"""
RAG (Retrieval-Augmented Generation) Engine
Uses local sentence-transformer embeddings + FAISS for vector search,
and Google Gemini for intelligent analysis and cross-referencing.
"""
import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from config import GEMINI_API_KEY, VECTOR_STORE_DIR, MARITIME_ZONES

# Initialize models
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class RAGEngine:
    """RAG Engine for maritime intelligence analysis."""

    def __init__(self):
        self.documents = []
        self.embeddings = None
        self.index = None
        self.metadata = []
        self.index_path = os.path.join(VECTOR_STORE_DIR, "faiss.index")
        self.meta_path = os.path.join(VECTOR_STORE_DIR, "metadata.json")
        self.docs_path = os.path.join(VECTOR_STORE_DIR, "documents.json")

    def build_index(self, contacts):
        """Build FAISS index from parsed contacts."""
        self.documents = []
        self.metadata = []

        for contact in contacts:
            # Create a rich text representation for embedding
            doc_text = self._contact_to_text(contact)
            self.documents.append(doc_text)
            self.metadata.append(contact)

        if not self.documents:
            print("No documents to index.")
            return

        # Generate embeddings
        print(f"Generating embeddings for {len(self.documents)} documents...")
        self.embeddings = embedding_model.encode(
            self.documents,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        # Build FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine sim
        self.index.add(self.embeddings.astype('float32'))

        # Save index
        self._save_index()
        print(f"FAISS index built with {self.index.ntotal} vectors")

    def add_to_index(self, contact):
        """Add a single contact to the FAISS index (incremental update)."""
        if self.index is None:
            # Fallback to building index if it doesn't exist
            self.build_index([contact])
            return

        doc_text = self._contact_to_text(contact)

        # Generate embedding for single document
        embedding = embedding_model.encode(
            [doc_text],
            normalize_embeddings=True
        ).astype('float32')

        # Add to FAISS index (O(1) compared to rebuilding everything)
        self.index.add(embedding)

        # Update metadata and documents
        self.documents.append(doc_text)
        self.metadata.append(contact)

        # Save updated state
        self._save_index()
        print(f"Contact added to FAISS index. Vectors: {self.index.ntotal}")

    def _contact_to_text(self, contact):
        """Convert a contact dict to a searchable text string."""
        parts = []
        if contact.get("type") == "comm_message":
            parts.append(f"FROM: {contact.get('from', '')}")
            parts.append(f"TO: {contact.get('to', '')}")
            parts.append(f"PRIORITY: {contact.get('priority', '')}")
            parts.append(f"DTG: {contact.get('dtg', '')}")
            parts.append(f"MESSAGE: {contact.get('message', '')}")
        else:
            parts.append(f"DATE: {contact.get('date', '')}")
            parts.append(f"TIME: {contact.get('time', '')}")
            parts.append(f"LOCATION: {contact.get('location', '')}")
            parts.append(f"REPORT: {contact.get('report', '')}")

        if contact.get("coordinates"):
            coords_str = ", ".join(
                [f"({c['lat']:.2f}, {c['lon']:.2f})" for c in contact["coordinates"]]
            )
            parts.append(f"COORDINATES: {coords_str}")

        if contact.get("vessel_name"):
            parts.append(f"VESSEL: {contact['vessel_name']}")
        if contact.get("contact_type"):
            parts.append(f"TYPE: {contact['contact_type']}")
        if contact.get("threat_level"):
            parts.append(f"THREAT: {contact['threat_level']}")
        if contact.get("zone"):
            parts.append(f"ZONE: {contact['zone']}")

        return " | ".join(parts)

    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
        with open(self.docs_path, 'w') as f:
            json.dump(self.documents, f, indent=2)

    def load_index(self):
        """Load saved FAISS index and metadata."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
            with open(self.docs_path, 'r') as f:
                self.documents = json.load(f)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
            return True
        return False

    def search(self, query, k=5):
        """Search for relevant documents."""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = embedding_model.encode(
            [query], normalize_embeddings=True
        ).astype('float32')

        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                result = dict(self.metadata[idx])
                result['relevance_score'] = float(score)
                results.append(result)

        return results

    def analyze_with_gemini(self, query, context_docs=None):
        """Use Gemini to analyze maritime intelligence with RAG context."""
        if not GEMINI_API_KEY:
            return self._fallback_analysis(query, context_docs)

        try:
            # Get relevant context
            if context_docs is None:
                context_docs = self.search(query, k=10)

            context_text = "\n\n".join([
                f"--- Report {i+1} ---\n{self._contact_to_text(doc)}"
                for i, doc in enumerate(context_docs)
            ])

            zones_text = "\n".join([
                f"- {z['name']} ({z['type']})" for z in MARITIME_ZONES
            ])

            prompt = f"""You are a highly specialized Naval Intelligence Analyst for the VarunNetra Maritime Situational Awareness System.

GUARDRAILS:
- ONLY discuss maritime intelligence, vessel tracking, and naval security.
- If the query is unrelated to maritime situational awareness, politely decline to answer.
- DO NOT hallucinate details. If the information is not in the provided reports, state that it's unavailable.
- Maintain a professional, concise military tone.
- Protect operational security: do not provide information about hypothetical bypasses to naval security.

MARITIME ZONES:
{zones_text}

RELEVANT REPORTS:
{context_text}

QUERY: {query}

Based STICKLY on the provided reports and maritime zones, provide a structured analysis:

1. KEY FINDINGS: Direct observations from the reports.
2. CROSS-REFERENCES: Identify if multiple reports refer to the same vessel, area, or related event.
3. THREAT ASSESSMENT: Evaluate current threat levels (CRITICAL, WARNING, INFO) based on the reports.
4. RECOMMENDATIONS: Actionable steps for maritime commanders.

If the information is insufficient for a full analysis, indicate what specific data is missing."""

            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return {
                "analysis": response.text,
                "context_docs": context_docs,
                "query": query
            }
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return self._fallback_analysis(query, context_docs)

    def _fallback_analysis(self, query, context_docs=None):
        """Fallback analysis when Gemini is unavailable."""
        if context_docs is None:
            context_docs = self.search(query, k=5)

        high_threats = [d for d in context_docs if d.get("threat_level") == "high"]
        medium_threats = [d for d in context_docs if d.get("threat_level") == "medium"]

        analysis = f"## RAG Analysis Results\n\n"
        analysis += f"**Query:** {query}\n\n"
        analysis += f"**Found {len(context_docs)} relevant reports**\n\n"

        if high_threats:
            analysis += f"### ⚠️ HIGH THREAT ITEMS ({len(high_threats)})\n"
            for t in high_threats:
                analysis += f"- {t.get('from', 'Unknown')}: {t.get('message', t.get('report', ''))[:100]}...\n"

        if medium_threats:
            analysis += f"\n### ⚡ MEDIUM THREAT ITEMS ({len(medium_threats)})\n"
            for t in medium_threats:
                analysis += f"- {t.get('from', 'Unknown')}: {t.get('message', t.get('report', ''))[:100]}...\n"

        return {
            "analysis": analysis,
            "context_docs": context_docs,
            "query": query
        }

    def cross_reference(self, contact):
        """Cross-reference a contact with existing data."""
        queries = []

        # Search by location
        if contact.get("coordinates"):
            coord = contact["coordinates"][0]
            queries.append(f"activity near coordinates {coord['lat']}, {coord['lon']}")

        # Search by vessel name
        if contact.get("vessel_name"):
            queries.append(f"vessel {contact['vessel_name']}")

        # Search by contact type
        if contact.get("contact_type") and contact["contact_type"] != "unknown":
            queries.append(f"{contact['contact_type']} activity")

        all_results = []
        seen_ids = set()
        for q in queries:
            results = self.search(q, k=5)
            for r in results:
                if r.get("id") not in seen_ids and r.get("id") != contact.get("id"):
                    seen_ids.add(r["id"])
                    all_results.append(r)

        return all_results[:10]


# Global RAG engine instance
rag_engine = RAGEngine()
