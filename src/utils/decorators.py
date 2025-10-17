def exclude_tool(func):
    """Mark a tool method as excluded from get_tools()."""
    func._exclude_tool = True
    return func

def critical_tool(func):
    """Mark a tool method as critical"""
    func._critical_tool = True
    return func