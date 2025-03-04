import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')

    # Get database credentials from .env
    DB_SERVER = os.environ.get("DB_SERVER", "your-server.database.windows.net")
    DB_NAME = os.environ.get("DB_NAME", "your-database-name")
    DB_USERNAME = os.environ.get("DB_USERNAME", "your-db-username")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "your-db-password")
    OPERATING_SYS = os.environ.get("OPERATING_SYS", "MAC")

    # SQLAlchemy connection string paramaters
    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
    )

    GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

    if(OPERATING_SYS=="MAC"):
    
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
    
    else:
    
        SQLALCHEMY_DATABASE_URI = f"mssql+pymssql://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"
    



    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False

    # MSAL configuration
    CLIENT_ID = os.environ.get("CLIENT_ID", "your_client_id")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "your_client_secret")
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPES = ["User.Read"]