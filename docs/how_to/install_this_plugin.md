
# How to Install This Plugin

We recommand to use nomad-destro-dev to install the plugin

## Installation Steps

1.  **Activate your NOMAD Python environment.**
    If you are using a virtual environment, activate it first:
    ```bash
    source .pyenv/bin/activate
    ```

after following the [nomad-destro-dev](https://github.com/FAIRmat-NFDI/nomad-distro-dev)

2.  **Install the plugin using pip:**
    ```bash
    git submodule add https://github.com/u-gajera/Battery-Database.git
    uv add packages/nomad-battery-database
    ```

3.  **Restart NOMAD.**
    After installation, you need to restart the NOMAD server and worker processes for the changes to take effect. If you are running NOMAD via Docker, you can restart the containers:
    ```bash
    uv run poe setup
    uv run poe start
    ```

After restarting, NOMAD will be able to recognize and parse files that match the battery database format.