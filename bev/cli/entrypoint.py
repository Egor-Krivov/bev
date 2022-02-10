import typer
from typint import List
from argparse import ArgumentParser

from .add import add
from .blame import blame
from .fetch import fetch
from .init import init
from .pull import pull, gather, PULL_MODES
from .storage import init_storage
from .update import update

app = typer.typer()


@app.command(name="init")
def _init(
        repository: str = typer.Argument('.'),
        permissions: str = typer.Option(None, "--permissions", "-p"),
        group: str = typer.Option(None, "--group", "-g")
        ):
    init(repository, permissions, group)


@app.command(name="add")
def _add(
        source: str = typer.Argument(..., help='a list of files/folders to be added'),
        destination: str = typer.Argument(..., help='the final location of the files/folders'),
        keep: bool = typer.Option(False, "--keep", "-k"),
        context: str = typer.Option(None, "--context", "-c")
        ):
    add(source, destination, keep, context)


@app.command(name="fetch")
def _fetch(
        paths: List[str] = typer.Argument(...),
        context: str = typer.Option(None, "--context", "-c")
        ):
    fetch(paths, context)


@app.command(name="pull")
def _pull(
        source: str = typer.Argument(...),
        destination: str = typer.Argument(...),
        mode: str = typer.Option(..., "--mode", "-m", prompt=True, help='how to pull the files from the hash.')
        ):
    pull(source, destination, mode)


@app.command(name="gather")
def _gather(
        source: str = typer.Argument(...),
        destination: str = typer.Argument(...),
        ):
    gather(source, destination)


@app.command(name="update")
def _update(
        source: str = typer.Argument(...),
        destination: str = typer.Argument(...),
        keep: bool = typer.Option(False, "--keep", "-k"),
        overwrite: bool = typer.Option(False, "--overwrite", "-o")
        ):
    update(source, destination, keep, overwrite)


@app.command(name="blame")
def _blame(
        path: str = typer.Argument(...),
        relative: str = typer.Argument(...),
        ):
    blame(path, relative)


def entrypoint():
    app()


def add_storage_functions(parser: ArgumentParser):
    subparsers = parser.add_subparsers()
    new = subparsers.add_parser('init')
    new.set_defaults(callback=init_storage)
