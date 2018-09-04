from invoke import task


@task()
def format(c):
    c.run("black ipytest tests setup.py tasks.py")


@task()
def test(c):
    c.run("py.test tests")


@task()
def precommit(c):
    format(c)
    test(c)
