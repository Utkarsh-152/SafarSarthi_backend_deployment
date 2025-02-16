from app import app
from flask import jsonify, request
from model.swipe_model import SwipeModel
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.logger import logging
from utils.get_user_id import get_user_id_from_username

swipe_model = SwipeModel()

@app.route('/api/swipes/remaining', methods=['POST'])
@jwt_required()
def get_remaining_swipes():
    try:
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        result = swipe_model.get_remaining_swipes(user_id)
        return jsonify(result), 200 if result["status"] == "success" else 400
        
    except Exception as e:
        logging.error(f"Error in get_remaining_swipes: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/swipe', methods=['POST'])
@jwt_required()
def process_swipe():
    try:
        data = request.get_json()
        target_username = data.get('target_username')
        direction = data.get('direction')
        
        if not all([target_username, direction]) or direction not in ['left', 'right']:
            return jsonify({
                "status": "error",
                "message": "Invalid request. Required: target_username and direction (left/right)"
            }), 400
            
        # Get user IDs
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)
        target_user_id = get_user_id_from_username(target_username)
        
        if not all([user_id, target_user_id]):
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        result = swipe_model.process_swipe(user_id, target_user_id, direction)
        return jsonify(result), 200 if result["status"] == "success" else 400
        
    except Exception as e:
        logging.error(f"Error in process_swipe: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/matches', methods=['POST'])
@jwt_required()
def get_matches():
    try:
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        result = swipe_model.get_matches(user_id)
        return jsonify(result), 200 if result["status"] == "success" else 400
        
    except Exception as e:
        logging.error(f"Error in get_matches: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/chat/send', methods=['POST'])
@jwt_required()
def send_message():
    try:
        data = request.get_json()
        receiver_username = data.get('receiver_username')
        message_text = data.get('message')
        
        if not all([receiver_username, message_text]):
            return jsonify({
                "status": "error",
                "message": "Invalid request. Required: receiver_username and message"
            }), 400
            
        # Get user IDs
        username = get_jwt_identity()
        sender_id = get_user_id_from_username(username)
        receiver_id = get_user_id_from_username(receiver_username)
        
        if not all([sender_id, receiver_id]):
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        result = swipe_model.send_message(sender_id, receiver_id, message_text)
        return jsonify(result), 200 if result["status"] == "success" else 400
        
    except Exception as e:
        logging.error(f"Error in send_message: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/chat/history', methods=['POST'])
@jwt_required()
def get_chat_history():
    try:
        data = request.get_json()
        other_username = data.get('username')
        
        if not other_username:
            return jsonify({
                "status": "error",
                "message": "Username is required"
            }), 400
            
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)
        other_user_id = get_user_id_from_username(other_username)
        
        if not all([user_id, other_user_id]):
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        result = swipe_model.get_chat_history(user_id, other_user_id)
        return jsonify(result), 200 if result["status"] == "success" else 400
        
    except Exception as e:
        logging.error(f"Error in get_chat_history: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500 