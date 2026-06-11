import os
import glob
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

print("🧠 Loading local sentence-transformers model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
print(f"📡 Connecting to Qdrant at {qdrant_url}...")
client = QdrantClient(url=qdrant_url)

COLLECTION_NAME = "compliance_rules"

print(f"🛠️ Creating/Resetting Qdrant collection: '{COLLECTION_NAME}'...")
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

chunks = []

# --- 1. PARSE OWASP API TOP 10 (Markdown) ---
print("📖 Parsing OWASP API Top 10 Markdown files...")
for filepath in glob.glob("corpus/raw/owasp-api-*.md"):
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = content.split("\n## ")
    title = sections[0].replace("#", "").strip()
    
    for sec in sections[1:]:
        lines = sec.split("\n")
        sec_title = lines[0].strip()
        sec_body = "\n".join(lines[1:]).strip()
        if len(sec_body) > 50:
            chunks.append({
                "source": "OWASP_API_TOP_10",
                "file": filename,
                "title": f"{title} - {sec_title}",
                "text": f"Category: {title}\nSection: {sec_title}\n\n{sec_body}"
            })

# --- 2. PARSE OWASP ASVS (CSV) ---
print("📊 Parsing OWASP ASVS 4.0.3 CSV...")
asvs_path = "corpus/raw/owasp-asvs-4.0.3.csv"
if os.path.exists(asvs_path):
    try:
        df = pd.read_csv(asvs_path, encoding="utf-8")
        desc_col = [col for col in df.columns if "desc" in col.lower() or "requirement" in col.lower()]
        id_col = [col for col in df.columns if "id" in col.lower() or "item" in col.lower() or "short" in col.lower()]
        
        col_text = desc_col[0] if desc_col else df.columns[2]
        col_id = id_col[0] if id_col else df.columns[0]
        
        for _, row in df.iterrows():
            text_val = str(row[col_text]).strip()
            id_val = str(row[col_id]).strip()
            if len(text_val) > 20 and text_val.lower() != "nan":
                chunks.append({
                    "source": "OWASP_ASVS",
                    "file": "owasp-asvs-4.0.3.csv",
                    "title": f"ASVS Requirement {id_val}",
                    "text": f"ASVS ID: {id_val}\nRequirement: {text_val}"
                })
    except Exception as e:
        print(f"⚠️ Error parsing ASVS CSV via pandas: {e}. Falling back to line parser.")
        with open(asvs_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 0 and len(line.strip()) > 20:
                    chunks.append({
                        "source": "OWASP_ASVS",
                        "file": "owasp-asvs-4.0.3.csv",
                        "title": f"ASVS Line {i}",
                        "text": line.strip()
                    })

# --- 3. PARSE ZALANDO GUIDELINES (AsciiDoc) ---
print("📐 Parsing Zalando REST Guidelines AsciiDoc files...")
for filepath in glob.glob("corpus/raw/zalando-*.adoc"):
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = content.split("\n===")
    for sec in sections:
        sec = sec.strip()
        if not sec: continue
        lines = sec.split("\n")
        sec_title = lines[0].strip()
        sec_body = "\n".join(lines[1:]).strip()
        if len(sec_body) > 50:
            chunks.append({
                "source": "ZALANDO_GUIDELINES",
                "file": filename,
                "title": f"Zalando Guidelines - {sec_title}",
                "text": f"Chapter: {filename.replace('zalando-', '').replace('.adoc', '')}\nSection: {sec_title}\n\n{sec_body}"
            })

print(f"✅ Extraction finished! Total generated rule chunks: {len(chunks)}")

# --- 4. EMBED AND UPUSERT TO QDRANT ---
print(f"🚀 Vectorizing chunks and seeding Qdrant collection '{COLLECTION_NAME}'...")
points = []
for idx, chunk in enumerate(chunks):
    vector = model.encode(chunk["text"]).tolist()
    points.append(PointStruct(id=idx, vector=vector, payload=chunk))

BATCH_SIZE = 50
for i in range(0, len(points), BATCH_SIZE):
    batch = points[i:i+BATCH_SIZE]
    client.upsert(collection_name=COLLECTION_NAME, points=batch)
    print(f"   📥 Pushed chunks {i} to {i+len(batch)} into Qdrant...")

print("\n🎯 DATABASE SEEDING COMPLETE! Your Vector Database is fully populated.")
