import inspect
import tokenize

import pylatex

from .traits import TraitRegistry, Trait


newlines = "\n\n"

def content_report(fidia_trait_registry):
    # type: (TraitRegistry) -> str
    assert isinstance(fidia_trait_registry, TraitRegistry)


    latex_lines = [
        r"""\documentclass{awg_report}

        \author{Andy Green}
        \title{SAMI Traits}

        \usepackage{hyperref}
        \usepackage{listings}
        \lstset{% general command to set parameter(s)
            basicstyle=\ttfamily\scriptsize,
            showstringspaces=false,
            numbers=left, numberstyle=\tiny, stepnumber=5, numbersep=5pt,
            breaklines=true,
            postbreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\color{red}\hookrightarrow\space}}}
        \lstset{language=Python}
        \usepackage{minted}

        \begin{document}

        \maketitle

        """
    ]



    latex_lines.extend(trait_report(fidia_trait_registry))

    latex_lines.append("\\end{document}")

    return latex_lines

def schema_hierarchy(fidia_trait_registry):
    # type: (TraitRegistry) -> str
    assert isinstance(fidia_trait_registry, TraitRegistry)

    schema = fidia_trait_registry.schema(include_subtraits=True, data_class='all', combine_levels=tuple(), verbosity='data_only', separate_metadata=True)


def trait_report(fidia_trait_registry):
    # type: (TraitRegistry) -> str
    assert isinstance(fidia_trait_registry, TraitRegistry)

    latex_lines = []

    additional_traits = []

    # Iterate over all Traits in the Registry:
    for trait_type in fidia_trait_registry.get_trait_types():
        for trait_class in fidia_trait_registry.get_trait_classes(trait_type_filter=trait_type):
            assert issubclass(trait_class, Trait)

            latex_lines.append(newlines + r"\section{Trait Class: %s}" % pylatex.utils.escape_latex(trait_class.__name__))
            latex_lines.append(r"\label{sec:%s}" % (trait_class.__name__.replace("_", "-")))

            latex_lines.append(newlines + r"\subsection{Trait Keys Included}")
            tk_list = []
            all_keys = fidia_trait_registry.get_all_traitkeys(trait_type_filter=trait_type)
            assert len(all_keys) > 0
            for tk in all_keys:
                class_for_key = fidia_trait_registry.retrieve_with_key(tk)
                assert issubclass(class_for_key, Trait)
                if class_for_key is trait_class:
                       tk_list.append(tk)
            latex_lines.extend(latex_format_trait_key_table(tk_list))



            if trait_class.init is not Trait.init:
                latex_lines.append(newlines + r"\subsection{Init Code}")
                latex_lines.extend(latex_format_code_for_object(trait_class.init))

            latex_lines.append(newlines + r"\subsection{Trait Properties}")
            latex_lines.extend(trait_property_report(trait_class))

            if hasattr(trait_class, 'sub_traits'):
                assert isinstance(trait_class.sub_traits, TraitRegistry)
                all_sub_traits = trait_class.sub_traits.get_trait_classes()
                if len(all_sub_traits) > 0:
                    latex_lines.append(newlines + r"\subsection{Sub traits}")
                    latex_lines.append(newlines + r"\begin{itemize}")
                    for sub_trait in all_sub_traits:
                        additional_traits.append(sub_trait)
                        latex_lines.append("\\item \\hyperref[{ref}]{{{text}}}".format(
                            ref=sub_trait.__name__.replace("_", "-"),
                            text=pylatex.utils.escape_latex(trait_class.__name__)
                        ))
                    latex_lines.append(r"\end{itemize}")


    assert isinstance(latex_lines, list)

    return latex_lines


def trait_property_report(trait):
    # type: (Trait) -> str
    assert issubclass(trait, Trait)

    latex_lines = []

    for trait_property_name in trait.trait_property_dir():
        trait_property = getattr(trait, trait_property_name)

        latex_lines.append(newlines + r"\subsubsection{Trait Property: %s}" % pylatex.utils.escape_latex(trait_property_name))

        # source_lines = inspect.getsourcelines(trait_property.fload)[0]
        latex_lines.extend(latex_format_code_for_object(trait_property.fload))

    assert isinstance(latex_lines, list)

    return latex_lines

def latex_format_trait_key_table(trait_key_list):

    latex_lines = [
        newlines + r"\begin{tabular}{llll}",
        r"Type & Qualifier & Branch & Version \\"
    ]
    for tk in trait_key_list:
        latex_lines.append(r"{type} & {qual} & {branch} & {version} \\".format(
            type=pylatex.utils.escape_latex(tk.trait_type),
            qual=pylatex.utils.escape_latex(tk.trait_qualifier),
            branch=pylatex.utils.escape_latex(tk.branch),
            version=pylatex.utils.escape_latex(tk.version)))

    latex_lines.append(r"\end{tabular}")
    assert isinstance(latex_lines, list)
    return latex_lines

def latex_format_code_for_object(obj, package='listings'):
    # type: (str) -> str

    # prev_toktype = token.INDENT
    # first_line = None
    # last_lineno = -1
    # last_col = 0
    #
    # tokgen = tokenize.generate_tokens(python_code)
    # for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
    #     if 0:   # Change to if 1 to see the tokens fly by.
    #         print("%10s %-14s %-20r %r" % (
    #             tokenize.tok_name.get(toktype, toktype),
    #             "%d.%d-%d.%d" % (slineno, scol, elineno, ecol),
    #             ttext, ltext
    #             ))
    #     if slineno > last_lineno:
    #         last_col = 0
    #     if scol > last_col:
    #         mod.write(" " * (scol - last_col))
    #     if toktype == token.STRING and prev_toktype == token.INDENT:
    #         # Docstring
    #         mod.write("#--")
    #     elif toktype == tokenize.COMMENT:
    #         # Comment
    #         mod.write("##\n")
    #     else:
    #         mod.write(ttext)
    #     prev_toktype = toktype
    #     last_col = ecol
    #     last_lineno = elineno

    python_code = inspect.getsourcelines(obj)[0]

    if obj.__doc__:
        code_string = "".join(python_code)
        code_string.replace(obj.__doc__, "")
        python_code = code_string.splitlines()


    if package == 'minted':
        latex_lines = [newlines + r"\begin{minted}[linenos,fontsize=\small]{python}"]
    else:
        latex_lines = [newlines + r"\begin{lstlisting}"]

    for line in python_code:
        latex_lines.append(line.strip("\n"))
    if package == 'minted':
        latex_lines.append(r"\end{minted}")
    else:
        latex_lines.append(r"\end{lstlisting}")

    assert isinstance(latex_lines, list)

    return latex_lines