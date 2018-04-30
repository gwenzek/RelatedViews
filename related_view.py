import sublime

import sublime_plugin

def log(*args):
    print("[RelatedView]", *args)

def check(value, message):
    assert value, "[RelatedView] " + message
    return value

MAIN_GROUP = 0;
RELATED_GROUP = 1;

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
  def on_load_async(self, view):
    self.maybe_update(view)

  # def on_activated(self, view):
  #   self.maybe_update(view)

  def maybe_update(self, view):
    window = view.window()
    if not window:
      return
    group, index = window.get_view_index(view)
    log("group, index", (group, index))
    if group == MAIN_GROUP:
      view.run_command("update_related_views")


class UpdateRelatedViewsCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    view = self.view
    window = view.window()
    related = get_related(view)
    if related:
      for v in window.views_in_group(RELATED_GROUP):
        window.focus_view(v)
        window.run_command("close")

    for r in related:
      rview = window.open_file(r)
      window.set_view_index(rview, RELATED_GROUP, 0)

    window.focus_view(view)


def get_related(main_view):
  main_file = check(
        main_view.file_name(), "Main view has no file associated")

  project_data = main_view.window().project_data()
  relations = project_data.get("related_views", [])

  for r in relations:
    if r["file"] == main_file:
      return r["related"]
  return []
