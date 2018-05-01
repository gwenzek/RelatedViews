import sublime

import copy
import os
import unittest

MAIN_GROUP = 0;
RELATED_GROUP = 1;
CLOSE_OPENED_VIEWS = True

PREFIX = os.path.dirname(os.path.abspath(__file__)) + "/tmp/"
FILE_A = PREFIX + "file_a.py"
FILE_A_TEST = PREFIX + "file_a_test.py"
FILE_B = PREFIX + "file_b.py"
FILE_B_TEST = PREFIX + "file_b_test.py"
FILE_B_DOC = PREFIX + "file_b_doc.md"
FILE_C = PREFIX + "file_c.py"
FILE_C_TEST = PREFIX + "file_c_test.py"

def touch(*files):
  for file_name in files:
    with open(file_name, 'w') as f:
      f.write("Test file: " + file_name +"\n")

class TestRelatedViews(unittest.TestCase):

  def __init__(self, *args):
    unittest.TestCase.__init__(self, *args)
    self.window = sublime.active_window()
    self.original_active_view = self.window.active_view()
    self.original_project_data = self.window.project_data()
    # Switch to two columns layout.
    self.window.run_command("set_layout", args={
      "cols": [0.0, 0.5, 1.0],
      "rows": [0.0, 1.0],
      "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
    })
    self.opened_views = []
    touch(FILE_A, FILE_A_TEST)
    touch(FILE_B, FILE_B_TEST, FILE_B_DOC)
    touch(FILE_C, FILE_C_TEST)

  def setUp(self):
    project_data = self.window.project_data()
    project_data["related_views"] = [
        { "file": FILE_A, "related": [FILE_A_TEST] },
        { "file": FILE_B, "related": [FILE_B_TEST, FILE_B_DOC] },
    ]
    self.window.set_project_data(project_data)

  def tearDown(self):
    if CLOSE_OPENED_VIEWS:
      for v in self.opened_views:
        self.window.focus_view(v)
        self.window.run_command("close")
      self.opened_views = []
    self.window.focus_view(self.original_active_view)
    self.window.set_project_data(self.original_project_data)

  def open_file(self, file_name):
    v = self.window.open_file(file_name)
    self.opened_views.append(v)
    return v

  def test_mark_as_related(self):
    # Open file_c.py and file_c_test.py.
    self.window.set_project_data({})
    c_view = self.open_file(FILE_C)
    self.window.set_view_index(c_view, MAIN_GROUP, 0)
    c_test_view = self.open_file(FILE_C_TEST)
    self.window.set_view_index(c_test_view, RELATED_GROUP, 0)

    self.window.focus_view(c_view)
    self.window.focus_view(c_test_view)

    # Ask file_c_test.py to be marked as related to file_c.py
    c_test_view.run_command("mark_as_related")

    # Check the relation has been saved to project_data.
    relations = self.window.project_data().get("related_views")
    expected_relations = [{ "file": FILE_C, "related": [FILE_C_TEST] }]
    self.assertEqual(expected_relations, relations)

  def test_related_file_is_open(self):
    self.window.focus_group(MAIN_GROUP)
    self.open_file(FILE_A)

    related_views = self.window.views_in_group(RELATED_GROUP)
    related_files = [v.file_name() for v in related_views]
    self.assertIn(FILE_A_TEST, related_files)

    v_test = self.window.active_view_in_group(RELATED_GROUP)
    self.assertEqual(FILE_A_TEST, v_test.file_name())

  def test_related_files_are_open_in_order(self):
    self.window.focus_group(MAIN_GROUP)
    self.open_file(FILE_B)

    related_views = self.window.views_in_group(RELATED_GROUP)
    related_files = [v.file_name() for v in related_views]
    self.assertIn(FILE_B_TEST, related_files)
    self.assertIn(FILE_B_DOC, related_files)

    v_test = self.window.active_view_in_group(RELATED_GROUP)
    self.assertEqual(FILE_B_TEST, v_test.file_name())
