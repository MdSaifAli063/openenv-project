---
title: Openenv Email Triage
colorFrom: indigo
colorTo: green
sdk: docker
pinned: false
app_port: 7860
base_path: /web
tags:
  - openenv
---

# Openenv Project Environment

An OpenEnv environment project with a Docker-based server and Python client.

## Quick Start

```python
from openenv_project import OpenenvProjectAction, OpenenvProjectEnv

try:
    openenv_project_env = OpenenvProjectEnv.from_docker_image(
        "openenv_project-env:latest"
    )

    result = openenv_project_env.reset()
    print(f"Reset: {result.observation.echoed_message}")

    for msg in ["Hello, World!", "Testing echo", "Final message"]:
        result = openenv_project_env.step(OpenenvProjectAction(message=msg))
        print(f"Sent: {msg}")
        print(f"Echoed: {result.observation.echoed_message}")
        print(f"Length: {result.observation.message_length}")
        print(f"Reward: {result.reward}")
finally:
    openenv_project_env.close()
```

## Build The Docker Image

From the project root:

```bash
docker build -t openenv_project-env:latest -f Dockerfile .
```

## Deploy To Hugging Face Spaces

1. Create a new Hugging Face Space with SDK set to `Docker`.
2. Use a Space name such as `openenv-email-triage`.
3. Log in with the Hugging Face CLI:

```bash
hf auth login
```

4. Add the Space as a git remote:

```bash
git remote add space https://huggingface.co/spaces/<username>/<space-name>
```

5. Push your `main` branch:

```bash
git push space main
```

## Run Locally

You can also run the server locally:

```bash
python -m server.app
```

The Docker container exposes port `7860`.

## Project Structure

```text
openenv_project/
|-- .gitignore
|-- Dockerfile
|-- README.md
|-- __init__.py
|-- client.py
|-- inference.py
|-- models.py
|-- openenv.yaml
|-- pyproject.toml
|-- requirements.txt
|-- server.py
|-- uv.lock
`-- server/
    |-- __init__.py
    |-- app.py
    |-- environment.py
    |-- graders.py
    `-- tasks.py
```
