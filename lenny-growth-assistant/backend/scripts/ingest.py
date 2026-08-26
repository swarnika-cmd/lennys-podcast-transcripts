import os
import re
import glob
import json
import yaml
import requests
import psycopg2
from psycopg2.extras import execute_values

# --- Config ---
TRANSCRIPT_REPO_PATH = os.environ.get("TRANSCRIPT_REPO_PATH", "..")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/embeddings")
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5435"),
    "dbname": os.environ.get("POSTGRES_DB", "lennys_podcast"),
    "user": os.environ.get("POSTGRES_USER", "lenny"),
    "password": os.environ.get("POSTGRES_PASSWORD", "lenny_password"),
}

# Your curated subset from index/growth-strategy.md and index/product-market-fit.md
SELECTED_GUESTS = [
    "adam-fishman",
    "archie-abrams",
    "bangaly-kaba",
    "brian-chesky",
    "casey-winters",
    "elena-verna-40",
    "melissa-tan",
    "sri-batchu",
    "yuriy-timen",
    "brian-balfour",
    "dan-hockenmaier",
    "eli-schwartz",
    "emily-kramer",
    "hila-qu",
    "nikita-bier",
    "nilan-peiris",
    "noah-weiss",
    "noam-lovinsky",
    "sean-ellis",
    "shishir-mehrotra",
    "dalton-caldwell",
    "mike-maples-jr",
    "naomi-gleit"
]


def read_transcript(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---")
    if len(parts) >= 3:
        frontmatter = yaml.safe_load(parts[1])
        transcript = "---".join(parts[2:]).strip()
        return frontmatter, transcript
    return {}, content


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def embed_chunk(text):
    resp = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": text})
    resp.raise_for_status()
    return resp.json()["embedding"]


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total_inserted = 0

    for guest_folder in SELECTED_GUESTS:
        filepath = os.path.join(TRANSCRIPT_REPO_PATH, "episodes", guest_folder, "transcript.md")
        if not os.path.exists(filepath):
            print(f"[SKIP] Not found: {filepath}")
            continue

        frontmatter, transcript = read_transcript(filepath)
        video_id = frontmatter.get("video_id", guest_folder)
        guest = frontmatter.get("guest", "")
        title = frontmatter.get("title", "")
        youtube_url = frontmatter.get("youtube_url", "")
        episode_metadata = json.dumps({
            "publish_date": str(frontmatter.get("publish_date", "")),
            "duration": frontmatter.get("duration", ""),
        })

        chunks = chunk_text(transcript)
        print(f"[{guest_folder}] {len(chunks)} chunks")

        rows = []
        for idx, chunk in enumerate(chunks):
            try:
                embedding = embed_chunk(chunk)
            except Exception as e:
                print(f"  [EMBED ERROR] chunk {idx}: {e}")
                continue
            rows.append((video_id, idx, chunk, embedding, guest, title, youtube_url, episode_metadata))

        if rows:
            execute_values(
                cur,
                """
                INSERT INTO transcript_chunks
                    (video_id, chunk_index, chunk_text, embedding, guest, title, youtube_url, episode_metadata)
                VALUES %s
                ON CONFLICT (video_id, chunk_index) DO NOTHING
                """,
                rows,
            )
            conn.commit()
            total_inserted += len(rows)

    cur.close()
    conn.close()
    print(f"\nDone. Inserted/attempted {total_inserted} chunks.")


if __name__ == "__main__":
    main()