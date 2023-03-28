# ruff: noqa
import argparse
import pathlib
import subprocess
import sys

from packaging import version

import minidoc

self_path = pathlib.Path(__file__).parent.resolve()

_md = lambda effect: lambda f: [f, effect(f)][0]
_ps = lambda o: vars(o).setdefault("__make__", {})
_as = lambda o: _ps(o).setdefault("__args__", [])
cmd = lambda **kw: _md(lambda f: _ps(f).update(kw))
arg = lambda *a, **k: _md(lambda f: _as(f).insert(0, (a, k)))


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

    self_path = pathlib.Path(__file__).parent.resolve()
    dist_path = self_path / "dist"

    max_wheel = max(dist_path.glob("*.whl"), key=parse_file_version)
    max_sdist = max(dist_path.glob("*.tar.gz"), key=parse_file_version)

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
        "black",
        "ipytest",
        "tests",
        "Example.ipynb",
        "x.py",
        "minidoc.py",
    )


@cmd()
def lint():
    python("ruff", self_path)


@cmd()
def test():
    python("pytest", "tests")


@cmd()
def integration():
    python(
        "pytest",
        "--nbval-lax",
        "--current-env",
        "Example.ipynb",
        *pathlib.Path("tests").glob("Test*.ipynb"),
    )


@cmd()
def compile_requirements():
    python(
        "piptools",
        "compile",
        "--resolver=backtracking",
        "--upgrade",
        "--no-annotate",
        "--no-header",
        "--generate-hashes",
        "--output-file",
        "requirements-dev.txt",
        "requirements-dev.in",
        "pyproject.toml",
    )


def parse_file_version(p):
    return version.parse(p.stem)


def python(*args, **kwargs):
    return run(sys.executable, "-m", *args, **kwargs)


def run(*args, **kwargs):
    kwargs.setdefault("check", True)

    args = [str(arg) for arg in args]
    print("::", " ".join(args))
    return subprocess.run(args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    for func in globals().values():
        if (desc := getattr(func, "__make__", None)) is not None:
            desc = dict(func.__make__)
            name = desc.pop("name", func.__name__.replace("_", "-"))
            args = desc.pop("__args__", [])

            subparser = subparsers.add_parser(name, **desc)
            subparser.set_defaults(__main__=func)

            for arg_args, arg_kwargs in args:
                subparser.add_argument(*arg_args, **arg_kwargs)

    args = vars(parser.parse_args())
    if (func := args.pop("__main__", None)) is not None:
        return func(**args)

    else:
        return parser.print_help()


if __name__ == "__main__":
    main()
