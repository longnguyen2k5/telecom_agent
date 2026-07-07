from app.schemas.alarm_dto import AlarmRepoQueryResult, NeInventoryRepoQueryResult
from app.db.mongodb import get_database
from app.models.infrastructure_schemas import AlarmHistoryModel, NeInventoryModel

async def get_alarm_history(alarm_type: str, cutoff_time: str, limit: int, alarm_table: str = "core_alarm_history") -> AlarmRepoQueryResult:
    """
    Lấy lịch sử cảnh báo từ MongoDB dựa trên loại cảnh báo và khoảng thời gian.
    """
    db = get_database()
    query = {
        'alarm_type': alarm_type,
        'event_time': {'$gte': cutoff_time}
    }
    
    raw_alarms = await db[alarm_table].find(query).to_list(length=limit)
    models = [AlarmHistoryModel(**alarm) for alarm in raw_alarms]
    
    return AlarmRepoQueryResult(
        data=models, 
        debug_query=f"db.{alarm_table}.find({query})"
    )
    
async def get_ne_inventory(lookup_keys_list: list[str], inventory_table: str = "ne_inventory") -> NeInventoryRepoQueryResult: 
    db = get_database()
    query = {
        "$or": [
            {"ip": {"$in": lookup_keys_list}},
            {"ne_name": {"$in": lookup_keys_list}}
        ]
    }
    raw_inventory = await db[inventory_table].find(query).to_list(length=len(lookup_keys_list))
    models = [NeInventoryModel(**record) for record in raw_inventory]
    return NeInventoryRepoQueryResult(
        data=models,
        debug_query=f"db.{inventory_table}.find({query})"
    )