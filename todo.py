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
PRIORITY_IMAP  = {v: k for k, v in PRIORITY_MAP.items()}
BULLET_RANK    = {c[1]:r for r,c in enumerate(BULLETS, 1)}
RANKED_BULLETS = {v:k for k,v in BULLET_RANK.items()}

COMMENT_DELIMS = ["'''", '"""', '```']

DEFAULT_FOLD = "lp_todo"
DEFAULT_FOLD_LEVEL = BULLET_RANK[PRIORITY_MAP["lp_todo"]]
MIN_FOLD = list(RANKED_BULLETS.keys())[0]
MAX_FOLD = list(RANKED_BULLETS.keys())[-1]


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


def fold(view, fold_level):
    full_region = sublime.Region(0, view.size())
    lines = view.lines(full_region)
    view.unfold(full_region)

    fold_regions = []
    current_fold_start = None

    def end_fold():
        nonlocal current_fold_start
        if current_fold_start is not None:
            fold_regions.append(sublime.Region(current_fold_start, current_fold_end))
            current_fold_start = None


    for line_region in lines:
        line_text = view.substr(line_region).strip()

        if not line_text or (len(line_text) > 2 and line_text[1] != " "):
            end_fold()
            continue

        # Get the symbol and priority
        symbol = line_text[0]
        priority = BULLET_RANK.get(symbol, 0)

        if priority > fold_level:
            if current_fold_start is None:
                current_fold_start = view.full_line(line_region.begin()).begin()
            # Always extend to the end of the current line
            current_fold_end = view.full_line(line_region.begin()).end()
        else:
            end_fold()

    # Final region flush
    end_fold()

    # Fold all collected regions
    for region in fold_regions:
        view.fold(region)



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
        if settings.get('remove_done_on_save', True):
            view.run_command('todo_remove_done')


class TodoRemoveDone(TodoTextCommand):
    @handle_errors
    def run(self, edit):
        view = self.view
        scope = self.get_all()
        lines = view.lines(scope)

        for line_region in reversed(lines):  # Reverse to avoid offset issues
            if view.substr(line_region).startswith("+ "):
                view.erase(edit, view.full_line(line_region.begin()))


class TodoFold(TodoTextCommand):
    @handle_errors
    def run(self, edit, level=DEFAULT_FOLD):
        fold_level = BULLET_RANK[PRIORITY_MAP[level]]
        fold(self.view, fold_level)
        self.view.settings().set("fold_level", fold_level)


class TodoToggleFold(TodoTextCommand):
    @handle_errors
    def run(self, edit):
        if self.view.folded_regions():
            self.view.run_command('unfold_all')
        else:
            fold_level = self.view.settings().get("fold_level", DEFAULT_FOLD_LEVEL)
            level = PRIORITY_IMAP[RANKED_BULLETS[fold_level]]
            self.view.run_command('todo_fold', {"level": level})


class TodoFoldLevel(TodoTextCommand):
    @handle_errors
    def run(self, edit, increase):
        fold_level = self.view.settings().get("fold_level", DEFAULT_FOLD_LEVEL)

        if increase:
            fold_level = max(fold_level - 1, MIN_FOLD-1)
        else:
            fold_level = min(fold_level + 1, MAX_FOLD)

        self.view.settings().set("fold_level", fold_level)

        fold(self.view, fold_level)

