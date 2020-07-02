"""
there are two states: "default browser view" and "focus on one element".
For the latter there are two states "editor only" and "sidebar with table maximized".
"""


"""
copyright 2019- ijgnd
          2015-2018 Glutanimate  <https://glutanimate.com/>
          2018 Arthur Milchior

I took some files from the add-on "Frozen Fields" and adjusted some functions
form browser_search_highlight_results.py.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from aqt.browser import Browser
from anki.hooks import addHook, wrap
from anki.lang import _
from aqt.gui_hooks import (
    browser_menus_did_init,

)
from aqt import mw
from aqt.qt import (
    QKeySequence,
)

from .toolbar import getMenu


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail


def mysetupTable(self):
    self.form.fieldsArea.setMinimumSize(50, 1)
    self.form.widget.setMinimumSize(50, 1)
    self.extremestate = 0   # for toggling views
    self.advbrowse_uniqueNote_state_original = mw.col.get_config("advbrowse_uniqueNote", False)

    val = gc("splitter_bigger", False)
    if val:
        #test for old config style that just had True and False
        if bool(val):
            val = 20
        self.form.splitter.setHandleWidth(val)
Browser.setupTable = wrap(Browser.setupTable, mysetupTable, "before")


def my_toggle_notes_only(self, arg):
    self.model.beginReset()
    mw.col.set_config("advbrowse_uniqueNote", arg)
    self.onSearchActivated()
    self.model.endReset()


def get_splitter_dimension(self):
    # bett compatibility with "browser side-by-side (horizontal split)"
    # https://ankiweb.net/shared/info/831846358
    try:
        if self.side_by_side:
            sh = self.form.splitter.size().width()
        else:
            sh = self.form.splitter.size().height()
    except:
        sh = self.form.splitter.size().height()
    return sh


def editor_only(self):
    #note only
    self.advbrowse_uniqueNote_state_original = mw.col.get_config("advbrowse_uniqueNote", False)
    my_toggle_notes_only(self, True)
    if self.sidebarDockWidget.isVisible():
        self.sidebarDockWidget.setVisible(False)
    sh = get_splitter_dimension(self)
    self.form.splitter.setSizes([ sh * 0.1, sh * 0.99])  #https://stackoverflow.com/a/47843697
    self.extremestate = 1


def table_only(self):
    my_toggle_notes_only(self, self.advbrowse_uniqueNote_state_original)
    # don't hide the editor via  self.form.fieldsArea.setVisible(False) so
    # that I can restore by dragging the splitter
    # ---
    # it's not enough to hide self.tableView because tableView and the search bar
    # are in a widget. If I hide the tableView this widget will only hold the
    # search bar and a lot of grey space.
    sh = get_splitter_dimension(self)
    self.form.splitter.setSizes([ sh * 0.99, sh * 0.01])  #https://stackoverflow.com/a/47843697
    self.extremestate = 0
    if self.sidebarDockWidget.isVisible():
        self.sidebarDockWidget.setVisible(False)
    #works but can't resize manually
    #self.form.fieldsArea.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    #self.form.widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

    #works but can't resize manually
    #self.form.fieldsArea.setFixedHeight(1)
    #self.form.widget.setFixedHeight(sh-1)

    #this has no effect:
    #self.form.splitter.setStretchFactor(100,1)

    #doesn't work
    #sw = self.form.splitter.size().width()
    #self.form.widget.resize(sw,sh)


def toggle_extremes(self):
    if not self.form.fieldsArea.isVisible():
        table_only(self)
    elif self.extremestate == 0:
        editor_only(self)
    else:
        table_only(self)


def back_to_default(self):
    my_toggle_notes_only(self, self.advbrowse_uniqueNote_state_original)
    mw.col.set_config("advbrowse_uniqueNote", self.advbrowse_uniqueNote_state_original)
    if not self.form.widget.isVisible():
        self.form.widget.setVisible(True)
    if not self.form.fieldsArea.isVisible():
        self.form.fieldsArea.setVisible(True)
    if not self.sidebarDockWidget.isVisible():
        self.sidebarDockWidget.setVisible(True)
    sh = get_splitter_dimension(self)
    self.form.splitter.setSizes([ sh * 0.5, sh * 0.5])  #https://stackoverflow.com/a/47843697


def my_toggle_sidebar(self):
    if not self.sidebarDockWidget.isVisible():
        self.sidebarDockWidget.setVisible(True)
    else:
        self.sidebarDockWidget.setVisible(False)


def onSetupMenus(self):
    # self is browser
    m = getMenu(self, "&View")

    #a.setCheckable(True)/a.toggled.connect(self.toggleTableAndSidebar) and maybe a.setChecked(True)
    #doesn't offer benefits here: you don't need visual feedbar in the menu
    #to see if the table view is hidden ...
    a = m.addAction('editor only')
    a.triggered.connect(lambda _, browser=self: editor_only(browser))
    a.setShortcut(QKeySequence(gc("hotkey_editor_only","")))

    a = m.addAction('table only')
    a.triggered.connect(lambda _, browser=self: table_only(browser))
    a.setShortcut(QKeySequence(gc("hotkey_table_only","")))

    a = m.addAction('toggle between "only table/sidebar" and "only editor"')
    a.triggered.connect(lambda _, browser=self: toggle_extremes(browser))
    a.setShortcut(QKeySequence(gc("hotkey_toggle","")))

    a = m.addAction('toggle sidebar')
    a.triggered.connect(lambda _, browser=self: my_toggle_sidebar(browser))
    a.setShortcut(QKeySequence(gc("hotkey_toggle_sidebar","")))

    a = m.addAction('reset to default')
    a.triggered.connect(lambda _, browser=self: back_to_default(browser))
    a.setShortcut(QKeySequence(gc("hotkey_back_to_default","")))
browser_menus_did_init.append(onSetupMenus)
