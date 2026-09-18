
from app.infrastructure.config import settings
"""
Credentials store for maintenance access.
This class provides access to the maintenance username and password from the application settings.
For now this is coming from configuration settings.
"""
class BasicCredentialsStore:
    def __init__(self, app_settings=settings):
        self.maintenance_username : str = app_settings.maintenance_username
        self.maintenance_password : str = app_settings.maintenance_password

    def find_by_user_name(self, user_name: str):
        if user_name == "maintenance":
            return {"maintenance_username": self.maintenance_username, "maintenance_password": self.maintenance_password}
        return None