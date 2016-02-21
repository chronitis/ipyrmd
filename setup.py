#!/usr/bin/env python3

from distutils.core import setup
from ipyrmd import __version__

setup(name="ipyrmd",
      version=__version__,
      description="Convert between IPython/Jupyter notebooks and RMarkdown",
      author="Gordon Ball",
      author_email="gordon@chronitis.net",
      url="https://github.com/chronitis/ipyrmd",
      packages=["ipyrmd"],
      license="MIT",
      install_requires=["nbformat", "pyyaml"],
      scripts=["scripts/ipyrmd"])
