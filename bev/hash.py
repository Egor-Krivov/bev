import json
import os
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple, Dict, Union

from tarn import Storage

from .utils import PathOrStr

Key = str
Tree = Dict[PathOrStr, Union[Key, Dict]]
HashType = Union[Key, Tree]


def is_hash(path: PathOrStr):
    return Path(path).name.endswith('.hash')


def to_hash(path: PathOrStr):
    path = Path(path)
    # TODO:
    assert not is_hash(path)
    return path.with_name(f'{path.name}.hash')


def from_hash(path: PathOrStr):
    path = Path(path)
    # TODO
    assert is_hash(path)
    return path.with_name(path.stem)


def is_tree(key: Key):
    return key.startswith('T:')


class FileHash(NamedTuple):
    key: Key
    path: Path
    hash: Path


class TreeHash(NamedTuple):
    key: Key
    path: Path
    hash: Path


class InsideTreeHash(NamedTuple):
    key: Key
    root: Path
    hash: Path
    relative: Path


def dispatch_hash(path):
    path = Path(path)
    key = load_key(path)
    stripped = strip_tree(key)
    if key == stripped:
        return FileHash(key, from_hash(path), path)
    return TreeHash(stripped, from_hash(path), path)


def load_key(path: PathOrStr):
    with open(path, 'r') as file:
        return file.read().strip()


def load_tree(path: Path):
    with open(path, 'r') as file:
        return json.load(file)


# FIXME: the names are misleading
def load_tree_key(path: Path):
    with open(path) as file:
        return strip_tree(file.read().strip())


def strip_tree(key):
    # TODO: remove this
    if key.startswith('tree:'):
        key = key[5:]
    elif key.startswith('T:'):
        key = key[2:]
    return key


def tree_to_hash(tree: Tree, storage: Storage):
    tree = normalize_tree(tree, storage.digest_size)
    # making sure that each time the same string will be saved
    tree = OrderedDict((k, tree[k]) for k in sorted(map(os.fspath, tree)))
    with tempfile.TemporaryDirectory() as tmp:
        tree_path = Path(tmp, 'hash')
        # TODO: storage should allow writing directly from memory
        with open(tree_path, 'w') as file:
            json.dump(tree, file)

        return 'T:' + storage.write(tree_path)


def normalize_tree(tree: Tree, digest_size: int):
    def flatten(x):
        for key, value in x.items():
            key = Path(os.fspath(key))

            if isinstance(value, str):
                if len(value) != digest_size * 2:
                    # TODO
                    raise ValueError(value)

                yield key, value

            elif isinstance(value, dict):
                for k, v in flatten(value):
                    yield key / k, v

            else:
                # TODO
                raise ValueError(value)

    # TODO: detect absolute paths
    result = {}
    for path, hash_ in flatten(tree):
        path = os.fspath(path)
        if path in result and result[path] != hash_:
            # TODO
            raise ValueError

        # TODO: check digest size and type
        result[path] = hash_

    # TODO: detect folders that have hashes
    return result
