from dbus_next.aio import MessageBus, ProxyObject


async def get_proxy_object(bus: MessageBus, bus_name: str, path: str) -> ProxyObject:
    return bus.get_proxy_object(bus_name, path, await bus.introspect(bus_name, path))
