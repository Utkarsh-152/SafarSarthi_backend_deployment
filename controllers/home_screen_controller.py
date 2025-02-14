from app import app
from flask import Blueprint, request, jsonify
from model.recommendation_model import RecommendationModel
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.logger import logging

recommendation_model = RecommendationModel()

@app.route('/user/recommendation', methods=['POST'])
@jwt_required()
def get_recommendations():
    try:
        logging.info("Getting recommendations")

        
        logging.info("Getting user")
        # Get user_id from JWT token
        username = get_jwt_identity()
        logging.info(f"user Id: {username}")
        
        logging.info(f"Getting recommendations for user: {username}")
        # Get recommendations from the model
        recommendations, status_code = recommendation_model.get_recommendations(username=username)
        
        return jsonify(recommendations), status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 