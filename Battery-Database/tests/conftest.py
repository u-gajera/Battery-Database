import nomad.config

# Ensure plugins are loaded properly before tests
if hasattr(nomad.config, "plugins") and nomad.config.plugins is not None:
    nomad.config.plugins.load_plugins()
