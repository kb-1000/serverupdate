import os
import pathlib

import configuration

config = configuration.read_config()

path = pathlib.Path(__file__).parent
context = config.to_dict()

os.makedirs("/etc/systemd/system", exist_ok=True)
os.makedirs("/etc/polkit-1/rules.d", exist_ok=True)

with open(path / "server.service", "r", encoding="utf-8") as rfp, open(
        f"/etc/systemd/system/{config.server_name}-server.service", "w", encoding="utf-8") as wfp:
    wfp.write(rfp.read().format(**context))

with open(path / "serverupdate.service", "r", encoding="utf-8") as rfp, open(
        f"/etc/systemd/system/{config.server_name}-serverupdate.service", "w", encoding="utf-8") as wfp:
    wfp.write(rfp.read().format(**context))

with open(path / "serverupdate.socket", "r", encoding="utf-8") as rfp, open(
        f"/etc/systemd/system/{config.server_name}-serverupdate.socket", "w", encoding="utf-8") as wfp:
    wfp.write(rfp.read().format(**context))

with open(path / "10-serverupdate-polkit.rules", "r", encoding="utf-8") as rfp, open(
        f"/etc/polkit-1/rules.d/10-{config.server_name}-serverupdate-polkit.rules", "w", encoding="utf-8") as wfp:
    wfp.write(rfp.read().replace("{", "{{").replace("}", "}}").replace("<", "{").replace(">", "}").format(**context))
