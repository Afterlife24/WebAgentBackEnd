# Import OS module for file access
import os

# Import SentenceTransformer for semantic search
from sentence_transformers import SentenceTransformer, util

# Global variables for model, embeddings, and text sections
MODEL = None
SECTION_EMBEDDINGS = None
SECTIONS = None

# Function to get the most relevant answer from the knowledge base using semantic search
def get_kb_answer(query: str) -> str:
    global MODEL, SECTION_EMBEDDINGS, SECTIONS

    # Lazy-load model and knowledge base only on first use
    if MODEL is None:
        from tqdm import tqdm  # For progress bar during embedding generation
        print("Initializing knowledge base...")

        # Read knowledge base content from the file
        kb_path = os.path.join(os.path.dirname(__file__), "KnowledgeBase.md")
        with open(kb_path, "r", encoding="utf-8") as f:
            KB_TEXT = f.read()

        # Split the KB text into sections separated by double newlines
        SECTIONS = KB_TEXT.split("\n\n")

        # Load pre-trained sentence transformer model for embeddings
        MODEL = SentenceTransformer("all-MiniLM-L6-v2")

        # Generate embeddings for each section of the KB
        SECTION_EMBEDDINGS = MODEL.encode(SECTIONS, convert_to_tensor=True, show_progress_bar=True)

    # Encode the user's query into a semantic embedding
    query_embedding = MODEL.encode(query, convert_to_tensor=True)

    # Perform semantic search to find the closest matching section
    hits = util.semantic_search(query_embedding, SECTION_EMBEDDINGS, top_k=1)

    # If no results found, return fallback message
    if not hits or not hits[0]:
        return "I'm sorry, I couldn't find an answer for that."

    # Extract the best match using corpus_id
    best_match = hits[0][0]

    # Return the matching section from the knowledge base
    return SECTIONS[best_match["corpus_id"]]
