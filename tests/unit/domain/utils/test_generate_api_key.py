from domain.utils.generate_api_key import generate_api_key


async def test_generate_api_key(test_settings):
    api_key = generate_api_key(test_settings.app_env.value)
    assert api_key.startswith(f"wk_{test_settings.app_env.value}")
