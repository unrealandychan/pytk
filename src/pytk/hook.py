import os
import re
from pathlib import Path

SENTINEL_START = "# >>> pytk hook start >>>"
SENTINEL_END = "# <<< pytk hook end <<<"

SUPPORTED_CMDS = [
    "git", "ls", "find", "tree",
    "pytest", "python",
    "grep", "rg", "ag",
    "cat", "head", "tail",
    "docker", "docker-compose",
    "kubectl", "k",
    "npm", "yarn", "pnpm", "npx",
    "cargo", "rustc",
    "curl", "http", "wget",
]

BASH_HOOK = '''
{start}
_pytk_proxy() {{
    local _pytk_cmd="$1"
    case "$_pytk_cmd" in
        {cmds})
            pytk "$@"
            return
            ;;
    esac
    command "$@"
}}
{aliases}
{end}
'''

FISH_HOOK = '''
{start}
{functions}
{end}
'''


def _detect_shell() -> str:
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    elif "fish" in shell:
        return "fish"
    return "bash"


def _get_config_file(shell: str) -> Path:
    home = Path.home()
    if shell == "zsh":
        return home / ".zshrc"
    elif shell == "fish":
        return home / ".config" / "fish" / "config.fish"
    return home / ".bashrc"


def _build_bash_snippet() -> str:
    cmds = "|\n        ".join(SUPPORTED_CMDS)
    aliases = "\n".join(f"alias {c}='_pytk_proxy {c}'" for c in SUPPORTED_CMDS)
    return BASH_HOOK.format(
        start=SENTINEL_START,
        end=SENTINEL_END,
        cmds=cmds,
        aliases=aliases,
    )


def _build_fish_snippet() -> str:
    functions = []
    for c in SUPPORTED_CMDS:
        functions.append(f"function {c}\n    pytk {c} $argv\nend")
    return FISH_HOOK.format(
        start=SENTINEL_START,
        end=SENTINEL_END,
        functions="\n".join(functions),
    )


def _is_enabled(cfg_file: Path) -> bool:
    if not cfg_file.exists():
        return False
    content = cfg_file.read_text()
    return SENTINEL_START in content


def enable_hook(shell: str | None = None, cfg_file: Path | None = None) -> tuple[bool, str]:
    """Returns (already_was_enabled, config_file_path)"""
    shell = shell or _detect_shell()
    cfg = cfg_file or _get_config_file(shell)

    if _is_enabled(cfg):
        return True, str(cfg)

    if shell == "fish":
        snippet = _build_fish_snippet()
    else:
        snippet = _build_bash_snippet()

    cfg.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg, "a") as f:
        f.write("\n" + snippet + "\n")
    return False, str(cfg)


def disable_hook(shell: str | None = None, cfg_file: Path | None = None) -> tuple[bool, str]:
    """Returns (was_enabled, config_file_path)"""
    shell = shell or _detect_shell()
    cfg = cfg_file or _get_config_file(shell)

    if not cfg.exists() or not _is_enabled(cfg):
        return False, str(cfg)

    content = cfg.read_text()
    # Remove block between sentinels (inclusive)
    pattern = re.compile(
        r'\n?' + re.escape(SENTINEL_START) + r'.*?' + re.escape(SENTINEL_END) + r'\n?',
        re.DOTALL
    )
    new_content = pattern.sub('', content)
    cfg.write_text(new_content)
    return True, str(cfg)


def hook_status(shell: str | None = None, cfg_file: Path | None = None) -> dict:
    shell = shell or _detect_shell()
    cfg = cfg_file or _get_config_file(shell)
    enabled = _is_enabled(cfg)
    return {
        "enabled": enabled,
        "shell": shell,
        "config_file": str(cfg),
    }
