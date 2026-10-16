import os, tempfile
# Isolate test data before any app module is imported.
os.environ["STUDIO_DB"] = tempfile.mktemp(suffix=".db")
os.environ["STUDIO_IMPORT_DIR"] = tempfile.mkdtemp(prefix="lgs-imports-")
os.environ.pop("OPENAI_API_KEY", None)
os.environ["STUDIO_SECRET_KEY_FILE"] = os.path.join(tempfile.mkdtemp(prefix="lgs-key-"), "secret.key")
