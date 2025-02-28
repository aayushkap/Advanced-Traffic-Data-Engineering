from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from traffic_query_builder import TrafficDataQueryBuilder
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize query builder instance
query_builder = TrafficDataQueryBuilder()

class QueryRequest(BaseModel):
    road: str
    time_granularity: Optional[str] = "Per Minute"
    vehicle_type: Optional[str] = "car"
    history: Optional[int] = 10

def format_metadata(data: dict) -> dict:
    menus = {}
    for item in data:
        region = item.get('region')
        road = item.get('road', '')
        # Convert underscores to spaces
        road_formatted = road.replace('_', ' ')
        # If the region already exists, add the road if it's not already there
        if region in menus:
            if road_formatted not in menus[region]['submenus']:
                menus[region]['submenus'].append(road_formatted)
        else:
            menus[region] = {'submenus': [road_formatted]}
    return menus

def post_process_result(result: dict, road:str) -> dict:

    for k, v in result.items():
        if v is None or v == []:
            print("No Data")
            return {}
    
    # --- Process Traffic Volume ---
    traffic_volume_data = {}
    for record in result.get('total_speeding_vehicles', []):
        print(record)
        time = record["time_per"]
        if time not in traffic_volume_data:
            traffic_volume_data[time] = {"time_per": time, "car": 0, "truck": 0, "violations": 0}
        traffic_volume_data[time]["violations"] = record["total_speeding_vehicles"]

    for record in result.get("traffic_volume", []):
        time = record["time_per"]
        vehicle_type = record["vehicle_type"].lower()
        volume = record["traffic_volume"]
        
        if time not in traffic_volume_data:
            traffic_volume_data[time] = {"time_per": time, "car": 0, "truck": 0, "violations": 0}
        
        if vehicle_type == "car":
            traffic_volume_data[time]["car"] = volume
        elif vehicle_type == "truck":
            traffic_volume_data[time]["truck"] = volume

    # Get latest timestamp data
    if traffic_volume_data:
        latest_time = max(traffic_volume_data.keys())
        latest_traffic_count = {
            "car": traffic_volume_data[latest_time]["car"],
            "truck": traffic_volume_data[latest_time]["truck"]
        }
    else:
        print("No Latest Time")
        return {}

    # --- Process AverageSpeed ---
    average_speed_data = {"count": latest_traffic_count,  # Use latest count
                          "speedingCount": {"car": 0, "truck": 0},
                          "speedLimit": {"car": 0, "truck": 0},
                          "avgSpeed": {"car": 0, "truck": 0}}

    for record in result.get("average_speed", []):
        vehicle_type = record["vehicle_type"].lower()
        avg_speed = record["average_speed"]

        average_speed_data["avgSpeed"][vehicle_type] = avg_speed

    for record in result.get("speeding_vehicles", []):
        vehicle_type = record["vehicle_type"].lower()
        speeding_count = record["speeding_vehicles"]

        average_speed_data["speedingCount"][vehicle_type] = speeding_count

    # Get speedlimit from metadata
    metadata = query_builder.get_metadata()
    for item in metadata:
        if item['road'] == road:
            average_speed_data["speedLimit"]["car"] = item['car_speed_limit']
            average_speed_data["speedLimit"]["truck"] = item['truck_speed_limit']

    # --- Lane Utilization ---
    lane_utilization_data = {}

    for record in result.get("lane_utilization", []):
        lane = f"Lane #{record['lane']}"
        vehicle_type = record["vehicle_type"].lower()
        count = record["vehicle_count"]

        if lane not in lane_utilization_data:
            lane_utilization_data[lane] = {"lane": lane, "cars": 0, "trucks": 0}

        lane_utilization_data[lane][vehicle_type + "s"] += count

    lane_utilization_data = list(lane_utilization_data.values())

    return {
        "traffic_volume": list(traffic_volume_data.values()),
        "average_speed": average_speed_data,
        "lane_utilization": lane_utilization_data
    }
    

@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {"message": "Welcome to the traffic data API!"}

@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

@app.post("/query_traffic_data")
async def query_traffic_data(request: QueryRequest):
    """
    API endpoint to build and execute traffic data queries.
    """
    # Construct query key
    print(request)
    request.road =request.road.replace(" ", "_")
    query_key_parts = [f"{request.road}", f"time_granularity={request.time_granularity}", f"history={request.history}"]

    # Add optional filters
    if request.vehicle_type:
        query_key_parts.append(f"vehicle_type={request.vehicle_type}")

    query_key = ";".join(query_key_parts)

    # Execute query
    result = query_builder.query_orchestrator(query_key)
    print("Preprocessed result: ", result)
    processed = post_process_result(result, request.road)
    print(processed)
    return {"result": processed}

@app.get("/metadata")
async def metadata():
    """
    API endpoint to return metadata about available roads
    """
    metadata = query_builder.get_metadata()
    return format_metadata(metadata)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8050, reload=False)
