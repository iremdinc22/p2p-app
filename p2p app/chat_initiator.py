import socket
import json
import os
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Util.number import getPrime
import base64

def get_private_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('10.255.255.255', 1))
        private_ip = sock.getsockname()[0]
    except Exception:
        private_ip = '127.0.0.1'
    finally:
        sock.close()
    return private_ip

def get_available_users():
    try:
        json_path = os.path.expanduser('users.json')
        with open(json_path) as f:
            users = json.load(f)
            now = datetime.now()
            online_users = [user['username'] for user in users if now - datetime.strptime(user['timestamp'], '%Y-%m-%d %H:%M:%S') < timedelta(seconds=10)]
            offline_users = [user['username'] for user in users if user['username'] not in online_users]
            
            print("Offline users:", *offline_users, sep="\n")
            print("\n------------------------\n")
            print("Online users:", *online_users, sep="\n")
            
            return online_users
    except (FileNotFoundError, json.JSONDecodeError):
        print("Users information not found or error decoding users information.")
        return []

def select_user(users):
    print("\nWhich user do you want to chat with?")
    for index, user in enumerate(users, 1):
        print(f"{index}-) {user}")
    while True:
        try:
            choice = int(input("Enter the number of the user: "))
            if 1 <= choice <= len(users):
                return users[choice - 1]
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def initiate_chat():
    available_users = get_available_users()
    if not available_users:
        print("No users available.")
        return

    selected_user = select_user(available_users)
    print(f"Selected user: {selected_user}")

    my_username = input("Enter your username: ")
    secure_chat = input("Do you want to chat securely? (yes/no): ").strip().lower() == "yes"
    server_ip = get_private_ip()
    port = 6001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, port))
        sock.sendall(my_username.encode())
        print("Connected to the server...")

        with open("chat_history.txt", "a") as chat_history:
            chat_history.write(f"Connected to {server_ip}:{port} as {my_username}\n")

        if secure_chat:
            client_private_key = getPrime(128)
            client_public_key = pow(2, client_private_key, 23)
            sock.sendall(json.dumps({"key": str(client_public_key)}).encode())
            response = json.loads(sock.recv(1024).decode())
            server_public_key = int(response["key"])
            shared_key = pow(server_public_key, client_private_key, 23)
            shared_key = scrypt(str(shared_key), b'salt', 32, N=2**14, r=8, p=1)
            print(f"Secure chat initiated. Shared key: {shared_key.hex()}")
            with open("chat_history.txt", "a") as chat_history:
                chat_history.write(f"Secure chat initiated. Shared key: {shared_key.hex()}\n")

        while True:
            message = input("Enter your message: ")
            if secure_chat:
                cipher = AES.new(shared_key, AES.MODE_EAX)
                ciphertext, tag = cipher.encrypt_and_digest(message.encode())
                encrypted_message = {
                    "encrypted message": base64.b64encode(ciphertext).decode(),
                    "nonce": base64.b64encode(cipher.nonce).decode(),
                    "tag": base64.b64encode(tag).decode()
                }
                sock.sendall(json.dumps(encrypted_message).encode())
                with open("chat_history.txt", "a") as chat_history:
                    chat_history.write(f"{my_username}: {message} (encrypted: {ciphertext.hex()})\n")
            else:
                sock.sendall(message.encode())
                with open("chat_history.txt", "a") as chat_history:
                    chat_history.write(f"{my_username}: {message}\n")

            response = sock.recv(1024)
            if secure_chat:
                response_data = json.loads(response.decode())
                nonce = base64.b64decode(response_data["nonce"])
                ciphertext = base64.b64decode(response_data["encrypted message"])
                tag = base64.b64decode(response_data["tag"])
                cipher = AES.new(shared_key, AES.MODE_EAX, nonce=nonce)
                decrypted_message = cipher.decrypt_and_verify(ciphertext, tag)
                print(f"{selected_user}: {decrypted_message.decode()} (hex: {ciphertext.hex()})")
                with open("chat_history.txt", "a") as chat_history:
                    chat_history.write(f"{selected_user}: {decrypted_message.decode()} (hex: {ciphertext.hex()})\n")
            else:
                print(f"{selected_user}: {response.decode()}")
                with open("chat_history.txt", "a") as chat_history:
                    chat_history.write(f"{selected_user}: {response.decode()}\n")

    except Exception as e:
        print("An error occurred:", e)
    finally:
        sock.close()

initiate_chat()
