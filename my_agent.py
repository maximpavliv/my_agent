from openai import OpenAI
import subprocess
import json
import os

client = OpenAI()
context = []
IMAGE_NAME = "my_agent_image"
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
    """Ensure the Docker image exists, the container exists, and it is running."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dockerfile_path = os.path.join(script_dir, "Dockerfile")

    # --- 1. Ensure image exists ---
    image_check = subprocess.run(
        ["docker", "images", "-q", IMAGE_NAME],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if not image_check.stdout.strip():
        print(f"Image '{IMAGE_NAME}' not found. Building it...")
        build = subprocess.run(
            ["docker", "build", "-t", IMAGE_NAME, script_dir],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if build.returncode != 0:
            print("Failed to build Docker image.")
            print(build.stderr)
            raise RuntimeError("Docker build failed")

    # --- 2. Check if container exists ---
    container_check = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{CONTAINER_NAME}$", "--format", "{{.Names}}"],
        text=True,
        stdout=subprocess.PIPE,
    )

    if container_check.stdout.strip() != CONTAINER_NAME:
        print(f"Container '{CONTAINER_NAME}' does not exist. Creating it...")
        create = subprocess.run(
            ["docker", "run", "-d", "--name", CONTAINER_NAME, IMAGE_NAME],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if create.returncode != 0:
            print("Failed to create Docker container.")
            print(create.stderr)
            raise RuntimeError("Docker run failed")

    # --- 3. Ensure container is running ---
    start = subprocess.run(
        ["docker", "start", CONTAINER_NAME],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if start.returncode != 0:
        print(f"Failed to start container '{CONTAINER_NAME}'.")
        print(start.stderr)
        raise RuntimeError("Docker start failed")

def cleanup_container():
    """Stop and remove the Docker container if it exists."""
    # Check if container exists
    check = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{CONTAINER_NAME}$", "--format", "{{.Names}}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if check.stdout.strip() != CONTAINER_NAME:
        print(f"Container '{CONTAINER_NAME}' does not exist. Nothing to clean up.")
        return

    print(f"Cleaning up container '{CONTAINER_NAME}'...")

    # Stop container (ignore errors if not running)
    subprocess.run(
        ["docker", "stop", CONTAINER_NAME],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Remove container
    rm = subprocess.run(
        ["docker", "rm", CONTAINER_NAME],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if rm.returncode == 0:
        print(f"Container '{CONTAINER_NAME}' removed.")
    else:
        print(f"Failed to remove container '{CONTAINER_NAME}':")
        print(rm.stderr)
        raise RuntimeError("Could not remove container")

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