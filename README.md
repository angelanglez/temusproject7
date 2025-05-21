# temusproject7

> Link: <a href="https://kmoyu.pythonanywhere.com">Research Helper</a>

## 🚀 Getting Started - Backend

1.  **Create the virtual environment:**
    ```bash
    uv venv --python 3.12
    ```

2.  **Activate the environment:**
    ```bash
    source .venv/bin/activate
    ```
    *Alternatively, you can use `make activate`, which will spawn a new shell with the environment activated.*

3.  **Install UV (if not already installed):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    *(You might need to restart your terminal or source your shell profile, e.g., `source ~/.bashrc` or `source ~/.zshrc`, for the `uv` command to be available if it was just installed).*

4.  **Install project dependencies:**
    ```bash
    uv sync
    ```
