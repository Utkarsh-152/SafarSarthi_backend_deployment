from utils.exception import CustomException
from utils.logger import logging
import sys
from config.config import *
import psycopg2
from psycopg2.extras import DictCursor




class HomeScreenModel:
    def __init__(self):
        try:        
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
        
    #def swipe