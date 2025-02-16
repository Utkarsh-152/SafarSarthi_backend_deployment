from config.config import *
import psycopg2
from psycopg2.extras import DictCursor
from utils.logger import logging

def get_user_id_from_username(username):
    """
    Utility function to get user_id from username
    Args:
        username (str): Username to look up
    Returns:
        int or None: User ID if found, None if not found or error occurs
    """
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            port=POSTGRES_PORT
        )
        cursor = connection.cursor(cursor_factory=DictCursor)
        
        # Query to get user ID
        query = "SELECT id FROM user_db WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        
        # Close database connections
        cursor.close()
        connection.close()
        
        return result['id'] if result else None
        
    except Exception as e:
        logging.error(f"Error getting user ID for username {username}: {str(e)}")
        return None 