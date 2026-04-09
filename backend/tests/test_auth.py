"""Authentication API tests."""
import pytest


class TestLogin:
    """Test login endpoint."""
    
    def test_login_success(self, client):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["username"] == "admin"
        assert data["data"]["user"]["role"] == "admin"
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401
    
    def test_login_operator(self, client):
        """Test operator login."""
        response = client.post(
            "/api/auth/login",
            data={"username": "operator", "password": "operator123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["user"]["role"] == "operator"


class TestProfile:
    """Test profile endpoint."""
    
    def test_get_profile_authenticated(self, client, auth_headers):
        """Test getting profile with valid token."""
        response = client.get("/api/auth/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin"
    
    def test_get_profile_unauthenticated(self, client):
        """Test getting profile without token."""
        response = client.get("/api/auth/profile")
        assert response.status_code == 401


class TestLogout:
    """Test logout endpoint."""
    
    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestPasswordChange:
    """Test password change endpoint."""
    
    def test_change_password_success(self, client, auth_headers):
        """Test successful password change."""
        response = client.put(
            "/api/auth/password",
            headers=auth_headers,
            json={
                "old_password": "admin123",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 200
        
        # Verify new password works
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "newpassword123"}
        )
        assert response.status_code == 200
    
    def test_change_password_wrong_old(self, client, auth_headers):
        """Test password change with wrong old password."""
        response = client.put(
            "/api/auth/password",
            headers=auth_headers,
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
