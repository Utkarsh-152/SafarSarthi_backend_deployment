import requests
import os
from dotenv import load_dotenv
from utils.logger import logging
from utils.exception import CustomException
import sys


load_dotenv()

class VerifyEmail:
    try:
        def __init__(self):
            self.email = os.getenv("EMAIL")
            self.api_key = os.getenv("ABSTRACT_API_KEY")


        def verify_email(self,email):
            url = f"https://emailvalidation.abstractapi.com/v1/?api_key={self.api_key}&email={email}"


            response = requests.get(url).json()
            
            if response.get("deliverability") == "DELIVERABLE":
                return True
            return False
    except Exception as e:
        logging.error(f"Error in verifyEmail: {e}")
        raise CustomException(e, sys)
