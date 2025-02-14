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
            query = """
                SELECT up.location, up.interest
                FROM user_profile up
                JOIN user_db ud ON up.user_id = ud.id
                WHERE ud.username = %s;
            """
            logging.info(f"Querying user profile for username: {username}")
            self.cursor.execute(query, (username,))
            result = self.cursor.fetchone()
            logging.info(f"User profile found: {result}")
            
            if not result:
                return {"error": "User profile not found"}, 404
                
            # Format query string similar to training data
            city, interests = result['location'], result['interest']
            
            # Convert list to comma-separated string if needed
            if isinstance(interests, (list, set)):
                interests = ', '.join(interests)
            query_string = f"user has city {city} and love {interests}"
            logging.info(f"Query string for FAISS: {query_string}")
            
            # Get all users for recommendations
            self.cursor.execute("""
                SELECT ud.username, up.location, up.interest
                FROM user_profile up
                JOIN user_db ud ON up.user_id = ud.id
                WHERE ud.username != %s;
            """, (username,))

            users = self.cursor.fetchall()
            logging.info(f"Found {len(users)} users for recommendations")
            documents = []

            # Convert user data to FAISS-compatible format
            for user in users:
                user_username = user['username']
                user_city = user['location']
                user_interests = user['interest']

                if user_city and user_interests:  # Ensure data is not null
                    doc = Document(
                        page_content=f"user has city {user_city} and love {user_interests}",
                        metadata={
                            "username": user_username,
                            "city": user_city,
                            "interests": user_interests
                        }
                    )
                    documents.append(doc)
            
            logging.info(f"Created {len(documents)} documents for FAISS")

            # Create and save vector store
            vector_store = FAISS.from_documents(documents, self.embed_model)
            results = vector_store.similarity_search_with_score(query_string, k=len(documents))
            logging.info(f"Found {len(results)} similar users")
            
            # Format recommendations
            recommendations = []
            for doc, score in results:
                metadata = doc.metadata
                recommendations.append({
                    "username": metadata["username"],
                    "city": metadata["city"],
                    "interests": metadata["interests"],
                    "similarity_score": round(1 - score, 3)  # Convert distance to similarity score
                })
            
            return {"recommendations": recommendations}, 200
            
        except Exception as e:
            logging.error(f"Error in get_recommendations: {str(e)}")
            return {"error": str(e)}, 500 