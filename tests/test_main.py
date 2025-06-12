from fastapi.testclient import TestClient
import time
import pytest
from main import app

client = TestClient(app)

def test_check_pytest():
    """Basic test to verify pytest is working"""
    assert 1 + 1 == 2

def test_read_main():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_login_success():
    # Test with valid credentials
    response = client.post(
        "/v1/login",
        data={
            "login": "new-00",
            "password": "viwera9jfg89435ut80tgji0osetj0p80yt35rw4g"
        },
        follow_redirects=False  # Important to not follow the redirect
    )
    
    # Should return 302 redirect
    assert response.status_code == 302
    assert response.headers['location'] == '/'
    
    # Check cookies were set
    print(response.headers.get('set-cookie'))
    print(response.cookies)

    # Verify cookies work by following redirect manually
    protected_response = client.get(
        '/',
        cookies=response.cookies
    )
    assert protected_response.status_code == 200

    response = client.post(
        "/v1/logout"
    )
    print(response.headers.get('set-cookie'))
    print(response.cookies)
    print(response.status_code)

@pytest.fixture
def cleanup_test_user():
    """Fixture to clean up test user after tests"""
    yield
    # Add cleanup logic here if needed
    # For example, delete the test user from database

def test_user_register(cleanup_test_user):
    """Test user registration and subsequent login"""
    # Register new user
    register_response = client.post(
        "/v1/register",
        data={
            "login": "test_login",
            "password": "test_pass",
            "password_again": "test_pass",
            "email": 'test@testservice.com'
        }
    )
    assert register_response.status_code == 200

    # Add delay to ensure registration completes
    time.sleep(2)

    # Test login with new credentials
    login_response = client.post(
        "/v1/login",
        data={
            "login": "test_login",
            "password": "test_pass"
        },
        follow_redirects=False
    )
    
    assert login_response.status_code == 302
    assert login_response.headers['location'] == '/'
    
    # Verify the login actually works
    protected_response = client.get(
        '/',
        cookies=login_response.cookies
    )
    assert protected_response.status_code == 200