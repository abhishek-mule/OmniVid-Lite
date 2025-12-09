import httpx

# Test video generation
try:
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/api/v1/render/render",
            json={"prompt": "A blue circle moves from left to right", "creative": False}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
