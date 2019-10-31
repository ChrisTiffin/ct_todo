#!/python

'''
    Formats a file according to the following todo-list structure

    Special 'todo-list' characters are:
        '>' : In progress
        '-' : To be done
        '?' : Other (e.g. delegated, on hold, waiting)
        '*' : Sublist
        '+' : Done

    Contiguous blocks of text starting with a special character will be grouped together.
    When in a group, a line that doesn't start with a special character will form a new group.

    Non todo-list groups will be left unformatted
'''

SPECIAL_CHARS_DICT = {
    '>':  0,  # in progress - top of the list
    '-': 85,  # remaining todo - next
    '?': 90,  # possible to do - could be ignored
    '*': 95,  # sub list
    '+': 99,  # done - at bottom
}
SPECIAL_CHARS = tuple(SPECIAL_CHARS_DICT.keys())

def is_num(word):
    ''' checks if is a number '''
    try:
        int(word)
        return True
    except:
        return False

def get_first_word(line):
    try:
        return line.split(' ', 1)[0]
    except:
        return None

def rank(line):
    ''' sort order for a line '''
    try:
        first = get_first_word(line)
        if first in SPECIAL_CHARS_DICT:
            return SPECIAL_CHARS_DICT[first]
        return int(first) + 1
    except:
        return 0

def line_of(line, char):
    ''' checks if a line is _just_ the given character '''
    return line and line == char * len(line)

def heading(line, length, chars=('-', '=', '~')):
    ''' expands a line of characters to a certain length '''
    for char in chars:
        if line_of(line, char):
            return char * length
    return line

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
        # handle unformatted blocks first
        if in_block:
            current.append(line)
            if line == in_block:
                in_block = False
                current = new_group(groups, current)
            continue

        if line in ["'''", '"""', '```']:
            current.append(line)
            in_block = line
            continue

        line = line.strip()
        first = get_first_word(line)

        if first and (first in SPECIAL_CHARS or is_num(first)):
            in_group = True
            current.append(line)

        elif in_group:
            in_group = False
            current = new_group(groups, current)
            if line or notes:
                current.append(line)

        elif not line:
            if notes and current and current[-1]:
                current.append(line)
            current = new_group(groups, current)

        else:
            # expand any headings etc
            if current:
                line = heading(line, len(current[-1]))
            if notes:
                current = new_group(groups, current)
            current.append(line)

    new_group(groups, current)
    return groups


def format_text(text, notes):
    '''
        Takes in a text block, loads the segments
        formats and returns the formatted text
    '''
    groups = parse(text, notes)

    # debug printouts
    # from pprint import pprint as pp
    # pp(groups)

    sorted_groups = []
    for group in groups:
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

    with open(filename) as file:
        text = format_text(file.read(), notes)

    with open(filename, 'w') as file:
        file.write(text)


