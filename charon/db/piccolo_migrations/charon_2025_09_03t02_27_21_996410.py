from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Boolean
from piccolo.columns.indexes import IndexMethod


ID = "2025-09-03T02:27:21:996410"
VERSION = "1.27.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="charon", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="Program",
        tablename="program",
        column_name="enabled",
        db_column_name="enabled",
        column_class_name="Boolean",
        column_class=Boolean,
        params={
            "default": True,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="Settings",
        tablename="settings",
        column_name="signup_enabled",
        db_column_name="signup_enabled",
        column_class_name="Boolean",
        column_class=Boolean,
        params={
            "default": True,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    return manager
