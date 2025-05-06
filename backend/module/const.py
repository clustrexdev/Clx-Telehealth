""" To store all the variables used across the applciation. """
import os
from dotenv import load_dotenv
load_dotenv()


# Base URLs
ATHENA_BASE_URL = "https://api.preview.platform.athenahealth.com"
APPLICATION_BASE_URL = "http://localhost:3000"

# CLIENT CREDENTIALS
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Athena Token
TOKEN = None
TOKEN_EXP_TIMESTAMP = None

# Vonage credentials
VONAGE_APPLICATION_ID = os.getenv("VONAGE_APPLICATION_ID")
VONAGE_PRIVATE_KEY_PATH = "private.key"


