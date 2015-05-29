ipyrmd
======

Convert between IPython/Jupyter notebooks and R Markdown documents
------------------------------------------------------------------

This script provides conversion in both directions between the [IPython](https://github.com/ipython/ipython) [notebook format](https://ipython.org/ipython-doc/3/notebook/nbformat.html) (JSON with separate markdown and code) and the [R Markdown](https://github.com/rstudio/rmarkdown) [format](http://rmarkdown.rstudio.com) (markdown text with annotated code blocks).

It only really makes sense to use it with IPython notebooks using the IPython [R kernel](http://github.com/IRkernel/IRkernel), but will work with any type of code if you insist.

Conversion is **not lossless**:

 * Inline code blocks in R Markdown (r somecode`) are currently ignored (they remain as markdown text). Inserting code blocks for them would be a possible extension but since the main use for such blocks is to display an output value I assume ignoring them should not usually change program flow.
 * The YAML header used in R Markdown does not have a functional equivalent in IPython. The contents of the header are stored in the IPython notebook metadata dictionary (as `Rmd_header`) for round-trip conversion, but are not otherwise used.
 * Chunk options for R Markdown (```` ```{r, foo=bar}````) also do not (currently) have any functional equivalent in the IPython notebook. The option string (as text) is stored in the cell metadata (as `Rmd_chunk_options`) for round-trip conversion.
 * Since whitespace is significant in markdown, we attempt to maintain blank lines within code and markdown blocks, but the boundaries between code and markdown may not be exactly reproduced (you may get extra blank lines).
 * The IPython notebook may contain both text and rich output, but there is no way to keep this for R Markdown - you will need to re-knit the document.

Usage
-----

`python3`, `ipython >= 3` and `pyyaml` are required.

    ipyrmd [--to Rmd|ipynb] [-y] [-o outfile] infile

By default the output filename and direction of conversion will be determined from the input filename.

TODO
----

 * Support for R files with embedded markdown (``#' markdown, #+ chunkopts`)
 * Options for how to handle inline R blocks
 * Consider using nbconvert machinery for ipynb -> Rmd conversion
 * Consider whether any chunk options can be emulated with IRdisplay calls
 * Check IPython API compatibility between IPython and Jupyter

History
-------

 *  0.1 (2015-05-27) Initial release
 *  0.2 (2015-05-29) Re-structure as a python library providing script `ipyrmd`
