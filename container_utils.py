IMAGE_NAME = "my_agent_image"
CONTAINER_NAME = "my_agent_container"

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
