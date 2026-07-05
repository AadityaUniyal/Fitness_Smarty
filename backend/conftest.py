import sqlalchemy

# Provide a placeholder for create_model_from_project used in tests.
if not hasattr(sqlalchemy, "create_model_from_project"):
    def _placeholder(*args, **kwargs):
        """No-op placeholder for sqlalchemy.create_model_from_project.
        Returns None.
        """
        return None
    sqlalchemy.create_model_from_project = _placeholder
