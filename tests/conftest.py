import importlib.metadata

import nomad.config

# nomad config is set up
if getattr(nomad.config, "plugins", None) is None:
    print("initializing nomad plugins manually...")
    nomad.config.plugins = nomad.config.models.config.Plugins()  # to create an empty plugins object

    # to register installed entry points
    for entry_point in importlib.metadata.entry_points().select(group="nomad.plugin"):
        nomad.config.plugins.entry_points.options[entry_point.name] = entry_point

    print("nomad plugins have manually registered.")
else:
    try:
        nomad.config.plugins.load_plugins()
    except AttributeError:
        print("warning:nomad plugin loading failed. Continuing with default settings.")
