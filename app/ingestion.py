from pathlib import Path
import hashlib
import json
import re

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.vector_store import collection


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS_PATH = PROJECT_ROOT / "data" / "documents"
PARENTS_PATH = PROJECT_ROOT / "data" / "parents.json"


parent_record = {}


parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=40
)

child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=40
)


def cleaning(text):
    text = text.replace("â€", "'")
    text = text.replace("â€œ", '"')

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def load_parent_records():
    global parent_record

    if PARENTS_PATH.exists():
        with open(PARENTS_PATH, "r", encoding="utf-8") as file:
            parent_record = json.load(file)
    else:
        parent_record = {}


def save_parent_records():
    with open(PARENTS_PATH, "w", encoding="utf-8") as file:
        json.dump(
            parent_record,
            file,
            ensure_ascii=False,
            indent=2
        )


def create_id(*values):
    raw_value = "|".join(str(value) for value in values)

    return hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()


def ingest():
    load_parent_records()

    child_ids = []
    child_documents = []
    child_metadatas = []

    pdf_files = list(DOCUMENTS_PATH.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files:

        print(f"Processing: {pdf_file.name}")

        pdf_document = pymupdf.open(pdf_file)

        for page_number, page in enumerate(pdf_document):

            raw_text = page.get_text()

            cleaned_text = cleaning(raw_text)

            if not cleaned_text:
                continue

            parent_chunks = parent_splitter.split_text(
                cleaned_text
            )

            for parent_index, parent_chunk in enumerate(parent_chunks):

                parent_id = create_id(
                    pdf_file.name,
                    page_number + 1,
                    parent_index
                )

                parent_record[parent_id] = {
                    "text": parent_chunk,
                    "source": pdf_file.name,
                    "page": page_number + 1
                }

                child_chunks = child_splitter.split_text(
                    parent_chunk
                )

                for child_index, child_chunk in enumerate(child_chunks):

                    child_id = create_id(
                        parent_id,
                        child_index
                    )

                    metadata = {
                        "source": pdf_file.name,
                        "page": page_number + 1,
                        "parent_id": parent_id,
                        "parent_index": parent_index,
                        "child_index": child_index
                    }

                    child_ids.append(child_id)
                    child_documents.append(child_chunk)
                    child_metadatas.append(metadata)

        pdf_document.close()

    if child_ids:
        collection.upsert(
            ids=child_ids,
            documents=child_documents,
            metadatas=child_metadatas
        )

    save_parent_records()

    print()
    print("Ingestion complete.")
    print(f"Parents stored: {len(parent_record)}")
    print(f"Children processed: {len(child_ids)}")
    print(f"Chroma records: {collection.count()}")


if __name__ == "__main__":
    ingest()