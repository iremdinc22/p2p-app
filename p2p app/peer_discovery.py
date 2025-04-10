import json
from datetime import datetime, timedelta
import time

# Define the path to the users.json file
file_path = 'users.json'

def check_users_status():
    # Read the JSON file
    with open(file_path, 'r') as file:
        users = json.load(file)

    # Define the time difference threshold
    time_difference_threshold = timedelta(seconds=8)

    # Create an array to store the user statuses
    user_list = []

    # Process each user
    for user in users:
        username = user['username']
        timestamp_str = user['timestamp']
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        # Get the current time for each user check
        current_time = datetime.now()

        # Calculate the time difference
        time_difference = current_time - timestamp

        # Determine the online status
        if time_difference <= time_difference_threshold:
            status = f"user {username} is online"
        else:
            status = f"user {username} is not online and its last seen is: {timestamp_str}"

        # Add the status to the user list
        user_list.append(status)

    # Print the user list
    for status in user_list:
        print(status)

# Loop to check the user status every 8 seconds
while True:
    check_users_status()
    print("-----")  # Separator for clarity
    time.sleep(8)
