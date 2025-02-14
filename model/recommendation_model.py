from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sqlalchemy import text
from config.config import *
from utils.exception import CustomException
from utils.logger import logging
import sys
import psycopg2
from langchain.schema import Document
from psycopg2.extras import DictCursor


class RecommendationModel:
    def __init__(self):
        try:
            self.embed_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
            self.vectordb_file_path = "./faiss_index"
            self.vector_store = FAISS.load_local(self.vectordb_file_path, self.embed_model, allow_dangerous_deserialization=True)
            
            self.connection = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                port=POSTGRES_PORT
            )
            self.cursor = self.connection.cursor(cursor_factory=DictCursor)
        except Exception as e:
            logging.info(f"Error while connecting to PostgreSQL or loading faiss index: {e}")
            raise CustomException(e, sys)
        

    def get_recommendations(self, username):
        try:
            # Get user profile data from PostgreSQL
            query = ("""
                SELECT uP.location, uP.interest
                FROM user_profile uP
                JOIN user_db uD ON uP.user_id = uD.id
                WHERE uD.username = username;
            """)
            logging.info(f"Querying user profile: {query} for recommendations")
            self.cursor.execute(query, {"username": username})
            result = self.cursor.fetchone()
            logging.info(f"User profile {result}")
            
            if not result:
                return {"error": "User profile not found"}, 404
                
            # Format query string similar to training data
            city, interests = result
            query_string = f"{result} has city {city} and love {interests}"
            logging.info(f"Query string for FAISS: {query_string}")

            
            # Get recommendations using FAISS similarity search
            self.cursor.execute("""
                SELECT uD.username AS user_id, uP.location, uP.interest
                FROM user_profile uP
                JOIN user_db uD ON uP.user_id = uD.id;
            """)

            users = self.cursor.fetchall()
            documents = []

            # Convert user data to FAISS-compatible format
            for user in users:
                username, city, interests = user  # Extract data

                if city and interests:  # Ensure data is not null
                    doc = Document(
                        page_content=f"{username} is from {city} and loves {interests}.",
                        metadata={
                            "username": username,
                            "city": city,
                            "interests": interests
                        }
                    )
                    documents.append(doc)
            
            logging.info(f"documents for FAISS: {documents}")

            # Store documents in FAISS
            vector_store = FAISS.from_documents(documents, self.embed_model)
            vector_store.save_local("./faiss_index")
            results = self.vector_store.similarity_search(query_string)
            logging.info(f"FAISS search results: {results}")  

            
            # Format recommendations
            recommendations = []
            for res in results:
                metadata = res.metadata
                logging.info(f"metadata for recommendation: {metadata}")
                recommendations.append({
                    "user_id": metadata.get("user_id"),
                    "city": metadata.get("city"),
                    "interests": metadata.get("interests"),
                    "similarity_score": metadata.get("score", 0)
                })
            
            return {"recommendations": recommendations}, 200
            
        except Exception as e:
            return {"error": str(e)}, 500 