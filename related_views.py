import sublime

import sublime_plugin

DEBUG = True
MAIN_GROUP = 0;
RELATED_GROUP = 1;
AGGRESSIVE_CLOSE = False;

def log(*args):
  if DEBUG:
    print("[RelatedView]", *args)

def check(value, message):
  assert value, "[RelatedView] " + message
  return value

class MarkAsRelatedCommand(sublime_plugin.TextCommand):

  def run(self, edit):
    related_file = check(
        self.view.file_name(), "Related view have no file associated")

    window = self.view.window()
    main_view = window.active_view_in_group(MAIN_GROUP)
    check(main_view != self.view, "Can't link a view to itself")

    main_file = check(main_view.file_name(), "Main view have no file associated")

    project_data = window.project_data()
    related_views = project_data.get("related_views", [])
    found = False

    for r in related_views:
      if r["file"] == main_file:
        found = True
        r["related"] += [related_file]
        break
    if not found:
      related_views.append({"file": main_file, "related": [related_file]})
    project_data["related_views"] = related_views
    window.set_project_data(project_data)

class MainFileChangeListener(sublime_plugin.EventListener):
  running = False

  def on_activated(self, view):
    self.maybe_update(view)

  def maybe_update(self, view):
    if self.running:
      log("Already running")
      return
    self.running = True
    try:
      window = view.window()
      if not window:
        return
      group, index = window.get_view_index(view)
      if group == MAIN_GROUP:
        view.run_command("update_related_views")
    finally:
      self.running = False

class _KeepFocusInPlace():
  def __init__(self, window):
    self.window = window

  def __enter__(self):
    self.focused = self.window.active_view()

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.window.focus_view(self.focused)

def keep_focus_in_place(window):
  return _KeepFocusInPlace(window)

class UpdateRelatedViewsCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    main_view = self.view
    if not main_view.file_name():
      return

    window = main_view.window()
    if not window:
      return
    related = get_related(main_view)
    if not related:
      log("No related files for:", main_view.file_name())
      return
    log("Found",  len(related), "related files for", main_view.file_name())
    already_opened = set()
    with keep_focus_in_place(window):
      # Closing views in RELATED_GROUP.
      for v in window.views_in_group(RELATED_GROUP):
        close, reason = should_close(v, related)
        if close:
          log("Closing", v.file_name())
          window.focus_view(v)
          window.run_command("close")
        elif reason == STILL_RELATED:
          already_opened.add(v.file_name())

      # Opening related files in the RELATED_GROUP.
      for i, r in enumerate(related[::-1]):
        if r in already_opened:
          continue
        log("Opening", r)
        v = window.open_file(r)
        window.set_view_index(v, RELATED_GROUP, 0)
        v.settings().set("opened_because_related", True)


# Reasons returned by should_close
STILL_RELATED = 1;
IS_DIRTY = 2;
NOT_OPENED_BY_US = 3;

def should_close(view, related_files):
  """Returns whether we should close a given view, and the reason why."""
  if view.file_name() in related_files:
    return False, STILL_RELATED
  if view.is_dirty():
    return False, IS_DIRTY

  if not AGGRESSIVE_CLOSE:
    if not view.settings().get("opened_because_related"):
      return False, NOT_OPENED_BY_US

  return True, None


def get_related(main_view):
  main_file = check(
      main_view.file_name(), "Main view has no file associated")

  project_data = main_view.window().project_data()
  relations = project_data.get("related_views", [])

  for r in relations:
    if r["file"] == main_file:
      return r["related"]
  return []
