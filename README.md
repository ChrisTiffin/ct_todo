Todo and Notes support for Sublime Text 3
=========================================

A formatter that provides simple list ordering and highlighting for sublime.


### Features:

* Format on save for `.todo` and `.notes` files
* Syntax highlighting for `todo` files.
* Commands for `todo` files
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
7. Select _"ct_todo"_

## Configuration

The defaults are available in the [todo.sublime-settings][settings_file] file.


.todo format
------------

The todo format (for any file with a .todo extension) allows a groups of lists, which will be formatted into a pre-defined order, and grouped with newlines between lists.

Format example, with the list items in order:
```
heading (optional)
--, ~~ or == (optional: will be expanded to match the heading length)
< in progress
> paused
* high priority todo
- normal priority todo
• low priority todo
? unsure whether to do
« separate list
» delegated
+ done
```

so a file that looks like:

```
todo
==

list one
--
+ completed task
- todo 1
- todo 2
< current task
* important task
list two
+ done
- todo 1
< other current task
• todo 2
- todo 3
```

once formatted, will become:

```
todo
====

list one
--------
< current task
> other current task
* important task
- todo 1
- todo 2
+ completed task

list two
- todo 1
- todo 3
• todo 2
+ done

```

.notes format
-------------

The notes (requires .notes extension) format is the same, however it won't force newlines between lists.

```
heading
--
item
- sub item 1 (follows todo format)
- sub item 2
another item
- another sub item
```
