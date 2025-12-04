import os
import sys
import importlib

# Ensure APEX backend "app" package is used for tests
# Repo root = this file's directory
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# Path that contains the APEX backend app package
APEX_BACKEND_PATH = os.path.join(REPO_ROOT, "core", "APEX", "backend")

# Put APEX backend at the *front* of sys.path
if APEX_BACKEND_PATH not in sys.path:
    sys.path.insert(0, APEX_BACKEND_PATH)

# Pre-import the correct `app` package so tests reuse it
#
# This should resolve to:
#   core/APEX/backend/app/__init__.py
app_pkg = importlib.import_module("app")

# Optional sanity check (leave commented if you don't want it to fail hard)
# import inspect
# assert "core{}APEX{}backend".format(os.sep, os.sep) in os.path.abspath(inspect.getfile(app_pkg)), \
#     f"Imported app is not APEX backend: {app_pkg.__file__}"
