from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from traffic_query_builder import TrafficDataQueryBuilder

# Initialize FastAPI app
app = FastAPI()

# Initialize query builder instance
query_builder = TrafficDataQueryBuilder()

class QueryRequest(BaseModel):
    road: str
    time_granularity: Optional[str] = "Per Minute"
    vehicle_type: Optional[str] = None
    lane: Optional[str] = None
    history: Optional[int] = 10

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
    query_key_parts = [f"{request.road}", f"time_granularity={request.time_granularity}", f"history={request.history}"]

    # Add optional filters
    if request.vehicle_type:
        query_key_parts.append(f"vehicle_type={request.vehicle_type}")

    query_key = ";".join(query_key_parts)

    print(f"Received query request: {query_key}")

    # Execute query
    result = query_builder.query_orchestrator(query_key)
    return {"result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8050, reload=False)
