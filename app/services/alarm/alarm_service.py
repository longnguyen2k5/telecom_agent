from datetime import datetime, timedelta
from app.schemas.alarm_dto import EnrichedAlarmItem, AlarmEnrichmentOutput
from .alarm_helper import extract_entities
from app.db.repositories.alarm_repo import get_alarm_history, get_ne_inventory

async def run_noc_alarm_enrichment(
    alarm_type: str,
    window_min: int,
    limit: int,
    alarm_table: str,
    inventory_table: str,
    key_fields: list,
    enrich_fields: list
) -> AlarmEnrichmentOutput:
    
    cutoff_time = (datetime.now() - timedelta(minutes=window_min)).strftime("%Y-%m-%d %H:%M:%S")
        
    try:
        repo_alarm_result = await get_alarm_history(
            alarm_type=alarm_type,
            cutoff_time=cutoff_time,
            limit=limit,
            alarm_table=alarm_table
        )
        query_step_1 = repo_alarm_result.debug_query
        target_alarms = repo_alarm_result.data
        
    except Exception as e:
        return AlarmEnrichmentOutput(status="error", message=f"Lỗi truy vấn cảnh báo: {str(e)}")
    
    if not target_alarms:
        return AlarmEnrichmentOutput(status="success", message="Không có cảnh báo nào thỏa mãn điều kiện.")
    
    enrichment_results = []
    all_keys_for_lookup = set()
    
    for alarm in target_alarms: 
        content_str = alarm.content
        extract_results = extract_entities(content_str, custom_patterns_file=None, key_fields=key_fields)
        extracted = extract_results.get('extracted', {})
        lookup_keys = extract_results.get('lookup_keys', [])
        all_keys_for_lookup.update(lookup_keys)
        
        alarm_item = EnrichedAlarmItem(
            alarm_id=alarm.alarm_id,
            content=content_str,
            ne_name=alarm.ne_name,
            severity=alarm.severity,
            last_seen=alarm.last_seen,
            extracted=extracted,
            lookup_keys=lookup_keys,
            enrichment={}
        )
        enrichment_results.append(alarm_item)
        
    lookup_keys_list = list(all_keys_for_lookup)
    
    try:
        repo_inventory_result = await get_ne_inventory(lookup_keys_list=lookup_keys_list, inventory_table=inventory_table)
        query_step_3 = repo_inventory_result.debug_query
        inventory_records = repo_inventory_result.data
        
    except Exception as e:
        return AlarmEnrichmentOutput(status="error", message=f"Lỗi truy vấn inventory: {str(e)}")
        
    for item in enrichment_results:
        enrichment_data = {}
        for key in item.lookup_keys:
            node_info = next((r for r in inventory_records if r.ip == key or r.ne_name == key), None)
            if node_info: 
                node_dict = node_info.model_dump()
                
                for field in enrich_fields:
                    if field in node_dict:
                        enrichment_data[field] = node_dict[field]
                break
        item.enrichment = enrichment_data
    
    return AlarmEnrichmentOutput(
        status="success",
        sql_step_1=f"db.{alarm_table}.find({query_step_1})",
        sql_step_3=f"db.{inventory_table}.find({query_step_3})",
        data=enrichment_results
    )