from . import IpynbTest, RmdTest

chunk_source = """```{r}
# no-options 0
```
```{r foo=1}
# single-option 1
```
```{r eval=-(4:5), results='markup', tidy=TRUE}
# multi-option 2
```
```{r        spaces=3        }
# many-spaces 3
```
```{r#nospaces}
# no-spaces 4
```
```{r, foo=5}
# r-comma-space 5
```
```{r,foo=6}
# r-comma-nospace 6
```
```{r,}
# r-comma-noopts 7
```"""
class TestChunkOptions(RmdTest):
    source = chunk_source
    # TODO: decide on how case 4 should actually be handled
    def test_opts_in_ipynb(self):
        cells = self.ipynb.cells
        self.assertNotIn("Rmd_chunk_options", cells[0].metadata)
        self.assertIn("Rmd_chunk_options", cells[1].metadata)
        self.assertIn("Rmd_chunk_options", cells[2].metadata)
        self.assertIn("Rmd_chunk_options", cells[3].metadata)
        #self.assertNotIn("Rmd_chunk_options", cells[4].metadata)
        self.assertIn("Rmd_chunk_options", cells[5].metadata)
        self.assertIn("Rmd_chunk_options", cells[6].metadata)
        self.assertNotIn("Rmd_chunk_options", cells[7].metadata)

        self.assertEquals(cells[1].metadata.Rmd_chunk_options, "foo=1")
        self.assertEquals(cells[2].metadata.Rmd_chunk_options,
                          "eval=-(4:5), results='markup', tidy=TRUE")
        self.assertEquals(cells[3].metadata.Rmd_chunk_options, "spaces=3")
        self.assertEquals(cells[5].metadata.Rmd_chunk_options, "foo=5")
        self.assertEquals(cells[6].metadata.Rmd_chunk_options, "foo=6")

    def test_opts_in_rmd(self):
        self.assertIn("```{r}\n# no-options", self.roundtrip)
        self.assertIn("```{r foo=1}", self.roundtrip)
        self.assertIn("```{r eval=-(4:5), results='markup', tidy=TRUE}", self.roundtrip)
        self.assertIn("```{r spaces=3}", self.roundtrip)
        self.assertIn("```{r foo=5}", self.roundtrip)
        self.assertIn("```{r foo=6}", self.roundtrip)
        self.assertIn("```{r}\n# r-comma-noopts", self.roundtrip)

spin_chunk_source = """#+ foo=0
code-0

#+ foo=1, bar=2
code-1

#+      foo=2
code-2

#+ foo=3

code-3

#' markdown-4

code-5

#+
code-6

#+foo=7
code-7"""
class TestSpinChunkOptions(RmdTest):
    source = spin_chunk_source
    use_rmd = False

    def test_opts_in_ipynb(self):
        cells = self.ipynb.cells
        self.assertIn("Rmd_chunk_options", cells[0].metadata)
        self.assertIn("Rmd_chunk_options", cells[1].metadata)
        self.assertIn("Rmd_chunk_options", cells[2].metadata)
        self.assertIn("Rmd_chunk_options", cells[3].metadata)
        self.assertNotIn("Rmd_chunk_options", cells[4].metadata)
        self.assertNotIn("Rmd_chunk_options", cells[5].metadata)

        self.assertEquals(cells[0].metadata.Rmd_chunk_options, "foo=0")
        self.assertEquals(cells[1].metadata.Rmd_chunk_options, "foo=1, bar=2")
        self.assertEquals(cells[2].metadata.Rmd_chunk_options, "foo=2")
        self.assertEquals(cells[3].metadata.Rmd_chunk_options, "foo=3")

    def test_opts_in_rmd(self):
        self.assertIn("#+ foo=0", self.roundtrip)
