from app import app #, supabase_client, get_db_connection
from flask import jsonify, request
from utils.logger import logging
from model.user_auth_model import UserAuthModel

@app.route('/api/user/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        if not all([username, email, password, confirm_password]):
            return jsonify({
                "status": "error",
                "message": "All fields are required"
            }), 400

        user_auth_model = UserAuthModel()
        result = user_auth_model.register_user(username, email, password, confirm_password)
        
        if result["status"] == "success":
            response = jsonify({
                "status": "success",
                "message": "Registration successful",
                "access_token": result["access_token"],
                "user": result["user"]
            })
            
            # Set cookie for web browsers
            response.set_cookie(
                'access_token_cookie',
                result["access_token"],
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=86400  # 24 hours
            )
            return response, 200
        else:
            return jsonify({
                "status": "error",
                "message": result["message"]
            }), 400
            
    except Exception as e:
        logging.error(f"Error in register: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred during registration"
        }), 500

@app.route('/api/user/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username') or data.get('email')  # Accept either username or email
        password = data.get('password')

        if not all([username, password]):
            return jsonify({
                "status": "error",
                "message": "Username/Email and password are required"
            }), 400

        user_auth_model = UserAuthModel()
        result = user_auth_model.login_user(username, password)
        
        if result["status"] == "success":
            response = jsonify({
                "status": "success",
                "message": "Login successful",
                "access_token": result["access_token"],
                "user": result["user"]
            })
            
            # Set cookie for web browsers
            response.set_cookie(
                'access_token_cookie',
                result["access_token"],
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=86400  # 24 hours
            )
            return response, 200
        else:
            return jsonify({
                "status": "error",
                "message": result["message"]
            }), 401
            
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred during login"
        }), 500

    