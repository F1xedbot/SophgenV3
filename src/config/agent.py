from utils.enums import AgentTable

INJECTOR_TOOL_CONFIG = {
    "table_name": AgentTable.INJECTOR
}

VALIDATOR_TOOL_CONFIG = {
    "table_name": AgentTable.VALIDATOR,
    "injection_group_key": "func_name",
    "injection_table": AgentTable.INJECTOR,
    "excluded_keys": ["id", "func_name", "timestamp"],
    "merge_key": "ref_hash"
}

RESEARCHER_TOOL_CONFIG = {
    "table_name" : AgentTable.RESEARCHER,
    "max_results": 5,
    "fresh_cache": False # <-- set this to True if you want the researcher to run on a fresh cache
}

CONDENSER_TOOL_CONFIG = {
    "table_name": AgentTable.CONDENSER,
    "ref_key": "cwe_label",
    "merge_key": "ref_hash",
    "references" : [AgentTable.INJECTOR, AgentTable.VALIDATOR],
    "excluded_keys": ["id", "func_name", "timestamp", "lines", "roi_index", 
                      "ref_hash", "tags", "camouflage", "attack_vec", "support_count"],
    "cwe_table": AgentTable.RESEARCHER,
    "cwe_table_ref_key": "cwe_id"
}