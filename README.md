Todo and Notes support for Sublime Text 3
=========================================

### Features:

* Format on save for `.todo` and `.notes` files
* Syntax highlighting for `.todo` files.
* Commands for `.todo` files
* Snippets

Installation
------------

### Using Package Control

1. Having [Package Control](https://packagecontrol.io/installation) installed
2. Open the palette by pressing `Ctrl+Shift+P` (Win, Linux) or `Cmd+Shift+P` (OS X).
3. Select _"Package Control: Add Repository"_
4. Enter `https://github.com/cjtiffin/sublime-todo`
5. Open command palette again
6. Select _"Package Control: Install Package"_
7. Select _"sublime-todo"_

## Configuration

The defaults are available in the [Terraform.sublime-settings][settings_file]
file.

.todo
-----

Format example:
```
heading (optional)
-- or ~~ or == (optional: will all be expanded in length to match the heading)
> in progress item
1 numbered item
- todo item
? low priority item
+ done item
```

so:

```
todo
==

list one
--
+ something that's been completed
- todo 1
- todo 2
1 prioritised item
> current

list two
+ done
- todo 1
- todo 2
```

once formatted, will be

```
todo
====

list one
--------
> current
1 prioritised item
- todo 1
- todo 2
+ something that's been completed

list two
- todo 1
- todo 2
+ done
```
