# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

# pylint: disable=too-many-lines

from __future__ import annotations

import os
import datetime
import inspect
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, cast
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


class Generator:
    """class which handles docs generation."""

    def __init__(self) -> None:
        self._index_keys: list[str] = []

        # Make a list of missing stuff so we can warn about it in one
        # big chunk at the end (so the user can batch their corrections).
        self._errors: list[Any] = []
        self._index: dict[str, tuple[str, Union[ClassInfo, FunctionInfo,
                                                AttributeInfo]]] = {}
        self._out = ''
        self._classes: list[ClassInfo] = []
        self._functions: list[FunctionInfo] = []
        self._merged_categories: list[tuple[str, str,
                                            list[Union[ClassInfo,
                                                       FunctionInfo]]]] = []

    def name_variants(self, name: str) -> list[str]:
        """Return variants of a word (such as plural) for linking."""
        # Do 'ies' plural for words ending in y.
        # (but not things like foo.y or display or prey)
        if (len(name) > 1 and name.endswith('y') and name[-2].isalpha()
                and name[-2] not in {'a', 'e', 'i', 'o', 'u'}):
            return [name, f'{name[:-1]}ies']
        # Otherwise assume plural just ends with s:
        return [name, f'{name}s']

    def _add_index_links(self,
                         docs: str,
                         ignore_links: Optional[list[str]] = None) -> str:
        """Add links to indexed classes/methods/etc found in a docstr."""
        sub_num = 0
        subs = {}

        # Ok now replace any names found in our index with links.
        for index_entry in self._index_keys:
            if ignore_links is not None and index_entry in ignore_links:
                continue

            for index_entry_actual in self.name_variants(index_entry):
                bits = docs.split(index_entry_actual)
                docs = bits[0]

                # Look at the first char after each split; if its
                # not alphanumeric, lets replace.
                for i in range(1, len(bits)):
                    bit = bits[i]
                    if not bit:
                        valid = True
                    else:
                        valid = not bit[:1].isalnum()
                    if valid:

                        # Strip out this name and replace it with a funky
                        # string to prevent further replacements from
                        # applying to it.. we'll then swap it back at the end.
                        sub_name = '<__SUB' + str(sub_num) + '__>'
                        subs[sub_name] = index_entry_actual
                        sub_num += 1

                        # Sub in link.
                        docs += ('<a href="#' + self._index[index_entry][0] +
                                 '">' + sub_name + '</a>')
                    else:
                        docs += index_entry_actual  # Keep original.
                    docs += bits[i]

        # Misc replacements:
        docs = docs.replace(
            'General message handling; can be passed any message object.',
            'General message handling; can be passed any <a href="#' +
            _get_class_category_href('Message Classes') +
            '">message object</a>.')

        for sub_name, sub_val in list(subs.items()):
            docs = docs.replace(sub_name, sub_val)
        return docs

    def _get_all_attrs_for_class(self, cls: type,
                                 docs: str) -> tuple[str, list[AttributeInfo]]:
        """
        if there's an 'Attributes' section in the docs, strip it out and
        create attributes entries out of it.
        Returns the stripped down docs as well as detected attrs.
        """
        attrs: list[AttributeInfo] = []

        # Start by pulling any type info we find in the doc str.
        # (necessary in many non-property cases since there's no other way
        # to annotate attrs)
        docs = parse_docs_attrs(attrs, docs)

        # In some cases we document an attr in the class doc-string but
        # provide an annotation for it at the type level.
        # (this is the case for simple class/instance attributes since we
        # can't provide docstrings along with those)
        self._get_class_level_types_for_doc_attrs(cls, attrs)

        # Now pull info on properties, which can have doc-strings and
        # annotations all in the same place; yay!
        self._get_property_attrs_for_class(cls, attrs)

        return docs, attrs

    def _get_class_level_types_for_doc_attrs(
            self, cls: type, attrs: list[AttributeInfo]) -> None:
        # Take note of all the attrs that we're aware of already;
        # these are the ones we can potentially provide type info for.
        existing_attrs_by_name = {a.name: a for a in attrs}

        cls_annotations = getattr(cls, '__annotations__', {})

        for aname, aval in cls_annotations.items():
            # (we expect __future__ annotations to always be on, which makes
            # these strings)
            assert isinstance(aval, str)
            if aname in existing_attrs_by_name:
                # Complain if there's a type in both the docs and the type.
                if existing_attrs_by_name[aname].attr_type is not None:
                    print('FOUND', existing_attrs_by_name[aname], aval)
                    self._errors.append(
                        f'attr {aname} for class {cls}'
                        'has both a docstring and class level annotation;'
                        ' should just have one')
                existing_attrs_by_name[aname].attr_type = aval

    def _get_property_attrs_for_class(self, cls: type,
                                      attrs: list[AttributeInfo]) -> None:
        for attrname in dir(cls):
            attr = getattr(cls, attrname)

            if isinstance(attr, property):
                if any(a.name == attrname for a in attrs):
                    raise Exception(f'attr "{attrname}" has both a'
                                    f' class docs and property entry')

                # Pull its docs.
                attrdocs = getattr(attr, '__doc__', None)
                if attrdocs is None:
                    self._errors.append(
                        f'property \'{attrname}\' on class {cls}')
                    attrdocs = '(no docs)'
                else:
                    attrdocs = attrdocs.strip()

                # Pull type annotations.
                attr_annotations = getattr(attr.fget, '__annotations__')
                if (not isinstance(attr_annotations, dict)
                        or 'return' not in attr_annotations
                        or not isinstance(attr_annotations['return'], str)):
                    raise Exception('property type annotation not found')
                attrtype = attr_annotations['return']

                if '(internal)' not in attrdocs:
                    attrs.append(
                        AttributeInfo(name=attrname,
                                      docs=attrdocs,
                                      attr_type=attrtype))

    def _get_base_docs_for_class(self, cls: type) -> str:
        if cls.__doc__ is not None:
            docs = cls.__doc__
            docs_lines = docs.splitlines()
            min_indent = 9999
            for i, line in enumerate(docs_lines):
                if line != '':
                    spaces = 0
                    while line and line[0] == ' ':
                        line = line[1:]
                        spaces += 1
                    if spaces < min_indent:
                        min_indent = spaces
            if min_indent == 9999:
                min_indent = 0

            for i, line in enumerate(docs_lines):
                if line != '':
                    if not line.startswith(' ' * min_indent):
                        raise Exception("expected opening whitespace: '" +
                                        line + "'; class " + str(cls))
                    docs_lines[i] = line[min_indent:]
            docs = '\n'.join(docs_lines)

        else:
            docs = '(no docs)'
            self._errors.append(f'base docs for class {cls}')
        return docs

    def _get_enum_values_for_class(self, cls: type) -> Optional[list[str]]:
        if issubclass(cls, Enum):
            return [val.name for val in cls]
        return None

    def _get_methods_for_class(
            self, cls: type) -> tuple[list[FunctionInfo], list[FunctionInfo]]:
        import types

        method_types = [
            types.MethodDescriptorType, types.FunctionType, types.MethodType
        ]
        methods_raw = [
            getattr(cls, name) for name in dir(cls)
            if any(isinstance(getattr(cls, name), t)
                   for t in method_types) and (
                       not name.startswith('_') or name == '__init__')
            and '_no_init' not in name
        ]

        methods: list[FunctionInfo] = []
        inherited_methods: list[FunctionInfo] = []
        for mth in methods_raw:

            # Protocols seem to give this...
            if mth.__name__ == '_no_init':
                continue

            # Keep a list of inherited methods but don't do a full
            # listing of them.
            if _is_inherited(cls, mth.__name__):
                dcls = _get_defining_class(cls, mth.__name__)
                assert dcls is not None
                inherited_methods.append(
                    FunctionInfo(name=mth.__name__,
                                 method_class=dcls.__module__ + '.' +
                                 dcls.__name__))
                continue

            # Use pydoc stuff for python methods since it includes args.

            # Its a c-defined method.
            if isinstance(mth, types.MethodDescriptorType):
                if mth.__doc__ is not None:
                    mdocs = mth.__doc__
                else:
                    mdocs = '(no docs)'
                    self._errors.append(mth)
                is_class_method = False

            # Its a python method.
            else:
                mdocs, is_class_method = self._python_method_docs(cls, mth)
            if '(internal)' not in mdocs:
                methods.append(
                    FunctionInfo(name=mth.__name__,
                                 docs=mdocs,
                                 is_class_method=is_class_method))
        return methods, inherited_methods

    def _python_method_docs(self, cls: type,
                            mth: Callable) -> tuple[str, bool]:
        import pydoc
        mdocs_lines = pydoc.plain(pydoc.render_doc(mth)).splitlines()[2:]

        # Remove ugly 'method of builtins.type instance'
        # on classmethods.
        mdocs_lines = [
            l.replace('method of builtins.type instance', '')
            for l in mdocs_lines
        ]

        # Pydoc indents all lines but the first 4 spaces;
        # undo that.
        for i, line in enumerate(mdocs_lines):
            if i != 0:
                if not line.startswith('    '):
                    raise Exception('UNEXPECTED')
                mdocs_lines[i] = line[4:]

        # Class-methods will show up as bound methods when we pull
        # them out of the type (with the type as the object).
        # Regular methods just show up as normal functions in
        # python 3 (no more unbound methods).
        is_class_method = inspect.ismethod(mth)

        # If this only gave us 1 line, it means there's no docs
        # (the one line is just the call signature).
        # In that case lets try parent classes to see if they
        # have docs.
        if len(mdocs_lines) == 1:
            mdocs_lines = self._handle_single_line_method_docs(
                cls, mdocs_lines, mth)

        # Add an empty line after the first.
        mdocs_lines = [mdocs_lines[0]] + [''] + mdocs_lines[1:]
        if len(mdocs_lines) == 2:
            # Special case: we allow dataclass types to have no __init__ docs
            # since they generate their own init (and their attributes tell
            # pretty much the whole story about them anyway).
            if (hasattr(cls, '__dataclass_fields__')
                    and mth.__name__ == '__init__'):
                pass
            else:
                self._errors.append((cls, mth))
        mdocs = '\n'.join(mdocs_lines)
        return mdocs, is_class_method

    def _handle_single_line_method_docs(self, cls: type,
                                        mdocs_lines: list[str],
                                        mth: Callable) -> list[str]:
        import pydoc
        for testclass in cls.mro()[1:]:
            testm = getattr(testclass, mth.__name__, None)
            if testm is not None:
                mdocs_lines_test = pydoc.plain(
                    pydoc.render_doc(testm)).splitlines()[2:]

                # Split before "unbound method" or "method".
                if 'unbound' in mdocs_lines_test[0]:
                    if len(mdocs_lines_test[0].split('unbound')) > 2:
                        raise Exception('multi-unbounds')
                    mdocs_lines_test[0] = \
                        mdocs_lines_test[0].split('unbound')[0]
                else:
                    if len(mdocs_lines_test[0].split('method')) > 2:
                        raise Exception('multi-methods')
                    mdocs_lines_test[0] = \
                        mdocs_lines_test[0].split('method')[0]

                # If this one has more info in it but its
                # first line (call signature) matches ours,
                # go ahead and use its docs in place of ours.
                if (len(mdocs_lines_test) > 1
                        and mdocs_lines_test[0] == mdocs_lines[0]):
                    mdocs_lines = mdocs_lines_test
        return mdocs_lines

    def _create_index(self) -> None:

        # Create an index of everything we can link to in classes and
        # functions.
        for cls in self._classes:
            key = cls.name
            if key in self._index:
                print('duplicate index entry:', key)
            self._index[key] = (_get_class_href(cls.name), cls)
            self._index_keys.append(key)

            # Add in methods.
            for mth in cls.methods:
                key = cls.name + '.' + mth.name
                if key in self._index:
                    print('duplicate index entry:', key)
                self._index[key] = (_get_method_href(cls.name, mth.name), mth)
                self._index_keys.append(key)

            # Add in attributes.
            for attr in cls.attributes:
                key = cls.name + '.' + attr.name
                if key in self._index:
                    print('duplicate index entry:', key)
                self._index[key] = (_get_attribute_href(cls.name,
                                                        attr.name), attr)
                self._index_keys.append(key)

        # Add in functions.
        for fnc in self._functions:
            key = fnc.name
            if key in self._index:
                print('duplicate index entry:', key)
            self._index[key] = (_get_function_href(fnc.name), fnc)
            self._index_keys.append(key)

        # Reverse this so when we replace things with links our longest
        # ones are searched first (such as nested classes like ba.Foo.Bar).
        self._index_keys.reverse()

    def _write_inherited_attrs(self, inherited_attrs: dict[str, str]) -> None:
        style = (' style="padding-left: 0px;"' if DO_STYLES else '')
        self._out += f'<h3{style}>Attributes Inherited:</h3>\n'
        style = (' style="padding-left: 30px;"' if DO_STYLES else '')
        self._out += f'<h5{style}>'
        inherited_attrs_sorted = list(inherited_attrs.items())
        inherited_attrs_sorted.sort(key=lambda x: x[0].lower())
        for i, attr in enumerate(inherited_attrs_sorted):
            if i != 0:
                self._out += ', '
            aname = attr[0]
            self._out += ('<a href="#' + attr[1] + '">' + aname + '</a>')
        self._out += '</h5>\n'

    def _write_attrs(self, cls: ClassInfo,
                     attributes: list[AttributeInfo]) -> None:
        # Include a block of links to our attrs if we have more
        # than one.
        if len(attributes) > 1:
            self._out += f'<h5{STYLE_PAD_L30}>'
            for i, attr in enumerate(attributes):
                if i != 0:
                    self._out += ', '
                aname = attr.name
                self._out += ('<a href="#' +
                              _get_attribute_href(cls.name, attr.name) + '">' +
                              aname + '</a>')
            self._out += '</h5>\n'

        self._out += '<dl>\n'
        for attr in attributes:
            cssclass = ' class="offsanchor"' if DO_CSS_CLASSES else ''
            self._out += (f'<dt><h4{STYLE_PAD_L30}>'
                          f'<a {cssclass}name="' +
                          _get_attribute_href(cls.name, attr.name) + '">' +
                          attr.name + '</a></h4></dt><dd>\n')

            # If we've got a type for the attr, spit that out.
            if attr.attr_type is not None:
                # Add links to any types we cover.
                typestr = self._add_index_links(attr.attr_type)
                style2 = (' style="color: #666677;"' if DO_STYLES else '')
                self._out += (f'<p{STYLE_PAD_L60}>'
                              f'<span{style2}>' + typestr + '</span></p>\n')
            else:
                self._errors.append(f"Attr '{attr.name}' on {cls.name} "
                                    'has no type annotation.')

            if attr.docs is not None:
                self._out += self._filter_docs(attr.docs, 'attribute')
            self._out += '</dd>\n'
        self._out += '</dl>\n'

    def _write_class_attrs_all(self, cls: ClassInfo,
                               attributes: list[AttributeInfo],
                               inherited_attrs: dict[str, str]) -> None:
        # If this class has no non-inherited attrs, just print a link to
        # the base class instead of repeating everything.
        # Nevermind for now; we never have many attrs so this isn't as
        # helpful as with methods.
        if bool(False):
            if cls.parents:
                self._out += f'<h3{STYLE_PAD_L0}>Attributes:</h3>\n'
                par = cls.parents[0]
                self._out += (f'<p{STYLE_PAD_L30}>&lt;'
                              'all attributes inherited from ' + '<a href="#' +
                              _get_class_href(par) + '">' + par + '</a>' +
                              '&gt;</p>\n')
        else:
            # Dump inherited attrs.
            if inherited_attrs:
                self._write_inherited_attrs(inherited_attrs)

            # Dump attributes.
            if attributes:
                if inherited_attrs:
                    self._out += (f'<h3{STYLE_PAD_L0}>'
                                  'Attributes Defined Here:</h3>\n')
                else:
                    self._out += f'<h3{STYLE_PAD_L0}>Attributes:</h3>\n'

                self._write_attrs(cls, attributes)

    def _write_enum_vals(self, cls: ClassInfo) -> None:
        if cls.enum_values is None:
            return
        self._out += f'<h3{STYLE_PAD_L0}>Values:</h3>\n'
        self._out += '<ul>\n'
        for val in cls.enum_values:
            self._out += '<li>' + val + '</li>\n'
        self._out += '</ul>\n'

    def _write_inherited_methods_for_class(self, cls: ClassInfo) -> None:
        """Dump inherited methods for a class."""
        if cls.inherited_methods:
            # If we inherit directly from a builtin class,
            # lets not print inherited methods at all since
            # we don't have docs for them.
            if (len(cls.parents) == 1
                    and cls.parents[0].startswith('builtins.')):
                pass
            else:
                self._out += f'<h3{STYLE_PAD_L0}>Methods Inherited:</h3>\n'
                self._out += f'<h5{STYLE_PAD_L30}>'
                for i, method in enumerate(cls.inherited_methods):
                    if i != 0:
                        self._out += ', '
                    mname = method.name + '()'
                    if mname == '__init__()':
                        mname = '&lt;constructor&gt;'
                    assert method.method_class is not None
                    self._out += (
                        '<a href="#' +
                        _get_method_href(method.method_class, method.name) +
                        '">' + mname + '</a>')
                self._out += '</h5>\n'

    def _write_methods_for_class(self, cls: ClassInfo,
                                 methods: list[FunctionInfo]) -> None:
        """Dump methods for a class."""
        if cls.methods:
            # Just say "methods" if we had no inherited ones.
            if cls.inherited_methods:
                self._out += (f'<h3{STYLE_PAD_L0}>'
                              'Methods Defined or Overridden:</h3>\n')
            else:
                self._out += f'<h3{STYLE_PAD_L0}>Methods:</h3>\n'

            # Include a block of links to our methods if we have more
            # than one.
            if len(methods) > 1:
                self._out += f'<h5{STYLE_PAD_L30}>'
                for i, method in enumerate(methods):
                    if i != 0:
                        self._out += ', '
                    mname = method.name + '()'
                    if mname == '__init__()':
                        mname = '&lt;constructor&gt;'
                    self._out += ('<a href="#' +
                                  _get_method_href(cls.name, method.name) +
                                  '">' + mname + '</a>')
                self._out += '</h5>\n'

            self._out += '<dl>\n'
            for mth in cls.methods:
                self._write_method(cls, mth)
            self._out += '</dl>\n'

    def _write_method(self, cls: ClassInfo, mth: FunctionInfo) -> None:
        name = mth.name + '()'
        ignore_links = []
        if name == '__init__()':
            ignore_links.append(cls.name)
            name = '&lt;constructor&gt;'

        # If we have a 3 part name such as
        # 'ba.Spaz.DeathMessage',
        # ignore the first 2 components ('ba.Spaz').
        dot_splits = cls.name.split('.')
        if len(dot_splits) == 3:
            ignore_links.append(dot_splits[0] + '.' + dot_splits[1])
        cssclass = ' class="offsanchor"' if DO_CSS_CLASSES else ''

        self._out += (f'<dt><h4{STYLE_PAD_L30}>'
                      f'<a{cssclass} name="' +
                      _get_method_href(cls.name, mth.name) + '">' + name +
                      '</a></dt></h4><dd>\n')
        if mth.docs is not None:
            mdocslines = mth.docs.splitlines()

            # Hmm should we be pulling from the class docs
            # as python suggests?..  hiding the suggestion to do so.
            mdocslines = [
                l for l in mdocslines
                if 'Initialize self.  See help(type(self))'
                ' for accurate signature' not in l
            ]

            # Kill any '-> None' on inits.
            if '__init__' in mdocslines[0]:
                mdocslines[0] = mdocslines[0].split(' -> ')[0]

            # Let's display '__init__(self, foo)' as 'Name(foo)'.
            mdocslines[0] = mdocslines[0].replace('__init__(self, ',
                                                  cls.name + '(')
            mdocslines[0] = mdocslines[0].replace('__init__(self)',
                                                  cls.name + '()')

            if mth.is_class_method:
                style2 = (' style="color: #CC6600;"' if DO_STYLES else '')
                self._out += (f'<h5{STYLE_PAD_L60}>'
                              f'<span{style2}>'
                              '<em>&lt;class method&gt;'
                              '</span></em></h5>\n')
            self._out += self._filter_docs('\n'.join(mdocslines),
                                           'method',
                                           ignore_links=ignore_links)
        self._out += '</dd>\n'

    def _get_type_display(self, name: str) -> str:
        """Given a string such as 'ba.ClassName', returns link/txt for it."""
        # Special-case; don't do links for built in classes.
        if name.startswith('builtins.'):
            shortname = name.replace('builtins.', '')

            # Show handy links for some builtin python types
            if shortname in {
                    'Exception', 'BaseException', 'RuntimeError', 'ValueError'
            }:
                return (f'<a href="https://docs.python.org/3/library'
                        f'/exceptions.html#{shortname}">{shortname}</a>')
        if name.startswith('ba.'):
            return ('<a href="#' + _get_class_href(name) + '">' + name +
                    '</a>')

        # Show handy links for various standard library types.
        if name in {'typing.Generic', 'typing.Protocol'}:
            return (f'<a href="https://docs.python.org/3/library'
                    f'/typing.html#{name}">{name}</a>')
        if name in {'enum.Enum'}:
            return (f'<a href="https://docs.python.org/3/library'
                    f'/enum.html#{name}">{name}</a>')

        return name

    def _write_class_inheritance(self, cls: ClassInfo) -> None:
        if cls.parents:
            self._out += f'<p{STYLE_PAD_L30}>Inherits from: '
            for i, par in enumerate(cls.parents):

                if i != 0:
                    self._out += ', '

                self._out += self._get_type_display(par)
        else:
            self._out += (f'<p{STYLE_PAD_L30}>'
                          '<em>&lt;top level class&gt;</em>\n')

    def _get_inherited_attrs(self, cls: ClassInfo,
                             attr_name_set: set[str]) -> dict[str, str]:
        inherited_attrs: dict[str, str] = {}
        for par in cls.parents:
            if par in self._index:
                parent_class = self._index[par][1]
                assert isinstance(parent_class, ClassInfo)
                for attr in parent_class.attributes:
                    if (attr.name not in attr_name_set
                            and attr.name not in inherited_attrs):
                        inherited_attrs[attr.name] = (_get_attribute_href(
                            parent_class.name, attr.name))
        self._out += '</p>\n'
        return inherited_attrs

    def _write_classes(self) -> None:
        # Now write out the docs for each class.
        for cls in self._classes:
            self._out += '<hr>\n'
            cssclass = ' class="offsanchor"' if DO_CSS_CLASSES else ''
            self._out += (f'<h2><strong><a{cssclass} name="' +
                          _get_class_href(cls.name) + '">' + cls.name +
                          '</a></strong></h3>\n')
            self._write_class_inheritance(cls)
            methods = cls.methods
            methods.sort(key=lambda x: x.name.lower())
            attributes = cls.attributes
            attributes.sort(key=lambda x: x.name.lower())

            attr_name_set = set()
            for attr in attributes:
                attr_name_set.add(attr.name)

            # Go through parent classes' attributes, including any
            # that aren't in our set in the 'inherited attributes' list.

            inherited_attrs = self._get_inherited_attrs(cls, attr_name_set)

            if cls.docs is not None:
                self._out += self._filter_docs(cls.docs, 'class')

            self._write_class_attrs_all(cls, attributes, inherited_attrs)

            self._write_enum_vals(cls)

            # If this class has no non-inherited methods, just print a link to
            # the base class instead of repeating everything.
            if cls.inherited_methods and not cls.methods:
                if cls.parents:
                    self._out += f'<h3{STYLE_PAD_L0}>Methods:</h3>\n'
                    par = cls.parents[0]
                    self._out += (f'<p{STYLE_PAD_L30}>&lt;'
                                  'all methods inherited from ' +
                                  self._get_type_display(par) + '&gt;</p>\n')
            else:
                self._write_inherited_methods_for_class(cls)
                self._write_methods_for_class(cls, methods)

    def _gather_funcs(self, module: ModuleType) -> None:
        import types
        import pydoc

        # Function, build-in-function.
        func_types = [types.FunctionType, types.BuiltinMethodType]

        names = dir(module)
        funcs = [
            getattr(module, name) for name in names if not name.startswith('_')
        ]
        funcs = [f for f in funcs if any(isinstance(f, t) for t in func_types)]

        for fnc in funcs:

            # For non-builtin funcs, use the pydoc rendering since it includes
            # args.
            # Chop off the first line which is just "Python Library
            # Documentation: and the second which is blank.
            docs = None
            if isinstance(fnc, types.FunctionType):
                docslines = pydoc.plain(pydoc.render_doc(fnc)).splitlines()[2:]

                # Pydoc indents all lines but the first 4 spaces; undo that.
                for i, line in enumerate(docslines):
                    if i != 0:
                        if not line.startswith('    '):
                            raise Exception('UNEXPECTED')
                        docslines[i] = line[4:]

                # Add an empty line after the first.
                docslines = [docslines[0]] + [''] + docslines[1:]

                if len(docslines) == 2:
                    docslines.append('(no docs)')
                    self._errors.append(fnc)
                docs = '\n'.join(docslines)
            else:
                if fnc.__doc__ is not None:
                    docs = fnc.__doc__
                else:
                    fnc.__doc__ = '(no docs)'
                    self._errors.append(fnc)
            assert docs is not None

            f_info = FunctionInfo(name=fnc.__module__ + '.' + fnc.__name__,
                                  category=_get_category(
                                      docs, CategoryType.FUNCTION),
                                  docs=docs)
            if '(internal)' not in docs:
                self._functions.append(f_info)

    def _process_classes(self, module: ModuleType) -> None:
        classes_by_name = _get_module_classes(module)
        for c_name, cls in classes_by_name:
            docs = self._get_base_docs_for_class(cls)
            bases = _get_bases(cls)
            methods, inherited_methods = self._get_methods_for_class(cls)
            enum_values = self._get_enum_values_for_class(cls)
            docs, attrs = self._get_all_attrs_for_class(cls, docs)

            c_info = ClassInfo(name=c_name,
                               parents=bases,
                               docs=docs,
                               enum_values=enum_values,
                               methods=methods,
                               inherited_methods=inherited_methods,
                               category=_get_category(docs,
                                                      CategoryType.CLASS),
                               attributes=attrs)
            self._classes.append(c_info)

    def _write_category_list(self) -> None:
        for cname, ctype, cmembers in self._merged_categories:
            if ctype == 'class':
                assert (isinstance(i, ClassInfo) for i in cmembers)
                cssclass = ' class="offsanchor"' if DO_CSS_CLASSES else ''
                self._out += (f'<h4><a{cssclass} name="' +
                              _get_class_category_href(cname) + '">' + cname +
                              '</a></h4>\n')
                classes_sorted = cast(list[ClassInfo], cmembers)
                classes_sorted.sort(key=lambda x: x.name.lower())
                pcc = _print_child_classes(classes_sorted, '', 0)
                self._out += pcc
            elif ctype == 'function':
                assert (isinstance(i, FunctionInfo) for i in cmembers)
                cssclass = ' class="offsanchor"' if DO_CSS_CLASSES else ''
                self._out += (f'<h4><a{cssclass} name="' +
                              _get_function_category_href(cname) + '">' +
                              cname + '</a></h4>\n'
                              '<ul>\n')
                funcs = cast(list[FunctionInfo], cmembers)
                funcs.sort(key=lambda x: x.name.lower())
                for fnc in funcs:
                    self._out += ('   <li><a href="#' +
                                  _get_function_href(fnc.name) + '">' +
                                  fnc.name + '()</a></li>\n')
                self._out += '</ul>\n'
            else:
                raise Exception('invalid ctype')

    def _filter_docs(self,
                     docs: str,
                     filter_type: str,
                     ignore_links: list[str] = None) -> str:
        get_category_href_func, indent = _filter_type_settings(filter_type)
        docs = docs.replace('>', '&gt;')
        docs = docs.replace('<', '&lt;')

        docs_lines = docs.splitlines()

        # Make sure empty lines are actually empty (so we can search for
        # '\n\n' and not get thrown off by something like '\n   \n').
        for i, line in enumerate(docs_lines):
            if line.strip() == '':
                docs_lines[i] = ''

        # If a line starts with 'Category:', make it a link to that category.
        for i, line in enumerate(docs_lines):
            if line.lower().strip().startswith(CATEGORY_STRING.lower()):
                if get_category_href_func is None:
                    raise Exception('cant do category for filter_type ' +
                                    filter_type)
                cat = line.strip()[len(CATEGORY_STRING):].strip()
                docs_lines[i] = (CATEGORY_STRING + ' <a href="#' +
                                 get_category_href_func(cat) + '">' + cat +
                                 '</a>')
        docs = '\n'.join(docs_lines)
        docs = _split_into_paragraphs(docs, filter_type, indent)
        docs = self._add_index_links(docs, ignore_links)
        return docs

    def run(self, outfilename: str) -> None:
        """Generate docs from within the game."""
        import ba

        self._gather_funcs(ba)
        self._process_classes(ba)

        # Start with our list of classes and functions.
        app = ba.app
        self._out += ('<h4><em>last updated on ' + str(datetime.date.today()) +
                      ' for Ballistica version ' + app.version + ' build ' +
                      str(app.build_number) + '</em></h4>\n')
        self._out += (
            '<p>This page documents the Python classes'
            ' and functions in the \'ba\' module,\n'
            ' which are the ones most relevant to modding in Ballistica.'
            ' If you come across something you feel'
            ' should be included here or could'
            ' be better explained, please '
            '<a href="mailto:support@froemling.net">'
            'let me know</a>. Happy modding!</p>\n')
        self._out += '<hr>\n'
        self._out += '<h2>Table of Contents</h2>\n'

        self._create_index()

        # Build a sorted list of class categories.
        c_categories: dict[str, list[Union[ClassInfo, FunctionInfo]]] = {}
        self._classes.sort(key=lambda x: x.name.lower())
        for cls in self._classes:
            assert cls.category is not None
            category = cls.category
            if category not in c_categories:
                c_categories[category] = []
            c_categories[category].append(cls)

        self._merged_categories = [(cname, 'class', cval)
                                   for cname, cval in c_categories.items()]

        # Build sorted function category list.
        f_categories: dict[str, list[FunctionInfo]] = {}
        for fnc in self._functions:
            if fnc.category is not None:
                category = fnc.category
            else:
                category = 'Misc'
            if category not in f_categories:
                f_categories[category] = []
            f_categories[category].append(fnc)

        self._merged_categories += [(cname, 'function',
                                     cast(list[Union[ClassInfo, FunctionInfo]],
                                          cval))
                                    for cname, cval in f_categories.items()]

        def sort_func(entry: tuple[str, str, Any]) -> str:
            name = entry[0].lower()

            # Sort a few recognized categories somewhat manually.
            overrides = {
                'gameplay classes': 'aaaa',
                'gameplay functions': 'aaab',
                'general utility classes': 'aaac',
                'general utility functions': 'aaad',
                'asset classes': 'aaae',
                'asset functions': 'aaaf',
                'message classes': 'aaag',
                'app classes': 'aaah',
                'app functions': 'aaai',
                'user interface classes': 'aaaj',
                'user interface functions': 'aaak',
            }
            return overrides.get(name, name)

        self._merged_categories.sort(key=sort_func)

        # Write out our category listings.
        self._write_category_list()
        self._write_classes()

        # Now write docs for each function.
        for fnc in self._functions:
            self._out += '<hr>\n'
            cssclass = ' class="offsanchor"' if DO_CSS_CLASSES else ''
            self._out += (f'<h2><strong><a{cssclass} name="' +
                          _get_function_href(fnc.name) + '">' + fnc.name +
                          '()</a></strong></h3>\n')
            if fnc.docs is not None:
                self._out += self._filter_docs(fnc.docs, 'function')

        # If we've hit any errors along the way, complain.
        if self._errors:
            max_displayed = 10
            print(
                len(self._errors), 'ISSUES FOUND GENERATING DOCS:\n' +
                '\n'.join(self._errors[:max_displayed]))
            clipped = max(0, len(self._errors) - max_displayed)
            if clipped:
                print(f'(and {clipped} more)')
            raise Exception(
                str(len(self._errors)) + ' docs generation issues.')

        with open(outfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(self._out)

        print(f"Generated docs file: '{Clr.BLU}{outfilename}.{Clr.RST}'")

        ba.quit()


def generate(projroot: str) -> None:
    """Main entry point."""
    toolsdir = os.path.abspath(os.path.join(projroot, 'tools'))

    # Make sure we're running from the dir above this script.
    os.chdir(projroot)

    outfilename = os.path.abspath('build/docs.html')

    # Let's build the cmake version; no sandboxing issues to contend
    # with there. Also going with the headless build; will need to revisit
    # if there's ever any functionality not available in that build.
    subprocess.run(['make', 'cmake-server-build'], check=True)

    # Launch ballisticacore and exec ourself from within it.
    print('Launching ballisticacore to generate docs...')

    try:
        subprocess.run(
            [
                './ballisticacore',
                '-exec',
                f'try:\n'
                f'    import sys\n'
                f'    import ba\n'
                f'    sys.path.append("{toolsdir}")\n'
                f'    import batools.docs\n'
                f'    batools.docs.Generator().run("{outfilename}")\n'
                f'    ba.quit()\n'
                f'except Exception:\n'
                f'    import sys\n'
                f'    import traceback\n'
                f'    print("ERROR GENERATING DOCS")\n'
                f'    traceback.print_exc()\n'
                f'    sys.exit(255)\n',
            ],
            cwd='build/cmake/server-debug/dist',
            check=True,
        )
    except Exception as exc2:
        # Keep our error simple here; we want focus to be on what went
        # wrong withing BallisticaCore.
        raise CleanError('BallisticaCore docs generation failed.') from exc2

    print('Docs generation complete.')
