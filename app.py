from flask import Flask, jsonify
from config.config import *
import psycopg2
#from supabase import create_client, Client
from flask_jwt_extended import JWTManager
from utils.logger import logging
from utils.exception import CustomException
from flask_socketio import SocketIO #update
import eventlet #update

eventlet.monkey_patch()
app = Flask(__name__)
logging.info("Flask app initialized")

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet') #update
logging.info("SocketIO initialized") #update

# Initialize Supabase client
#supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Connect to PostgreSQL database
def get_db_connection():
    logging.info("Connecting to PostgreSQL database")
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )
    logging.info("PostgreSQL database connected")
    return conn

with app.app_context():
    from controllers.user_auth_controller import *
    from controllers.user_onboarding_controller import *
    from controllers.swipe_controller import *
    from controllers.chat_controller import * #update
    

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) #update
