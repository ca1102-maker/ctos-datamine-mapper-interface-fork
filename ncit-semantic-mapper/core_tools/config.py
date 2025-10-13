import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


class Config:
    """
    Configuration class for Neo4j credentials, migrated for local model usage.
    """
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    @classmethod
    def validate(cls):
        """
        Validate that all required Neo4j environment variables are set.
        """
        # This check ensures that the URI, username, AND password are all present.
        if not all([cls.NEO4J_URI, cls.NEO4J_USERNAME, cls.NEO4J_PASSWORD]):
            raise ValueError(
                "Neo4j credentials not found or are incomplete. Please set the following environment variables:\n"
                "NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD"
            )