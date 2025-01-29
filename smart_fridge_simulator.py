import os
import time
import uuid
import random
import requests
from datetime import datetime, timedelta
from azure.iot.device import IoTHubDeviceClient, Message

# ---------------------------------------------------------
# CONFIG - ADAPT AS NEEDED
# ---------------------------------------------------------
IOTHUB_DEVICE_CONNECTION_STRING = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING", "")
REST_API_BASE_URL = os.getenv("REST_API_BASE_URL", "http://127.0.0.1:5000")

# Safe temperature range
SAFE_TEMP_MIN = 1.0
SAFE_TEMP_MAX = 5.0

current_temperature = random.uniform(SAFE_TEMP_MIN, SAFE_TEMP_MAX)
inventory_items = [
    {
        "id": str(uuid.uuid4()),
        "deviceId": "MyFridge01",
        "itemName": "Milk",
        "quantity": 2,
        "expirationDate": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
    },
    {
        "id": str(uuid.uuid4()),
        "deviceId": "MyFridge01",
        "itemName": "Eggs",
        "quantity": 12,
        "expirationDate": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
    }
]

enable_iot_telemetry = bool(IOTHUB_DEVICE_CONNECTION_STRING)
iot_client = None
if enable_iot_telemetry:
    iot_client = IoTHubDeviceClient.create_from_connection_string(IOTHUB_DEVICE_CONNECTION_STRING)

def send_temperature_to_iot_hub(temp):
    if not iot_client:
        print("IoT Client not configured. Skipping IoT Hub send.")
        return
    data_payload = {
        "deviceId": "MyFridge01",
        "temperature": temp,
        "timestamp": datetime.utcnow().isoformat()
    }
    msg_str = str(data_payload)
    message = Message(msg_str)
    iot_client.send_message(message)
    print(f"[IoT Hub] Sent telemetry: {msg_str}")

def call_rest_api_to_add_telemetry(temp):
    if not REST_API_BASE_URL:
        print("No REST_API_BASE_URL set. Skipping direct REST call.")
        return
    data_payload = {
        "deviceId": "MyFridge01",
        "temperature": temp,
        "timestamp": datetime.utcnow().isoformat()
    }
    url = f"{REST_API_BASE_URL}/telemetry"
    try:
        r = requests.post(url, json=data_payload)
        if r.status_code == 201:
            print("[REST API] Telemetry posted successfully.")
        else:
            print(f"[REST API] Failed to post telemetry. Status: {r.status_code}, Msg: {r.text}")
    except Exception as e:
        print(f"[REST API] Error posting telemetry: {e}")

def check_temperature_and_alert(temp):
    if temp < SAFE_TEMP_MIN or temp > SAFE_TEMP_MAX:
        print(f"*** ALERT *** Temperature {temp:.2f}°C out of safe range ({SAFE_TEMP_MIN}-{SAFE_TEMP_MAX})!")

def update_temperature():
    global current_temperature
    delta = random.uniform(-0.5, 0.5)
    current_temperature += delta
    if current_temperature < -5:
        current_temperature = -5
    elif current_temperature > 15:
        current_temperature = 15
    return current_temperature

def manage_inventory():
    today = datetime.now().date()
    for item in inventory_items:
        exp_date = datetime.strptime(item["expirationDate"], "%Y-%m-%d").date()
        days_left = (exp_date - today).days
        if days_left <= 2:
            print(f"Warning: {item['itemName']} expires in {days_left} day(s).")
        if item["quantity"] <= 1:
            print(f"Low stock: {item['itemName']} only has {item['quantity']} left.")

def add_inventory_item():
    item_name = input("Enter item name: ")
    quantity = int(input("Enter quantity: "))
    days_until_expire = int(input("Enter days until expiration: "))
    new_item = {
        "id": str(uuid.uuid4()),
        "deviceId": "MyFridge01",
        "itemName": item_name,
        "quantity": quantity,
        "expirationDate": (datetime.now() + timedelta(days=days_until_expire)).strftime("%Y-%m-%d")
    }
    inventory_items.append(new_item)
    print(f"Added new item: {new_item}")

def call_rest_api_for_inventory_sync():
    if not REST_API_BASE_URL:
        print("No REST_API_BASE_URL set. Skipping inventory sync.")
        return
    for item in inventory_items:
        url = f"{REST_API_BASE_URL}/inventory"
        try:
            r = requests.post(url, json=item)
            if r.status_code == 201:
                print(f"[REST API] Inventory item posted: {item['itemName']}")
            else:
                print(f"[REST API] Failed to post {item['itemName']}. Status: {r.status_code}")
        except Exception as e:
            print(f"[REST API] Error posting inventory item: {e}")

def get_recipe_suggestions():
    if not REST_API_BASE_URL:
        print("No REST_API_BASE_URL set. Can't fetch recipe suggestions.")
        return
    url = f"{REST_API_BASE_URL}/recipes"  # must match the route in your REST API
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            print("Recipe Suggestions:")
            print(data)  # or parse as needed
        else:
            print(f"Failed to get recipes. Status: {r.status_code}, {r.text}")
    except Exception as e:
        print(f"Error calling recipe endpoint: {e}")

def display_dashboard():
    print("-------------------------------------------------")
    print(" SMART FRIDGE DASHBOARD")
    print("-------------------------------------------------")
    print(f" Current Temperature: {current_temperature:.2f}°C")
    print(" Inventory Items:")
    for item in inventory_items:
        print(f"  - {item['itemName']}, Qty: {item['quantity']}, Exp: {item['expirationDate']} (id={item['id']})")
    print("-------------------------------------------------")

def main():
    print("=== Smart Fridge Simulator ===")
    print("Features:")
    print("1) Temperature monitoring (IoT Hub or direct REST).")
    print("2) Inventory management (local or sync to REST).")
    print("3) Recipe suggestions from REST API.")
    print("4) Basic text-based dashboard.")

    while True:
        print("\nMenu:")
        print("1. Update Temperature & Send Telemetry")
        print("2. Check & Manage Inventory (Local)")
        print("3. Add Inventory Item (Local)")
        print("4. Display Dashboard")
        print("5. Sync Inventory with REST API")
        print("6. Get Recipe Suggestions")
        print("7. Quit")

        choice = input("Select an option: ")
        if choice == "1":
            new_temp = update_temperature()
            print(f"New Temperature: {new_temp:.2f}°C")
            check_temperature_and_alert(new_temp)
            if IOTHUB_DEVICE_CONNECTION_STRING:
                send_temperature_to_iot_hub(new_temp)
            else:
                call_rest_api_to_add_telemetry(new_temp)

        elif choice == "2":
            manage_inventory()

        elif choice == "3":
            add_inventory_item()

        elif choice == "4":
            display_dashboard()

        elif choice == "5":
            call_rest_api_for_inventory_sync()

        elif choice == "6":
            get_recipe_suggestions()

        elif choice == "7":
            print("Exiting simulator. Goodbye!")
            break
        else:
            print("Invalid choice, try again.")

    if iot_client:
        iot_client.disconnect()

if __name__ == "__main__":
    main()
