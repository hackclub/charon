from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Varchar
from piccolo.columns.indexes import IndexMethod


ID = "2025-09-10T16:57:41:418738"
VERSION = "1.27.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="charon", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="Program",
        tablename="program",
        column_name="user_token",
        db_column_name="user_token",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 255,
            "default": "",
            "null": True,
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
