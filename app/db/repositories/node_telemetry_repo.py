from app.db.mongodb import get_database
from datetime import datetime, timedelta 
from app.models.infrastructure_schemas import NodeTelemetryRawModel

async def get_node_telemetry(node_identifier: str, window_minutes: int) -> list[NodeTelemetryRawModel]:
    db = get_database()
    
    time_threshold = datetime.now() - timedelta(minutes=window_minutes)
    
    query = {
        'node_identifier': node_identifier,
        'timestamp': {'$gte': time_threshold},
    } 
    
    projection = {
        "metrics.cpu_usage": 1,
        "metrics.ram_usage": 1,
        "timestamp": 1,
        "_id": 0 
    }
    
    cursor = db["node_telemetry"].find(query, projection).sort("timestamp", -1)
    
    raw_records = await cursor.to_list(length=1000) # Limit to 1000 records for performance
    
    return [NodeTelemetryRawModel(**record) for record in raw_records]
