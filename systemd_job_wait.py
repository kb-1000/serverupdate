import asyncio
import collections
import typing

from dbus_next.aio import ProxyInterface

futures: typing.Dict[str, typing.List[asyncio.Future]] = collections.defaultdict(list)


def on_job_removed(job_id: int, job_path: str, primary_unit: str, result: str):
    future_list = futures.pop(job_path, [])
    for future in future_list:
        if result in ("done", "skipped"):
            future.set_result(None)
        else:
            future.set_exception(Exception(f"Job {job_id} (primary unit {primary_unit}) failed with result {result}"))


async def setup_job_collector(interface: ProxyInterface):
    await interface.call_Subscribe()
    interface.on_JobRemoved(on_job_removed)


async def wait_for_job(job_path: str):
    future = asyncio.Future()
    futures[job_path].append(future)
    return await future
