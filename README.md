# My Agent

In this repo, I create a small AI agent and experiment with its capabilities.
The idea and architecture are inspired by [this blog post](https://fly.io/blog/everyone-write-an-agent/).

The agent supports **tool calling**, allowing it to interact with the outside world through controlled functions.

## Features
### ✅ Ping Tool

The agent can test connectivity to any website or server using a ping tool.
Example:
- > \> Ping google.com
- > \> Check if github is reachable

### ✅ Bash Tool (Sandboxed)

The agent can execute **unrestricted bash commands**, but **safely**, because every command runs inside a
**secure Docker container** (auto-created and auto-removed).
This keeps your machine protected while still enabling powerful interactions.

Example things you can ask it to do with the bash tool:
- > \> Write and run a Python script that generates a Mandelbrot fractal as ASCII art.
- > \> Create a tiny text-adventure game as a Python script and run it.
- > \> Generate files, explore directories, or run small utilities inside the container.

## Requirements

Before running the agent, set your OpenAI API key:
```
export OPENAI_API_KEY="your-key-here"
```

Make sure Docker is correctly installed and configured. Install `openai` into your virtual environment.

## Running

Once the environment is ready, simply run the script and start chatting with your agent.
Ask it to ping a site, run bash commands in the sandbox, or create and execute code.