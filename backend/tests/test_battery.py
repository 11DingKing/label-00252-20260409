"""Battery System API tests."""
import pytest


class TestBatterySystems:
    """Test battery systems endpoints."""
    
    def test_get_battery_systems(self, client, auth_headers):
        """Test getting all battery systems."""
        response = client.get("/api/battery/systems", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_get_battery_systems_unauthenticated(self, client):
        """Test getting battery systems without authentication."""
        response = client.get("/api/battery/systems")
        assert response.status_code == 401


class TestBatteryRealtime:
    """Test battery realtime endpoint."""
    
    def test_get_battery_realtime(self, client, auth_headers):
        """Test getting real-time battery data."""
        response = client.get("/api/battery/realtime", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestBatterySystemCRUD:
    """Test battery system CRUD operations."""
    
    def test_create_battery_system(self, client, auth_headers):
        """Test creating a new battery system."""
        response = client.post(
            "/api/battery/systems",
            headers=auth_headers,
            json={
                "name": "Test Battery System",
                "capacity_kwh": 500.0,
                "max_charge_rate": 100.0,
                "max_discharge_rate": 100.0,
                "charge_efficiency": 0.95,
                "discharge_efficiency": 0.95,
                "min_soc": 0.1,
                "max_soc": 0.9
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Battery System"
    
    def test_get_battery_system_by_id(self, client, auth_headers):
        """Test getting a battery system by ID."""
        # First create a system
        create_response = client.post(
            "/api/battery/systems",
            headers=auth_headers,
            json={
                "name": "Test Battery System 2",
                "capacity_kwh": 600.0,
                "max_charge_rate": 150.0,
                "max_discharge_rate": 150.0,
                "charge_efficiency": 0.95,
                "discharge_efficiency": 0.95,
                "min_soc": 0.1,
                "max_soc": 0.9
            }
        )
        system_id = create_response.json()["data"]["id"]
        
        # Then get it
        response = client.get(f"/api/battery/systems/{system_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Test Battery System 2"
    
    def test_update_battery_system(self, client, auth_headers):
        """Test updating a battery system."""
        # First create a system
        create_response = client.post(
            "/api/battery/systems",
            headers=auth_headers,
            json={
                "name": "Test Battery System 3",
                "capacity_kwh": 500.0,
                "max_charge_rate": 100.0,
                "max_discharge_rate": 100.0,
                "charge_efficiency": 0.95,
                "discharge_efficiency": 0.95,
                "min_soc": 0.1,
                "max_soc": 0.9
            }
        )
        system_id = create_response.json()["data"]["id"]
        
        # Then update it
        response = client.put(
            f"/api/battery/systems/{system_id}",
            headers=auth_headers,
            json={
                "capacity_kwh": 800.0,
                "max_charge_rate": 200.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["capacity_kwh"] == 800.0
    
    def test_get_nonexistent_battery_system(self, client, auth_headers):
        """Test getting a non-existent battery system."""
        response = client.get("/api/battery/systems/99999", headers=auth_headers)
        assert response.status_code == 404
