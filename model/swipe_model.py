from config.config import *
from utils.exception import CustomException
from utils.logger import logging
import sys
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta

class SwipeModel:
    DAILY_SWIPE_LIMIT = 10
    
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
            
    def get_remaining_swipes(self, user_id):
        """Calculate remaining swipes for the day"""
        try:
            # Get swipes made in the last 24 hours
            query = """
                SELECT COUNT(*) as swipe_count
                FROM swipe_logs
                WHERE user_id = %s
                AND swiped_at > NOW() - INTERVAL '24 hours';
            """
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            
            swipes_used = result['swipe_count'] if result else 0
            remaining_swipes = self.DAILY_SWIPE_LIMIT - swipes_used
            
            return {
                "status": "success",
                "remaining_swipes": remaining_swipes,
                "total_limit": self.DAILY_SWIPE_LIMIT
            }
            
        except Exception as e:
            logging.error(f"Error getting remaining swipes: {e}")
            return {"status": "error", "message": str(e)}
            
    def process_swipe(self, user_id, target_user_id, direction):
        """Process a swipe action and check for matches"""
        try:
            # Check remaining swipes
            remaining = self.get_remaining_swipes(user_id)
            if remaining["status"] == "error":
                return remaining
                
            if remaining["remaining_swipes"] <= 0:
                return {
                    "status": "error",
                    "message": "Daily swipe limit reached"
                }
                
            # Log the swipe
            swipe_query = """
                INSERT INTO swipe_logs (user_id, target_user_id, swipe_direction)
                VALUES (%s, %s, %s)
                RETURNING swipe_id;
            """
            self.cursor.execute(swipe_query, (user_id, target_user_id, direction))
            swipe_id = self.cursor.fetchone()['swipe_id']
            
            # If right swipe, check for match
            match_found = False
            if direction == 'right':
                # Check if target user has already swiped right
                match_check_query = """
                    SELECT swipe_id
                    FROM swipe_logs
                    WHERE user_id = %s 
                    AND target_user_id = %s
                    AND swipe_direction = 'right'
                    AND swiped_at > NOW() - INTERVAL '7 days';
                """
                self.cursor.execute(match_check_query, (target_user_id, user_id))
                existing_swipe = self.cursor.fetchone()
                
                if existing_swipe:
                    # Create match
                    match_query = """
                        INSERT INTO matches (user1_id, user2_id)
                        VALUES (%s, %s)
                        ON CONFLICT (user1_id, user2_id) DO NOTHING
                        RETURNING match_id;
                    """
                    # Ensure smaller ID is user1_id for consistency
                    user1, user2 = sorted([user_id, target_user_id])
                    self.cursor.execute(match_query, (user1, user2))
                    match_result = self.cursor.fetchone()
                    match_found = bool(match_result)
            
            self.connection.commit()
            
            return {
                "status": "success",
                "swipe_id": swipe_id,
                "match_found": match_found,
                "remaining_swipes": remaining["remaining_swipes"] - 1
            }
            
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error processing swipe: {e}")
            return {"status": "error", "message": str(e)}
            
    def get_matches(self, user_id):
        """Get all active matches for a user"""
        try:
            query = """
                SELECT 
                    m.match_id,
                    CASE 
                        WHEN m.user1_id = %s THEN m.user2_id
                        ELSE m.user1_id
                    END as matched_user_id,
                    ud.username as matched_username,
                    up.location as matched_location,
                    up.interest as matched_interests,
                    m.matched_at,
                    m.is_active
                FROM matches m
                JOIN user_db ud ON (
                    CASE 
                        WHEN m.user1_id = %s THEN ud.id = m.user2_id
                        ELSE ud.id = m.user1_id
                    END
                )
                JOIN user_profile up ON ud.id = up.user_id
                WHERE (m.user1_id = %s OR m.user2_id = %s)
                AND m.is_active = TRUE
                ORDER BY m.matched_at DESC;
            """
            self.cursor.execute(query, (user_id, user_id, user_id, user_id))
            matches = self.cursor.fetchall()
            
            return {
                "status": "success",
                "matches": [dict(match) for match in matches]
            }
            
        except Exception as e:
            logging.error(f"Error getting matches: {e}")
            return {"status": "error", "message": str(e)}
            
    