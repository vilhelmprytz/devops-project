import pytest

from dgadetect.features import InvalidDomain, extract_name


@pytest.mark.parametrize(
    ("domain", "name"),
    [
        ("google.com", "google"),
        ("www.google.com.", "google"),
        ("bbc.co.uk", "bbc"),
        ("  EXAMPLE.org ", "example"),
        ("xn--bcher-kva.de", "xn--bcher-kva"),
    ],
)
def test_extract_name(domain, name):
    assert extract_name(domain) == name


@pytest.mark.parametrize(
    "domain",
    [
        "",
        "co.uk",  # only a suffix
        "google",  # no suffix
        "localhost",
        "abc.bit",  # .bit is not a real TLD
        "a_b.com",
        "1.2.3.4",
        "bücher.de",  # must be punycode
        "x" * 64 + ".com",  # a label is at most 63 characters
        "abc\n.com",  # a newline must not slip past the name check
        "bücher.google.com",  # every label is checked, not only the name
        "a." * 2500 + "com",  # a domain is at most 253 characters
    ],
)
def test_invalid_domain(domain):
    with pytest.raises(InvalidDomain):
        extract_name(domain)
