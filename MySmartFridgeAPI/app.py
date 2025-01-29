import os
import uuid
from flask import Flask, request, jsonify
from azure.cosmos import CosmosClient, PartitionKey

# -----------------------------------------------------------------------------
# 1) CONFIGURATION
# -----------------------------------------------------------------------------
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://myfridgecosmosdb123gojo.documents.azure.com:443/")
COSMOS_KEY = os.getenv("COSMOS_KEY", "vRODmeJazjqLY0VQ6qhSfgkyAVcBepbkiy0XqlqgnYAslSqlfMK7lH4NKg3jNedt1aBwHgIfJwsGACDbWfTHgg==")
DATABASE_NAME = "SmartFridgeDB"
CONTAINER_NAME = "TelemetryContainer"

client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
database = client.create_database_if_not_exists(DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/deviceId")
)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Smart Fridge REST API (Cosmos-Integrated)!"

# -----------------------------------------------------------------------------
# TELEMETRY ENDPOINTS
# -----------------------------------------------------------------------------
@app.route("/telemetry", methods=["GET"])
def get_telemetry():
    query = "SELECT * FROM c WHERE c.type = 'telemetry'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return jsonify({"telemetry_data": items}), 200

@app.route("/telemetry", methods=["POST"])
def add_telemetry():
    data = request.json
    if "deviceId" not in data:
        return jsonify({"error": "deviceId is required in the payload"}), 400

    data["type"] = "telemetry"
    if "id" not in data:
        data["id"] = str(uuid.uuid4())

    created_item = container.create_item(data)
    return jsonify({
        "message": "Telemetry added",
        "item": created_item
    }), 201

# -----------------------------------------------------------------------------
# INVENTORY ENDPOINTS
# -----------------------------------------------------------------------------
@app.route("/inventory", methods=["GET"])
def get_inventory():
    query = "SELECT * FROM c WHERE c.type = 'inventory'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return jsonify({"inventory": items}), 200

@app.route("/inventory", methods=["POST"])
def add_inventory():
    item = request.json
    if "deviceId" not in item:
        item["deviceId"] = "inventoryDefault"
    item["type"] = "inventory"
    if "id" not in item:
        item["id"] = str(uuid.uuid4())

    created_item = container.create_item(item)
    return jsonify({
        "message": "Item added",
        "item": created_item
    }), 201

# -----------------------------------------------------------------------------
# RECIPE ENDPOINT (Example)
# -----------------------------------------------------------------------------
@app.route("/recipes", methods=["GET"])
def get_recipes():
    """
    For demo: returns a static list or a simple example based on inventory
    In a real scenario, you might query an external API or more complex logic
    """
    # You might look at the existing inventory in Cosmos DB, see which items are close to expiration, etc.
    # For simplicity, we'll just return some static recipes
    sample_recipes = [
        {"recipeName": "Omelette", "requiredItems": ["Eggs"]},
        {"recipeName": "Milkshake", "requiredItems": ["Milk"]},
        {"recipeName": "Scrambled Eggs", "requiredItems": ["Eggs", "Milk"]},
    ]
    return jsonify({"recipes": sample_recipes}), 200

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
