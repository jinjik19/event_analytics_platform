
from domain.utils.formatting import split_camel_case


async def test_split_camel_case():
    assert split_camel_case("helloWorld") == ["hello", "world"]
