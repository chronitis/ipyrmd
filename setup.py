#!/usr/bin/env python3

from setuptools import setup
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
      scripts=["scripts/ipyrmd"],
      keywords="ipython jupyter irkernel rmarkdown ipynb",
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Environment :: Console",
        "Framework :: IPython",
        "Topic :: Scientific/Engineering",
        "Topic :: Utilities"
      ])
