"""Landlock must be exercised in a disposable child, never the pytest process."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from tau_coding import linux_sandbox as sandbox


def test_modes(monkeypatch):
    monkeypatch.delenv('TAU_LINUX_SANDBOX', raising=False)
    monkeypatch.delenv('TAU_LINUX_SANDBOX_DEFAULT_ON', raising=False)
    assert not sandbox.should_enter_linux_sandbox(disabled=False)
    monkeypatch.setenv('TAU_LINUX_SANDBOX', 'required')
    monkeypatch.setenv('TAU_LINUX_SANDBOXED', '1')
    assert sandbox.should_enter_linux_sandbox(disabled=False, platform='linux')
    assert not sandbox.should_enter_linux_sandbox(disabled=True)
    assert not sandbox.should_enter_linux_sandbox(disabled=False, platform='darwin')


def test_auto_and_unsupported(monkeypatch, tmp_path):
    monkeypatch.delenv('TAU_LINUX_SANDBOX', raising=False)
    monkeypatch.setenv('TAU_LINUX_SANDBOX_DEFAULT_ON', '1')
    monkeypatch.setattr(sandbox, 'landlock_abi', lambda: 0)
    assert not sandbox.should_enter_linux_sandbox(disabled=False)
    with pytest.raises(sandbox.LinuxSandboxError, match='ABI 3'):
        sandbox.enter_linux_sandbox(project_dir=tmp_path)
    monkeypatch.setattr(sandbox, 'landlock_abi', lambda: 3)
    assert sandbox.should_enter_linux_sandbox(disabled=False, platform='linux')


def test_extra_paths():
    assert sandbox.extra_writable_paths_from_env('/one:/two') == (Path('/one'), Path('/two'))


def test_kernel_enforcement(tmp_path):
    if sandbox.landlock_abi() < 3:
        pytest.skip('Host does not expose Landlock ABI 3')
    script = r'''
import os, sys, subprocess
from pathlib import Path
from types import SimpleNamespace
from tau_coding.linux_sandbox import enter_linux_sandbox
base = Path(sys.argv[1]); project = base/'project'; project.mkdir()
outside = base/'outside'; outside.write_text('original')
paths = SimpleNamespace(home=base/'state', logs_dir=base/'logs')
enter_linux_sandbox(project_dir=project, tau_paths=paths, temp_dir=base/'temp')
(project/'ok').write_text('ok')
assert outside.read_text() == 'original'
for operation in [lambda: outside.write_text('bad'), lambda: outside.unlink(), lambda: os.truncate(outside, 0), lambda: (base/'new').mkdir(), lambda: (project/'ok').rename(base/'escaped')]:
    try: operation()
    except PermissionError: pass
    else: raise AssertionError('write escaped sandbox')
result = subprocess.run([sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("bad")', str(outside)], capture_output=True)
assert result.returncode != 0
assert outside.read_text() == 'original'
'''
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
