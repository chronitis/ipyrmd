#!/usr/bin/env python3

"""
ipyrmd - Convert between IPython/Jupyter notebooks and R Markdown documents

This script provides conversion in both directions between the IPython notebook
format (JSON with seperate markdown and code) and the R markdown format
(markdown text with annotated code blocks).

It only really makes sense to use it with IPython notebooks using the R kernel
(github:IRkernel/IRkernel), but will work with any type of code if you insist.

Conversion is not lossless:

 * Inline code blocks in R Markdown (`r somecode`) are currently ignored (they
   remain as markdown text). Inserting code blocks for them would be a possible
   extension but since the main use for such blocks is to display an output
   value I assume ignoring them should not usually change program flow.
 * The YAML header used in R Markdown does not largely have an equivalent in
   IPython. The contents of the header are stored in the IPython notebook
   metadata dictionary (as "Rmd_header") for round-trip conversion, but are
   not otherwise used.
 * Chunk options for R Markdown (```{r, foo=bar}) also do not currently have
   any functional equivalent in the IPython notebook. The option string (as
   text) is stored in the cell metadata (as "Rmd_chunk_options") for round-trip
   conversion.
 * Since whitespace is significant in markdown, we attempt to maintain blank
   lines within code and markdown blocks, but the boundaries between code and
   markdown may not be exactly reproduced (you may get extra blank lines).
 * The IPython notebook may contain both text and rich output, but there is no
   way to keep this for R Markdown - you will need to re-run the document.

TODO:

 * Support for R files with embedded markdown (#' markdown, #+ chunkopts)
 * Options for how to handle inline R blocks
 * Consider using nbconvert machinery for ipynb -> Rmd conversion
 * Consider whether any chunk options can be emulated with IRdisplay calls

Version: 0.1 (2015-05-27)
"""

__author__ = "Gordon Ball <gordon@chronitis.net>"
__version__ = "0.1"

import IPython.nbformat
import yaml
import re

# cell.source can be either "source" or ["source", "source"]
# notebook does not insert implicit newlines in the list case
maybe_join = lambda x: x if isinstance(x, str) else "".join(x)

# join two blocks of text, adding a newline if there is not already
# a leading or trailing one
maybe_newline = lambda x, y: x+y if x.endswith("\n") or y.startswith("\n") else x+"\n"+y


# ensure NotebookNode objects are represented as plain dicts in YAML
def NN_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", dict(data),
                                    flow_style=False)

yaml.add_representer(IPython.nbformat.NotebookNode, NN_representer)


def ipynb_to_rmd(infile, outfile, header=None):
    with open(infile) as f:
        node = IPython.nbformat.reader.read(f)

    # ipynb format 4 is current as of IPython 3.0; update the data structure
    # for consistency if it is an older version
    ipynb_version = IPython.nbformat.reader.get_version(node)
    if ipynb_version < (4, 0):
        node = IPython.nbformat.convert(node, 4)

    notebook_lang = node.metadata.get('language_info', {}).get('name', None)
    if not notebook_lang == 'R':
        print('Warning: Notebook language "{0}" != R'.format(notebook_lang))
        print("Output is unlikely to be a valid Rmd document")

    result = []

    # to allow round-tripping, if no explicit header is specified and
    # node.metadata.Rmd_header exists, dump it as a YAML header
    if header is None:
        if "Rmd_header" in node.metadata:
            # header will consist of NotebookNode rather than dict objects
            # we added a representer function for these above
            header = node.metadata["Rmd_header"]

    if header is not None:
        # yaml.dump generates "..." as a document end marker instead of the
        # "---" conventionally used by rmarkdown, so manually add that instead
        text = maybe_newline(yaml.dump(header, explicit_start=True), "---")
        result.append(text)

    for cell in node.cells:
        if cell.cell_type == "markdown":
            result.append(maybe_join(cell.source))
        elif cell.cell_type == "code":
            if 'Rmd_chunk_options' in cell.metadata:
                start = "```{{r{0}}}".format(cell.metadata["Rmd_chunk_options"])
            else:
                start = "```{r}"

            # ensure start and end delimiters are on newlines but don't add
            # extra blank lines
            text = maybe_newline(start, maybe_join(cell.source))
            text = maybe_newline(text, "```")

            result.append(text)

    with open(outfile, "w") as f:
        # separate blocks with blank lines to ensure that code blocks stand
        # alone as paragraphs
        # TODO: check more carefully here, we tend to produce excess whitespace
        f.write("\n\n".join(result))

    return True

METADATA = dict(kernelspec=dict(display_name="R", language="R", name="ir"),
                language_info=dict(name="R", file_extension=".r",
                                   codemirror_mode="r",
                                   mimetype="text/x-r-source",
                                   pygments_lexer="r"))


def rmd_to_ipynb(infile, outfile):
    NN = IPython.nbformat.NotebookNode
    node = NN(nbformat=4, nbformat_minor=0, metadata=NN(**METADATA), cells=[])

    with open(infile) as f:
        rmdlines = f.readlines()

    # YAML front matter appears to be restricted to strictly ---\nYAML\n---
    re_yaml_delim = re.compile(r"^---\s*$")
    delim_lines = [i for i, l in enumerate(rmdlines) if re_yaml_delim.match(l)]
    if len(delim_lines) >= 2 and delim_lines[1] - delim_lines[0] > 1:
        yamltext = '\n'.join(rmdlines[delim_lines[0]+1:delim_lines[1]])
        try:
            header = yaml.load(yamltext)
            node.metadata["Rmd_header"] = header
        except yaml.YAMLError as e:
            print("Error reading document metadata block: {0}".format(e))
            print("Trying to continue without header")
        rmdlines = rmdlines[delim_lines[1]+1:]

    # the behaviour of rmarkdown appears to be that a code block does not
    # have to have matching numbers of start and end `s - just >=3
    # and there can be any number of spaces before the {r, meta} block,
    # but "r" must be the first character of that block

    re_code_start = re.compile(r"^````*\s*{r(.*)}\s*$")
    re_code_end = re.compile(r"^````*\s*$")
    re_code_inline = re.compile(r"`r.+`")

    MD, CODE = range(2)

    def add_cell(celltype, celldata, **meta):
        if celltype == MD:
            cell = NN(cell_type="markdown", metadata=NN(**meta),
                      source=celldata)
        else:
            cell = NN(cell_type="code", execution_count=None, source=celldata,
                      metadata=NN(collapsed=True, autoscroll=False, **meta),
                      outputs=[])
        node.cells.append(cell)

    state = MD
    celldata = []
    meta = {}

    for i, l in enumerate(rmdlines):
        if state == MD:
            match = re_code_start.match(l)
            if match:
                state = CODE
                # only add MD cells with non-whitespace content
                if any([c.strip() for c in celldata]):
                    add_cell(MD, celldata, **meta)

                celldata = []
                meta = {}

                if match.group(1):
                    meta['Rmd_chunk_options'] = match.group(1)
            else:
                if re_code_inline.search(l):
                    print("Inline R code detected - treated as text")
                # cell.source in ipynb does
                # not include implicit newlines
                celldata.append(l.strip() + "\n")
        else:  # CODE
            if re_code_end.match(l):
                state = MD
                # unconditionally add code blocks regardless of content
                # as above, possible extension to store {r meta} in metadata
                add_cell(CODE, celldata, **meta)
                celldata = []
                meta = {}
            else:
                celldata.append(l.strip() + "\n")

    if state == CODE or celldata:
        add_cell(state, celldata, **meta)

    with open(outfile, "w") as f:
        IPython.nbformat.write(node, outfile)

    return True


if __name__ == '__main__':
    import argparse
    import sys
    import pathlib

    parser = argparse.ArgumentParser(description="Convert between IPYNB and RMD formats")
    parser.add_argument("--to", choices=["ipynb", "Rmd"],
                        help="Output format (default: inferred from input filename)")
    parser.add_argument("-o", "--out", type=str,
                        help="Output filename (default: input filename with switched extension)")
    parser.add_argument("-y", action="store_true", default=False,
                        help="Overwrite existing output file")
    parser.add_argument("filename", help="Input filename")

    args = parser.parse_args()

    if args.to is not None:
        target = args.to
    else:
        if args.filename.lower().endswith("ipynb"):
            target = "Rmd"
        elif args.filename.lower().endswith("rmd"):
            target = "ipynb"
        else:
            print("Filename does not end either .ipynb or .Rmd")
            print("Please specify output format with --to")
            sys.exit(1)

    path_in = pathlib.Path(args.filename)
    if not path_in.exists():
        print('Input filename "{0}" does not exist'.format(path_in))
        sys.exit(1)

    if args.out is not None:
        path_out = pathlib.Path(args.out)
    else:
        path_out = path_in.with_suffix("." + target)

    if path_out.exists() and not args.y:
        print('Output filename "{0}" exists (allow overwrite with -y)'.format(path_out))
        sys.exit(1)

    if target == "Rmd":
        print("Converting (ipynb->Rmd) {0} to {1}".format(path_in, path_out))
        ipynb_to_rmd(str(path_in), str(path_out))
    else:
        print("Converting (Rmd->ipynb) {0} to {1}".format(path_in, path_out))
        rmd_to_ipynb(str(path_in), str(path_out))
