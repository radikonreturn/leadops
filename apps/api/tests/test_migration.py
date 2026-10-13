import os
from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_migrations_validity():
    ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    assert os.path.exists(ini_path)

    config = Config(ini_path)
    script = ScriptDirectory.from_config(config)

    # Check heads
    heads = script.get_heads()
    assert "20261013_02" in heads

    # Traverse revision history from head to base
    revisions = list(script.walk_revisions())
    rev_ids = [rev.revision for rev in revisions]
    assert "20261013_02" in rev_ids
    assert "20261013_01" in rev_ids
