
import inspect
import re
from typing import Literal

import mypy.api

import pytest


mypy_args_key = pytest.StashKey[list[str]]()
mypy_expect_key = pytest.StashKey[int]()
mypy_expmsg_key = pytest.StashKey[list[str]]()

mypy_fail_key = pytest.StashKey[bool]()
mypy_msg_key = pytest.StashKey[str]()


def prepare_source(item):
    """Extract the test body only."""
    source = inspect.getsource(item.obj)
    result = []
    indent = None
    hide = True
    for line in source.splitlines():
        if hide:
            if line.startswith('def '):
                hide = False
            continue
        if indent is None:
            m = re.match(r'^(\s*)(.*)$', line)
            indent = m.group(1)
            line = m.group(2)
        elif line.startswith(indent):
            line = line[len(indent):]
        result.append(line)
    return '\n'.join(result)

def init_mypy(
    item: pytest.Item,
    marker: pytest.Mark,
) -> None:
    """Attach mypy arguments to ``item``."""
    args = []
   
    for key, value in marker.kwargs.items():
        arg_name = '--' + key.replace('_', '-')
        if arg_name not in args:
            args.append(arg_name)
            args.append(value)
       
    source = prepare_source(item)
    args.extend(['-c', '\n' + source])
    item.stash[mypy_args_key] = args
    item.stash[mypy_expmsg_key] = marker.args
    
            
def run_mypy(item: pytest.Item) -> None:
    """Run mypy on the given test."""
    item.stash[mypy_fail_key] = False
    args = item.stash[mypy_args_key]
    expected_status = item.stash[mypy_expect_key]
   
    stdout, stderr, exit_status = mypy.api.run(args)
    if exit_status == 2:
        # severe problem
        raise pytest.UsageError(
            f'mypy panicked: {stderr}'
        )
    if exit_status != expected_status:
        item.stash[mypy_fail_key] = True
        if exit_status == 1:
            item.stash[mypy_msg_key] = (
                f'mypy failed unexpectedly: {stdout}'
            )
        else:
            item.stash[mypy_msg_key] = (
                f'mypy should have failed but did not: {stdout}'
            )
    else:
        for msg in item.stash.get(mypy_expmsg_key, []):
            if msg not in stdout:
                item.stash[mypy_fail_key] = True
                item.stash[mypy_msg_key] = (
                    f'mypy message missing {msg!r} in:\n{stdout}'
                )
                break

def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Modify tests."""
    for item in items:
        for marker in item.iter_markers(name="mypy"):
            item.stash[mypy_expect_key] = 0
            init_mypy(item, marker)
        for marker in item.iter_markers(name="mypy_xfail"):
            item.stash[mypy_expect_key] = 1
            init_mypy(item, marker)

def pytest_runtest_call(item: pytest.Item) -> None:
    """Run the test."""
    if item.stash.get(mypy_expect_key, -1) < 0:
        item.runtest()
    else:
        run_mypy(item)
    
    
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
) -> pytest.TestReport | None:
    """Create the test report."""
    if call.when != "call":
        return None

    report = pytest.TestReport.from_item_and_call(item, call)
    if item.stash.get(mypy_fail_key, False):
        report.outcome = 'failed'
        report.longrepr = item.stash.get(mypy_msg_key, 'unknown mypy problem')
    return report
            