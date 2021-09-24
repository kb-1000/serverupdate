import os
import pathlib
import re
import typing

import yaml


class ConfigurationDict(typing.TypedDict):
    remote_ip: str
    base_dir: str
    """
    Set to true on Windows (which has different file locking handling)
    """
    file_pattern: str
    server_name: str
    server_description: str
    pipenv: str
    backups: bool
    user: str


class Configuration:
    __slots__ = (
        "backups", "base_dir", "file_pattern", "game_dir", "pipenv", "remote_ip", "server_description", "server_name",
        "systemd_unit", "user")
    remote_ip: str
    base_dir: pathlib.Path
    game_dir: pathlib.Path
    file_pattern: "re.Pattern[str]"
    systemd_unit: str
    backups: bool
    server_name: str
    server_description: str
    pipenv: str

    def __init__(self, remote_ip: str, base_dir: os.PathLike, file_pattern: typing.Union["re.Pattern[str]", str],
                 server_name: str, server_description: str, backups: bool, pipenv: str, user: str):
        self.remote_ip = remote_ip
        self.base_dir = pathlib.Path(base_dir)
        self.game_dir = self.base_dir / server_name
        self.file_pattern = re.compile(file_pattern)
        self.systemd_unit = f"{server_name}-server.service"
        self.server_name = server_name
        self.server_description = server_description
        self.backups = backups
        self.pipenv = pipenv
        self.user = user

    def to_dict(self):
        return {name: getattr(self, name) for name in Configuration.__slots__}


def read_config():
    with open("config.yaml", "rb") as fp:
        config_dict: ConfigurationDict = yaml.full_load(fp)
        return Configuration(**config_dict)
