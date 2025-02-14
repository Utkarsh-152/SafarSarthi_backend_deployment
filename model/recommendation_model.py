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
import json


class RecommendationModel:
    DEFAULT_RECOMMENDATION_LIMIT = 50  # Fixed limit for recommendations
    
    def __init__(self):
        try:
            self.embed_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2"
            )            
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
    
    def get_user_id(self, username):
        """Get user ID from username"""
        try:
            query = "SELECT id FROM user_db WHERE username = %s"
            self.cursor.execute(query, (username,))
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except Exception as e:
            logging.error(f"Error getting user ID for username {username}: {str(e)}")
            return None
    
    def store_recommendations(self, username, recommendations):
        try:
            # Get user_id for the current user
            user_id = self.get_user_id(username)
            if not user_id:
                logging.error(f"User ID not found for username: {username}")
                return False
            
            # First, delete existing recommendations for this user
            delete_query = """
                DELETE FROM user_recommendation_entries 
                WHERE user_id = %s;
            """
            self.cursor.execute(delete_query, (user_id,))
            
            # Insert new recommendations
            insert_query = """
                INSERT INTO user_recommendation_entries 
                (user_id, recommended_user_id, similarity_score, rank)
                VALUES (%s, %s, %s, %s);
            """
            
            for idx, rec in enumerate(recommendations):
                recommended_user_id = self.get_user_id(rec['username'])
                if recommended_user_id:
                    self.cursor.execute(
                        insert_query, 
                        (
                            user_id, 
                            recommended_user_id, 
                            rec['similarity_score'],
                            idx + 1  # rank starts from 1
                        )
                    )
            
            self.connection.commit()
            logging.info(f"Stored recommendations for user: {username}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing recommendations: {str(e)}")
            self.connection.rollback()
            return False
        
    def get_recommendations(self, username):
        try:
            # Get user profile data from PostgreSQL
            query = """
                SELECT up.location, up.interest, ud.id as user_id
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
                SELECT ud.username, ud.id, up.location, up.interest
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
                user_id = user['id']

                if user_city and user_interests:  # Ensure data is not null
                    doc = Document(
                        page_content=f"user has city {user_city} and love {user_interests}",
                        metadata={
                            "username": user_username,
                            "user_id": user_id,
                            "city": user_city,
                            "interests": user_interests
                        }
                    )
                    documents.append(doc)
            
            logging.info(f"Created {len(documents)} documents for FAISS")

            # Create and save vector store
            vector_store = FAISS.from_documents(documents, self.embed_model)
            # Get top N most similar users (N = min(DEFAULT_LIMIT, total_users))
            k = min(self.DEFAULT_RECOMMENDATION_LIMIT, len(documents))
            results = vector_store.similarity_search_with_score(query_string, k=k)
            logging.info(f"Found top {k} similar users out of {len(documents)} total users")
            
            # Format recommendations and sort by similarity score
            recommendations = []
            for doc, score in results:
                metadata = doc.metadata
                recommendations.append({
                    "username": metadata["username"],
                    "user_id": metadata["user_id"],
                    "city": metadata["city"],
                    "interests": metadata["interests"],
                    "similarity_score": round(1 - score, 3)  # Convert distance to similarity score
                })
            
            # Sort recommendations by similarity score in descending order
            recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Store recommendations in database
            self.store_recommendations(username, recommendations)
            
            # Add rank to recommendations
            for idx, rec in enumerate(recommendations):
                rec['rank'] = idx + 1
            
            return {"recommendations": recommendations}, 200
            
        except Exception as e:
            logging.error(f"Error in get_recommendations: {str(e)}")
            return {"error": str(e)}, 500 