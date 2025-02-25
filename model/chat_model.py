import psycopg2
from psycopg2.extras import DictCursor
import sys
from config.config import *
from utils.exception import CustomException
from utils.logger import logging
from datetime import datetime

class ChatModel:
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
            logging.error(f"Error connecting to database: {e}")
            raise CustomException(e, sys)

    def send_message(self, sender_id, receiver_id, message_text):
        """Send a message to another user if they are matched"""
        try:
            # First check if users are matched
            match_check_query = """
                SELECT match_id FROM matches 
                WHERE ((user1_id = %s AND user2_id = %s) 
                    OR (user1_id = %s AND user2_id = %s))
                AND is_active = TRUE;
            """
            self.cursor.execute(match_check_query, (sender_id, receiver_id, receiver_id, sender_id))
            match = self.cursor.fetchone()
            
            if not match:
                return {"status": "error", "message": "Users are not matched"}
                
            # If matched, insert the message
            message_query = """
                INSERT INTO messages (sender_id, receiver_id, message_text, status)
                VALUES (%s, %s, %s, 'sent') 
                RETURNING message_id, sent_at;
            """
            
            self.cursor.execute(message_query, (sender_id, receiver_id, message_text))
            result = self.cursor.fetchone()
            self.connection.commit()
            
            return {
                "status": "success", 
                "message": "Message sent",
                "data": {
                    "message_id": result['message_id'],
                    "sent_at": result['sent_at'].isoformat()
                }
            }
            
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error sending message: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_chat_history(self, user_id, other_user_id):
        """Get chat history between two users"""
        try:
            # First check if users are matched
            match_check_query = """
                SELECT match_id FROM matches 
                WHERE ((user1_id = %s AND user2_id = %s) 
                    OR (user1_id = %s AND user2_id = %s))
                AND is_active = TRUE;
            """
            self.cursor.execute(match_check_query, (user_id, other_user_id, other_user_id, user_id))
            match = self.cursor.fetchone()
            
            if not match:
                return {"status": "error", "message": "Users are not matched"}

            # Get messages between the users
            query = """
                SELECT m.message_id, m.sender_id, m.receiver_id, m.message_text, 
                       m.sent_at, m.status,
                       s.username as sender_username,
                       r.username as receiver_username
                FROM messages m
                JOIN user_db s ON m.sender_id = s.id
                JOIN user_db r ON m.receiver_id = r.id
                WHERE (m.sender_id = %s AND m.receiver_id = %s)
                   OR (m.sender_id = %s AND m.receiver_id = %s)
                ORDER BY m.sent_at ASC;
            """
            self.cursor.execute(query, (user_id, other_user_id, other_user_id, user_id))
            messages = self.cursor.fetchall()
            
            # Update status to 'read' for received messages
            update_query = """
                UPDATE messages 
                SET status = 'read'
                WHERE receiver_id = %s AND sender_id = %s AND status != 'read';
            """
            self.cursor.execute(update_query, (user_id, other_user_id))
            self.connection.commit()
            
            return {
                "status": "success", 
                "data": [{
                    "message_id": msg['message_id'],
                    "sender_id": msg['sender_id'],
                    "receiver_id": msg['receiver_id'],
                    "message_text": msg['message_text'],
                    "sent_at": msg['sent_at'].isoformat(),
                    "status": msg['status'],
                    "sender_username": msg['sender_username'],
                    "receiver_username": msg['receiver_username']
                } for msg in messages]
            }
            
        except Exception as e:
            logging.error(f"Error getting chat history: {e}")
            return {"status": "error", "message": str(e)}

    def get_recent_chats(self, user_id):
        """Get list of recent chats for a user"""
        try:
            query = """
                WITH LastMessages AS (
                    SELECT DISTINCT ON (
                        CASE 
                            WHEN sender_id = %s THEN receiver_id 
                            ELSE sender_id 
                        END
                    )
                    m.message_id, m.sender_id, m.receiver_id, m.message_text, 
                    m.sent_at, m.status,
                    CASE 
                        WHEN sender_id = %s THEN receiver_id 
                        ELSE sender_id 
                    END as other_user_id
                    FROM messages m
                    WHERE sender_id = %s OR receiver_id = %s
                    ORDER BY other_user_id, sent_at DESC
                )
                SELECT 
                    lm.*,
                    u.username as other_username,
                    u.email as other_email
                FROM LastMessages lm
                JOIN user_db u ON u.id = lm.other_user_id
                ORDER BY lm.sent_at DESC;
            """
            self.cursor.execute(query, (user_id, user_id, user_id, user_id))
            chats = self.cursor.fetchall()
            
            return {
                "status": "success",
                "data": [{
                    "message_id": chat['message_id'],
                    "other_user_id": chat['other_user_id'],
                    "other_username": chat['other_username'],
                    "other_email": chat['other_email'],
                    "last_message": chat['message_text'],
                    "sent_at": chat['sent_at'].isoformat(),
                    "status": chat['status']
                } for chat in chats]
            }
            
        except Exception as e:
            logging.error(f"Error getting recent chats: {e}")
            return {"status": "error", "message": str(e)}

    def delete_message(self, message_id, user_id):
        """Delete a message (soft delete)"""
        try:
            query = """
                UPDATE messages 
                SET is_deleted = TRUE
                WHERE message_id = %s AND (sender_id = %s OR receiver_id = %s)
                RETURNING message_id;
            """
            self.cursor.execute(query, (message_id, user_id, user_id))
            result = self.cursor.fetchone()
            self.connection.commit()
            
            if result:
                return {"status": "success", "message": "Message deleted"}
            return {"status": "error", "message": "Message not found or unauthorized"}
            
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error deleting message: {e}")
            return {"status": "error", "message": str(e)}
