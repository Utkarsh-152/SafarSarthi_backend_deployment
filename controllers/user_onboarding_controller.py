from app import app #, supabase_client, get_db_connection
from flask import jsonify, request
from utils.logger import logging
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from utils.jwt_utils import jwt_blacklist
from model.user_onboarding_model import UserOnboardingmodel
import os

@app.route('/api/onboarding/age', methods=['POST'])
@jwt_required()
def onboarding_age():
    try:
        data = request.get_json()
        age = data.get('age')
        
        if not age:
            return jsonify({
                "status": "error",
                "message": "Age is required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_age(age)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Age updated successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_age: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating age"
        }), 500

@app.route('/api/onboarding/gender', methods=['POST'])
@jwt_required()
def onboarding_gender():
    try:
        data = request.get_json()
        gender = data.get('gender')
        
        if not gender:
            return jsonify({
                "status": "error",
                "message": "Gender is required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_gender(gender)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Gender updated successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_gender: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating gender"
        }), 500

@app.route('/api/onboarding/location', methods=['POST'])
@jwt_required()
def onboarding_location():
    try:
        data = request.get_json()
        location = data.get('location')
        
        if not location:
            return jsonify({
                "status": "error",
                "message": "Location is required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_location(location)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Location updated successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_location: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating location"
        }), 500

@app.route('/api/onboarding/occupation', methods=['POST'])
@jwt_required()
def onboarding_occupation():
    try:
        data = request.get_json()
        occupation = data.get('occupation')
        
        if not occupation:
            return jsonify({
                "status": "error",
                "message": "Occupation is required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_occupation(occupation)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Occupation updated successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_occupation: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating occupation"
        }), 500

@app.route('/api/onboarding/interests', methods=['POST'])
@jwt_required()
def onboarding_interests():
    try:
        data = request.get_json()
        interests = data.get('interests')
        
        if not interests:
            return jsonify({
                "status": "error",
                "message": "Interests are required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_interests(interests)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Interests updated successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_interests: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating interests"
        }), 500

@app.route('/api/onboarding/bio', methods=['POST'])
@jwt_required()
def onboarding_bio():
    try:
        data = request.get_json()
        bio = data.get('bio')
        
        if not bio:
            return jsonify({
                "status": "error",
                "message": "Bio is required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_bio(bio)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Bio Added successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_bio: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating bio"
        }), 500

@app.route('/api/onboarding/videos', methods=['POST'])
@jwt_required()
def onboarding_videos():
    try:
        if 'video' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No video file provided"
            }), 400
            
        video = request.files['video']
        if not video or video.filename == '':
            return jsonify({
                "status": "error",
                "message": "No video selected"
            }), 400
            
        # Get current user's username
        username = get_jwt_identity()
        
        # Save the video with a unique filename
        extension = video.filename.split('.')[-1]
        filename = f"{username}_video.{extension}"
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video.save(video_path)

        # Save the video filename to the database
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_videos(video)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Video uploaded successfully",
                "video_url": f"/static/uploads/{filename}"
            }), 200
        else:
            # Clean up the uploaded file if database operation failed
            if os.path.exists(video_path):
                os.remove(video_path)
            return jsonify({
                "status": "error",
                "message": result["message"]
            }), 400
            
    except Exception as e:
        logging.error(f"Error in onboarding_videos: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while uploading video"
        }), 500

@app.route('/api/onboarding/prompts', methods=['POST'])
@jwt_required()
def onboarding_prompts():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({
                "status": "error",
                "message": "Prompt is required"
            }), 400
            
        user_onboarding_model = UserOnboardingmodel()
        result = user_onboarding_model.add_prompt(prompt)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Prompt updated successfully"
            }), 200
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400
    except Exception as e:
        logging.error(f"Error in onboarding_prompts: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while updating prompt"
        }), 500

@app.route('/user/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        jti = get_jwt()["jti"]
        jwt_blacklist.add(jti)
        
        response = jsonify({
            "status": "success",
            "message": "Logged out successfully"
        })
        response.delete_cookie('access_token_cookie')
        return response, 200
        
    except Exception as e:
        logging.error(f"Error in logout: {e}")
        return jsonify({
            "status": "error",
            "message": "An error occurred during logout"
        }), 500