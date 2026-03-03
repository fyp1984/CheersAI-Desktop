import pytest
from yarl import URL


def test_yarl_urls():
    expected_1 = "https://cheersai.cloud/api"
    assert str(URL("https://cheersai.cloud") / "api") == expected_1
    assert str(URL("https://cheersai.cloud/") / "api") == expected_1

    expected_2 = "http://cheersai.cloud:12345/api"
    assert str(URL("http://cheersai.cloud:12345") / "api") == expected_2
    assert str(URL("http://cheersai.cloud:12345/") / "api") == expected_2

    expected_3 = "https://cheersai.cloud/api/v1"
    assert str(URL("https://cheersai.cloud") / "api" / "v1") == expected_3
    assert str(URL("https://cheersai.cloud") / "api/v1") == expected_3
    assert str(URL("https://cheersai.cloud/") / "api/v1") == expected_3
    assert str(URL("https://cheersai.cloud/api") / "v1") == expected_3
    assert str(URL("https://cheersai.cloud/api/") / "v1") == expected_3

    expected_4 = "api"
    assert str(URL("") / "api") == expected_4

    expected_5 = "/api"
    assert str(URL("/") / "api") == expected_5

    with pytest.raises(ValueError) as e1:
        str(URL("https://cheersai.cloud") / "/api")
    assert str(e1.value) == "Appending path '/api' starting from slash is forbidden"
