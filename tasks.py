import os.path
from invoke import task


@task()
def format(c):
    c.run("black ipytest tests setup.py tasks.py")


@task()
def test(c):
    c.run("py.test tests")


@task()
def docs(c):
    try:
        from chmp.tools.mddocs import transform

    except ImportError:
        raise RuntimeError("Need chmp installed to create docs")

    self_path = os.path.dirname(__file__)
    source_path = os.path.join(self_path, "Readme.in")
    target_path = os.path.join(self_path, "Readme.md")

    with open(source_path, "rt") as fobj:
        content = fobj.read()

    content = transform(content, source_path)

    with open(target_path, "wt") as fobj:
        fobj.write(content)


@task()
def precommit(c):
    format(c)
    docs(c)
    test(c)
