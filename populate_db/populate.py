import requests
import json

endpoint = "https://data.cityofnewyork.us/resource/erm2-nwe9.json?$query=SELECT%0A%20%20%60unique_key%60%2C%0A%20%20%60created_date%60%2C%0A%20%20%60closed_date%60%2C%0A%20%20%60agency%60%2C%0A%20%20%60complaint_type%60%2C%0A%20%20%60descriptor%60%2C%0A%20%20%60latitude%60%2C%0A%20%20%60longitude%60%0AWHERE%20%60created_date%60%20%3E%3D%20%222025-09-01T00%3A00%3A00%22%20%3A%3A%20floating_timestamp%0AORDER%20BY%20%60created_date%60%20DESC%20NULL%20FIRST%0A"
# Fetch the data from the API
response = requests.get(endpoint)
data = response.json()

# Pretty print the first JSON object
if data:
    print(json.dumps(data[0], indent=4))
else:
    print("No data was retrieved from the endpoint.")
