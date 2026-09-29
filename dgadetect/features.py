"""Turn a domain into the name part the model sees."""

import re

import tldextract

# suffix_list_urls=() means: use the suffix list bundled with tldextract, never fetch
_extract = tldextract.TLDExtract(suffix_list_urls=())
_VALID_LABEL = re.compile(r"[a-z0-9-]{1,63}")
MAX_DOMAIN_LENGTH = 253


class InvalidDomain(ValueError):
    pass


def extract_name(domain: str) -> str:
    """Return the registrable name without its public suffix: www.bbc.co.uk -> bbc."""
    cleaned = domain.strip().lower().removesuffix(".")
    labels_ok = all(_VALID_LABEL.fullmatch(label) for label in cleaned.split("."))
    parts = (
        _extract(cleaned) if labels_ok and len(cleaned) <= MAX_DOMAIN_LENGTH else None
    )
    if parts is None or not parts.suffix or not parts.domain:
        raise InvalidDomain(f"not a valid domain: {domain!r}")
    return parts.domain
