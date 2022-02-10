# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

from __future__ import annotations

import sys
import os
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from enum import Enum

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from types import ModuleType
    from typing import Optional, Callable, Any, Sequence

CATEGORY_STRING = 'Category:'

DO_STYLES = False
DO_CSS_CLASSES = False

STYLE_PAD_L0 = ' style="padding-left: 0px;"' if DO_STYLES else ''
STYLE_PAD_L30 = ' style="padding-left: 30px;"' if DO_STYLES else ''
STYLE_PAD_L60 = ' style="padding-left: 60px;"' if DO_STYLES else ''


class CategoryType(Enum):
    """Self explanatory."""
    FUNCTION = 0
    CLASS = 1


@dataclass
class AttributeInfo:
    """Info about an attribute of a class."""
    name: str
    attr_type: Optional[str] = None
    docs: Optional[str] = None


@dataclass
class FunctionInfo:
    """Info about a function/method."""
    name: str
    category: Optional[str] = None
    method_class: Optional[str] = None
    docs: Optional[str] = None
    is_class_method: bool = False


@dataclass
class ClassInfo:
    """Info about a class of functions/classes."""
    name: str
    category: str
    methods: list[FunctionInfo]
    inherited_methods: list[FunctionInfo]
    attributes: list[AttributeInfo]
    parents: list[str]
    docs: Optional[str]
    enum_values: Optional[list[str]]


def parse_docs_attrs(attrs: list[AttributeInfo], docs: str) -> str:
    """Given a docs str, parses attribute descriptions contained within."""
    docs_lines = docs.splitlines()
    attr_line = None
    for i, line in enumerate(docs_lines):
        if line.strip() in ['Attributes:', 'Attrs:']:
            attr_line = i
            break
    if attr_line is not None:

        # Docs is now everything *up to* this.
        docs = '\n'.join(docs_lines[:attr_line])

        # Go through remaining lines creating attrs and docs for each.
        cur_attr: Optional[AttributeInfo] = None
        for i in range(attr_line + 1, len(docs_lines)):
            line = docs_lines[i].strip()

            # A line with a single alphanumeric word preceding a colon
            # is a new attr.
            splits = line.split(':')
            if (len(splits) in (1, 2) and splits[0]
                    and splits[0].replace('_', '').isalnum()):
                if cur_attr is not None:
                    attrs.append(cur_attr)
                cur_attr = AttributeInfo(name=splits[0])
                if len(splits) == 2:
                    cur_attr.attr_type = splits[1]

            # Any other line gets tacked onto the current attr.
            else:
                if cur_attr is not None:
                    if cur_attr.docs is None:
                        cur_attr.docs = ''
                    cur_attr.docs += line + '\n'

        # Finish out last.
        if cur_attr is not None:
            attrs.append(cur_attr)

        for attr in attrs:
            if attr.docs is not None:
                attr.docs = attr.docs.strip()
    return docs


def _get_defining_class(cls: type, name: str) -> Optional[type]:
    for i in cls.mro()[1:]:
        if hasattr(i, name):
            return i
    return None


def _get_bases(cls: type) -> list[str]:
    bases = []
    for par in cls.mro()[1:]:
        if par is not object:
            bases.append(par.__module__ + '.' + par.__name__)
    return bases


def _split_into_paragraphs(docs: str, filter_type: str, indent: int) -> str:
    indent_str = str(indent) + 'px'

    # Ok, now break into paragraphs (2 newlines denotes a new paragraph).
    paragraphs = docs.split('\n\n')
    docs = ''
    for i, par in enumerate(paragraphs):

        # For function/method signatures, indent lines after the first so
        # our big multi-line function signatures are readable.
        if (filter_type in ['function', 'method'] and i == 0
                and len(par.split('(')) > 1
                and par.strip().split('(')[0].replace('.', '').replace(
                    '_', '').isalnum()):
            style = (' style="padding-left: ' + str(indent + 50) +
                     'px; text-indent: -50px;"') if DO_STYLES else ''
            style2 = ' style="color: #666677;"' if DO_STYLES else ''
            docs += f'<p{style}><span{style2}>'

            # Also, signatures seem to have quotes around annotations.
            # Let's just strip them all out. This will look wrong if
            # we have a string as a default value though, so don't
            # in that case.
            if " = '" not in par and ' = "' not in par:
                par = par.replace("'", '')
            docs += par
            docs += '</span></p>\n\n'

        # Emphasize a few specific lines.
        elif par.strip() in [
                'Conditions:', 'Available Conditions:', 'Actions:',
                'Available Actions:', 'Play Types:',
                'Available Setting Options:', 'Available Values:', 'Usage:'
        ]:
            style = (' style="padding-left: ' + indent_str +
                     ';"' if DO_STYLES else '')
            docs += f'<p{style}><strong>'
            docs += par
            docs += '</strong></p>\n\n'

        elif par.lower().strip().startswith(CATEGORY_STRING.lower()):
            style = (' style="padding-left: ' + indent_str +
                     ';"' if DO_STYLES else '')
            docs += f'<p{style}>'
            docs += par
            docs += '</p>\n\n'

        elif par.strip().startswith('#'):
            p_lines = par.split('\n')
            for it2, line in enumerate(p_lines):
                if line.strip().startswith('#'):
                    style = (' style="color: #008800;"' if DO_STYLES else '')
                    p_lines[it2] = (f'<span{style}><em><small>' + line +
                                    '</small></em></span>')
            par = '\n'.join(p_lines)
            style = (' style="padding-left: ' + indent_str +
                     ';"' if DO_STYLES else '')
            docs += f'<pre{style}>'
            docs += par
            docs += '</pre>\n\n'
        else:
            style = (' style="padding-left: ' + indent_str +
                     ';"' if DO_STYLES else '')
            docs += f'<p{style}>'
            docs += par
            docs += '</p>\n\n'
    return docs


def _filter_type_settings(filter_type: str) -> tuple[Optional[Callable], int]:
    get_category_href_func = None
    if filter_type == 'class':
        indent = 30
        get_category_href_func = _get_class_category_href
    elif filter_type == 'method':
        indent = 60
    elif filter_type == 'function':
        indent = 30
        get_category_href_func = _get_function_category_href
    elif filter_type == 'attribute':
        indent = 60
    else:
        raise Exception('invalid filter_type: ' + str(filter_type))
    return get_category_href_func, indent


def _get_defining_class_backwards(cls: type, name: str) -> Optional[type]:
    mro = cls.mro()
    mro.reverse()
    for i in mro:
        if hasattr(i, name):
            return i
    return None


def _get_module_classes(module: ModuleType) -> list[tuple[str, type]]:
    names = dir(module)

    # Look for all public classes in the provided module.
    class_objs = [
        getattr(module, name) for name in names if not name.startswith('_')
    ]
    class_objs = [
        c for c in class_objs if str(c).startswith('<class ')
        or str(c).startswith('<type ') or str(c).startswith('<enum ')
    ]

    # Build a map of full names and their corresponding classes.
    classes_by_name = [(c.__module__ + '.' + c.__name__, c)
                       for c in class_objs]

    # Strip duplicates (for instance ba.Dep and ba.Dependency are the same
    # thing at runtime)
    classes_by_name = list(set(classes_by_name))

    # And add those classes' inner classes.
    _add_inner_classes(class_objs, classes_by_name)
    return classes_by_name


def _is_inherited(cls: type, name: str) -> bool:
    method = getattr(cls, name)

    # Classmethods are already bound with the class as self.
    # we need to just look at the im_func in that case
    is_class_method = (inspect.ismethod(method) and method.__self__ is cls)
    if is_class_method:
        for mth in cls.mro()[1:]:
            mth2 = getattr(mth, name, None)
            if mth2 is not None:
                if method.__func__ == mth2.__func__:
                    return True
    else:
        return any(method == getattr(i, name, None) for i in cls.mro()[1:])
    return False


def _get_function_category_href(c_name: str) -> str:
    """Return a href for linking to the specified function category."""
    return 'function_category_' + c_name.replace('.', '_').replace(' ', '_')


def _get_class_category_href(c_name: str) -> str:
    """Return a href for linking to the specified class category."""
    return 'class_category_' + c_name.replace('.', '_').replace(' ', '_')


def _get_class_href(c_name: str) -> str:
    """Return a href for linking to the specified class."""
    return 'class_' + c_name.replace('.', '_')


def _get_function_href(f_name: str) -> str:
    """Return a href for linking to the specified function."""
    return 'function_' + f_name.replace('.', '_')


def _get_method_href(c_name: str, f_name: str) -> str:
    """Return a href for linking to the specified method."""
    return 'method_' + c_name.replace('.', '_') + '__' + f_name.replace(
        '.', '_')


def _get_attribute_href(c_name: str, a_name: str) -> str:
    return 'attr_' + c_name.replace('.', '_') + '__' + a_name.replace('.', '_')


def _get_category(docs: str, category_type: CategoryType) -> str:
    """Parse the category name from a docstring."""
    category_lines = [
        l for l in docs.splitlines()
        if l.lower().strip().startswith(CATEGORY_STRING.lower())
    ]
    if category_lines:
        category = category_lines[0].strip()[len(CATEGORY_STRING):].strip()
    else:
        category = {
            CategoryType.CLASS: 'Misc Classes',
            CategoryType.FUNCTION: 'Misc Functions'
        }[category_type]
    return category


def _print_child_classes(category_classes: list[ClassInfo], parent: str,
                         indent: int) -> str:
    out = ''
    valid_classes = []
    for cls in category_classes:
        if cls.parents:
            c_parent = cls.parents[0]
        else:
            c_parent = ''

        # If it has a parent not in this category, consider it to
        # have no parent.
        if c_parent != '':
            found = False
            for ctest in category_classes:
                if c_parent == ctest.name:
                    found = True
                    break
            if not found:
                c_parent = ''

        # Print only if its parent matches what we want.
        if c_parent == parent:
            valid_classes.append(cls)
    if valid_classes:
        out += '   ' * indent + '<ul>\n'
    for cls in valid_classes:
        out += ('   ' * indent + '   <li><a href="#' +
                _get_class_href(cls.name) + '">' + cls.name + '</a></li>\n')
        out += _print_child_classes(category_classes, cls.name, indent + 1)
    if valid_classes:
        out += '   ' * indent + '</ul>\n'
    return out


def _add_inner_classes(class_objs: Sequence[type],
                       classes_by_name: list[tuple[str, type]]) -> None:
    # Ok, now go through all existing classes and look for classes
    # defined within.
    for cls in class_objs:
        for name in dir(cls):
            if name.startswith('_'):
                continue
            obj = getattr(cls, name)
            if not inspect.isclass(obj):
                continue
            if _get_defining_class_backwards(cls, name) != cls:
                continue
            classes_by_name.append(
                (cls.__module__ + '.' + cls.__name__ + '.' + name, obj))


def generate(projroot: str) -> None:
    """Main entry point."""
    import pdoc

    # Make sure we're running from the dir above this script.
    os.chdir(projroot)

    pythondir = str(
        Path(projroot, 'assets', 'src', 'ba_data', 'python').absolute())
    sys.path.append(pythondir)
    outdirname = Path('build', 'docs_html').absolute()

    try:
        pdoc.pdoc('ba', 'bastd', output_directory=outdirname)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise CleanError('Docs generation failed') from exc

    print(f'{Clr.GRN}Docs generation complete.{Clr.RST}')
