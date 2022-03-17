from unittest import mock

import pytest

from bev.config import parse, load_config


@pytest.mark.parametrize('name', ['first', 'second', 'third'])
def test_select_name(name):
    config = {
        'first': {'storage': [{'root': '1'}]},
        'second': {'storage': [{'root': '2'}]},
        'meta': {'fallback': 'first'}
    }
    with mock.patch('socket.gethostname', return_value=name):
        config = parse('<string input>', config)
        if name == 'third':
            assert config.local.name == 'first'
        else:
            assert config.local.name == name
        assert len(config.remotes) == 1


def test_parser(tests_root, subtests):
    for file in tests_root.glob('configs/**/*.yml'):
        with subtests.test(config=file.name):
            load_config(file)


def test_simplified(tests_root):
    assert load_config(tests_root / 'configs/single-full.yml') == load_config(
        tests_root / 'configs/single-simplified.yml')
