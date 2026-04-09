"""User management API tests."""
import pytest


class TestGetUsers:
    """Test get users endpoint."""
    
    def test_get_users_as_admin(self, client, auth_headers):
        """Test getting users list as admin."""
        response = client.get("/api/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert len(data["data"]) >= 2  # admin and operator
    
    def test_get_users_as_operator(self, client, operator_token):
        """Test getting users list as operator (should fail)."""
        headers = {"Authorization": f"Bearer {operator_token}"}
        response = client.get("/api/users", headers=headers)
        assert response.status_code == 403
    
    def test_get_users_unauthenticated(self, client):
        """Test getting users without authentication."""
        response = client.get("/api/users")
        assert response.status_code == 401
    
    def test_get_users_pagination(self, client, auth_headers):
        """Test users pagination."""
        response = client.get(
            "/api/users",
            headers=auth_headers,
            params={"page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data


class TestCreateUser:
    """Test create user endpoint."""
    
    def test_create_user_success(self, client, auth_headers):
        """Test creating a new user."""
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "testuser",
                "password": "testpass123",
                "role": "operator",
                "is_active": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["role"] == "operator"
        assert data["data"]["is_active"] is True
    
    def test_create_user_duplicate_username(self, client, auth_headers):
        """Test creating user with duplicate username."""
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "admin",  # Already exists
                "password": "testpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_create_user_short_password(self, client, auth_headers):
        """Test creating user with too short password."""
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "newuser",
                "password": "12345",  # Less than 6 chars
                "role": "operator"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_user_short_username(self, client, auth_headers):
        """Test creating user with too short username."""
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "ab",  # Less than 3 chars
                "password": "testpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 422
    
    def test_create_user_invalid_role(self, client, auth_headers):
        """Test creating user with invalid role."""
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "newuser",
                "password": "testpass123",
                "role": "superadmin"  # Invalid role
            }
        )
        assert response.status_code == 422
    
    def test_create_user_as_operator(self, client, operator_token):
        """Test creating user as operator (should fail)."""
        headers = {"Authorization": f"Bearer {operator_token}"}
        response = client.post(
            "/api/users",
            headers=headers,
            json={
                "username": "newuser",
                "password": "testpass123",
                "role": "viewer"
            }
        )
        assert response.status_code == 403


class TestUpdateUser:
    """Test update user endpoint."""
    
    def test_update_user_role(self, client, auth_headers, db_session):
        """Test updating user role."""
        # First create a user
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "updatetest",
                "password": "testpass123",
                "role": "operator"
            }
        )
        user_id = response.json()["data"]["id"]
        
        # Update role
        response = client.put(
            f"/api/users/{user_id}",
            headers=auth_headers,
            json={"role": "viewer"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["role"] == "viewer"
    
    def test_update_user_status(self, client, auth_headers):
        """Test updating user active status."""
        # Create user
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "statustest",
                "password": "testpass123",
                "role": "operator"
            }
        )
        user_id = response.json()["data"]["id"]
        
        # Deactivate user
        response = client.put(
            f"/api/users/{user_id}",
            headers=auth_headers,
            json={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["data"]["is_active"] is False
    
    def test_update_user_password(self, client, auth_headers):
        """Test updating user password."""
        # Create user
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "pwdtest",
                "password": "oldpass123",
                "role": "operator"
            }
        )
        user_id = response.json()["data"]["id"]
        
        # Update password
        response = client.put(
            f"/api/users/{user_id}",
            headers=auth_headers,
            json={"password": "newpass123"}
        )
        assert response.status_code == 200
        
        # Verify new password works
        response = client.post(
            "/api/auth/login",
            data={"username": "pwdtest", "password": "newpass123"}
        )
        assert response.status_code == 200
    
    def test_update_nonexistent_user(self, client, auth_headers):
        """Test updating non-existent user."""
        response = client.put(
            "/api/users/99999",
            headers=auth_headers,
            json={"role": "viewer"}
        )
        assert response.status_code == 404


class TestDeleteUser:
    """Test delete user endpoint."""
    
    def test_delete_user_success(self, client, auth_headers):
        """Test deleting a user."""
        # Create user
        response = client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "deletetest",
                "password": "testpass123",
                "role": "viewer"
            }
        )
        user_id = response.json()["data"]["id"]
        
        # Delete user
        response = client.delete(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify user is deleted
        response = client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_self(self, client, auth_headers):
        """Test deleting yourself (should fail)."""
        # Get current user ID
        response = client.get("/api/auth/profile", headers=auth_headers)
        user_id = response.json()["data"]["id"]
        
        # Try to delete self
        response = client.delete(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"].lower()
    
    def test_delete_nonexistent_user(self, client, auth_headers):
        """Test deleting non-existent user."""
        response = client.delete("/api/users/99999", headers=auth_headers)
        assert response.status_code == 404


class TestGetUser:
    """Test get single user endpoint."""
    
    def test_get_user_success(self, client, auth_headers):
        """Test getting a single user."""
        # Get users list first
        response = client.get("/api/users", headers=auth_headers)
        user_id = response.json()["data"][0]["id"]
        
        # Get single user
        response = client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["id"] == user_id
    
    def test_get_nonexistent_user(self, client, auth_headers):
        """Test getting non-existent user."""
        response = client.get("/api/users/99999", headers=auth_headers)
        assert response.status_code == 404
