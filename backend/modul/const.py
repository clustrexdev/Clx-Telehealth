"""Configuration module to store environment variables and constants used across the application."""

import os
from dotenv import load_dotenv
load_dotenv()

# Base URLs
ATHENA_BASE_URL = "https://api.preview.platform.athenahealth.com"
APPLICATION_BASE_URL = os.getenv("APPLICATION_BASE_URL")


# Athena Client Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


# Athena Token Storage
TOKEN = None
TOKEN_EXP_TIMESTAMP = None


# Vonage Credentials
VONAGE_APPLICATION_ID = os.getenv("VONAGE_APPLICATION_ID")      # Also used in subscriber.html
VONAGE_PRIVATE_KEY_PATH = os.getenv("VONAGE_PRIVATE_KEY_PATH")


# AWS Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")


# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

