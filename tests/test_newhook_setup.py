import json

from pytest import Pytester


def test_no_execute(pytester: Pytester):
    remote = pytester.mkpydir('foo')
    _setup__pytest_xvirt_setup(pytester, remote)

    (remote / 'some_test.py').write_text('even no valid python')

    pytester.runpytest().assert_outcomes(passed=0)


def test_no_execute_for_submodule(pytester: Pytester):
    remote = pytester.mkpydir('foo')
    sub = pytester.mkpydir('foo/sub')
    _setup__pytest_xvirt_setup(pytester, sub)

    (remote / 'some_test.py').write_text('def test_1(): pass\ndef test_2(): pass')
    (sub / 'sub_test.py').write_text('even no valid python')
    pytester.runpytest().assert_outcomes(passed=2)


def test_xvirt_collect(pytester: Pytester):
    foo = pytester.mkpydir('foo')

    (foo / 'sub_test.py').write_text('even no valid python')

    nodeids = ['m_test.py::test_a', 'm_test.py::test_b', 'm_test.py::test_c']
    nodeids_json = json.dumps(nodeids)
    _setup__pytest_xvirt_setup(pytester, foo, additional=f"""

def pytest_xvirt_collect_file(file_path, path, parent):   
    from xvirt.collectors import VirtCollector
    result = VirtCollector.from_parent(parent, name=file_path.name)
    result.nodeid_array = {nodeids_json}
    return result
    """)

    result = pytester.runpytest('-v')
    stdout_lines = '\n'.join(result.stdout.lines)

    for nodeid in nodeids:
        assert nodeid in stdout_lines

    result.assert_outcomes(passed=3)


def test_xvirt_collect_should_not_be_called(pytester: Pytester):
    bar = pytester.mkpydir('bar')
    (bar / 'bar_test.py').write_text('def test_bar(): pass')

    foo = pytester.mkpydir('foo')
    (foo / 'sub_test.py').write_text('even no valid python')

    _setup__pytest_xvirt_setup(pytester, foo, additional=f"""
def pytest_xvirt_collect_file(file_path, path, parent):   
    assert 'this should not be executed' == ''
    """)

    result = pytester.runpytest(f'{bar}/')
    result.assert_outcomes(passed=1)


def _setup__pytest_xvirt_setup(pytester, remote, additional=''):
    """
    Writes a conftest.py file with a pytest_xvirt_setup hook
    :param remote: defines the remote path to be added to xvirt_packages
    :param additional: Additional conftest.py content
    """
    remote_str = str(remote)
    content = f"""            
def pytest_xvirt_setup(config, xvirt_packages):
    xvirt_packages.append('{remote_str}')
    
{additional}"""
    pytester.makeconftest(content)
