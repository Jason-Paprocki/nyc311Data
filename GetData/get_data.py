import requests
import json

base_endpoint = 'https://data.cityofnewyork.us/resource/erm2-nwe9.json?$query=SELECT%0A%20%20%60unique_key%60%2C%0A%20%20%60created_date%60%2C%0A%20%20%60closed_date%60%2C%0A%20%20%60agency%60%2C%0A%20%20%60agency_name%60%2C%0A%20%20%60complaint_type%60%2C%0A%20%20%60descriptor%60%2C%0A%20%20%60location_type%60%2C%0A%20%20%60incident_zip%60%2C%0A%20%20%60incident_address%60%2C%0A%20%20%60street_name%60%2C%0A%20%20%60cross_street_1%60%2C%0A%20%20%60cross_street_2%60%2C%0A%20%20%60intersection_street_1%60%2C%0A%20%20%60intersection_street_2%60%2C%0A%20%20%60address_type%60%2C%0A%20%20%60city%60%2C%0A%20%20%60landmark%60%2C%0A%20%20%60facility_type%60%2C%0A%20%20%60status%60%2C%0A%20%20%60due_date%60%2C%0A%20%20%60resolution_description%60%2C%0A%20%20%60resolution_action_updated_date%60%2C%0A%20%20%60community_board%60%2C%0A%20%20%60bbl%60%2C%0A%20%20%60borough%60%2C%0A%20%20%60x_coordinate_state_plane%60%2C%0A%20%20%60y_coordinate_state_plane%60%2C%0A%20%20%60open_data_channel_type%60%2C%0A%20%20%60park_facility_name%60%2C%0A%20%20%60park_borough%60%2C%0A%20%20%60vehicle_type%60%2C%0A%20%20%60taxi_company_borough%60%2C%0A%20%20%60taxi_pick_up_location%60%2C%0A%20%20%60bridge_highway_name%60%2C%0A%20%20%60bridge_highway_direction%60%2C%0A%20%20%60road_ramp%60%2C%0A%20%20%60bridge_highway_segment%60%2C%0A%20%20%60latitude%60%2C%0A%20%20%60longitude%60%2C%0A%20%20%60location%60%0AORDER%20BY%20%60created_date%60%20DESC%20NULL%20FIRST'

limit = 1000
offset = 0
all_data = []

while True:
    # Append the limit and offset to the query
    paginated_endpoint = f"{base_endpoint} LIMIT {limit} OFFSET {offset}"

    print(f"Fetching data with offset: {offset}")
    response = requests.get(paginated_endpoint)

    # Check for a successful response
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        break

    data = response.json()

    # If no data is returned, we've reached the end
    if not data:
        print("No more data to fetch.")
        break

    # Add the fetched data to our list
    all_data.extend(data)

    # Increment the offset for the next page
    offset += limit
    if offset >= 10000:
        break

print(f"\nTotal records fetched: {len(all_data)}")

# Optionally, save all data to a file
with open('all_nyc_311_data.json', 'w') as f:
    json.dump(all_data, f, indent=4)

print("All data saved to all_nyc_311_data.json")
