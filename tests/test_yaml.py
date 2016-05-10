from . import IpynbTest, RmdTest

yaml_source = """---
title: Test document
author: foobar <foo@bar.tld>
date: 1970-01-01T00:00:00+0000
output:
    html_document:
        toc: true
ünicode: £¼±å
---
lorem ipsum
```{r}
1+1
```
"""
class TestYAMLHeader(RmdTest):
    source = yaml_source

    def test_header_in_ipynb(self):
        self.assertIn("Rmd_header", self.ipynb.metadata)
        header = self.ipynb.metadata.Rmd_header
        self.assertIn("title", header)
        self.assertIn("author", header)
        self.assertIn("date", header)
        self.assertIn("output", header)
        self.assertIn("ünicode", header)
        self.assertEqual("Test document", header.title)
        self.assertEqual("foobar <foo@bar.tld>", header.author)
        self.assertEqual("1970-01-01T00:00:00+0000", header.date)
        self.assertEqual(True, header.output.html_document.toc)
        self.assertEqual("£¼±å", header.ünicode)


    def test_header_in_rmd(self):
        self.assertIn("---", self.roundtrip)
        self.assertIn("Test document", self.roundtrip)
        self.assertIn("foobar <foo@bar.tld>", self.roundtrip)
        self.assertIn("1970-01-01T00:00:00+0000", self.roundtrip)
        self.assertIn("£¼±å", self.roundtrip)
        self.assertRegexpMatches(self.roundtrip, r"output:\s*html_document:\s*toc:\s*true")
        self.assertIn("1+1", self.roundtrip)
        self.assertIn("lorem ipsum", self.roundtrip)

spin_yaml_source = """#' ---
#' title: Test document
#' author: foobar <foo@bar.tld>
#' date: 1970-01-01T00:00:00+0000
#' output:
#'     html_document:
#'         toc: true
#' ünicode: £¼±å
#' ---
#' lorem ipsum
1+1
"""
class TestSpinYAMLHeader(TestYAMLHeader):
    source = spin_yaml_source
    use_rmd = False
