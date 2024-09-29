import requests
import json

# Base URL for OpenMRS REST API
BASE_URL = "https://demo.openmrs.org/openmrs/ws/rest/v1"
SESSION_URL = f"{BASE_URL}/session"

# Replace with your Base64 encoded API credentials (admin:Admin123)
API_KEY = "YWRtaW46QWRtaW4xMjM="  # Base64 encoded 'admin:Admin123'

# Headers for Basic Authentication
headers = {
    "Authorization": f"Basic {API_KEY}",
    "Content-Type": "application/json"
}

# Login to retrieve JSESSIONID
def login():
    response = requests.get(SESSION_URL, headers=headers)
    if response.status_code == 200 and response.json().get("authenticated"):
        jsessionid = response.cookies.get("JSESSIONID")
        print(f"Logged in successfully! JSESSIONID: {jsessionid}")
        return jsessionid
    else:
        print(f"Login failed: {response.status_code}, {response.text}")
        return None

# Fetch patient by name
def fetch_patient_by_name(jsessionid, patient_name):
    session_headers = headers.copy()
    session_headers["Cookie"] = f"JSESSIONID={jsessionid}"
    
    url = f"{BASE_URL}/patient?q={patient_name}&v=default&includeVoided=true"
    response = requests.get(url, headers=session_headers)
    res = {}
    res["status"] = 400
    res["message"] = "Failed"
    res["results"] = []
    
    if response.status_code == 200:
        json_response = response.json()
        res["status"] = 200
        res["message"] = "Successfull"
        print(json_response)
        res["results"] = json_response["results"]
        return res
    
    return res


def get_location_uuid(location, session_headers):
    url=f"{BASE_URL}/location?q={location}"
    response =requests.get(url, headers=session_headers);
    json_response= response.json().get('results', [])
    if json_response:
        return json_response["uuid"]
    else:
        return None


# Create an identifier for the patient
def create_identifier( session_headers,person_uuid):
    identifier = input("Enter the identifier (e.g., '111:CLINIC1'): ")
    location = input("Enter the location (e.g., '8d6c993e-c2cc-11de-8d13-0010c6dffd0f'): ")
    location_uuid = get_location_uuid(location, session_headers)
    preferred = input("Is this identifier preferred? (true/false): ").strip().lower() == 'true'
    
    identifier_data = {
        "identifier": identifier,
        "identifierType": person_uuid,
        "location": location_uuid,
        "preferred": preferred
    }
    
    return identifier_data

# Create a new patient
def create_patient(jsessionid, patient_data):
    session_headers = headers.copy()
    session_headers["Cookie"] = f"JSESSIONID={jsessionid}"
    
    # First, create a person
    url = f"{BASE_URL}/person"
    person_response = requests.post(url, json=patient_data, headers=session_headers)

    if person_response.status_code == 201:
        person_uuid = person_response.json()['uuid']
        print("Person created successfully.")
        
        # Create a patient identifier
        identifier_data = create_identifier(session_headers, person_uuid)
        if identifier_data is None:
            return None  # Exit if identifier creation fails
        
        # Now create a patient with the identifier
        patient_request = requests.post(f"{BASE_URL}/patient", json={
            "person": person_uuid,
            "identifiers": [identifier_data]
        }, headers=session_headers)

        if patient_request.status_code == 201:
            print(f"Patient created successfully with identifier: {identifier_data['identifier']}")
            return patient_request.json()
        else:
            print(f"Error creating patient: {patient_request.status_code}, {patient_request.text}")
            return None
    else:
        print(f"Error creating person: {person_response.status_code}, {person_response.text}")
        return None

# Update an existing patient
def update_patient(jsessionid, patient_id, patient_data):
    session_headers = headers.copy()
    session_headers["Cookie"] = f"JSESSIONID={jsessionid}"
    url = f"{BASE_URL}/patient/{patient_id}"
    response = requests.put(url, json=patient_data, headers=session_headers)
    
    if response.status_code == 200:
        print("Patient updated successfully.")
        return response.json()
    else:
        print(f"Error updating patient: {response.status_code}, {response.text}")
        return None

# Delete a patient
def delete_patient(jsessionid, patient_id):
    session_headers = headers.copy()
    session_headers["Cookie"] = f"JSESSIONID={jsessionid}"
    url = f"{BASE_URL}/patient/{patient_id}"
    response = requests.delete(url, headers=session_headers)
    data = response.json()
    print(data)
    
    if response.status_code == 204:
        print("Patient deleted successfully.")
    else:
        print(f"Error deleting patient: {response.status_code}, {response.text}")

# List deceased patients
def list_dead_patients(jsessionid):
    session_headers = headers.copy()
    session_headers["Cookie"] = f"JSESSIONID={jsessionid}"
    url = f"{BASE_URL}/person?includeVoided=true&q=all&v=default"
    response = requests.get(url, headers=session_headers)
    res = {}
    res["status"] = 400
    res["message"] = "Failed"
    res["death"] = []
    
    if response.status_code == 200:
        patients = response.json()
        res["status"] = 200
        res["message"] = "Successful"
        
        for patient in patients["results"]:
            if patient["dead"]:
                r = {}
                r[patient["display"]] = {"gender": patient["gender"], "address": patient["preferredAddress"]["display"]}
                res["death"].append(r)
        
        print(res)
        return res
    
    return res

# Logout to end the session
def logout(jsessionid):

    session_headers = headers.copy()
    session_headers["Cookie"] = f"JSESSIONID={jsessionid}"
    response = requests.delete(SESSION_URL, headers=session_headers)
    
    if response.status_code == 204:
        print("Logged out successfully.")
    else:
        print(f"Logout failed: {response.status_code}, {response.text}")

# Function to get user input for patient creation
def get_user_input():
    given_name = input("Enter given name: ")
    family_name = input("Enter family name: ")
    gender = input("Enter gender (M/F): ")
    birthdate = input("Enter birthdate (YYYY-MM-DD): ")
    
    address1 = input("Enter address: ")
    city_village = input("Enter city/village: ")
    country = input("Enter country: ")
    postal_code = input("Enter postal code: ")

    return {
        "names": [
            {
                "givenName": given_name,
                "familyName": family_name
            }
        ],
        "gender": gender,
        "birthdate": birthdate,
        "addresses": [
            {
                "address1": address1,
                "cityVillage": city_village,
                "country": country,
                "postalCode": postal_code
            }
        ]
    }

# Main interactive loop
def main():
    jsessionid = login()
    if not jsessionid:
        return  # Exit if login fails

    while True:
        print("\nSelect an option:")
        print("1. Fetch patient by name")
        print("2. Create patient")
        print("3. Update patient")
        print("4. Delete patient")
        print("5. List dead patients")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Enter patient name: ")
            patient_record = fetch_patient_by_name(jsessionid, name)
            print(json.dumps(patient_record, indent=2))

        elif choice == '2':
            patient_data = get_user_input()
            create_patient(jsessionid, patient_data)

        elif choice == '3':
            patient_id = input("Enter patient ID to update: ")
            print("Enter updated patient data as JSON:")
            patient_data_str = input("Updated patient data: ")
            try:
                patient_data = json.loads(patient_data_str)
                update_patient(jsessionid, patient_id, patient_data)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON format: {e}")

        elif choice == '4':
            patient_id = input("Enter patient ID to delete: ")
            delete_patient(jsessionid, patient_id)

        elif choice == '5':
            dead_patients = list_dead_patients(jsessionid)
            print(json.dumps(dead_patients, indent=2))

        elif choice == '6':
            logout(jsessionid)
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()