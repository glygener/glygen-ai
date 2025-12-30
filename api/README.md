# API Directory Structure

| Directory/File                | Description                                                                |
| ----------------------------- | -------------------------------------------------------------------------- |
| `glygen_llm_api`              | The actual api module.                                                     |
| `config.json`                 | Centralized configuration file for the API and the data loading processes. |
| `create_ai_api_container.py`  | Creates the AI API docker container.                                       |
| `Dockerfile`                  | Dockerfile for the api image (used in `create_ai_api_container.py`)        |
| `requirements.txt`            | Requirements file for the API container.                                   |
| `setup.py`                    | Setup script for packaging the glygen_llm_api project.                     |
