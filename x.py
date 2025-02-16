# ruff: noqa: E401, E731
__effect = lambda effect: lambda func: [func, effect(func.__dict__)][0]
cmd = lambda **kw: __effect(lambda d: d.setdefault("@cmd", {}).update(kw))
arg = lambda *a, **kw: __effect(lambda d: d.setdefault("@arg", []).append((a, kw)))

self_path = __import__("pathlib").Path(__file__).parent.resolve()


@cmd()
def precommit():
    format()
    lint()
    docs()
    test()
    integration()


@cmd()
def release():
    _sh(f"{python} -m build -s -w .")

    dist_path = self_path / "dist"

    max_wheel = max(
        dist_path.glob("*.whl"),
        key=lambda p: parse_file_version(p, suffix=".whl"),
    )
    max_sdist = max(
        dist_path.glob("*.tar.gz"),
        key=lambda p: parse_file_version(p, suffix=".tar.gz"),
    )

    print(f"Upload {[max_wheel.name, max_sdist.name]}?")

    if input("[yN] ") == "y":
        _sh(f"{python} -m twine upload -u __token__ {_q(max_wheel)} {_q(max_sdist)}")


@cmd()
def docs():
    import minidoc

    print("Update documentation")
    minidoc.update_docs(self_path / "Readme.md")


@cmd()
def format():
    _sh("uv run --group dev ruff format ipytest tests Example.ipynb x.py minidoc.py")


@cmd()
@arg("--fix", action="store_true")
def lint(fix=False):
    _sh(f"uv run --group dev ruff check {_q(self_path)}", "--fix" if fix else "")


@cmd()
def test():
    _sh("uv run --group dev  -m pytest tests")


@cmd()
def integration():
    notebooks = [
        "Example.ipynb",
        *(
            p
            for p in self_path.joinpath("tests").glob("**/Test*.ipynb")
            if ".ipynb_checkpoints" not in p.parts
        ),
    ]

    _sh(
        "uv run --group dev pytest --nbval-lax --nbval-current-env "
        * (_q(p) for p in notebooks),
    )


def parse_file_version(p, suffix):
    from packaging import version

    assert p.name.endswith(suffix)

    _, version_part, *_ = p.name[: -len(suffix)].split("-")
    return version.parse(version_part)


_sh = lambda *c, **kw: __import__("subprocess").run(
    [
        args := __import__("shlex").split(" ".join(c).replace("\n", " ")),
        print("::", *args),
    ][0],
    **{"check": True, "cwd": self_path, "encoding": "utf-8", **kw},
)
_q = lambda arg: __import__("shlex").quote(str(arg))
python = _q(__import__("sys").executable)

if __name__ == "__main__":
    _sps = (_p := __import__("argparse").ArgumentParser()).add_subparsers()
    for _f in (f for _, f in sorted(globals().items()) if hasattr(f, "@cmd")):
        _sp = _sps.add_parser(_f.__name__.replace("_", "-"), **getattr(_f, "@cmd"))
        _sp.set_defaults(_=_f)
        [_sp.add_argument(*a, **kw) for a, kw in reversed(getattr(_f, "@arg", []))]
    (_a := vars(_p.parse_args())).pop("_", _p.print_help)(**_a)
