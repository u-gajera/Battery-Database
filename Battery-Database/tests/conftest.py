import nomad.config

# Ensure plugins are loaded before running tests
if hasattr(nomad.config, "plugins") and nomad.config.plugins is not None:
    try:
        nomad.config.plugins.load_plugins()
    except AttributeError:
        print("Warning: NOMAD plugin loading failed. Continuing with default settings.")
