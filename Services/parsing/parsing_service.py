from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        self.model:str = "thenlper/gte-small"


    async def embed(self, text: str):
        '''commentaire'''
        model = SentenceTransformer(self.model)
        embeddings = model.encode([text])
        return embeddings[0].tolist()
