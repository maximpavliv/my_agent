from openai import OpenAI
import subprocess
import json

client = OpenAI()
context = []
CONTAINER_NAME = "my_agent_container"

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
   "type": "function", "name": "bash",
   "description": "execute a bash command in a secure Docker container",
   "parameters": {
       "type": "object", "properties": {
           "command": {
             "type": "string", "description": "bash command to execute",
            },
       },
       "required": ["command"],
    },},]

def ensure_container():
    """Ensure the Docker container exists and is running"""
    # Check if container exists
    check = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if CONTAINER_NAME not in check.stdout:
        # Container doesn't exist, create it
        subprocess.run(
            ["docker", "run", "-d", "--name", CONTAINER_NAME, "my_agent_image"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        # Container exists, ensure it's running
        subprocess.run(
            ["docker", "start", CONTAINER_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

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

def bash(command=""):
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

def call(tools):
    return client.responses.create(model="gpt-5", tools=tools, input=context)

def tool_call(item):
    tool_name = item.name
    args = json.loads(item.arguments)

    if tool_name == "ping":
        result = ping(**args)
    elif tool_name == "bash":
        result = bash(**args)
    else:
        result = f"error: unknown tool {tool_name}"

    return {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": result
    }

def handle_tools(tools, response):
    context.extend(response.output)
    called_function = False
    for item in response.output:
        if item.type == "function_call":
            context.append(tool_call(item))
            called_function = True
    return called_function

def process(line):
    context.append({"role": "user", "content": line})
    response = call(tools)
    # resolve tool calls
    while handle_tools(tools, response):
        response = call(tools)
    context.append({"role": "assistant", "content": response.output_text})
    return response.output_text

def main():
    while True:
        line = input("> ")
        result = process(line)
        print(f">>> {result}\n")

if __name__ == "__main__":
    main()