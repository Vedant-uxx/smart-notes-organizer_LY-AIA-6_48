from smart_notes.organizer import parse_notes, render_markdown, organize_notes

SAMPLE = open("sample_notes.txt", encoding="utf-8").read()


def test_parse_lines_and_bullets():
    assert parse_notes("- a\n- b\n* c") == ["a", "b", "c"]


def test_parse_blocks():
    assert parse_notes("line one\nstill one\n\nsecond") == ["line one still one", "second"]


def test_render():
    md = render_markdown([{"heading": "X", "notes": ["a", "b"]}])
    assert "## X" in md and "- a" in md


def test_local_keeps_every_note():
    md = organize_notes(SAMPLE, backend="local")
    assert md.count("\n- ") == len(parse_notes(SAMPLE))
    assert md.count("## ") >= 2
