import os.path
from invoke import task


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
        "tests/TestIntegration.ipynb",
        "tests/TestAsync.ipynb",
        "Example.ipynb",
    ]

    c.run("pytest --nbval-lax " + " ".join(notebooks))


@task()
def docs(c):
    """Render the documentation."""
    try:
        from chmp.tools.mddocs import transform_file

    except ImportError:
        raise RuntimeError("Need chmp installed to create docs")

    self_path = os.path.dirname(__file__)

    transform_file(
        os.path.join(self_path, "Readme.in"), os.path.join(self_path, "Readme.md")
    )


@task()
def precommit(c):
    format(c)
    docs(c)
    test(c)
    integration(c)
