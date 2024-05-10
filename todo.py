#!/python3

import sublime
import sublime_plugin
import traceback
import os



'''
    Formatting Side:

    Formats a file according to the following todo-list structure

    Contiguous blocks of text starting with a special character will be grouped together.
    When in a group, a line that doesn't start with a special character will form a new group.

    Non todo-list groups will be left unformatted
'''

BULLETS = [
    ["doing",      u'<'],
    ["paused",     u'>'],
    ["hp_todo",    u'*'],
    ["todo",       u'-'],
    ["lp_todo",    u'•'],
    ["unsure",     u'?'],
    ["list",       u'«'],
    ["delegated",  u'»'],
    ["done",       u'+'],
]
PRIORITY_MAP   = {c[0]:c[1] for c in BULLETS}
BULLET_RANK    = {c[1]:r for r,c in enumerate(BULLETS, 1)}
RANKED_BULLETS = {v:k for k,v in BULLET_RANK.items()}

COMMENT_DELIMS = ["'''", '"""', '```']


def is_repeated_char(line):
    ''' checks if a line is only made up of the same character '''
    for c in line:
        if c != line[0]:
            return False
    return True

def get_list_item_type(line):
    # allow mistakes, such as '-item 1', while still allowing detection of headings '--'
    try:
        to_fix = False
        split_line = line.split(' ', 1)
        first_word = split_line[0]
        if len(first_word) > 1:
            if len(split_line) == 1 and is_repeated_char(first_word):
                return None, False
            to_fix = True
        return first_word[0], to_fix
    except:
        return None, False

def rank(line):
    ''' sort order for a line '''
    try:
        # split on space so we don't rank headers
        return BULLET_RANK[line.split(' ', 1)[0]]
    except:
        return 0

def heading(line, length, chars=('-', '=', '~')):
    ''' expands a line of characters to a certain length '''
    if line and line[0] in chars and is_repeated_char(line):
        return line[0] * length
    return line

def inject_space(line):
    return line[:1] + ' ' + line[1:]

def new_group(groups, current):
    ''' Appends to a group if needed '''
    if current:
        groups.append(current)
    return []


def parse(text, notes):
    groups = []
    current = []
    in_group = False
    in_block = False

    # run through the text and group the sections
    for line in text.split('\n'):
        # check for end of a comment/text block
        if in_block:
            current.append(line)
            if line == in_block:
                in_block = False
                current = new_group(groups, current)
            continue

        # check for start of a comment/text block
        if line in COMMENT_DELIMS:
            current.append(line)
            in_block = line
            continue

        # remove any whitespace
        line = line.strip()
        # and grab the first 'word' to see how to handle the line
        litype, fix_spacing = get_list_item_type(line)

        # if it starts with a special character, add to the group
        if litype and litype in BULLET_RANK:
            in_group = True
            if fix_spacing:
                line = inject_space(line)
            current.append(line)

        # otherwise, if we're already in a group, end it
        elif in_group:
            in_group = False
            current = new_group(groups, current)
            if line or notes:
                current.append(line)

        # if it's a newline only
        elif not line:
            if notes and current and current[-1]:
                current.append(line)
            current = new_group(groups, current)

        # if there was a line, but it wasn't special, and we weren't in a group
        else:
            # expand any headings etc
            if current:
                line = heading(line, len(current[-1]))
            if notes:
                current = new_group(groups, current)
            current.append(line)

    new_group(groups, current)
    return groups


def mark_as(lines, style):
    bullet = PRIORITY_MAP.get(style, "-")

    all_lines = []
    for line in lines.split("\n"):
        if line.split(" ")[0] in BULLET_RANK:
            newline = bullet + " "  + " ".join(line.split(" ")[1:])
        else:
            newline = bullet + " " + line
        all_lines.append(newline)

    return "\n".join(all_lines)


def promote(lines, down=False):
    print(lines, down)
    all_lines = []
    for line in lines.split("\n"):
        original_bullet = line.split(" ")[0]
        if original_bullet in BULLET_RANK:
            original_rank = BULLET_RANK[original_bullet]
            if down:
                rank = original_rank + 1
            else:
                rank = original_rank - 1

            bullet = RANKED_BULLETS.get(rank, original_bullet)
            print("original_bullet", original_bullet)
            print("original_rank", original_rank)
            print("rank", rank)
            print("bullet", bullet)

            newline = bullet + " "  + " ".join(line.split(" ")[1:])
        else:
            newline = line
        all_lines.append(newline)

    return "\n".join(all_lines)



def format_text(text, notes):
    '''
        Takes in a text block, loads the segments
        formats and returns the formatted text
    '''
    groups = parse(text, notes)

    sorted_groups = []
    for group in groups:
        if group and group[0] and group[0] in COMMENT_DELIMS:
            sorted_groups.append('\n'.join(group))
        else:
            # decorate, sort, un-decorate
            decorated = [(rank(line), line) for line in group]
            decorated.sort(key=lambda a: a[0]) # stable sort with only the ranking
            sorted_groups.append('\n'.join([line for (t, line) in decorated]))

    spacing = '\n' if notes else '\n\n'
    ending = '' if notes else '\n'
    return spacing.join(sorted_groups) + ending


def format_file(filename):
    ''' Helper for test cases '''
    notes = filename.endswith('.notes')

    import codecs
    with codecs.open(filename, 'r', encoding='utf8') as file:
        text = format_text(file.read(), notes)

    with codecs.open(filename, 'w', encoding='utf8') as file:
        file.write(text)



'''
    Sublime Side:

    Helper functions
'''

def is_notes_file(view):
    # less damaging to default to notes type
    try:
        _, ext = os.path.splitext(view.file_name())
        return ext != '.todo'
    except:
        return True

def is_todo_source(view):
    return "todo.sublime-syntax" in view.settings().get("syntax")

def show_error(view):
    window = view.window()
    panel = window.create_output_panel('todo_fmt_error')
    panel.set_syntax_file('Packages/Text/Plain text.tmLanguage')
    panel.settings().set('line_numbers', False)
    panel.set_scratch(True)

    panel.set_read_only(False)
    panel.run_command('append', {'characters': str(traceback.format_exc())})
    panel.set_read_only(True)
    window.run_command('show_panel', { 'panel': 'output.todo_fmt_error' })

def hide_error(view):
    view.window().run_command('hide_panel', { 'panel': 'output.todo_fmt_error' })

def handle_errors(func):
    def inner(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
            hide_error(self.view)
        except:
            show_error(self.view)
    return inner




'''
    Sublime Side:

    Commands and event listeners
'''

class TodoTextCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return is_todo_source(self.view)

    def get_all(self):
        return sublime.Region(0, self.view.size())

    def get_scope(self, region):
        return self.view.expand_to_scope(region.a, "todo.list")

    def get_line(self, region):
        return self.view.line(region)


    def runner(self, fn, edit, scope, *args, **kwargs):
        if scope is not None:
            text = self.view.substr(scope)
            res = fn(text, *args, **kwargs)
            self.view.replace(edit, scope, res)


class TodoFmt(TodoTextCommand):
    @handle_errors
    def run(self, edit, all=True):
        notes = is_notes_file(self.view)

        if all:
            self.runner(format_text, edit, self.get_all(), notes)
        else:
            for region in self.view.sel():
                self.runner(format_text, edit, self.get_scope(region), notes)


class TodoMarkAs(TodoTextCommand):
    @handle_errors
    def run(self, edit, style="todo"):
        for region in self.view.sel():
            self.runner(mark_as, edit, self.get_line(region), style)
        self.view.run_command('todo_fmt', False)


class TodoPromote(TodoTextCommand):
    @handle_errors
    def run(self, edit, down=False):
        for region in self.view.sel():
            self.runner(promote, edit, self.get_line(region), down)
        self.view.run_command('todo_fmt', False)



class TodoFmtOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        settings = sublime.load_settings('todo.sublime-settings')
        if settings.get('format_on_save', True):
            view.run_command('todo_fmt')
