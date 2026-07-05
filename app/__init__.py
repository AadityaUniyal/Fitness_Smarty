import pathlib, sys
_backend_app_path = pathlib.Path(__file__).parent.parent / "backend" / "app"
if _backend_app_path.is_dir():
    # Add to package path for 'app' namespace
    __path__.append(str(_backend_app_path))
    sys.path.insert(0, str(_backend_app_path))
