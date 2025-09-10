def test_importing_app():
    # this will raise an exception if pydantic model validation fails for th app
    from nomad_battery_database.apps import battery_app

    assert battery_app.app.label == 'Extracted Battery Database'
