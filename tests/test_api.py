import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_calculate_add():
    response = client.post("/calculate", json={"operation": "add", "operands": [1, 2, 3]})
    assert response.status_code == 200
    assert response.json() == {"result": 6.0}

def test_calculate_subtract():
    response = client.post("/calculate", json={"operation": "subtract", "operands": [10, 2, 1]})
    assert response.status_code == 200
    assert response.json() == {"result": 7.0}

def test_calculate_multiply():
    response = client.post("/calculate", json={"operation": "multiply", "operands": [2, 3, 4]})
    assert response.status_code == 200
    assert response.json() == {"result": 24.0}

def test_calculate_divide():
    response = client.post("/calculate", json={"operation": "divide", "operands": [12, 2, 2]})
    assert response.status_code == 200
    assert response.json() == {"result": 3.0}

def test_calculate_divide_by_zero():
    response = client.post("/calculate", json={"operation": "divide", "operands": [10, 0]})
    assert response.status_code == 400
    assert response.json()["detail"] == "Division by zero"

def test_calculate_invalid_op():
    response = client.post("/calculate", json={"operation": "modulo", "operands": [10, 3]})
    assert response.status_code == 400
    assert "Unsupported operation" in response.json()["detail"]

def test_calculate_empty_operands():
    response = client.post("/calculate", json={"operation": "add", "operands": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "Operands list cannot be empty"
