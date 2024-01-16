import functools as ft
import pathlib
import subprocess
import sys

from packaging import version

import minidoc

# ruff: noqa: E401, E731
__effect = lambda effect: lambda func: [func, effect(func.__dict__)][0]
cmd = lambda **kw: __effect(lambda d: d.setdefault("@cmd", {}).update(kw))
arg = lambda *a, **kw: __effect(lambda d: d.setdefault("@arg", []).append((a, kw)))

self_path = pathlib.Path(__file__).parent.resolve()


@cmd()
def precommit():
    format()
    lint()
    docs()
    test()
    integration()


@cmd()
def release():
    python("build", "-s", "-w", ".")

    dist_path = self_path / "dist"

    max_wheel = max(
        dist_path.glob("*.whl"),
        key=ft.partial(parse_file_version, suffix=".whl"),
    )
    max_sdist = max(
        dist_path.glob("*.tar.gz"),
        key=ft.partial(parse_file_version, suffix=".tar.gz"),
    )

    print(f"Upload {[max_wheel.name, max_sdist.name]}?")

    if input("[yN] ") == "y":
        run("twine", "upload", "-u", "__token__", max_wheel, max_sdist)


@cmd()
def docs():
    print("Update documentation")
    minidoc.update_docs(self_path / "Readme.md")


@cmd()
def format():
    python(
        "ruff",
        "format",
        "ipytest",
        "tests",
        "Example.ipynb",
        "x.py",
        "minidoc.py",
    )


@cmd()
def lint():
    python("ruff", "check", self_path)


@cmd()
def test():
    python("pytest", "tests")


@cmd()
def integration():
    python(
        "pytest",
        "--nbval-lax",
        "--nbval-current-env",
        "Example.ipynb",
        *pathlib.Path("tests").glob("Test*.ipynb"),
    )


@cmd()
def compile_requirements():
    run("poetry", "lock")
    run(
        "poetry",
        "export",
        "-f",
        "requirements.txt",
        "--output",
        "requirements-dev.txt",
        "--with=dev",
    )


def parse_file_version(p, suffix):
    assert p.name.endswith(suffix)

    _, version_part, *_ = p.name[: -len(suffix)].split("-")
    return version.parse(version_part)


def python(*args, **kwargs):
    return run(sys.executable, "-m", *args, **kwargs)


def run(*args, **kwargs):
    kwargs.setdefault("check", True)
    kwargs.setdefault("cwd", str(self_path))

    args = [str(arg) for arg in args]
    print("::", " ".join(args))
    return subprocess.run(args, **kwargs)


if __name__ == "__main__":
    _sps = (_p := __import__("argparse").ArgumentParser()).add_subparsers()
    for _f in (f for f in list(globals().values()) if hasattr(f, "@cmd")):
        _sp = _sps.add_parser(_f.__name__.replace("_", "-"), **getattr(_f, "@cmd"))
        _sp.set_defaults(_=_f)
        [_sp.add_argument(*a, **kw) for a, kw in reversed(getattr(_f, "@arg", []))]
    (_a := vars(_p.parse_args())).pop("_", _p.print_help)(**_a)
