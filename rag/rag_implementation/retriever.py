from langchain_chroma import Chroma

from models import get_embeddings, get_reranker

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    RETRIEVAL_K,
    FINAL_K,
    RERANK_THRESHOLD
)


embeddings = get_embeddings()

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings
)

reranker = get_reranker()


def retrieve_documents(query, filters=None):

    documents = vectorstore.similarity_search(
        query,
        k=RETRIEVAL_K
    )

    if filters:

        filtered_documents = []

        for doc in documents:

            match = True

            for key, value in filters.items():

                if str(doc.metadata.get(key)) != str(value):
                    match = False
                    break

            if match:
                filtered_documents.append(doc)

        documents = filtered_documents

    if not documents:

        return {
            "status": "missing_knowledge",
            "query": query,
            "evidence": [],
            "message": "No relevant information was found in the local knowledge base."
        }

    pairs = []

    for doc in documents:

        pairs.append([
            query,
            doc.page_content
        ])

    scores = reranker.predict(pairs)

    ranked_documents = []

    for doc, score in zip(documents, scores):

        ranked_documents.append(
            {
                "document": doc.metadata.get("document"),
                "page": doc.metadata.get("page"),
                "section": doc.metadata.get("section"),
                "content": doc.page_content,
                "rerank_score": float(score),
                "source_type": "local"
            }
        )

    ranked_documents.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    ranked_documents = ranked_documents[:FINAL_K]

    if ranked_documents[0]["rerank_score"] < RERANK_THRESHOLD:

        return {
            "status": "missing_knowledge",
            "query": query,
            "evidence": [],
            "message": "The local knowledge base does not contain sufficiently relevant information."
        }

    return {
        "status": "success",
        "query": query,
        "evidence": ranked_documents
    }