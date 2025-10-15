from nomad_battery_database.apps import battery_app


def test_importing_app():
    # this will raise an exception if pydantic model validation fails for th app

    assert battery_app.app.label == 'Battery Database'
