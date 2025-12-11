"""
Keycloak Admin API integration for user management.
"""
import requests
from typing import Optional
from .config import settings


class KeycloakAdmin:
    """Helper class for Keycloak Admin API operations."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'KEYCLOAK_ADMIN_URL', None)
        self.realm = getattr(settings, 'KEYCLOAK_REALM', None)
        self.admin_username = getattr(settings, 'KEYCLOAK_ADMIN_USERNAME', None)
        self.admin_password = getattr(settings, 'KEYCLOAK_ADMIN_PASSWORD', None)
        self._token = None
    
    def _get_admin_token(self) -> str:
        """Get admin access token from Keycloak master realm."""
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        data = {
            'client_id': 'admin-cli',
            'username': self.admin_username,
            'password': self.admin_password,
            'grant_type': 'password'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    
    def _get_headers(self, refresh: bool = False) -> dict:
        """Get headers with admin token for API requests."""
        if not self._token or refresh:
            self._token = self._get_admin_token()
        return {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a request with automatic token refresh on 401."""
        # Try with existing token
        if 'headers' not in kwargs:
            kwargs['headers'] = self._get_headers()
        
        response = requests.request(method, url, **kwargs)
        
        # If 401, refresh token and retry once
        if response.status_code == 401:
            kwargs['headers'] = self._get_headers(refresh=True)
            response = requests.request(method, url, **kwargs)
        
        return response
    
    def _get_user_id(self, username: str) -> Optional[str]:
        """Get user ID by username."""
        users_url = f"{self.base_url}/admin/realms/{self.realm}/users"
        params = {'username': username, 'exact': 'true'}
        
        response = self._make_request('GET', users_url, params=params)
        response.raise_for_status()
        users = response.json()
        
        if users:
            return users[0]['id']
        return None
    
    def _get_role_representation(self, role_name: str) -> Optional[dict]:
        """Get role representation by name."""
        roles_url = f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}"
        
        try:
            response = self._make_request('GET', roles_url)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def _get_user_roles(self, user_id: str) -> list:
        """Get all realm roles assigned to a user."""
        role_mapping_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        response = self._make_request('GET', role_mapping_url)
        response.raise_for_status()
        return response.json()
    
    def _remove_role_from_user(self, user_id: str, role_name: str):
        """Remove a realm role from a user."""
        role_rep = self._get_role_representation(role_name)
        if not role_rep:
            return  # Role doesn't exist, nothing to remove
        
        role_mapping_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        response = self._make_request('DELETE', role_mapping_url, json=[role_rep])
        response.raise_for_status()
    
    def _assign_role_to_user(self, user_id: str, role_name: str):
        """Assign a realm role to a user."""
        role_rep = self._get_role_representation(role_name)
        if not role_rep:
            raise Exception(f"Role {role_name} not found in Keycloak")
        
        role_mapping_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        response = self._make_request('POST', role_mapping_url, json=[role_rep])
        response.raise_for_status()
    
    def update_user_role(self, user_id: str, old_role: str, new_role: str):
        """Update a user's role by removing old role and assigning new role."""
        # Remove old application role (skip default Keycloak roles)
        if old_role in ['platform_admin', 'tenant_admin', 'user']:
            try:
                self._remove_role_from_user(user_id, old_role)
            except:
                pass  # Old role might not exist, continue
        
        # Assign new role
        if new_role in ['platform_admin', 'tenant_admin', 'user']:
            self._assign_role_to_user(user_id, new_role)
    
    def create_user(self, username: str, password: str, role: str = 'user', 
                   email: Optional[str] = None, enabled: bool = True) -> bool:
        """
        Create a user in Keycloak.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            role: Role to assign (platform_admin, tenant_admin, or user)
            email: Optional email address
            enabled: Whether the user account is enabled
            
        Returns:
            True if user was created successfully, False if user already exists
            
        Raises:
            requests.HTTPError: If creation fails for reasons other than user exists
        """
        users_url = f"{self.base_url}/admin/realms/{self.realm}/users"
        
        # Generate email if not provided (required by Keycloak)
        if not email:
            email = f"{username}@ecommerce.local"
        
        user_data = {
            'username': username,
            'enabled': enabled,
            'emailVerified': True,
            'email': email,
            'firstName': username.capitalize(),
            'lastName': 'User',
            'attributes': {},
            'requiredActions': [],
            'credentials': []
        }
        
        try:
            response = self._make_request('POST', users_url, json=user_data)
            
            if response.status_code == 201:
                # User created successfully, now set password and assign role
                user_id = self._get_user_id(username)
                if user_id:
                    # Set password using PUT endpoint
                    password_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/reset-password"
                    password_data = {
                        'type': 'password',
                        'value': password,
                        'temporary': False
                    }
                    pwd_response = self._make_request('PUT', password_url, json=password_data)
                    pwd_response.raise_for_status()
                    
                    # Assign role
                    if role:
                        self._assign_role_to_user(user_id, role)
                return True
            elif response.status_code == 409:
                # User already exists
                return False
            else:
                response.raise_for_status()
                return False
        except requests.HTTPError as e:
            if e.response.status_code == 409:
                return False
            raise
    
    def delete_user(self, username: str) -> bool:
        """
        Delete a user from Keycloak.
        
        Args:
            username: Username to delete
            
        Returns:
            True if user was deleted, False if user not found
        """
        # First, get user ID by username
        users_url = f"{self.base_url}/admin/realms/{self.realm}/users"
        params = {'username': username, 'exact': 'true'}
        
        try:
            response = self._make_request('GET', users_url, params=params)
            response.raise_for_status()
            users = response.json()
            
            if not users:
                return False
            
            user_id = users[0]['id']
            delete_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}"
            response = self._make_request('DELETE', delete_url)
            
            return response.status_code == 204
        except requests.HTTPError:
            return False
    
    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists in Keycloak.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        users_url = f"{self.base_url}/admin/realms/{self.realm}/users"
        params = {'username': username, 'exact': 'true'}
        
        try:
            response = self._make_request('GET', users_url, params=params)
            response.raise_for_status()
            users = response.json()
            return len(users) > 0
        except requests.HTTPError:
            return False


# Singleton instance
keycloak_admin = KeycloakAdmin()
