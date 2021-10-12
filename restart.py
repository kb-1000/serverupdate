from dbus_next.aio import ProxyInterface

import configuration
from systemd_job_wait import wait_for_job


async def stop(interface: ProxyInterface, config: configuration.Configuration):
    await wait_for_job(await interface.call_StopUnit(config.systemd_unit, "replace"))


async def start(interface: ProxyInterface, config: configuration.Configuration):
    # restart instead of start in case something went wrong while stopping
    await wait_for_job(await interface.call_RestartUnit(config.systemd_unit, "replace"))
