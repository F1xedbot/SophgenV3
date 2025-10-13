from utils.enums import AgentTable

INJECTOR_TOOL_CONFIG = {
    "table_name": AgentTable.INJECTOR
}

VALIDATOR_TOOL_CONFIG = {
    "table_name": AgentTable.VALIDATOR,
    "injection_group_key": "func_name",
    "injection_table": AgentTable.INJECTOR,
    "excluded_keys": ["id", "func_name", "timestamp"]
}