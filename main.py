from http.server import BaseHTTPRequestHandler, HTTPServer
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from urllib.parse import urlparse, parse_qs
import base64
import json
import jwt
import datetime

#project 2
import sqlite3

hostName = "localhost"
serverPort = 8080

#project 2
#Open or create SQLite database file
db_connection = sqlite3.connect("totally_not_my_privateKeys.db")
db_cursor = db_connection.cursor()

#Create keys table if it does not exist
db_cursor.execute('''CREATE TABLE IF NOT EXISTS keys(
                    kid INTEGER PRIMARY KEY AUTOINCREMENT,
                    key BLOB NOT NULL,
                    exp INTEGER NOT NULL
                    )''')

#Generate private keys
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
expired_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.TraditionalOpenSSL,
                                encryption_algorithm=serialization.NoEncryption())

expired_pem = expired_key.private_bytes(encoding=serialization.Encoding.PEM,
                                         format=serialization.PrivateFormat.TraditionalOpenSSL,
                                         encryption_algorithm=serialization.NoEncryption())


def int_to_base64(value):
    """Convert an integer to a Base64URL-encoded string"""
    value_hex = format(value, 'x')
    # Ensure even length
    if len(value_hex) % 2 == 1:
        value_hex = '0' + value_hex
    value_bytes = bytes.fromhex(value_hex)
    encoded = base64.urlsafe_b64encode(value_bytes).rstrip(b'=')
    return encoded.decode('utf-8')

# Function to store keys in the database
def store_key_in_db(key, exp):
    db_cursor.execute("INSERT INTO keys(key, exp) VALUES (?, ?)", (key, exp))
    db_connection.commit()

# Store private keys in the database
store_key_in_db(pem, datetime.datetime.utcnow() + datetime.timedelta(hours=1))
store_key_in_db(expired_pem, datetime.datetime.utcnow() - datetime.timedelta(hours=1))

class MyServer(BaseHTTPRequestHandler):
    def do_PUT(self):
        self.send_response(405)
        self.end_headers()
        return

    def do_PATCH(self):
        self.send_response(405)
        self.end_headers()
        return

    def do_DELETE(self):
        self.send_response(405)
        self.end_headers()
        return

    def do_HEAD(self):
        self.send_response(405)
        self.end_headers()
        return

    def do_POST(self):
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)
        if parsed_path.path == "/auth":
            headers = {"kid": "goodKID"}
            token_payload = {"user": "username", "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}

            # Check if "expired" query parameter is present
            if 'expired' in params:
                headers["kid"] = "expiredKID"
                # Retrieve expired key from database
                db_cursor.execute("SELECT key FROM keys WHERE exp < ?", (datetime.datetime.utcnow(),))
                key_data = db_cursor.fetchone()
            else:
                # Retrieve valid (unexpired) key from database
                db_cursor.execute("SELECT key FROM keys WHERE exp >= ?", (datetime.datetime.utcnow(),))
                key_data = db_cursor.fetchone()

            if key_data:
                private_key = serialization.load_pem_private_key(key_data[0], password=None)
                encoded_jwt = jwt.encode(token_payload, private_key, algorithm="RS256", headers=headers)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(encoded_jwt, "utf-8"))
                return

        self.send_response(405)
        self.end_headers()
        return


def do_GET(self):
    if self.path == "/.well-known/jwks.json":
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        keys = {
            "keys": []
        }
        # Retrieve valid (non-expired) keys from database
        db_cursor.execute("SELECT key, kid FROM keys WHERE exp >= ?", (datetime.datetime.utcnow(),))
        rows = db_cursor.fetchall()
        for row in rows:
            key_dict = {
                "alg": "RS256",
                "kty": "RSA",
                "use": "sig",
                "kid": f"key_{row[1]}",
                "n": int_to_base64(row[0].public_numbers().n),
                "e": int_to_base64(row[0].public_numbers().e),
            }
            keys["keys"].append(key_dict)
        self.wfile.write(bytes(json.dumps(keys), "utf-8"))
        return


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
