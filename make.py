import argparse
import pathlib
import subprocess
import sys

from packaging import version

self_path = pathlib.Path(__file__).parent.resolve()

_md = lambda effect: lambda f: [f, effect(f)][0]
_ps = lambda o: vars(o).setdefault("__chmp__", {})
_as = lambda o: _ps(o).setdefault("__args__", [])
cmd = lambda **kw: _md(lambda f: _ps(f).update(kw))
arg = lambda *a, **k: _md(lambda f: _as(f).insert(0, (a, k)))


@cmd()
def precommit():
    format()
    docs()
    test()
    integration()


@cmd()
def release():
    run(sys.executable, "setup.py", "bdist_wheel")
    run(sys.executable, "setup.py", "sdist", "--formats=gztar")

    self_path = pathlib.Path(__file__).parent.resolve()
    dist_path = self_path / "dist"

    max_wheel = max(dist_path.glob("*.whl"), key=parse_file_version)
    max_sdist = max(dist_path.glob("*.tar.gz"), key=parse_file_version)

    print(f"Upload {[max_wheel.name, max_sdist.name]}?")

    if input("[yN] ") == "y":
        run("twine", "upload", max_wheel, max_sdist)


@cmd()
def docs():
    try:
        from chmp.tools.mddocs import transform_file

    except ImportError:
        raise RuntimeError("Need chmp installed to create docs")

    self_path = pathlib.Path(__file__).parent.resolve()
    transform_file(self_path / "Readme.in", self_path / "Readme.md")


@cmd()
def format():
    python(
        "black",
        "ipytest",
        "tests",
        "Example.ipynb",
        "setup.py",
        "make.py",
    )


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
    res = python(
        "piptools",
        "compile",
        "--upgrade",
        "--no-annotate",
        "--no-header",
        "requirements-dev.in",
        capture_output=True,
    )
    reqs = res.stderr.decode("utf8")
    reqs = replace_absolute_requirements(reqs)
    pathlib.Path("requirements-dev.txt").write_text(reqs)


def replace_absolute_requirements(requirements):
    requirements = requirements.splitlines()

    for i in range(len(requirements)):
        if requirements[i].startswith("-e"):
            requirements[i] = "-e ."

    return "\n".join(requirements)


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
        if not hasattr(func, "__chmp__"):
            continue

        desc = dict(func.__chmp__)
        name = desc.pop("name", func.__name__.replace("_", "-"))
        args = desc.pop("__args__", [])

        subparser = subparsers.add_parser(name, **desc)
        subparser.set_defaults(__main__=func)

        for arg_args, arg_kwargs in args:
            subparser.add_argument(*arg_args, **arg_kwargs)

    args = vars(parser.parse_args())

    if "__main__" not in args:
        return parser.print_help()

    func = args.pop("__main__")
    return func(**args)


if __name__ == "__main__":
    main()
