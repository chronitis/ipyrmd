from . import IpynbTest, RmdTest


rmd_basic = """markdown-0-0

markdown-0-1
```{r}
code-1
```
markdown-2-0
markdown-2-1

```{r}
code-3
```"""
class TestRmdBasic(RmdTest):
    source = rmd_basic
    def test_basic_ipynb(self):
        cells = self.ipynb.cells
        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[0].cell_type, "markdown")
        self.assertEqual(cells[1].cell_type, "code")
        self.assertEqual(cells[2].cell_type, "markdown")
        self.assertEqual(cells[3].cell_type, "code")

    def test_basic_rmd(self):
        self.assertEqual(self.roundtrip, rmd_basic)

spin_basic = """#' markdown-0-0
#' markdown-0-1
code-1
#'
#' markdown-2-0
#' markdown-2-1

code-3-0
code-3-1

code-3-2

#' markdown-4-0

#' markdown-4-1"""
class TestSpinBasic(RmdTest):
    source = spin_basic
    use_rmd = False
    def test_basic_ipynb(self):
        cells = self.ipynb.cells
        self.assertEqual(len(cells), 5)
        self.assertEqual(cells[0].cell_type, "markdown")
        self.assertEqual(cells[1].cell_type, "code")
        self.assertEqual(cells[2].cell_type, "markdown")
        self.assertEqual(cells[3].cell_type, "code")
        self.assertEqual(cells[4].cell_type, "markdown")

    def test_basic_rmd(self):
        self.assertEqual(self.roundtrip, spin_basic)

class TestIpynbBasic(IpynbTest):
    cells = [
        dict(cell_type="markdown", metadata={}, source="markdown-0-0\nmarkdown-0-1"),
        dict(cell_type="code", execution_count=0, metadata={}, outputs=[], source="code-1"),
        dict(cell_type="markdown", metadata={}, source=["markdown-2-0\n", "markdown-2-1\n", ""]),
        dict(cell_type="code", execution_count=0, metadata={}, outputs=[], source=["code-3"]),
    ]
    def test_basic_rmd(self):
        self.assertEqual(self.rmd, rmd_basic)

    def test_basic_ipynb(self):
        self.assertEqual(len(self.roundtrip.cells), len(self.cells))
