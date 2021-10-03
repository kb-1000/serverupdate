import argparse
import datetime
import os
import pathlib
import shutil
import socket
import tempfile

import aiohttp.web
import aiohttp_remotes

import configuration
import restart

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument("--path")
parser.add_argument("--port")
parser.add_argument("--systemd", action="store_true")
parser.add_argument("--aiohttp-remotes", action="store_true")

routes = aiohttp.web.RouteTableDef()


@routes.post("/")
async def upload(request: aiohttp.web.Request):
    # XXX: remove localhost before deploying
    if request.remote != config.remote_ip and request.remote != '127.0.0.1':
        raise aiohttp.web.HTTPForbidden()

    with tempfile.TemporaryDirectory(dir=config.game_dir / "updater") as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        multipart_reader = await request.multipart()
        file = await multipart_reader.next()
        filename = file.filename
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
        await restart.stop(config)

        # Back up the world
        shutil.make_archive(config.game_dir / "backups" / datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"), "zip",
                            root_dir=config.game_dir, base_dir="world")

        await restart.start(config)


if __name__ == "__main__":
    args = parser.parse_args()

    async def make_app():
        app = aiohttp.web.Application()
        if args.aiohttp_remotes:
            await aiohttp_remotes.setup(app, aiohttp_remotes.XForwardedRelaxed())
        app.add_routes(routes)

    config = configuration.read_config()
    os.makedirs(config.game_dir / "updater", exist_ok=True)
    os.makedirs(config.game_dir / "mods", exist_ok=True)
    os.makedirs(config.game_dir / "backups", exist_ok=True)

    sock = None
    if args.systemd:
        sock = socket.fromfd(3, socket.AF_UNIX, socket.SOCK_STREAM)
    aiohttp.web.run_app(make_app(), path=args.path, port=args.port, sock=sock)
