# run the test cases with `python3 -m unittest` from the project root

import unittest
import nbformat
import tempfile
import ipyrmd

NBFORMAT_VERSION = 4

# generic test classes which start from either an ipynb or rmd source
# file, write it to a tempfile, then convert it back and forth, after
# which the outputs can be compared

class IpynbTest(unittest.TestCase):
    default_metadata = {
        "language_info": {
            "name": "R",
        }
    }
    cells = []
    metadata = None
    use_rmd = True

    def setUp(self):
        if self.metadata is None:
            metadata = self.default_metadata
        else:
            metadata = self.metadata
        self.orig = nbformat.from_dict({
            "nbformat": NBFORMAT_VERSION,
            "nbformat_minor": 0,
            "metadata": metadata,
            "cells": self.cells
        })

        with tempfile.TemporaryDirectory() as d:
            ipynb0_name = d + "/0"
            rmd_name = d + "/1"
            ipynb1_name = d + "/2"

            with open(ipynb0_name, "w") as f:
                nbformat.write(self.orig, f)

            if self.use_rmd:
                ipyrmd.ipynb_to_rmd(ipynb0_name, rmd_name)
                ipyrmd.rmd_to_ipynb(rmd_name, ipynb1_name)
            else:
                ipyrmd.ipynb_to_spin(ipynb0_name, rmd_name)
                ipyrmd.spin_to_ipynb(rmd_name, ipynb1_name)

            with open(rmd_name) as f:
                self.rmd = f.read()

            with open(ipynb1_name) as f:
                self.roundtrip = nbformat.read(f, NBFORMAT_VERSION)

class RmdTest(unittest.TestCase):
    source = ""
    use_rmd = True
    def setUp(self):
        with tempfile.TemporaryDirectory() as d:
            rmd0_name = d + "/0"
            ipynb_name = d + "/1"
            rmd1_name = d + "/2"

            with open(rmd0_name, "w") as f:
                f.write(self.source)

            if self.use_rmd:
                ipyrmd.rmd_to_ipynb(rmd0_name, ipynb_name)
                ipyrmd.ipynb_to_rmd(ipynb_name, rmd1_name)
            else:
                ipyrmd.spin_to_ipynb(rmd0_name, ipynb_name)
                ipyrmd.ipynb_to_spin(ipynb_name, rmd1_name)

            with open(ipynb_name) as f:
                self.ipynb = nbformat.read(f, NBFORMAT_VERSION)

            with open(rmd1_name) as f:
                self.roundtrip = f.read()
