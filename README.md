# Assignments for CS146S: The Modern Software Developer

This is the home of the assignments for [CS146S: The Modern Software Developer](https://themodernsoftware.dev), taught at Stanford University fall 2025.

## Repo Setup
These steps work with Python 3.12.

1. Install Anaconda
   - Download and install: [Anaconda Individual Edition](https://www.anaconda.com/download)
   - Open a new terminal so `conda` is on your `PATH`.

2. Create and activate a Conda environment (Python 3.12)
   ```bash
   conda create -n cs146s python=3.12 -y
   conda activate cs146s
   ```

3. Install Poetry
   ```bash
   curl -sSL https://install.python-poetry.org | python -
   ```

4. Install project dependencies with Poetry (inside the activated Conda env)
   From the repository root:
   ```bash
   poetry install --no-interaction
   ```


------

# Use docker compose to set up the CS146S environment

### Use docker container
```
   mkdir CS146S
   cd CS146S
   git clone https://github.com/mihail911/modern-software-dev-assignments.git
   docker run -it --rm -v D:\CS146S:/cs146s condaforge/miniforge3:26.1.0-0 
   mamba install conda-forge::poetry
   
   cd /cs146s/modern-software-dev-assignments/
   poetry config virtualenvs.create false
   poetry install --no-interaction
```

## 背景執行 docker-compose.yml
```
docker compose up -d

or 

docker compose -f project-specific-compose.yml up -d
```

## 進入 docker-compose 的 ollama bash
```
docker compose exec ollama bash
```

## 下載 ollama model
```
ollama pull mistral-nemo:12b
ollama pull llama3.1:8b

or 

在其他地方下載好後，模型資訊(blobs、manifests)要放入
OLLAMA_MODEL\models\blobs
OLLAMA_MODEL\models\manifests
```