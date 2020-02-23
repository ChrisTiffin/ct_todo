#!/python3
# coding=utf-8

'''
    Formats a file according to the following todo-list structure

    Contiguous blocks of text starting with a special character will be grouped together.
    When in a group, a line that doesn't start with a special character will form a new group.

    Non todo-list groups will be left unformatted
'''

SPECIAL_CHARS_DICT = {
    u'>': 10,  # in progress
    u'*': 20,  # high priority todo
    u'-': 30,  # normal priority todo
    u'•': 40,  # low priority todo
    u'?': 50,  # unsure todo
    u'«': 60,  # separate list
    u'»': 70,  # delegated
    u'+': 80,  # done
}
SPECIAL_CHARS = tuple(SPECIAL_CHARS_DICT.keys())

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
        return SPECIAL_CHARS_DICT[line.split(' ', 1)[0]]
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
                current.append('')
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
        if litype and litype in SPECIAL_CHARS:
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

        # if it's a newline only
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


def format_text(text, notes):
    '''
        Takes in a text block, loads the segments
        formats and returns the formatted text
    '''
    groups = parse(text, notes)

    ## debug printouts
    # from pprint import pprint as pp
    # pp(groups)

    sorted_groups = []
    for group in groups:
        print (group)
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


if __name__ == "__main__":
    format_file("syntax_test_todo")
