import pathlib

from invoke import task
from packaging import version


@task()
def format(c):
    """Format the code."""
    c.run("black ipytest tests setup.py tasks.py")


@task()
def test(c):
    """Execute unit tests."""
    c.run("py.test tests")


@task()
def integration(c):
    """Test ipytest - ipython integration."""
    notebooks = [
        "Example.ipynb",
        *(str(p) for p in pathlib.Path("tests").glob("Test*.ipynb")),
    ]

    c.run("pytest --nbval-lax " + " ".join(notebooks))


@task()
def docs(c):
    """Render the documentation."""
    try:
        from chmp.tools.mddocs import transform_file

    except ImportError:
        raise RuntimeError("Need chmp installed to create docs")

    self_path = pathlib.Path(__file__).parent.resolve()
    transform_file(self_path / "Readme.in", self_path / "Readme.md")


@task()
def precommit(c):
    format(c)
    docs(c)
    test(c)
    integration(c)


@task()
def release(c):
    c.run("python setup.py bdist_wheel")
    c.run("python setup.py sdist --formats=gztar")

    self_path = pathlib.Path(__file__).parent.resolve()
    dist_path = self_path / "dist"

    max_wheel = max(dist_path.glob("*.whl"), key=parse_file_version)
    max_sdist = max(dist_path.glob("*.tar.gz"), key=parse_file_version)

    print(f"Upload {[max_wheel.name, max_sdist.name]}?")

    if input("[yN] ") == "y":
        c.run(f"twine upload '{max_wheel!s}' '{max_sdist!s}'")


def parse_file_version(p):
    return version.parse(p.stem)
