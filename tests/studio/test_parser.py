from cleanpaste_studio.parser import detect_format, parse_document


def test_markdown_structure_and_safe_links():
    source = """# Title

Paragraph with **bold**, *italic*, `code`, [safe](https://example.com), and [bad](javascript:alert(1)).

- Parent
  - Child

| A | B |
| - | - |
| 1 | 2 |

```python
print('ok')
```
"""
    parsed = parse_document(source, "Fixture", "auto")
    assert parsed.source_format == "markdown"
    assert [block.kind for block in parsed.blocks] == [
        "heading",
        "paragraph",
        "list_item",
        "list_item",
        "table",
        "code",
    ]
    assert parsed.blocks[3].level == 1
    links = [span.href for block in parsed.blocks for span in block.spans if span.href]
    assert links == ["https://example.com"]
    assert parsed.blocks[-1].language == "python"


def test_html_removes_unsafe_ui_and_preserves_semantics():
    source = """
    <nav>Provider controls</nav><h2>Answer</h2>
    <p>Hello <strong>world</strong> <a href="mailto:test@example.com">email</a>.</p>
    <ul><li>One<ul><li>Nested</li></ul></li></ul>
    <table><tr><th>Name</th><th>Value</th></tr><tr><td>A</td><td>1</td></tr></table>
    <script>steal()</script>
    """
    parsed = parse_document(source, source_format="html")
    assert "Provider controls" not in " ".join(block.text for block in parsed.blocks)
    assert "steal" not in " ".join(block.text for block in parsed.blocks)
    assert any(block.kind == "heading" and block.text == "Answer" for block in parsed.blocks)
    assert any(block.kind == "table" and block.rows[1] == ["A", "1"] for block in parsed.blocks)
    assert any(
        span.bold and span.text == "world" for block in parsed.blocks for span in block.spans
    )


def test_plain_and_malformed_html_are_stable():
    assert detect_format("First paragraph\n\nSecond paragraph") == "plain"
    plain = parse_document("First paragraph\n\nSecond paragraph")
    assert [block.text for block in plain.blocks] == ["First paragraph", "Second paragraph"]
    malformed = parse_document("<p>One<strong> two<p>Three", source_format="html")
    assert malformed.blocks


def test_source_hash_is_deterministic_and_source_is_not_embedded_in_model():
    first = parse_document("private text")
    second = parse_document("private text")
    assert first.source_hash == second.source_hash
    assert "private text" not in repr(first.source_hash)
