import requests
import json
import os
import time

# Server URL
base_url = "http://localhost:5000"

# File path - absolute path
file_path = "/Users/a677022/Desktop/woodman/boq_app/uploads/Blank BOQ AIS ASP Zeer รังสิต-1.xlsx"

# First request - process BOQ file
def process_boq():
    print("Processing BOQ file...")
    
    # Prepare the file for upload
    files = {
        'file': (os.path.basename(file_path), open(file_path, 'rb'), 
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    # Make the POST request
    response = requests.post(
        f"{base_url}/api/process-boq",
        files=files
    )
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"Successfully processed BOQ file")
            print(f"Session ID: {result.get('session_id')}")
            print(f"Match rate: {result.get('summary', {}).get('match_rate', 0):.2f}%")
            return result.get('session_id')
        else:
            print(f"Error: {result.get('error')}")
            return None
    else:
        print(f"Error: HTTP status {response.status_code}")
        return None

# Second request - generate final BOQ
def generate_final_boq(session_id):
    print(f"Generating final BOQ for session {session_id}...")
    
    # Prepare request data
    data = {
        'session_id': session_id
    }
    
    # Make the POST request
    response = requests.post(
        f"{base_url}/api/generate-final-boq",
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"Successfully generated final BOQ")
            print(f"Filename: {result.get('filename')}")
            print(f"Items processed: {result.get('items_processed')}")
            print(f"Debug info: {result.get('debug_info')}")
            return result.get('filename')
        else:
            print(f"Error: {result.get('error')}")
            return None
    else:
        print(f"Error: HTTP status {response.status_code}")
        return None

# Run the complete workflow
def main():
    # Step 1: Process the BOQ file
    session_id = process_boq()
    
    if not session_id:
        print("Failed to process BOQ file. Exiting.")
        return
    
    # Wait a moment for server processing (optional)
    time.sleep(1)
    
    # Step 2: Generate the final BOQ
    filename = generate_final_boq(session_id)
    
    if not filename:
        print("Failed to generate final BOQ. Exiting.")
        return

if __name__ == "__main__":
    main()