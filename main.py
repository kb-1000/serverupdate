import datetime
import os
import pathlib
import shutil
import tempfile

import aiohttp.web

import configuration
import restart

config = configuration.read_config()
os.makedirs(config.game_dir / "updater", exist_ok=True)
os.makedirs(config.game_dir / "mods", exist_ok=True)
os.makedirs(config.game_dir / "backups", exist_ok=True)

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


app = aiohttp.web.Application()
app.add_routes(routes)
aiohttp.web.run_app(app)
