import argparse
import datetime
import logging
import os
import pathlib
import shutil
import socket
import tempfile

import aiohttp.web
import aiohttp_remotes
import cysystemd.journal
from aiohttp.web_response import Response
from dbus_next import BusType
from dbus_next.aio import MessageBus

import configuration
import restart
import systemd_job_wait
from dbus_util import get_proxy_object

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument("--path")
parser.add_argument("--port", type=int)
parser.add_argument("--systemd", action="store_true")
parser.add_argument("--aiohttp-remotes", action="store_true")
parser.add_argument("--log-level", default="INFO")

routes = aiohttp.web.RouteTableDef()

logger = logging.getLogger("serverupdate")


@routes.post("/")
async def upload(request: aiohttp.web.Request):
    if request.remote != config.remote_ip:
        logger.warning(f"Blocking update request from {request.remote}")
        raise aiohttp.web.HTTPForbidden()
    logger.info(f"Accepting update request from {request.remote}")

    with tempfile.TemporaryDirectory(dir=config.game_dir / "updater") as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        multipart_reader = await request.multipart()
        file = await multipart_reader.next()
        filename = file.filename
        logger.info(f"Update file name {filename}")
        if "/" in filename or "\\" in filename or ":" in filename or not config.file_pattern.match(filename):
            raise aiohttp.web.HTTPBadRequest(
                text=f"Invalid filename: {filename}")
        with open(tmpdir / file.filename, "wb") as fp:
            fp.write(await file.read(decode=True))
        if await multipart_reader.next():
            raise aiohttp.web.HTTPBadRequest(text="One file is enough.")
        for file in (config.game_dir / "mods").iterdir():
            if config.file_pattern.match(file.name):
                pass
        shutil.move(tmpdir / filename, config.game_dir / "mods" / filename)
        await restart.stop(request.app["systemd_interface"], config)

        # Back up the world
        shutil.make_archive(config.game_dir / "backups" / datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"), "zip",
                            root_dir=config.game_dir, base_dir="world")

        await restart.start(request.app["systemd_interface"], config)
        return Response(body="Update finished")


if __name__ == "__main__":
    args = parser.parse_args()

    if args.systemd:
        handler = cysystemd.journal.JournaldLogHandler()
    else:
        handler = logging.StreamHandler()

    logging.basicConfig(level=args.log_level.upper(), handlers=[handler])


    async def make_app():
        bus = MessageBus(bus_type=BusType.SYSTEM)
        await bus.connect()
        interface = (
            await get_proxy_object(bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1")).get_interface(
            "org.freedesktop.systemd1.Manager")
        await systemd_job_wait.setup_job_collector(interface)
        app = aiohttp.web.Application()
        app.on_shutdown.append(lambda event: bus.disconnect())
        if args.aiohttp_remotes:
            await aiohttp_remotes.setup(app, aiohttp_remotes.XForwardedRelaxed())
        app.add_routes(routes)
        app["systemd_interface"] = interface
        return app


    config = configuration.read_config()
    os.makedirs(config.game_dir / "updater", exist_ok=True)
    os.makedirs(config.game_dir / "mods", exist_ok=True)
    os.makedirs(config.game_dir / "backups", exist_ok=True)

    sock = None
    if args.systemd:
        sock = socket.fromfd(3, socket.AF_UNIX, socket.SOCK_STREAM)
    aiohttp.web.run_app(make_app(), path=args.path, port=args.port, sock=sock)
