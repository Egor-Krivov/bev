import os
import shutil
import warnings
from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer
from rich.progress import track

from ..exceptions import HashError
from ..hash import from_hash, is_hash, to_hash
from ..ops import Conflict, load_hash
from .add import add
from .app import _app, app_command, cli_error
from .utils import normalize_sources, normalize_sources_and_destination


class PullMode(Enum):
    """
    How to restore the files:

    hash - restore the file hash. Useful for basic files/folders manipulation, e.g. removing parts of a tree

    copy - copy the files. Useful for making changes to files' contents
    """

    hash = 'hash'
    copy = 'copy'


@app_command
def pull(
        sources: List[Path] = typer.Argument(..., help='The source paths to add', show_default=False),
        mode: PullMode = typer.Option(..., help=PullMode.__doc__, show_default=False),
        destination: Optional[Path] = typer.Option(
            None, '--destination', '--dst',
            help='The destination at which the results will be stored. '
                 'If none -  the results will be stored alongside the source'
        ),
        keep: bool = typer.Option(False, help='Whether to keep the sources after pulling the real files'),
        fetch: bool = typer.Option(False, help='Whether to fetch the missing files from remote, if possible'),
        repository: Path = typer.Option(
            None, '--repository', '--repo', help='The bev repository. It is usually detected automatically',
            show_default=False,
        )
):
    """Restore the files and folders that were added to storage"""

    raw_sources = normalize_sources(sources)
    sources = []
    for source in raw_sources:
        if source.exists():
            if source.is_dir():
                for file in source.glob('**/*'):
                    if file.is_file() and is_hash(file):
                        sources.append(file)

            else:
                if not is_hash(source):
                    raise HashError(f'The source "{source}" is not a hash')

                sources.append(source)

        else:
            if not is_hash(source):
                source = to_hash(source)
            if not source.exists():
                raise HashError(f'The source "{source}" does not exist')

            sources.append(source)

    pairs, repo = normalize_sources_and_destination(sources, destination, repository)
    if not pairs:
        return

    for source, destination in pairs:
        if is_hash(destination):
            destination = from_hash(destination)

        if source == destination:
            # TODO: warn
            continue

        _pull(source, destination, mode, keep, repo, fetch)


def _pull(source, destination, mode, keep, repo, fetch):
    def add_ext(p):
        if mode is PullMode.hash and not is_hash(p):
            p = to_hash(p)
        return p

    h = load_hash(source, repo.storage, fetch)
    if isinstance(h, dict):
        if destination.is_file():
            raise cli_error(
                OSError,
                f'The destination ({destination}) is a file, but the hash ({source}) contains a folder',
            )

        for file, value in track(h.items(), total=len(h)):
            file = add_ext(destination / file)
            file.parent.mkdir(parents=True, exist_ok=True)
            PULL_MODES[mode](value, file, repo, fetch)

    else:
        destination = add_ext(destination)
        if destination.is_dir():
            raise cli_error(
                OSError,
                f'The destination ({destination}) is a folder, but the hash ({source}) contains a single file',
            )

        if source == destination:
            # TODO: warn
            return

        PULL_MODES[mode](h, destination, repo, fetch)

    if not keep:
        os.remove(source)


def save_hash(value, file, repo, fetch):
    with open(file, 'w') as f:
        f.write(value)


PULL_MODES = {
    PullMode.copy: lambda h, dst, repo, fetch: repo.storage.read(shutil.copyfile, h, dst, fetch=fetch),
    PullMode.hash: save_hash,
}


@_app.command(deprecated=True)
def gather(
        source: Path = typer.Argument(..., help='The source path to gather', show_default=False),
        destination: Optional[Path] = typer.Option(
            None, '--destination', '--dst',
            help='The destination at which the hashes will be stored. '
                 'If none -  the hashes will be stored alongside the source'
        ),
):  # pragma: no cover
    """Reverse a "pull" command. Warning! this command is superseded by "add" and will be removed soon"""

    warnings.warn('This command is deprecated. Use "add" instead', UserWarning)
    warnings.warn('This command is deprecated. Use "add" instead', DeprecationWarning)
    return add([source], destination, False, Conflict.error, '.')
