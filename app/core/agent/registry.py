from app.tools import alarm_enrich, baseline_tuner, node_health, node_telemetry_stats, node_policy_fetcher
from google.genai import types

TOOL_REGISTRY = {
    "noc_alarm_enrichment": alarm_enrich.execute,
    "node_health_autoremediate": node_health.execute,
    "fetch_node_telemetry_stats": node_telemetry_stats.execute,
    "adaptive_policy_tuner": baseline_tuner.execute, 
    "fetch_node_policy_baseline" : node_policy_fetcher.execute
}


def get_allowed_tools(role : str): 
    tools = [alarm_enrich.get_tools_declaration()]
    if role in ['admin', 'tier1']: 
        tools.append(node_health.get_tools_declaration())
        tools.append(baseline_tuner.get_tools_declaration())
        tools.append(node_telemetry_stats.get_tools_declaration())
        tools.append(node_policy_fetcher.get_tools_declaration())
        
    return [types.Tool(function_declarations=tools)] 