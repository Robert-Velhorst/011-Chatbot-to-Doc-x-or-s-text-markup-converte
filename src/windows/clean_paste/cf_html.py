from __future__ import annotations

import re


def parse_cf_html(raw: bytes | str) -> tuple[str, str]:
    value = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    source = re.search(r"^SourceURL:(.+)\r?$", value, re.M | re.I)
    start = re.search(r"^StartFragment:(\d+)\r?$", value, re.M | re.I)
    end = re.search(r"^EndFragment:(\d+)\r?$", value, re.M | re.I)
    if not start or not end:
        return source.group(1).strip() if source else "", value
    encoded = value.encode("utf-8")
    fragment = encoded[int(start.group(1)):int(end.group(1))].decode("utf-8", errors="replace")
    return source.group(1).strip() if source else "", fragment


def build_cf_html(fragment: str, source_url: str) -> bytes:
    body = f"<html><body><!--StartFragment-->{fragment}<!--EndFragment--></body></html>"
    template = "Version:1.0\r\nStartHTML:{start_html:010d}\r\nEndHTML:{end_html:010d}\r\nStartFragment:{start_fragment:010d}\r\nEndFragment:{end_fragment:010d}\r\nSourceURL:{source_url}\r\n"
    provisional = template.format(start_html=0, end_html=0, start_fragment=0, end_fragment=0, source_url=source_url)
    start_html = len(provisional.encode("utf-8"))
    start_marker = "<!--StartFragment-->"
    end_marker = "<!--EndFragment-->"
    start_fragment = start_html + len(body[:body.index(start_marker) + len(start_marker)].encode("utf-8"))
    end_fragment = start_html + len(body[:body.index(end_marker)].encode("utf-8"))
    end_html = start_html + len(body.encode("utf-8"))
    header = template.format(start_html=start_html, end_html=end_html, start_fragment=start_fragment, end_fragment=end_fragment, source_url=source_url)
    return (header + body).encode("utf-8")
