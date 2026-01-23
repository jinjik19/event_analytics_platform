from domain.utils.generate_api_key import generate_api_key


async def test_generate_api_key(mock_settings):
    api_key = generate_api_key(mock_settings.app_env.value)
    assert api_key.startswith(f"wk_{mock_settings.app_env.value}")
