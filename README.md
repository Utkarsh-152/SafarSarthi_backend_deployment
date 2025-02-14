# Travel Mate Backend

A Flask-based backend service for the Travel Mate application that provides user authentication, profile management, and AI-powered user recommendations.

## Project Structure

```
server/
├── config/
│   ├── __init__.py
│   ├── verify_email.py   # verify email to verify real emails right now it is commented
│   └── config.py         # Configuration settings and environment variables
├── controllers/
│   ├── __init__.py
│   ├── user_auth_controller.py      # Authentication endpoints
│   ├── user_onboarding_controller.py # User profile management
│   └── home_screen_controller.py     # Recommendation endpoints
├── model/
│   ├── user_auth_model.py           # Authentication business logic
│   ├── user_onboarding_model.py     # Profile management logic
│   ├── home_screen_model.py         # Home screen related logic not started yet it will have swipe, match logics 
│   └── recommendation_model.py       # AI recommendation system
├── utils/
│   ├── jwt_utils.py      # JWT blacklist lists
│   ├── logger.py         # Logging configuration
│   └── exception.py      # Custom exception handling
├── logs/                 # Application logs
├── app.py               # Main application entry point
├── .env                 # This mf consists of environment variables which I won't be sharing in my public repository
├── requirements.txt     # Project dependencies
├── render.yaml         # I don't know why the fuck I made it, its just mf gpt told me.
├── .gitignore          # Project dependencies
└── gunicorn.conf.py    # Gunicorn server configuration

```

## API Endpoints

### Authentication Endpoints
- `POST /api/user/register`
  - Register a new user
  - Body: 
    ```json
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "confirmPassword": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Registration successful",
        "access_token": "JWT_token_string",
        "user": {
            // User details
        }
    }
    ```

- `POST /api/user/login`
  - Login existing user
  - Body:
    ```json
    {
        "username": "string", // or "email": "string"
        "password": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Login successful",
        "access_token": "JWT_token_string",
        "user": {
            // User details
        }
    }
    ```

- `POST /user/logout`
  - Logout user
  - Requires: JWT Token
  - Response:
    ```json
    {
        "status": "success",
        "message": "Logged out successfully"
    }
    ```

### User Onboarding Endpoints
All onboarding endpoints require JWT Token in header: `Authorization: Bearer <token>`

- `POST /api/onboarding/age`
  - Update user age
  - Body:
    ```json
    {
        "age": "integer"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Age updated successfully"
    }
    ```

- `POST /api/onboarding/gender`
  - Update user gender
  - Body:
    ```json
    {
        "gender": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Gender updated successfully"
    }
    ```

- `POST /api/onboarding/location`
  - Update user location
  - Body:
    ```json
    {
        "location": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Location updated successfully"
    }
    ```

- `POST /api/onboarding/occupation`
  - Update user occupation
  - Body:
    ```json
    {
        "occupation": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Occupation updated successfully"
    }
    ```

- `POST /api/onboarding/interests`
  - Update user interests
  - Body:
    ```json
    {
        "interests": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Interests updated successfully"
    }
    ```

- `POST /api/onboarding/bio`
  - Update user bio
  - Body:
    ```json
    {
        "bio": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Bio Added successfully"
    }
    ```

- `POST /api/onboarding/videos`
  - Upload user video
  - Body: Form-data with key "video" and file upload
  - Response:
    ```json
    {
        "status": "success",
        "message": "Video uploaded successfully",
        "video_url": "/static/uploads/username_video.extension"
    }
    ```

- `POST /api/onboarding/prompts`
  - Update user prompts
  - Body:
    ```json
    {
        "prompt": "string"
    }
    ```
  - Response:
    ```json
    {
        "status": "success",
        "message": "Prompt updated successfully"
    }
    ```

### Recommendation Endpoints
- `POST /user/recommendation`
  - Get personalized user recommendations
  - Requires: JWT Token
  - Response:
    ```json
    {
        "recommendations": [
            {
                "username": "string",
                "city": "string",
                "interests": "string",
                "similarity_score": "float"
            }
        ]
    }
    ```

### Error Responses
All endpoints return error responses in this format:
```json
{
    "status": "error",
    "message": "Error description"
}
```

Common HTTP Status Codes:
- 200: Success
- 400: Bad Request (missing or invalid fields)
- 401: Unauthorized (invalid or missing token)
- 500: Internal Server Error

## Database Table schemas
### user_db: 
stores data during user registration

```SQL
CREATE TABLE user_db (
    id serial PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### user_profile: 
stores basic data of a user like age, gender, location etc.
```SQL
-- First, create the ENUM type for gender
CREATE TYPE gender_enum AS ENUM ('Male', 'Female', 'Other');

-- Now, create the user_profile table
CREATE TABLE user_profile (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    age INT DEFAULT NULL,
    bio TEXT DEFAULT NULL,
    gender gender_enum DEFAULT NULL,  -- Use ENUM type
    interest TEXT DEFAULT NULL,
    location VARCHAR(255) DEFAULT NULL,
    occupation VARCHAR(100) DEFAULT NULL,
    videos JSON DEFAULT NULL,
    prompt TEXT DEFAULT NULL,
    profile_photo JSON DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES user_db(id) ON DELETE CASCADE
);
```

### user_recommendation_entries: 
recommendation model data for recommeding users with similar interests and location
```SQL
CREATE TABLE user_recommendation_entries (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,  -- The user for whom recommendations are generated
    recommended_user_id INT NOT NULL,  -- The recommended user
    similarity_score FLOAT DEFAULT NULL,  -- Optional similarity score
    rank INT NOT NULL,  -- Rank of the recommendation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Track when the recommendation was generated
    FOREIGN KEY (user_id) REFERENCES user_db(id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_user_id) REFERENCES user_db(id) ON DELETE CASCADE,
    UNIQUE (user_id, recommended_user_id)  -- Ensures a user can't have duplicate recommendations
); 
```

## Technologies Used
- Flask
- PostgreSQL
- JWT Authentication
- FAISS Vector Database
- HuggingFace Embeddings
- Sentence Transformers

## Setup and Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in config/config.py:
```python
POSTGRES_HOST
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_PORT
JWT_SECRET_KEY
```

3. Run the application:
```bash
python app.py
```

For production deployment:
```bash
gunicorn app:app
```

## Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Error Handling
The API returns standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

Each error response includes a message explaining the error:
```json
{
    "error": "Error message description"
}
```

## Rate Limiting
- API endpoints are rate-limited to prevent abuse
- Login attempts are limited to 5 per minute per IP
- Other endpoints are limited to 100 requests per minute per user 