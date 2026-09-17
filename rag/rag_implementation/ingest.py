import os
import pymupdf
import shutil

from langchain_core.documents import Document
from langchain_chroma import Chroma

from chunking import split_text
from models import get_embeddings

from config import DOCUMENT_DIR, CHROMA_DIR, COLLECTION_NAME


def load_pdfs():

    documents = []

    for file_name in os.listdir(DOCUMENT_DIR):

        if not file_name.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(DOCUMENT_DIR, file_name)

        print("Loading:", file_name)

        pdf = pymupdf.open(file_path)

        for page_number, page in enumerate(pdf):

            text = page.get_text()

            if not text.strip():
                continue

            chunks = split_text(text)

            for chunk in chunks:

                document = Document(
                    page_content=chunk,
                    metadata={
                        "document": file_name,
                        "page": page_number + 1,
                        "section": "Unknown",
                        "source_type": "local"
                    }
                )

                documents.append(document)

        pdf.close()

    return documents


def create_database():

    documents = load_pdfs()

    print("Total chunks:", len(documents))

    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)

    embeddings = get_embeddings()

    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )

    print("Knowledge base created successfully")


if __name__ == "__main__":
    create_database()