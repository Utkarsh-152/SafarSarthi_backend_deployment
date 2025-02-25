from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from model.chat_model import ChatModel
from utils.get_user_id import get_user_id_from_username
from utils.logger import logging
from app import app, socketio

chat_model = ChatModel()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    try:
        # Get user from JWT token
        username = get_jwt_identity()
        if not username:
            return False  # Reject connection if no valid token
        
        user_id = get_user_id_from_username(username)
        if not user_id:
            return False
        
        # Join user's personal room
        join_room(f"user_{user_id}")
        logging.info(f"User {username} connected to WebSocket")
        
        return True
    except Exception as e:
        logging.error(f"Error in WebSocket connect: {e}")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    try:
        username = get_jwt_identity()
        if username:
            user_id = get_user_id_from_username(username)
            if user_id:
                leave_room(f"user_{user_id}")
                logging.info(f"User {username} disconnected from WebSocket")
    except Exception as e:
        logging.error(f"Error in WebSocket disconnect: {e}")

@socketio.on('join_chat')
def handle_join_chat(data):
    try:
        other_username = data.get('username')
        if not other_username:
            return
        
        # Get current user's info
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)
        other_user_id = get_user_id_from_username(other_username)
        
        if not all([user_id, other_user_id]):
            return
        
        # Create and join a room for this chat
        chat_room = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        join_room(chat_room)
        logging.info(f"User {username} joined chat room with {other_username}")
        
    except Exception as e:
        logging.error(f"Error in join_chat: {e}")

@socketio.on('leave_chat')
def handle_leave_chat(data):
    try:
        other_username = data.get('username')
        if not other_username:
            return
        
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)
        other_user_id = get_user_id_from_username(other_username)
        
        if not all([user_id, other_user_id]):
            return
        
        chat_room = f"chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}"
        leave_room(chat_room)
        logging.info(f"User {username} left chat room with {other_username}")
        
    except Exception as e:
        logging.error(f"Error in leave_chat: {e}")

@socketio.on('new_message')
def handle_new_message(data):
    try:
        receiver_username = data.get('receiver_username')
        message_text = data.get('message')
        
        if not all([receiver_username, message_text]):
            return
        
        # Get user IDs
        sender_username = get_jwt_identity()
        sender_id = get_user_id_from_username(sender_username)
        receiver_id = get_user_id_from_username(receiver_username)
        
        if not all([sender_id, receiver_id]):
            return
        
        # Save message to database
        result = chat_model.send_message(sender_id, receiver_id, message_text)
        
        if result["status"] == "success":
            # Prepare message data
            message_data = {
                "message_id": result["data"]["message_id"],
                "sender_username": sender_username,
                "receiver_username": receiver_username,
                "message": message_text,
                "sent_at": result["data"]["sent_at"]
            }
            
            # Emit to the chat room
            chat_room = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
            emit('message', message_data, room=chat_room)
            
            # Also emit to receiver's personal room for notifications
            emit('new_message_notification', message_data, room=f"user_{receiver_id}")
            
    except Exception as e:
        logging.error(f"Error in new_message: {e}")

# REST API routes
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
                "message": "Both receiver_username and message are required"
            }), 400

        # Get sender's username from JWT
        sender_username = get_jwt_identity()
        
        # Get user IDs
        sender_id = get_user_id_from_username(sender_username)
        receiver_id = get_user_id_from_username(receiver_username)

        if not all([sender_id, receiver_id]):
            return jsonify({
                "status": "error", 
                "message": "User not found"
            }), 404

        result = chat_model.send_message(sender_id, receiver_id, message_text)
        
        if result["status"] == "success":
            # Emit the message through WebSocket
            message_data = {
                "message_id": result["data"]["message_id"],
                "sender_username": sender_username,
                "receiver_username": receiver_username,
                "message": message_text,
                "sent_at": result["data"]["sent_at"]
            }
            chat_room = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
            socketio.emit('message', message_data, room=chat_room)
            socketio.emit('new_message_notification', message_data, room=f"user_{receiver_id}")
            
            return jsonify(result), 200
        return jsonify(result), 400

    except Exception as e:
        logging.error(f"Error in send_message: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while sending message"
        }), 500

@app.route('/api/chat/history', methods=['POST'])
@jwt_required()
def get_chat_history():
    try:
        other_username = request.args.get('username')

        if not other_username:
            return jsonify({
                "status": "error", 
                "message": "Username parameter is required"
            }), 400

        # Get current user's username from JWT
        username = get_jwt_identity()
        
        # Get user IDs
        user_id = get_user_id_from_username(username)
        other_user_id = get_user_id_from_username(other_username)

        if not all([user_id, other_user_id]):
            return jsonify({
                "status": "error", 
                "message": "User not found"
            }), 404

        result = chat_model.get_chat_history(user_id, other_user_id)
        
        if result["status"] == "success":
            return jsonify(result), 200
        return jsonify(result), 400

    except Exception as e:
        logging.error(f"Error in get_chat_history: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching chat history"
        }), 500

@app.route('/api/chat/recent', methods=['POST'])
@jwt_required()
def get_recent_chats():
    try:
        # Get current user's username from JWT
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)

        if not user_id:
            return jsonify({
                "status": "error", 
                "message": "User not found"
            }), 404

        result = chat_model.get_recent_chats(user_id)
        
        if result["status"] == "success":
            return jsonify(result), 200
        return jsonify(result), 400

    except Exception as e:
        logging.error(f"Error in get_recent_chats: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching recent chats"
        }), 500

@app.route('/api/chat/message/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    try:
        username = get_jwt_identity()
        user_id = get_user_id_from_username(username)

        if not user_id:
            return jsonify({
                "status": "error", 
                "message": "User not found"
            }), 404

        result = chat_model.delete_message(message_id, user_id)
        
        if result["status"] == "success":
            return jsonify(result), 200
        return jsonify(result), 400

    except Exception as e:
        logging.error(f"Error in delete_message: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while deleting message"
        }), 500