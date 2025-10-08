# How to Contribute to this Plugin

Contributions are very welcome! Whether you're fixing a bug, adding a new feature, or improving documentation, your help is very much appreciated.

## Development Workflow

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Battery-Database.git
    cd Battery-Database
    ```
3.  **Set up a development environment.** It is highly recommended to install the plugin using [destro]((https://github.com/FAIRmat-NFDI/nomad-distro-dev)) in editable mode within your NOMAD environment:
    ```bash
    git submodule add https://github.com/u-gajera/Battery-Database.git
    uv add packages/nomad-battery-database
    ```
4.  **Make your changes.** Implement your new feature or bug fix.
5.  **Add tests** for your changes to ensure they work as expected and don't break existing functionality.
6.  **Run tests** to make sure everything is passing.
7.  **Commit your changes** with a clear and descriptive message.
8.  **Push your branch** to your fork on GitHub:
    ```bash
    git push origin feature/my-new-feature
    ```
9. **Open a Pull Request** from your branch to the `main` branch of the original repository. Provide a detailed description of your changes in the PR.