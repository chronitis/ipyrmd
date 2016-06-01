from . import IpynbTest, RmdTest


rmd_basic = """markdown-0-0
markdown-0-1

```{r}
code-1
```

markdown-2-0
markdown-2-1

```{r}
code-3-0
code-3-1
code-3-2
```"""
class TestRmdBasic(RmdTest):
    source = rmd_basic
    def test_basic_ipynb(self):
        cells = self.ipynb.cells
        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[0].cell_type, "markdown")
        self.assertIn("markdown-0-0\nmarkdown-0-1", cells[0].source)
        self.assertEqual(cells[1].cell_type, "code")
        self.assertIn("code-1", cells[1].source)
        self.assertEqual(cells[2].cell_type, "markdown")
        self.assertIn("markdown-2-0\nmarkdown-2-1", cells[2].source)
        self.assertEqual(cells[3].cell_type, "code")
        self.assertIn("code-3-0\ncode-3-1\ncode-3-2", cells[3].source)

    def test_basic_rmd(self):
        self.assertEqual(self.roundtrip, self.source)

spin_basic = """#' markdown-0-0
#' markdown-0-1

code-1

#' markdown-2-0
#' markdown-2-1

code-3-0
code-3-1
code-3-2
"""
class TestSpinBasic(TestRmdBasic):
    source = spin_basic
    use_rmd = False

class TestIpynbBasic(IpynbTest):
    cells = [
        dict(cell_type="markdown", metadata={}, source="markdown-0-0\nmarkdown-0-1\n"),
        dict(cell_type="code", execution_count=0, metadata={}, outputs=[], source="code-1"),
        dict(cell_type="markdown", metadata={}, source=["markdown-2-0\n", "markdown-2-1\n", "\n"]),
        dict(cell_type="code", execution_count=0, metadata={}, outputs=[], source=["code-3-0\ncode-3-1\n", "code-3-2"]),
    ]
    def test_basic_rmd(self):
        self.assertEqual(self.rmd, rmd_basic)

    def test_basic_ipynb(self):
        self.assertEqual(len(self.roundtrip.cells), len(self.cells))

rmd_repeat = """markdown-0
```{r}
code-1
```

```{r}
code-2
```
```{r}
code-3
```"""
class TestRmdRepeat(RmdTest):
    source = rmd_repeat
    def test_repeated_rmd(self):
        cells = self.ipynb.cells
        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[0].cell_type, "markdown")
        self.assertEqual(cells[1].cell_type, "code")
        self.assertEqual(cells[2].cell_type, "code")
        self.assertEqual(cells[3].cell_type, "code")
        self.assertIn("markdown-0", cells[0].source)
        self.assertIn("code-1", cells[1].source)
        self.assertIn("code-2", cells[2].source)
        self.assertIn("code-3", cells[3].source)
