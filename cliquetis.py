#!/usr/bin/env python3
"""
Cliquetis provides a graphical user interface for command line tools.

It is written in Python 3 and uses only standard libraries.
"""

from sys import argv
from pathlib import Path
from json import loads
from tkinter import RIGHT, BooleanVar, Tk, Text, StringVar
from tkinter import N, S, E, W, END, TOP, X, VERTICAL, BOTH
from tkinter import ttk, filedialog
from subprocess import run


class Cliquetis:
    """A class to store constants and utility functions for Cliquetis."""

    """The gap between widgets."""
    WIDGET_GAP = 5

    """The TkInter theme used by the application."""
    TK_THEME = "clam"

    """The type of a column containing numbers."""
    NUMBER = 0

    """The type of a column containing strings."""
    STRING = 1

    """The average width of a character in a monospaced font."""
    AVERAGE_CHAR_WIDTH = 10

    """The default wrap length for text."""
    DEFAULT_WRAPLENGTH = 600

    """The user's home directory."""
    HOME_DIRECTORY = Path.home()


    def default(dictionary, key, default_value=None):
        """Return the value of a key in a dictionary or a default value."""
        return dictionary[key] if key in dictionary else default_value


    def get_value(value):
        """Return the value of a TkInter variable."""
        try:
            return value.get_null()
        except AttributeError:
            return value.get()


class NullBooleanVar(BooleanVar):
    """A BooleanVar that may return a None value when the value is false.
    
    This is useful because TkInter is not able to handle None values.
    """
    def __init__(self, value=False, onvalue=True, offvalue=False):
        """Create a new NullBooleanVar with a default value.
        
        Args:
            value: The default value of the variable.
            onvalue: The value returned by the get_null method when the variable
            is true.
            offvalue: The value returned by the get_null method when the
            variable is false.
        """
        super().__init__()
        self.onvalue = onvalue
        self.offvalue = offvalue
        self.set(value)

    def set(self, value):
        super().set(value)

    def get_null(self):
        """Return the corresponding value of the variable."""
        return (self.onvalue if self.get() else self.offvalue)


class TabularData:
    """A class to store and manipulate tabular data."""

    def __init__(self):
        self.headings = []
        self.data = []
        self.width = 0
        self.column_types = []
        self.maximum_lengths = []

    def has_tree(self):
        """Return True if the data is a tree stored in a dictionary, False
        otherwise.
        """
        return isinstance(self.data, dict)

    def insertable_items(self):
        """Yield the items that can be inserted in a tree."""
        if isinstance(self.data, dict):
            for group in self.data:
                yield ('', group)
                for row in self.data[group]:
                    yield (group, row)
        else:
            for row in self.data:
                yield ('', row)

    def import_data(self, data):
        """Import data from a list of lists.
        
        The first list is the headings and the other lists are the rows.
        """
        if len(data) < 2:
            return

        self.headings = data[0]
        self.data = data[1:]
        self.width = len(self.headings)
        self.column_types = self._find_column_types()
        self.maximum_lengths = self._find_maximum_length()

        return self

    def import_raw_data(self, text, separator="\t", group_by=None):
        """Import data from a raw text."""
        self.import_data([
            row.split(separator)
            for row in text.decode('utf-8').splitlines()
        ])

        if group_by is not None:
            self.group_by(group_by)

        return self

    def group_by(self, column):
        """Group the data by a column."""
        groups = {}
        for row in self.data:
            group_name = row[column]
            del row[column]
            if group_name in groups:
                groups[group_name].append(row)
            else:
                groups[group_name] = [row]

        del self.headings[column]
        self.data = groups
        del self.maximum_lengths[column]
        del self.column_types[column]

        return self

    def _find_maximum_length(self):
        """Find the maximum length of each column."""
        maximum = [len(value) for value in self.headings]
        for row in self.data:
            for column, value in enumerate(row):
                if len(value) > maximum[column]:
                    maximum[column] = len(value)

        return maximum

    def _find_column_types(self):
        """Find the type of each column."""
        types = [Cliquetis.NUMBER] * self.width
        all_string = [Cliquetis.STRING] * self.width

        for row in self.data:
            if types == all_string:
                break

            for column, value in enumerate(row):
                if types[column] == Cliquetis.STRING or value.strip() == '':
                    continue

                try:
                    _ = float(value)
                    types[column] = Cliquetis.NUMBER
                except ValueError:
                    types[column] = Cliquetis.STRING

        return types


class Action:
    """A class to store and run an action."""

    def __init__(self, arguments, values, configuration):
        self.arguments = arguments
        self.values = values
        self.configuration = configuration

    def expand(self, argument):
        """Expand the argument with the values."""
        for value_name in self.values:
            token = f"{{{value_name}}}"

            if argument == token:
                return self.values[value_name]

        for value_name in self.values:
            token = f"{{{value_name}}}"

            value = self.values[value_name]

            if value is None:
                value = ''

            argument = argument.replace(token, value)

        return argument

    def run(self):
        """Run the action and return the result."""
        expanded = [
            expanded_value
            for expanded_value in map(self.expand, self.arguments)
            if expanded_value is not None
        ]

        output = run(expanded, capture_output=True)

        if self.configuration['viewer'] == 'table':
            separator = (
                self.configuration['separator']
                if 'separator' in self.configuration else "\t"
            )

            group_by = (
                self.configuration['group-by']
                if 'group-by' in self.configuration else None
            )

            return TabularData().import_raw_data(
                output.stdout,
                separator,
                group_by
            )
        elif self.configuration['viewer'] == 'json':
            return loads(output.stdout)
        else:
            return output.stdout


class Application(ttk.Frame):
    """The main GUI."""

    def __init__(self, parent, configuration):
        super().__init__(parent)

        self.parent = parent
        self.configuration = configuration
        self.action = None

        self.create_widgets()

    def select_file(self, entry):
        """Open a file dialog and insert the selected file in an entry."""
        filetypes = (
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        filename = filedialog.askopenfilename(
            title='Open a file',
            initialdir=Cliquetis.HOME_DIRECTORY,
            filetypes=filetypes
        )

        if filename:
            entry.delete(0, 'end')
            entry.insert(0, filename)

    def create_widget_text(self, parent, option_index, option):
        option_label = ttk.Label(parent, text=option['name'])
        option_label.grid(column=0, row=option_index, sticky=(N, S, E, W))

        option_entry = ttk.Entry(parent)
        option_entry.grid(column=1, row=option_index, sticky=(N, E, W))

        return option_entry

    def create_widget_file(self, parent, option_index, option):
        variable = StringVar()
        variable.set(option['default'] if 'default' in option else '')

        option_label = ttk.Label(parent, text=option['name'])
        option_label.grid(column=0, row=option_index, sticky=(N, S, E, W))

        option_entry = ttk.Entry(parent)
        option_entry.grid(column=1, row=option_index, sticky=(N, S, E, W))

        browse_button = ttk.Button(
            parent,
            text="Select file",
            command=(lambda: self.select_file(option_entry))
        )

        browse_button.grid(column=2, row=option_index, sticky=(N, S, E, W))

        return option_entry

    def create_widget_list(self, parent, option_index, option):
        option_label = ttk.Label(parent, text=option['name'])
        option_label.grid(column=0, row=option_index, sticky=(N, S, E, W))

        if 'values' in option:
            option_combobox = ttk.Combobox(
                parent,
                values=option['values'],
                state='readonly'
            )
        elif 'source' in option:
            resultat = run(
                option['source'],
                shell=True,
                capture_output=True,
                text=True
            )

            option_combobox = ttk.Combobox(
                parent,
                values=resultat.stdout.splitlines(),
                state='readonly'
            )
        else:
            option_combobox = ttk.Combobox(parent, values=[])

        option_combobox.grid(
            column=1,
            columnspan=2,
            row=option_index,
            sticky=(N, S, E, W)
        )

        return option_combobox

    def create_widget_boolean(self, parent, option_index, option):
        variable = NullBooleanVar(
            onvalue=option['true'],
            offvalue=option['false']
        )

        variable.set(option["default"])

        check = ttk.Checkbutton(
            parent,
            text=option['name'],
            variable=variable,
            onvalue=True,
            offvalue=False
        )

        check.grid(column=1, row=option_index, sticky=W, columnspan=2)

        return variable

    def create_header(self, description):
        header = ttk.Label(
            self,
            text=description,
            background='white',
            wraplength=Cliquetis.DEFAULT_WRAPLENGTH,
            padding=Cliquetis.AVERAGE_CHAR_WIDTH
        )

        header.pack(side=TOP, fill=X)

    def create_buttons(self, name, option_index):
        button_frame = ttk.Frame(self)
        button_frame.pack(
            side=RIGHT,
            anchor=E,
            pady=Cliquetis.WIDGET_GAP*2,
            padx=Cliquetis.WIDGET_GAP*2
        )

        action_button = ttk.Button(
            button_frame,
            text=name,
            command=self.create_action
        )

        action_button.grid(column=1, row=0, sticky=E)
        self.bind('<Return>', action_button.invoke)

        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        )
        cancel_button.grid(column=2, row=0, sticky=E)

    def create_widgets(self):
        self.pack(expand=True, fill=BOTH)

        ttk.Style().theme_use(Cliquetis.TK_THEME)

        self.create_header(self.configuration['description'])

        frame_config = ttk.Frame(self)
        frame_config.pack(
            expand=True,
            fill=BOTH,
            padx=Cliquetis.WIDGET_GAP*2,
            pady=Cliquetis.WIDGET_GAP*2
        )

        frame_config.grid_columnconfigure(0, pad=Cliquetis.WIDGET_GAP)
        frame_config.grid_columnconfigure(
            1, weight=1, pad=Cliquetis.WIDGET_GAP)
        frame_config.grid_columnconfigure(2, pad=Cliquetis.WIDGET_GAP)

        for action in self.configuration['actions']:
            option_index = 0
            for key in action['options']:
                option = action['options'][key]

                create_widget_method = getattr(
                    self,
                    "create_widget_" + option['type']
                )

                option['widget'] = create_widget_method(
                    frame_config,
                    option_index,
                    option
                )

                option_index += 1
                self.grid_rowconfigure(option_index, pad=Cliquetis.WIDGET_GAP)

            self.create_buttons(action['name'], option_index)

    def cancel(self):
        self.parent.destroy()

    def create_action(self):
        action_config = self.configuration['actions'][0]
        self.action = Action(
            action_config['command'],
            {key: Cliquetis.get_value(action_config['options'][key]['widget'])
             for key in action_config['options']
             },
            action_config['output']
        )

        self.parent.destroy()


class MultilineViewer(ttk.Frame):
    def __init__(self, parent, text):
        super().__init__(parent)

        self.parent = parent
        self.text = text

        self.create_widgets()

    def create_widgets(self):
        ttk.Style().theme_use(Cliquetis.TK_THEME)

        self.pack(
            expand=True,
            fill=BOTH,
            padx=Cliquetis.WIDGET_GAP*2,
            pady=Cliquetis.WIDGET_GAP*2
        )

        text_frame = ttk.Frame(self)
        text_frame.pack(expand=True, fill=BOTH)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        text_widget = Text(text_frame)
        text_widget.insert('1.0', self.text)
        text_widget.grid(column=0, row=0, sticky=(N, S, E, W))

        text_scrollbar = ttk.Scrollbar(
            text_frame,
            orient=VERTICAL,
            command=text_widget.yview
        )
        text_widget.configure(yscroll=text_scrollbar.set)
        text_scrollbar.grid(column=1, row=0, sticky=(N, S))

        close_button = ttk.Button(
            self,
            text="Close",
            command=self.parent.destroy
        )
        close_button.pack(
            side='right',
            anchor=E,
            pady=(Cliquetis.WIDGET_GAP*2, 0)
        )


class TableViewer(ttk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)

        self.parent = parent
        self.data = data

        self.create_widgets()

    def insert_data(self, table):
        """Insert the data in the table."""
        for column, name in enumerate(self.data.headings):
            table.heading(name, text=name)

            column_type = self.data.column_types[column]
            column_length = self.data.maximum_lengths[column]

            table.column(
                name,
                width=column_length * Cliquetis.AVERAGE_CHAR_WIDTH,
                anchor=E if column_type == Cliquetis.NUMBER else W
            )

        for (parent, row) in self.data.insertable_items():
            if parent == '' and isinstance(row, str):
                table.insert('', END, iid=row, text=row)
            else:
                table.insert(parent, END, values=row)

    def create_widgets(self):
        """Create the widgets."""
        ttk.Style().theme_use(Cliquetis.TK_THEME)

        self.pack(
            expand=True,
            fill=BOTH,
            padx=Cliquetis.WIDGET_GAP*2,
            pady=Cliquetis.WIDGET_GAP*2
        )

        table_frame = ttk.Frame(self)
        table_frame.pack(expand=True, fill=BOTH)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        table_widget = ttk.Treeview(
            table_frame,
            columns=self.data.headings,
            show='tree headings' if self.data.has_tree() else 'headings'
        )
        table_widget.grid(column=0, row=0, sticky=(N, S, E, W))
        self.insert_data(table_widget)

        table_scrollbar = ttk.Scrollbar(
            table_frame,
            orient=VERTICAL,
            command=table_widget.yview
        )
        table_widget.configure(yscroll=table_scrollbar.set)
        table_scrollbar.grid(column=1, row=0, sticky=(N, S))

        close_button = ttk.Button(
            self,
            text="Close",
            command=self.parent.destroy
        )
        close_button.pack(
            side=RIGHT,
            anchor=E,
            pady=(Cliquetis.WIDGET_GAP*2, 0)
        )


class TreeViewer(ttk.Frame):
    def __init__(self, parent, data, collapsed=True, key_values=None):
        super().__init__(parent)

        self.parent = parent
        self.data = data
        self.collapsed = collapsed
        self.key_values = key_values

        self.create_widgets()

    def has_key_values(self, data):
        if isinstance(data, dict) and self.key_values is not None:
            return all(key in data for key in self.key_values)

        return False

    def display_data(self, data, tree, parent=''):
        if self.has_key_values(data):
            field_key = self.key_values[0]
            field_values = self.key_values[1:]
            field_key_exists = field_key in data
            field_values_exist = all(
                [field_value in data for field_value in field_values]
            )
            if field_key_exists and field_values_exist:
                tree.insert(
                    parent,
                    END,
                    text=data[field_key],
                    values=[data[field_value] for field_value in field_values]
                )
                return

        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], dict) or isinstance(data[key], list):
                    item = tree.insert(
                        parent,
                        END,
                        text=key,
                        values=[f'{len(data[key])} item(s)'],
                        open=not self.collapsed
                    )
                    self.display_data(data[key], tree, item)
                else:
                    item = tree.insert(
                        parent,
                        END,
                        text=key,
                        values=[data[key]]
                    )
            return

        if isinstance(data, list):
            for index, row in enumerate(data):
                if self.has_key_values(row):
                    self.display_data(row, tree, parent)
                elif isinstance(row, dict) or isinstance(row, list):
                    item = tree.insert(
                        parent,
                        END,
                        text=index,
                        open=not self.collapsed
                    )

                    self.display_data(row, tree, item)
                else:
                    tree.insert(parent, END, text=index, values=[row])

            return

        tree.insert(parent, END, values=[data])

    def create_widgets(self):
        ttk.Style().theme_use(Cliquetis.TK_THEME)

        self.pack(
            expand=True,
            fill=BOTH,
            padx=Cliquetis.WIDGET_GAP*2,
            pady=Cliquetis.WIDGET_GAP*2
        )

        tree_frame = ttk.Frame(self)
        tree_frame.pack(expand=True, fill=BOTH)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        if self.key_values is not None:
            columns = self.key_values[1:]
            column_tree = self.key_values[0]
        else:
            columns = ['value']
            column_tree = 'tree'

        tree_widget = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='tree headings'
        )

        tree_widget.heading('#0', text=column_tree)
        for name in columns:
            tree_widget.heading(name, text=name)

        tree_widget.grid(column=0, row=0, sticky=(N, S, E, W))

        self.display_data(self.data, tree_widget)

        tree_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient=VERTICAL,
            command=tree_widget.yview
        )
        tree_widget.configure(yscroll=tree_scrollbar.set)
        tree_scrollbar.grid(column=1, row=0, sticky=(N, S))

        close_button = ttk.Button(
            self,
            text="Close",
            command=self.parent.destroy
        )

        close_button.pack(
            side='right',
            anchor=E,
            pady=(Cliquetis.WIDGET_GAP*2, 0)
        )


def main(script):
    stream = b"\n".join([
        line
        for line in open(script, 'rb')
        if not line.startswith(b'#')
    ])

    configuration = loads(stream)

    root = Tk()
    root.title(configuration['title'])
    application = Application(root, configuration)
    application.mainloop()

    if application.action:
        result = application.action.run()
        root = Tk()
        root.title("Result")

        output_config = configuration['actions'][0]['output']
        viewer_type = Cliquetis.default(output_config, 'viewer', 'multiline')
        if viewer_type == 'table':
            viewer = TableViewer(root, result)
        elif viewer_type == 'json':
            viewer = TreeViewer(
                root,
                result,
                collapsed=Cliquetis.default(output_config, 'collapsed', False),
                key_values=Cliquetis.default(output_config, 'key-values', None)
            )
        else:
            viewer = MultilineViewer(root, result)

        viewer.mainloop()

    exit(0)


if __name__ == '__main__':
    if len(argv) != 2:
        exit(1)

    main(argv[1])
