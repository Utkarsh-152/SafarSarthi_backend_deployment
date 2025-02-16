import bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity
import json
import psycopg2
from psycopg2.extras import DictCursor
from utils.logger import logging
from utils.exception import CustomException
from config.verifyEmail import VerifyEmail
import sys
from config.config import *

class UserAuthModel:
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
            logging.info(f"Error while connecting to PostgreSQL database: {e}")
            raise CustomException(e, sys)
        
    def register_user(self, username, email, password, confirm_password):
        try:
            logging.info("Registering user")
            if username == '' or email == '' or password == '' or confirm_password == '':
                return {"status": "error", "message": "Please fill in all fields"}

            if password != confirm_password:
                logging.info("Passwords do not match")
                return {"status": "error", "message": "Passwords do not match"}
        
            # Check if email exists
            self.cursor.execute('SELECT * FROM user_db WHERE email = %s', (email,))
            existing_email = self.cursor.fetchone()
            if existing_email:
                logging.info("Email already exists")
                return {"status": "error", "message": "Email already registered"}

            # Check if username exists
            self.cursor.execute('SELECT * FROM user_db WHERE username = %s', (username,))
            existing_user = self.cursor.fetchone()
            if existing_user:
                logging.info("Username already exists")
                return {"status": "error", "message": "Username already taken"}
            
            # If neither exists, proceed with registration
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.cursor.execute('INSERT INTO user_db (username, email, password) VALUES (%s, %s, %s)', 
                        (username, email, hashed_password))
            self.connection.commit()
            
            # Generate JWT token for the new user
            access_token = create_access_token(identity=username)
            logging.info("Registration successful")
            return {
                "status": "success",
                "message": "Registration successful",
                "access_token": access_token,
                "user": {
                    "username": username,
                    "email": email
                }
            }
        except Exception as e:
            logging.error(f"Error in register_user: {e}")
            raise CustomException(e, sys)
        
    def login_user(self, username, password):
        try:
            logging.info("Logging in user")
            # Try to find user by username or email
            self.cursor.execute('SELECT * FROM user_db WHERE username = %s OR email = %s', (username, username))
            user = self.cursor.fetchone()

            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                access_token = create_access_token(identity=user['username'])
                return {
                    "status": "success",
                    "message": "Login successful",
                    "access_token": access_token,
                    "user": {
                        "username": user['username'],
                        "email": user['email']
                    }
                }
            else:
                logging.info("Invalid credentials")
                return {
                    "status": "error",
                    "message": "Invalid username/email or password"
                }
        except Exception as e:
            logging.error(f"Error in login_user: {e}")
            raise CustomException(e, sys)
        

