import configuration
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType
from dbus_next.message import Message


async def stop(config: configuration.Configuration):
    bus = MessageBus(bus_type=BusType.SYSTEM)
    await bus.connect()
    await bus.call(Message(
        destination="org.freedesktop.systemd1",
        path="/org/freedesktop/systemd1",
        member="StopUnit",
        signature="ss",
        body=[config.systemd_unit, "replace"],
    ))
    await bus.disconnect()


async def start(config: configuration.Configuration):
    bus = MessageBus(bus_type=BusType.SYSTEM)
    await bus.connect()
    # restart instead of start in case something went wrong while stopping
    await bus.call(Message(
        destination="org.freedesktop.systemd1",
        path="/org/freedesktop/systemd1",
        member="RestartUnit",
        signature="ss",
        body=[config.systemd_unit, "replace"],
    ))
    await bus.disconnect()
