import wifi
import socketpool
import time
import json
import board
import digitalio
import reciver


# Credenziali WiFi
with open(".env") as f:
    SSID = f.readline().split('"')[1]
    PASSWORD = f.readline().split('"')[1]

print("Connettendo al WiFi...")
wifi.radio.connect(SSID, PASSWORD)
ip = wifi.radio.ipv4_address
print("Connesso! IP:", ip)

pool = socketpool.SocketPool(wifi.radio)
server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
server.settimeout(None)
server.bind((str(ip), 80))
server.listen(1)

def get_webpage():
    # Non serve più se usi invio a blocchi, ma puoi tenerla per altri usi
    with open("index.html", "r") as f:
        html = f.read()
    return html.replace("{{ip}}", str(ip))

def send_file_in_chunks(conn, filename, chunk_size=512):
    with open(filename, "rb") as f:  # binario!
        # Invio header HTTP (testo, lo encode)
        header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        conn.send(header.encode("utf-8"))

        while True:
            chunk = f.read(chunk_size)  # leggo chunk di byte
            if not chunk:
                break
            conn.send(chunk)  # invio byte senza encode
            
def send_webpage(conn, filename="index.html", chunk_size=256):
    header = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
    conn.send(header.encode("utf-8"))
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            conn.send(chunk)
            time.sleep(0.01)  # piccolo delay per non saturare buffer

print("Server in ascolto su http://{}".format(ip))

while True:
    try:
        conn, addr = server.accept()
        reciver.conn = conn
        
        print("Connessione da", addr)

        buffer = bytearray(2048)
        num_bytes = conn.recv_into(buffer)
        request = buffer[:num_bytes].decode("utf-8")
        print("Richiesta:", request)

        if "POST" in request:
            headers_end = request.find("\r\n\r\n")
            body = request[headers_end + 4:]
            print("Body ricevuto:", body)

            try:
                json_data = json.loads(body)
                print("JSON ricevuto:", json_data)
                reciver.onRequestRecived(json_data.get("type"), json_data.get("value"))

            except Exception as e:
                print("Errore parsing JSON: ", e)

            conn.send("HTTP/1.1 200 OK\r\n\r\nComando ricevuto.".encode("utf-8"))

        else:
            send_webpage(conn)

        conn.close()

    except Exception as e:
        print("Errore:", e)
        continue
