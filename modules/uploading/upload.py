from sqlalchemy import  text
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession


def cosine_sim(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    '''Cosine similarity between `query_vec` and each row of `doc_matrix`.'''
    q = query_vec / (np.linalg.norm(query_vec) + 1e-12)
    d = doc_matrix / (np.linalg.norm(doc_matrix) + 1e-12)
    return d @ q

class RetrievalService:

    def __init__(self, model:str,target:str = "Experiences"):
        self.model = model
        self.target = target

    
    async def retrieve(self, username: str, session: AsyncSession, retrieval_vector: list[float]):
        statement = text(f"""
                    select A.title,content, 1-(A.embedding <=> '{retrieval_vector}') as similarity
                    FROM "{self.target}" AS A
                    LEFT JOIN alice AS C
                        ON A.user_id = C.user_id
                    WHERE C.name ILIKE '{username}' 
                    AND 1-(A.embedding <=> '{retrieval_vector}') > 0
                    order by 1-(A.embedding <=> '{retrieval_vector}') desc
                    limit 3
                """)    
        experiences_task = await session.execute(statement, {"retrieval_vector": retrieval_vector, "username": username, "target": self.target})
        best_experiences = experiences_task.fetchall()
        json_results = [
            {
                "title": row[0],
                "description": row[1],
                "score": row[2]
            }
            for row in best_experiences
        ]
        return json_results


