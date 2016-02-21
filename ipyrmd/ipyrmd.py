#!/usr/bin/env python3

"""
ipyrmd - Convert between IPython/Jupyter notebooks and R Markdown documents

This script provides conversion in both directions between the IPython notebook
format (JSON with seperate markdown and code) and the R markdown format
(markdown text with annotated code blocks).

TODO:

 * Options for how to handle inline R blocks
 * Consider using nbconvert machinery for ipynb -> Rmd conversion
 * Consider whether any chunk options can be emulated with IRdisplay calls
"""

import nbformat
import yaml
import re

# cell.source can be either "source" or ["source", "source"]
# notebook does not insert implicit newlines in the list case
maybe_join = lambda x: x if isinstance(x, str) else "".join(x)

# join two blocks of text, adding a newline if there is not already
# a leading or trailing one
maybe_newline = lambda x, y: x+y if x.endswith("\n") or y.startswith("\n") else x+"\n"+y


def join_with_emptylines(text):
    """
    Join a list of strings with \n\n (one empty line, to force separate
    markdown paragraphs, stripping any extra newlines.
    """
    if len(text) == 1:
        return text[0]
    result = text[0]
    for t in text[1:]:
        result = result.rstrip("\n") + "\n\n" + t.lstrip("\n")
    return result


def prepend_lines(text, prefix):
    """
    Insert a prefix at the beginning of each line, eg #'
    """
    return "\n".join([prefix+t for t in text.split("\n")])

unprepend_line = lambda x, p: x[len(p):] if x.startswith(p) else x


def unprepend_lines(text, prefix):
    return "\n".join([unprepend_line(t, prefix) for t in text.split("\n")])


# ensure NotebookNode objects are represented as plain dicts in YAML
def NN_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", dict(data),
                                    flow_style=False)

yaml.add_representer(nbformat.NotebookNode, NN_representer)


def read_ipynb(infile, header=None):
    with open(infile) as f:
        node = nbformat.reader.read(f)

    # ipynb format 4 is current as of IPython 3.0; update the data structure
    # for consistency if it is an older version
    ipynb_version = nbformat.reader.get_version(node)
    if ipynb_version < (4, 0):
        node = nbformat.convert(node, 4)

    notebook_lang = node.metadata.get('language_info', {}).get('name', None)
    if not notebook_lang == 'R':
        print('Warning: Notebook language "{0}" != R'.format(notebook_lang))
        print("Output is unlikely to be a valid Rmd document")

    # to allow round-tripping, if no explicit header is specified and
    # node.metadata.Rmd_header exists, dump it as a YAML header
    if header is None:
        if "Rmd_header" in node.metadata:
            # header will consist of NotebookNode rather than dict objects
            # we added a representer function for these above
            header = node.metadata["Rmd_header"]

    return node, header


def ipynb_to_rmd(infile, outfile, header=None):
    result = []

    node, header = read_ipynb(infile, header)

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
                start = "```{{r, {0}}}".format(cell.metadata["Rmd_chunk_options"])
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
        f.write(join_with_emptylines(result))

    return True


def ipynb_to_spin(infile, outfile, header=None):
    result = []

    node, header = read_ipynb(infile, header)

    if header is not None:
        # yaml.dump generates "..." as a document end marker instead of the
        # "---" conventionally used by rmarkdown, so manually add that instead
        text = maybe_newline(yaml.dump(header, explicit_start=True), "---")
        text = prepend_lines(text, "#' ")
        result.append(text)

    for cell in node.cells:
        if cell.cell_type == "markdown":
            result.append(prepend_lines(maybe_join(cell.source), "#' "))
        elif cell.cell_type == "code":
            if 'Rmd_chunk_options' in cell.metadata:
                start = "#+ " + cell.metadata["Rmd_chunk_options"]
                text = maybe_newline(start, maybe_join(cell.source))
            else:
                text = maybe_join(cell.source)
            result.append(text)

    with open(outfile, "w") as f:
        # separate blocks with blank lines to ensure that code blocks stand
        # alone as paragraphs
        # not strictly necessary in this case
        f.write(join_with_emptylines(result))

    return True

METADATA = dict(kernelspec=dict(display_name="R", language="R", name="ir"),
                language_info=dict(name="R", file_extension=".r",
                                   codemirror_mode="r",
                                   mimetype="text/x-r-source",
                                   pygments_lexer="r"))


def rmd_to_ipynb(infile, outfile):
    NN = nbformat.NotebookNode
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
        rmdlines = rmdlines[:delim_lines[0]] + rmdlines[delim_lines[1]+1:]

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

    for l in rmdlines:
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
                    meta['Rmd_chunk_options'] = match.group(1).strip(" ,")
            else:
                if re_code_inline.search(l):
                    print("Inline R code detected - treated as text")
                # cell.source in ipynb does not include implicit newlines
                celldata.append(l.rstrip() + "\n")
        else:  # CODE
            if re_code_end.match(l):
                state = MD
                # unconditionally add code blocks regardless of content
                add_cell(CODE, celldata, **meta)
                celldata = []
                meta = {}
            else:
                if len(celldata) > 0:
                    celldata[-1] = celldata[-1] + "\n"
                celldata.append(l.rstrip())

    if state == CODE or celldata:
        add_cell(state, celldata, **meta)

    with open(outfile, "w") as f:
        nbformat.write(node, outfile)

    return True


def spin_to_ipynb(infile, outfile):
    NN = nbformat.NotebookNode
    node = NN(nbformat=4, nbformat_minor=0, metadata=NN(**METADATA), cells=[])

    with open(infile) as f:
        lines = f.readlines()

    re_spin = re.compile(r"^#' (.*)$")
    re_spinprop = re.compile(r"^#\+ (.*)$")
    re_yaml_delim = re.compile(r"^#' ---\s*$")

    delim_lines = [i for i, l in enumerate(lines) if re_yaml_delim.match(l)]

    if len(delim_lines) >= 2 and delim_lines[1] - delim_lines[0] > 1:
        yamltext = '\n'.join(lines[delim_lines[0]+1:delim_lines[1]])
        yamltext = unprepend_lines(yamltext, "#' ")
        try:
            header = yaml.load(yamltext)
            node.metadata["Rmd_header"] = header
        except yaml.YAMLError as e:
            print("Error reading document metadata block: {0}".format(e))
            print("Trying to continue without header")
        lines = lines[:delim_lines[0]] + lines[delim_lines[1]+1:]

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

    for l in lines:
        spinmatch = re_spin.match(l)
        propmatch = re_spinprop.match(l)
        if state == MD:
            if spinmatch:
                celldata.append(spinmatch.group(1).rstrip() + "\n")
            else:
                state = CODE
                # only add MD cells with non-whitespace content
                if any([c.strip() for c in celldata]):
                    add_cell(MD, celldata, **meta)

                celldata = []
                meta = {}

                if propmatch:
                    meta['Rmd_chunk_options'] = propmatch.group(1).strip(" ,")
                else:
                    celldata.append(l.rstrip() + "\n")
        else:
            if spinmatch:
                if any([c.strip() for c in celldata]):
                    add_cell(CODE, celldata, **meta)
                state = MD
                celldata = []
                meta = {}
                celldata.append(spinmatch.group(1).rstrip())
            elif propmatch:
                if any([c.strip() for c in celldata]):
                    add_cell(CODE, celldata, **meta)
                celldata = []
                meta = {}
                meta['Rmd_chunk_options'] = propmatch.group(1).strip(" ,")
            else:
                celldata.append(l.rstrip()+"\n")

    if any([c.strip() for c in celldata]):
        add_cell(state, celldata, **meta)

    with open(outfile, "w") as f:
        nbformat.write(node, outfile)

    return True
