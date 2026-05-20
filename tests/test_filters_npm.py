import pytest
from pytk.filters.npm import NpmFilter

f = NpmFilter()


def test_matches_npm():
    assert f.matches(['npm', 'install'])

def test_matches_yarn():
    assert f.matches(['yarn', 'add', 'lodash'])

def test_matches_pnpm():
    assert f.matches(['pnpm', 'install'])

def test_matches_npx():
    assert f.matches(['npx', 'create-react-app'])

def test_no_match():
    assert not f.matches(['node', 'index.js'])
    assert not f.matches([])


NPM_INSTALL_RAW = """\
npm warn deprecated pkg@1.0.0: use new-pkg instead
⸨░░░░░░░░░░░░░░░⸩ ⠴ reify:lodash: http fetch GET 200
⸨░░░░░░░░░░░░░░░⸩ ⠦ reify:express: http fetch GET 200
added 142 packages in 4s
"""

def test_npm_install_strips_progress():
    out = f.filter(NPM_INSTALL_RAW, ['npm', 'install'])
    assert 'added 142' in out
    assert '⸨░░░░' not in out

def test_npm_install_keeps_deprecation():
    out = f.filter(NPM_INSTALL_RAW, ['npm', 'install'])
    assert 'warn deprecated' in out


NPM_RUN_RAW = """\
> myapp@1.0.0 build
> webpack

webpack 5.0
Building... [====] 80%
Done in 2s
"""

def test_npm_run_strips_header():
    out = f.filter(NPM_RUN_RAW, ['npm', 'run', 'build'])
    assert '> myapp@1.0.0 build' not in out
    assert '[====] 80%' not in out
    assert 'webpack 5.0' in out
    assert 'Done in 2s' in out


NPM_AUDIT_RAW = """\
# lodash

Severity: critical
Package: lodash
Patched in: >=4.17.21
More info: https://npmjs.com/advisories/1065

found 3 vulnerabilities (1 critical, 2 high)
  run `npm audit fix` to fix them, or `npm audit` for details
"""

def test_npm_audit_summary_only():
    out = f.filter(NPM_AUDIT_RAW, ['npm', 'audit'])
    assert 'found 3 vulnerabilities' in out
    assert 'npm audit fix' in out
    assert '# lodash' not in out
    assert 'Patched in' not in out


YARN_ADD_RAW = """\
yarn add v1.22.19
[1/4] Resolving packages...
[2/4] Fetching packages...
[3/4] Linking dependencies...
[4/4] Building fresh packages...
success Saved lockfile.
success Saved 1 new dependency.
info Direct dependencies
info All dependencies
└─ lodash@4.17.21
Done in 1.23s.
"""

def test_yarn_add_compressed():
    out = f.filter(YARN_ADD_RAW, ['yarn', 'add', 'lodash'])
    assert '[1/4]' not in out
    assert 'Done in 1.23s' in out


PNPM_INSTALL_RAW = """\
Packages: +50
Progress: resolved 50, reused 48, downloaded 2, added 50, done

dependencies:
+ lodash 4.17.21
"""

def test_pnpm_install_compressed():
    out = f.filter(PNPM_INSTALL_RAW, ['pnpm', 'install'])
    assert 'lodash 4.17.21' in out


NPX_RAW = """\
Need to install the following packages:
  create-react-app
Ok to proceed? (y)
Creating a new React app...
"""

def test_npx_strips_install_prompt():
    out = f.filter(NPX_RAW, ['npx', 'create-react-app', 'myapp'])
    assert 'Need to install the following packages:' not in out
    assert 'create-react-app' not in out
    assert 'Creating a new React app' in out
