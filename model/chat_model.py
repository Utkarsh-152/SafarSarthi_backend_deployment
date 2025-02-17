# def send_message(self, sender_id, receiver_id, message_text):
#         """Send a message to a matched user"""
#         try:
#             # First check if users are matched
#             match_check_query = """
#                 SELECT match_id 
#                 FROM matches 
#                 WHERE ((user1_id = %s AND user2_id = %s) 
#                     OR (user1_id = %s AND user2_id = %s))
#                 AND is_active = TRUE;
#             """
#             self.cursor.execute(match_check_query, (sender_id, receiver_id, receiver_id, sender_id))
#             match = self.cursor.fetchone()
            
#             if not match:
#                 return {
#                     "status": "error",
#                     "message": "Cannot send message - users are not matched"
#                 }
                
#             # Send message
#             message_query = """
#                 INSERT INTO messages (sender_id, receiver_id, message_text)
#                 VALUES (%s, %s, %s)
#                 RETURNING message_id, sent_at;
#             """
#             self.cursor.execute(message_query, (sender_id, receiver_id, message_text))
#             result = self.cursor.fetchone()
#             self.connection.commit()
            
#             return {
#                 "status": "success",
#                 "message_id": result['message_id'],
#                 "sent_at": result['sent_at']
#             }
            
#         except Exception as e:
#             self.connection.rollback()
#             logging.error(f"Error sending message: {e}")
#             return {"status": "error", "message": str(e)}
            
#     def get_chat_history(self, user_id, other_user_id):
#         """Get chat history between two users"""
#         try:
#             query = """
#                 SELECT 
#                     message_id,
#                     sender_id,
#                     receiver_id,
#                     message_text,
#                     sent_at
#                 FROM messages
#                 WHERE (sender_id = %s AND receiver_id = %s)
#                     OR (sender_id = %s AND receiver_id = %s)
#                 ORDER BY sent_at ASC;
#             """
#             self.cursor.execute(query, (user_id, other_user_id, other_user_id, user_id))
#             messages = self.cursor.fetchall()
            
#             return {
#                 "status": "success",
#                 "messages": [dict(msg) for msg in messages]
#             }
            
#         except Exception as e:
#             logging.error(f"Error getting chat history: {e}")
#             return {"status": "error", "message": str(e)} 