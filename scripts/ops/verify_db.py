
import requests
import json
import time

BASE_URL = "https://a2a-agent-node-72l52c6ndq-an.a.run.app"

def test_db():
    print(f"Testing connectivity to {BASE_URL}...")
    
    # 1. Register a project
    new_project = {
        "name": f"Test Project {int(time.time())}",
        "description": "Validation test for Cloud SQL",
        "apiUrl": "https://example.com/api",
        "ownerDid": "did:ethr:0x1234567890abcdef"
    }
    
    print(f"Creating project: {new_project['name']}...")
    try:
        res = requests.post(f"{BASE_URL}/api/projects", json=new_project)
        print(f"POST Status: {res.status_code}")
        if res.status_code == 201:
            print("Project created successfully.")
            print(res.json())
        else:
            print("Failed to create project.")
            print(res.text)
            return False
            
        # 2. List projects
        print("Listing projects...")
        res = requests.get(f"{BASE_URL}/api/projects")
        print(f"GET Status: {res.status_code}")
        if res.status_code == 200:
            projects = res.json()
            print(f"Found {len(projects)} projects.")
            found = any(p['name'] == new_project['name'] for p in projects)
            if found:
                print("SUCCESS: Persistence verified.")
                return True
            else:
                print("FAILURE: Project created but not found in list.")
                return False
        else:
            print("Failed to list projects.")
            print(res.text)
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    test_db()
