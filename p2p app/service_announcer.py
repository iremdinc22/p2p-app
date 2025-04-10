import socket
import json
import time
import threading
import os

def get_local_ip():
    # Use a UDP socket to get the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public IP to get the local IP
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def service_announcement(port):
    # Retrieve the local IP address
    ip_address = get_local_ip()

    # Prompt user to enter username
    username = input("Enter your username: ")

    # Prepares the message with username and local IP address
    message = json.dumps({'username': username, 'ip_address': ip_address})

    # Creates a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # Sends the encoded message to the specified IP and port
        sock.sendto(message.encode(), (ip_address, port))

        # Write user information to users.json
        write_user_info(username, ip_address)

        # Sleeps for 8 seconds before repeating
        time.sleep(8)

def write_user_info(username, ip_address):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    user_data = {'username': username, 'timestamp': timestamp, 'ip_address': ip_address}

    users = []
    json_path = "users.json"  # Path to the JSON file

    # Check if the JSON file exists
    if os.path.exists(json_path):
        with open(json_path, "r") as infile:
            try:
                users = json.load(infile)
            except json.JSONDecodeError:
                pass

    # Check if the user with the same username exists
    user_found = False
    for user in users:
        if user['username'] == username:
            user['timestamp'] = timestamp
            user_found = True
            break

    # If user not found, append the new user data
    if not user_found:
        users.append(user_data)

    # Write the updated data back to the JSON file
    with open(json_path, "w") as outfile:
        json.dump(users, outfile, indent=4)

# Starts the service announcement thread with default arguments
threading.Thread(target=service_announcement, args=(6000,)).start()
