"""
Test script to verify that the patched version works correctly
"""
import requests
import json
import os
import time
import subprocess
import sys
import signal
import threading

def run_server():
    """Run the patched server in a separate process"""
    print("Starting the patched BOQ server...")
    server_process = subprocess.Popen(["python", "main_patched.py"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
    
    # Give the server time to start
    time.sleep(3)
    return server_process

def test_api(server_process):
    """Test the API with the patched server"""
    base_url = "http://localhost:5000"
    
    # File path
    file_path = "uploads/Blank BOQ AIS ASP Zeer รังสิต-1.xlsx"
    
    if not os.path.exists(file_path):
        print(f"Test file not found: {file_path}")
        return False
        
    try:
        # Step 1: Process BOQ
        print("\n=== Testing process-boq endpoint ===")
        files = {
            'file': (os.path.basename(file_path), open(file_path, 'rb'), 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(f"{base_url}/api/process-boq", files=files)
        
        if response.status_code != 200:
            print(f"Error: HTTP status {response.status_code}")
            return False
            
        result = response.json()
        if not result.get('success'):
            print(f"Error: {result.get('error')}")
            return False
            
        session_id = result.get('session_id')
        print(f"Successfully processed BOQ file")
        print(f"Session ID: {session_id}")
        print(f"Match rate: {result.get('summary', {}).get('match_rate', 0):.2f}%")
        
        # Step 2: Generate final BOQ
        print("\n=== Testing generate-final-boq endpoint ===")
        data = {'session_id': session_id}
        
        response = requests.post(
            f"{base_url}/api/generate-final-boq",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP status {response.status_code}")
            return False
            
        result = response.json()
        if not result.get('success'):
            print(f"Error: {result.get('error')}")
            return False
            
        filename = result.get('filename')
        items_processed = result.get('items_processed')
        debug_info = result.get('debug_info', {})
        
        print(f"Successfully generated final BOQ")
        print(f"Filename: {filename}")
        print(f"Items processed: {items_processed}")
        print(f"Items with zero cost: {debug_info.get('items_with_zero_cost', 0)}")
        print(f"Items with zero quantity: {debug_info.get('items_with_zero_qty', 0)}")
        
        # Verify the output file
        output_path = os.path.join("output", filename)
        if not os.path.exists(output_path):
            print(f"Output file not found: {output_path}")
            return False
            
        print(f"Output file created: {output_path}")
        
        # The test passed if we have items processed and non-zero costs
        success = (items_processed > 0 and debug_info.get('items_with_zero_cost', 0) < items_processed)
        if success:
            print("\n✅ TEST PASSED - Items were successfully processed with non-zero costs")
        else:
            print("\n❌ TEST FAILED - Items still have zero costs")
            
        return success
    
    except Exception as e:
        print(f"Error during testing: {e}")
        return False
    finally:
        # Stop the server
        if server_process:
            print("\nStopping the server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    server_process = run_server()
    
    try:
        # Run the test in a separate thread
        test_thread = threading.Thread(target=test_api, args=(server_process,))
        test_thread.start()
        
        # Wait for the test to complete (with timeout)
        test_thread.join(timeout=60)
        
        if test_thread.is_alive():
            print("Test timed out after 60 seconds")
            server_process.terminate()
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        server_process.terminate()
    
    finally:
        # Make sure the server is stopped
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
        
        print("Server stopped")