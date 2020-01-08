import sublime
import sublime_plugin
import traceback

import sys
from os import path

class TodoFmtOnSave(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    if not is_todo_source(view):
      return

    view.run_command('todo_fmt')


class TodoFmt(sublime_plugin.TextCommand):
  def is_enabled(self):
    settings = sublime.load_settings('todo.sublime-settings')
    fmt_enabled = settings.get('format_on_save', True)

    return fmt_enabled and is_todo_source(self.view)


  def run(self, edit):
    try:
      from ct_todo.format import format_text
      res = format_text(self.get_content(), is_notes_file(self.view))

      # replace the buffer with Todo fmt output
      self.view.replace(edit, sublime.Region(0, self.view.size()), res)

      # hide previous errors
      self.view.window().run_command('hide_panel', { 'panel': 'output.todo_fmt_error' })

    except:
      self.show_error()


  def get_content(self):
    region = sublime.Region(0, self.view.size())
    return self.view.substr(region)


  def show_error(self):
    window = self.view.window()
    panel = window.create_output_panel('todo_fmt_error')
    panel.set_syntax_file('Packages/Text/Plain text.tmLanguage')
    panel.settings().set('line_numbers', False)
    panel.set_scratch(True)

    panel.set_read_only(False)
    panel.run_command('append', {'characters': str(traceback.format_exc())})
    panel.set_read_only(True)
    window.run_command('show_panel', { 'panel': 'output.todo_fmt_error' })


def is_notes_file(view):
  try:
    _, ext = path.splitext(view.file_name())
    return ext == '.notes'
  except:
    return False


def is_todo_source(view):
  tp = 0
  sel = view.sel()
  if sel is not None:
    tp = sel[0].begin()

  return view.match_selector(tp, 'source.todo')
