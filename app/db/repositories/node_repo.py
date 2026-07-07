from app.db.mongodb import get_database
from app.models.infrastructure_schemas import NeInventoryModel
from app.schemas.node_health_dto import SSHConnectionInfo

async def find_node_by_identifier(host_identifier: str) -> SSHConnectionInfo:
    try:
        db = get_database()
    except Exception as e:
        raise ConnectionError(f"Không thể kết nối MongoDB: {e}")

    raw_record = await db["ne_inventory"].find_one({
        "$or": [{"ip": host_identifier}, {"ne_name": host_identifier}]
    })

    if not raw_record:
        raise ValueError(f"Không tìm thấy thiết bị {host_identifier} trong kho hạ tầng.")

    return NeInventoryModel(**raw_record)
    
