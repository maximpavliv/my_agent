from openai import OpenAI
import subprocess
import json
import os

from container_utils import ensure_container, cleanup_container, CONTAINER_NAME

client = OpenAI()
context = []

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

def call(tools):
    return client.responses.create(model="gpt-5", tools=tools, input=context)

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
    try:
        while True:
            line = input("> ")
            result = process(line)
            print(f">>> {result}\n")
    finally:
        cleanup_container()

if __name__ == "__main__":
    main()