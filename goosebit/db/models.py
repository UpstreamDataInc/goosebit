from __future__ import annotations

import datetime
import ipaddress
from enum import IntEnum

from sqlmodel import Field, Relationship, SQLModel


class UpdateModeEnum(IntEnum):
    NONE = 0
    LATEST = 1
    PINNED = 2
    ROLLOUT = 3
    ASSIGNED = 4

    def __str__(self):
        return self.name.capitalize()

    @classmethod
    def from_str(cls, name):
        try:
            return cls[name.upper()]
        except KeyError:
            return cls.NONE


class UpdateStateEnum(IntEnum):
    NONE = 0
    UNKNOWN = 1
    REGISTERED = 2
    RUNNING = 3
    ERROR = 4
    FINISHED = 5

    def __str__(self):
        return self.name.capitalize()

    @classmethod
    def from_str(cls, name):
        try:
            return cls[name.upper()]
        except KeyError:
            return cls.NONE


class Device(SQLModel, table=True):  # type: ignore[call-arg]
    uuid: int = Field(primary_key=True)
    name: str | None = None

    assigned_software: Software | None = Relationship(back_populates="devices")

    force_update: bool = False
    sw_version: str | None = None
    hardware: Hardware | None = Relationship(back_populates="devices")
    feed: str = "default"
    update_mode: UpdateModeEnum = UpdateModeEnum.ROLLOUT
    last_state: UpdateStateEnum = UpdateStateEnum.UNKNOWN
    progress: int | None = None
    log_complete: bool = False
    last_log: str | None = None
    last_seen: int | None = None
    last_ipv4: ipaddress.IPv4Address | None = None
    last_ipv6: ipaddress.IPv6Address | None = None

    @property
    def last_ip(self) -> str | None:
        if self.last_ipv4 is not None:
            return str(self.last_ipv4)
        elif self.last_ipv6 is not None:
            return str(self.last_ipv6)
        return None


class HardwareSoftwareLink(SQLModel, table=True):  # type: ignore[call-arg]
    hardware_id: int | None = Field(default=None, foreign_key="hardware.id", primary_key=True)
    software_id: int | None = Field(default=None, foreign_key="software.id", primary_key=True)


class Software(SQLModel, table=True):  # type: ignore[call-arg]
    id: int | None = Field(primary_key=True, default=None)
    uri: str
    size: int
    hash: str
    version: str

    compatibility: list[Hardware] = Relationship(link_model=HardwareSoftwareLink, back_populates="compatible_software")
    rollouts: list[Rollout] = Relationship(back_populates="software")
    devices: list[Device] = Relationship(back_populates="assigned_software")


class Hardware(SQLModel, table=True):  # type: ignore[call-arg]
    id: int | None = Field(primary_key=True, default=None)
    model: str
    revision: str
    compatible_software: list[Software] = Relationship(link_model=HardwareSoftwareLink, back_populates="compatibility")
    devices: list[Device] = Relationship(back_populates="hardware")


class Rollout(SQLModel, table=True):  # type: ignore[call-arg]
    id: int | None = Field(primary_key=True, default=None)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    name: str | None = None
    feed: str = "default"
    software: Software | None = Relationship(back_populates="rollouts")
    paused: bool = False
    success_count: int = 0
    failure_count: int = 0
