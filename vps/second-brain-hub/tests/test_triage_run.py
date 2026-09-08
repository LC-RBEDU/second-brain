

def test_next_id_ceiling_sees_both_id_spellings():
    """RBU63 a RBU-S63 je stejné číslo — jinak by triáž přidělila kolizi."""
    import re

    pattern = re.compile(r"^RBU(?:-[EST])?(\d+)[a-z]?")
    assert pattern.match("RBU-S63 — Story.md").group(1) == "63"
    assert pattern.match("RBU51 — Starý tvar.md").group(1) == "51"
    assert pattern.match("RBU-E69 — Epic.md").group(1) == "69"
