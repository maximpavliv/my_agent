from openai import OpenAI
from tools import tool_call, tools
from container_utils import cleanup_container

client = OpenAI()
context = []

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