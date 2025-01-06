Cliquetis
=========

Cliquetis is a lightweight graphical interface for controlling command-line
tools.

Written in Python 3, it uses only standard libraries, ensuring compatibility and
ease of installation.

It allows to give a simple graphical interface to CLI tools without rewriting
them or programming an interface.

Features
--------

-  **Graphical user interface**: Provides a `tkinter` based user interface for
   interacting with command line tools.
-  **Flexible configuration**: Allows actions, options and outputs to be
   configured via a JSON file.
-  **Results display**: Displays results in different formats (text, table,
   JSON) depending on configuration.
-  **File support**: Selection of files via an integrated dialogue.

Installation
------------

No additional installation is required. Just make sure Python 3 and the standard
libraries are installed on your system.

Prerequisites
-------------

- Python 3.x
- Standard libraries
- No additional dependencies

Usage
-----

1. Prepare a JSON configuration file describing the command line tool to be
   used, its options and the output format.
2. Run the script with the configuration file as an argument:

```bash
./cliquetis.py <configuration.json>
```

Advanced features
-----------------

-  **Column grouping**: Tabular data can be grouped by column via the `group-by`
   key.
-  **JSON support**: JSON output is displayed as a tree structure.
-  **Default values**: Options can be pre-filled with default values.

License
-------

This project is licensed under the MIT license. See the `LICENSE` file for more
information.
