""" Code builder class to build lines of code. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2019"
__license__ = "Apache License 2.0"

__all__ = ["CodeBuilder"]


from contextlib import contextmanager
import types
from typing import Any, Optional, Sequence, Union, Generator


class CodeBuilder:
    """ Code building class.

    This class provides methods to build code, and also helps to manage variable
    names and nested sections of code.  Nested sections increase the variable
    name depth by adding an "s<num> item, where each new nested section becomes
    a new part: v1 = first variable at top, s1v1, variable in first section at
    top, s2s1v1 - first variable in first section under the second section from
    the top.  Note that variables used by this begin with "s" and "v" so other
    variables should start differently.
    """

    def __init__(self, _var_prefix=""):
        """ Initialize the code builder. """

        self._var_prefix = _var_prefix
        self._var_index = 0
        self._var_index_stack = []
        self._section_index = 0
        self._lines = []
        self._sections = {}
        self._flags = {}

    def indent(self):
        """ Increase indentation. """
        self._lines.append(1)

    def dedent(self):
        """ Decrease indentation. """
        self._lines.append(-1)

    @contextmanager
    def indenter(self):
        """ Increase indent in a with context. """
        try:
            self.indent()
            yield
        finally:
            self.dedent()

    def save(self):
        """ Save the current variable index. """
        self._var_index_stack.append(self._var_index)

    def restore(self):
        """ Restore the variable index. """
        self._var_index = self._var_index_stack.pop()

    @contextmanager
    def saver(self):
        """ Save variable index within a with context. """
        try:
            self.save()
            yield
        finally:
            self.restore()

    @property
    def nextvar(self) -> str:
        """ Retrieve the next variable.

        Returns
        -------
        str
            The next variable to use

        """
        self._var_index += 1
        return "{}v{}".format(self._var_prefix, self._var_index)

    def set_flag(self, name: str, value: Any = True):
        """ Set a flag.

        Parameters
        ----------
        name : str
            The name of a flag to set.
        value : Any, default=True
            The value of the flag
        """
        self._flags[name] = value

    def get_flag(self, name: str, default: Optional[Any] = None) -> Any:
        """ Get a flag.

        Parameters
        ----------
        name : str
            The name of the flag
        default : Optional[Any]
            The value if the flag is not set

        Returns
        -------
        Any
            The value of the flag if set, otherwise the default value or None
        """
        return self._flags.get(name, default)

    def clear_flag(self, name: str):
        """ Clear a flag.

        Parameters
        ----------
        name : str
            The name of the flag
        """
        self._flags.pop(name, None)

    def add(
            self,
            content: Union[
                str,
                'CodeBuilder',
                int,
                Sequence[Union[
                    str,
                    'CodeBuilder',
                    int
                ]]
            ]
        ):

        """ Add content to the builder.

        Parmaeters
        ----------
        content : str
            Insert the given line
        content : CodeBuilder
            Insert a nested section at the current location
        content : int
            Increase or decrease the indentation level
        content : tuple/list/generator
            Add all items from the tuple or list.  Expected types are the
            same as above.  Nested tuples and lists are not supported.
        """
        if isinstance(content, (str, int, CodeBuilder)):
            self._lines.append(content)
        elif isinstance(content, (tuple, list, types.GeneratorType)):
            self._lines.extend(content)

    def create_section(
            self,
            name: Optional[str] = None,
            reset: bool = False
        ):
        """ Create a section but don't add it.

        This allows for a section that can be reused over and over by
        adding it at multiple places.

        Parameters
        ----------
        name : Optional[str], default=None
            The name to give the section.  If specified, the section will
            be added the the list of named sections.

        reset : bool, default=False
            Whether to reset the variable prefix.  This can be used  in
            sections that contain a function so as the function's variables
            don't contain a mess of prefixes if not needed

        Returns
        -------
        CodeBuilder
            The created section
        """
        if reset:
            var_prefix = ""
        else:
            self._section_index += 1
            var_prefix = "{}s{}".format(self._var_prefix, self._section_index)

        section = CodeBuilder(var_prefix)

        if name is not None:
            self._sections[name] = section

        return section

    def add_section(
            self,
            name: Optional[str] = None,
            reset: bool = False
        ):
        """ Create a section and add it to the lines

        Parameters
        ----------
        name : Optional[str], default=None
            The name to give the section
        reset : bool, default=None
            Whether to reset the variable prefix.

        Returns
        -------
        CodeBuilder
            The added section
        """
        section = self.create_section(name, reset)
        self._lines.append(section)
        return section

    def get_section(self, name: str) -> Optional['CodeBuilder']:
        """ Get a section.

        This will also get nested sections separated by the period.

        Parameters
        ----------
        name : str
            The name of the sectoin to get.

        Returns
        -------
        CodeBuilder
            If the named section was found
        None
            If the section was not found
        """
        parts = name.split(".", 1)
        section = self._sections.get(parts[0])
        if section is not None:
            if len(parts) == 1:
                return section

            return section.get_section(parts[1])

        return None

    def insert_section(self, section: Union[str, 'CodeBuilder']):
        """ Insert a reference to a section in the current section.  If the
        section does not exist, this does nothing.

        Parameters
        ----------
        section : str
            The name of the section to insert
        section : CodeBuilder
            The section to insert
        """

        if isinstance(section, str):
            section = self.get_section(section)

        if section is not None:
            self.add(section)

    def expand_section(self, section: Union[str, 'CodeBuilder']):
        """ Expand the contents of an existing section into the current section.
        If the section does not exist, this does nothing.

        Parameters
        ----------
        section : str
            The name or section to expand.
        section : 'CodeBuilder'
            The section to expand.
        """

        if isinstance(section, str):
            section = self.get_section(section)

        if section is not None:
            self.add(section.flatten())

    def flatten(self, _visited=None) -> Generator[Union[str, int], None, None]:
        """ Flatten the results into a list of strings and integers.

        This is a generator that will yield a flat list of each section's items.
        This method does not handle indents, so the result will still contain
        both the strings of the lines as well as the indent markers.

        Yields
        ------
        str
            A line of code
        int
            A value to increase or decrease the indent level by.
        """

        # First make sure we havent been visited yet to avoid recursive sections
        # This is possibly since insert_section may insert a section from one
        # place into another place
        if _visited is None:
            _visited = []
        elif self in _visited:
            raise RuntimeError("CodeBuilder section nested recursively.")

        try:
            _visited.append(self)

            for line in self._lines:
                if isinstance(line, (int, str)):
                    yield line
                elif isinstance(line, CodeBuilder):
                    yield from line.flatten(_visited)
        finally:
            _visited.pop()

    def render(self, indent: str = "    ") -> str:
        """ Render the lines into a block of text.

        Parameters
        ----------
        indent : str, default="    "
            The text to use for indenting.

        Returns
        -------
        str
            The rendered code.
        """

        level = 0
        lines = []
        for line in self.flatten():
            if isinstance(line, int):
                level += line
            elif isinstance(line, str):
                lines.append("{}{}".format(level * indent, line))

        return "\n".join(lines)

    def __str__(self):
        """ Get the code as a string. """
        return self.render()
