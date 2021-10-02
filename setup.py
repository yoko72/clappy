import pathlib
from setuptools import setup


def _read_readme():
    return open((pathlib.Path() / 'README.md'), encoding='utf-8').read().replace("\r", "")


setup(
    long_description=_read_readme(),
    long_description_content_type="text/markdown",
)
