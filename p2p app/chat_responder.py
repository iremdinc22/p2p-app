import socket
import json
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Util.number import getPrime

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

def start_server():
    host = get_private_ip()
    port = 6001
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print("Server started. Waiting for connections...")
        
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Got a connection from {addr}")
            
            client_username = client_socket.recv(1024).decode()
            print(f"Client username: {client_username}")

            try:
                secure_chat = False
                shared_key = None
                
                while True:
                    client_message = client_socket.recv(1024).decode()
                    if not client_message:
                        break

                    try:
                        client_message_data = json.loads(client_message)
                        if "key" in client_message_data:
                            client_key = int(client_message_data["key"])
                            server_private_key = getPrime(128)
                            server_public_key = pow(2, server_private_key, 23)
                            shared_key = pow(client_key, server_private_key, 23)
                            shared_key = scrypt(str(shared_key), b'salt', 32, N=2**14, r=8, p=1)
                            secure_chat = True
                            server_response = json.dumps({"key": str(server_public_key)})
                            client_socket.sendall(server_response.encode())
                            print(f"Secure chat initiated. Shared key: {shared_key.hex()}")
                        elif "encrypted message" in client_message_data:
                            nonce = base64.b64decode(client_message_data["nonce"])
                            ciphertext = base64.b64decode(client_message_data["encrypted message"])
                            tag = base64.b64decode(client_message_data["tag"])
                            cipher = AES.new(shared_key, AES.MODE_EAX, nonce=nonce)
                            decrypted_message = cipher.decrypt_and_verify(ciphertext, tag)
                            print(f"{client_username}: {decrypted_message.decode()} (hex: {ciphertext.hex()})")
                        else:
                            print(f"{client_username}: {client_message}")
                    except json.JSONDecodeError:
                        print(f"{client_username}: {client_message}")

                    message = input("Enter your message: ")
                    if secure_chat:
                        cipher = AES.new(shared_key, AES.MODE_EAX)
                        ciphertext, tag = cipher.encrypt_and_digest(message.encode())
                        encrypted_message = {
                            "encrypted message": base64.b64encode(ciphertext).decode(),
                            "nonce": base64.b64encode(cipher.nonce).decode(),
                            "tag": base64.b64encode(tag).decode()
                        }
                        client_socket.sendall(json.dumps(encrypted_message).encode())
                        print(f"Message encrypted with key {shared_key.hex()}: {ciphertext.hex()}")
                    else:
                        client_socket.sendall(message.encode())
            
            except Exception as e:
                print("An error occurred:", e)
            finally:
                client_socket.close()

    except Exception as e:
        print("An error occurred:", e)
    finally:
        server_socket.close()

start_server()
