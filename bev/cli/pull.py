import shutil
import typer

from pathlib import Path

from tqdm import tqdm

from ..shortcuts import get_current_repo
from ..hash import is_hash, to_hash, from_hash, load_tree, dispatch_hash, TreeHash
from .add import save_tree
from .app import app


@app.command()
def pull(
        source: str = typer.Argument(...),
        destination: str = typer.Argument(...),
        mode: str = typer.Option(..., "--mode", "-m", prompt=True, help='how to pull the files from the hash.')
        ):
    repo = get_current_repo()

    assert mode in PULL_MODES, mode
    source, destination = Path(source), Path(destination)
    if not is_hash(source):
        source = to_hash(source)

    if not source.exists():
        raise FileNotFoundError(source)

    h = dispatch_hash(source)
    if isinstance(h, TreeHash):
        mapping = repo.storage.read(load_tree, h.key)

        for file, value in tqdm(mapping.items()):
            file = destination / file
            file.parent.mkdir(parents=True, exist_ok=True)
            PULL_MODES[mode](value, file, repo)

    else:
        PULL_MODES[mode](h.key, destination, repo)


def save_hash(value, file, repo):
    with open(to_hash(file), 'w') as f:
        f.write(value)


PULL_MODES = {
    'copy': lambda h, dst, repo: repo.storage.read(shutil.copyfile, h, dst),
    'hash': save_hash,
}


@app.command()
def gather(
        source: str = typer.Argument(...),
        destination: str = typer.Argument(...)
        ):
    repo = get_current_repo()

    source, destination = Path(source), Path(destination)
    if not is_hash(destination):
        destination = to_hash(destination)

    if not source.exists():
        raise FileNotFoundError(source)

    tree = {}
    files = [file for file in source.glob('**/*') if not file.is_dir()]
    for file in tqdm(files):
        assert is_hash(file)
        relative = file.relative_to(source)
        with open(file, 'r') as f:
            tree[str(from_hash(relative))] = f.read()

    save_tree(repo, tree, destination)
