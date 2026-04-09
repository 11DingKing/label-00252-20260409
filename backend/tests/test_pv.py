"""PV System API tests."""
import pytest


class TestPVSystems:
    """Test PV systems endpoints."""
    
    def test_get_pv_systems(self, client, auth_headers):
        """Test getting all PV systems."""
        response = client.get("/api/pv/systems", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_get_pv_systems_unauthenticated(self, client):
        """Test getting PV systems without authentication."""
        response = client.get("/api/pv/systems")
        assert response.status_code == 401


class TestPVRealtime:
    """Test PV realtime endpoint."""
    
    def test_get_pv_realtime(self, client, auth_headers):
        """Test getting real-time PV data."""
        response = client.get("/api/pv/realtime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestPVSystemCRUD:
    """Test PV system CRUD operations."""
    
    def test_create_pv_system(self, client, auth_headers):
        """Test creating a new PV system."""
        response = client.post(
            "/api/pv/systems",
            headers=auth_headers,
            json={
                "name": "Test PV System",
                "capacity_kw": 100.0,
                "efficiency": 0.18,
                "panel_area": 500.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test PV System"
    
    def test_get_pv_system_by_id(self, client, auth_headers):
        """Test getting a PV system by ID."""
        # First create a system
        create_response = client.post(
            "/api/pv/systems",
            headers=auth_headers,
            json={
                "name": "Test PV System 2",
                "capacity_kw": 150.0,
                "efficiency": 0.20,
                "panel_area": 800.0
            }
        )
        system_id = create_response.json()["data"]["id"]
        
        # Then get it
        response = client.get(f"/api/pv/systems/{system_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Test PV System 2"
    
    def test_update_pv_system(self, client, auth_headers):
        """Test updating a PV system."""
        # First create a system
        create_response = client.post(
            "/api/pv/systems",
            headers=auth_headers,
            json={
                "name": "Test PV System 3",
                "capacity_kw": 100.0,
                "efficiency": 0.18,
                "panel_area": 500.0
            }
        )
        system_id = create_response.json()["data"]["id"]
        
        # Then update it
        response = client.put(
            f"/api/pv/systems/{system_id}",
            headers=auth_headers,
            json={
                "capacity_kw": 200.0,
                "efficiency": 0.22
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["capacity_kw"] == 200.0
    
    def test_get_nonexistent_pv_system(self, client, auth_headers):
        """Test getting a non-existent PV system."""
        response = client.get("/api/pv/systems/99999", headers=auth_headers)
        assert response.status_code == 404
