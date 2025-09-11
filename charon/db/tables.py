import enum
from datetime import datetime

from piccolo.columns import Boolean
from piccolo.columns import ForeignKey
from piccolo.columns import JSON
from piccolo.columns import LazyTableReference
from piccolo.columns import M2M
from piccolo.columns import Serial
from piccolo.columns import Timestamp
from piccolo.columns import Varchar
from piccolo.table import Table


class SignupStage(enum.Enum):
    INVITED = "invited"
    PROMOTED = "promoted"
    JOINED = "joined"
    DEACTIVATED = "deactivated"
    ERRORED = "errored"


class Person(Table):
    id = Serial(primary_key=True)
    slack_id = Varchar(index=True, unique=True)
    admin = Boolean(default=False)

    programs = M2M(LazyTableReference("PersonProgramLink", module_path=__name__))

    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(auto_update=datetime.now)


class Program(Table):
    id = Serial(primary_key=True)
    name = Varchar(index=True)
    mcg_channels = JSON(default=list)
    full_channels = JSON(default=list)
    verification_required = Boolean(default=False)
    webhook = Varchar(index=True)
    approved = Boolean(default=False)
    enabled = Boolean(default=True)
    user_id = Varchar(null=True)
    user_token = Varchar(null=True)
    xoxc_token = Varchar(null=True)
    xoxd_token = Varchar(null=True)
    api_key = Varchar(null=True)

    managers = M2M(LazyTableReference("PersonProgramLink", module_path=__name__))

    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(auto_update=datetime.now)


class PersonProgramLink(Table):
    user_id = ForeignKey(Person)
    program_id = ForeignKey(Program)

    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(auto_update=datetime.now)


class Settings(Table):
    id = Serial(primary_key=True)
    global_verification = Boolean(default=False)
    signup_enabled = Boolean(default=True)

    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(auto_update=datetime.now)


class Signup(Table):
    id = Serial(primary_key=True)
    slack_id = Varchar(null=True)
    status = Varchar(choices=SignupStage, index=True, default=SignupStage.INVITED)
    email = Varchar(index=True, unique=True)
    ip = Varchar(null=True, index=True)
    program_id = ForeignKey(Program, null=True)

    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(auto_update=datetime.now)
