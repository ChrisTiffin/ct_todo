#!/python3

import sublime
import sublime_plugin
import traceback
import os

from .src.format import format_text

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


class TodoFmt(sublime_plugin.TextCommand):
    def is_enabled(self):
        return is_todo_source(self.view)

    def run(self, edit, notes=None):
        try:
            if notes is None:
                notes = is_notes_file(self.view)

            # replace the buffer with Todo fmt output
            res = format_text(self.get_content(), notes)
            self.view.replace(edit, sublime.Region(0, self.view.size()), res)
            hide_error(self.view)

        except:
            show_error(self.view)

    def get_content(self):
        region = sublime.Region(0, self.view.size())
        return self.view.substr(region)


class TodoFmtOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        settings = sublime.load_settings('todo.sublime-settings')
        if settings.get('format_on_save', True):
            view.run_command('todo_fmt')

