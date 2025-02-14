from app import app
from flask import request, jsonify
from model.recommendation_model import RecommendationModel
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.logger import logging

recommendation_model = RecommendationModel()

@app.route('/user/recommendation', methods=['POST'])
@jwt_required()
def get_recommendations():
    try:
        logging.info("Getting recommendations")
        
        # Get username from JWT token
        username = get_jwt_identity()
        logging.info(f"Username from token: {username}")
        
        # Get recommendations from the model
        recommendations, status_code = recommendation_model.get_recommendations(username)
        logging.info(f"Recommendations received: {recommendations}")
        
        return jsonify(recommendations), status_code
        
    except Exception as e:
        logging.error(f"Error in get_recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500 