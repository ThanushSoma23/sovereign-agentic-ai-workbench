from sentence_transformers import SentenceTransformer, CrossEncoder

from config import EMBEDDING_MODEL, RERANKER_MODEL


class LocalEmbeddings:

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def embed_documents(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True
        ).tolist()

    def embed_query(self, text):
        return self.model.encode(
            text,
            normalize_embeddings=True
        ).tolist()


def get_embeddings():
    return LocalEmbeddings()


def get_reranker():
    return CrossEncoder(RERANKER_MODEL)