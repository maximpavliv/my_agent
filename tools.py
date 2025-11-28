import subprocess
import json
from container_utils import ensure_container, CONTAINER_NAME

tools = [{
   "type": "function", "name": "ping",
   "description": "ping some host on the internet",
   "parameters": {
       "type": "object", "properties": {
           "host": {
             "type": "string", "description": "hostname or IP",
            },
       },
       "required": ["host"],
    },},
   {
   "type": "function", "name": "bash_in_container",
   "description": "execute a bash command in a secure Docker container",
   "parameters": {
       "type": "object", "properties": {
           "command": {
             "type": "string", "description": "bash command to execute inside the container",
            },
       },
       "required": ["command"],
    },},]

def ping(host=""):
    try:
        result = subprocess.run(
            ["ping", "-c", "5", host],
            text=True,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE)
        return result.stdout
    except Exception as e:
        return f"error: {e}"

def bash_in_container(command=""):
    try:
        ensure_container()
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", command],
            text=True,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            timeout=30
        )
        return result.stdout if result.stdout else result.stderr
    except subprocess.TimeoutExpired:
        return "error: command timed out after 30 seconds"
    except Exception as e:
        return f"error: {e}"

def tool_call(item):
    tool_name = item.name
    args = json.loads(item.arguments)

    if tool_name == "ping":
        result = ping(**args)
    elif tool_name == "bash_in_container":
        result = bash_in_container(**args)
    else:
        result = f"error: unknown tool {tool_name}"

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": result
    }