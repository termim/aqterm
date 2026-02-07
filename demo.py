
import asyncio
import functools
import sys
from typing import Optional

import qasync
from qasync import QEventLoop, asyncClose, asyncSlot

from qtpy import QtGui, QtCore, QtWidgets

from aqterm.asyncsshsession import SSHClientSession
from aqterm.terminal import TerminalWidget
from aqterm.schemes import ColorScheme


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.terminals = TabbedTerminal(self)
        self.setCentralWidget(self.terminals)

        menu = QtWidgets.QMenu("&Options", self)
        self.menuBar().addMenu(menu)
        action_group = QtGui.QActionGroup(self, exclusive=True)
        for name, path in ColorScheme.list_schemes():
            action = action_group.addAction(name)
            action.setCheckable(True)
            action.triggered.connect(functools.partial(self.terminals.set_scheme, name, path))
            menu.addAction(action)


class TabbedTerminal(QtWidgets.QTabWidget):

    def __init__(self, parent=None):
        super(TabbedTerminal, self).__init__(parent)

        self.setWindowTitle("Terminal")
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        self.setTabsClosable(True)
        self.setMovable(True)

        self.tabCloseRequested[int].connect(self.on_tabCloseRequested)
        self.currentChanged[int].connect(self.on_currentChanged)

        self._new_button = QtWidgets.QPushButton(self)
        self._new_button.setText("New")
        self._new_button.clicked.connect(self.createNewTerminal)
        self.setCornerWidget(self._new_button)

        self.color_schema = None


    def set_scheme(self, name, path):

        self.color_schema = ColorScheme.load_schema(path)
        self.currentWidget().setColorScheme(self.color_schema)


    def closeEvent(self, event):
        for idx in range(self.count()):
            self.widget(idx).close()


    def on_tabCloseRequested(self, idx):
        term = self.widget(idx)
        term.stop()


    def on_currentChanged(self, idx):
        term = self.widget(idx)
        self._update_title(term)


    def _update_title(self, term):
        if term is None:
            self.setWindowTitle("Terminal")
            return
        idx = self.indexOf(term)
        title = "Terminal"
        self.setTabText(idx, title)
        self.setWindowTitle(title)


    @asyncSlot()
    async def createNewTerminal(self):
        """
        Create session
        """
        session = await SSHClientSession.create_session(
                host='localhost',
                program='/usr/bin/bash',
                term_type='xterm-color',
                term_size=(80, 24)
            )
        term = TerminalWidget(session, parent = self)
        if self.color_schema:
            term.setColorScheme(self.color_schema)
        idx = self.addTab(term, "Terminal")
        term.sessionClosed.connect(functools.partial(self.on_sessionClosed, idx))
        self.setCurrentWidget(term)
        term.setFocus()


    def on_sessionClosed(self, idx):
        """
        Terminal session closed
        """
        self.removeTab(idx)



def main():

    app = QtWidgets.QApplication(sys.argv)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    win = MainWindow()
    win.resize(800, 600)
    win.show()

    async def async_main():
        await win.terminals.createNewTerminal()
        await app_close_event.wait()

    # for 3.11 or older use qasync.run instead of asyncio.run
    qasync.run(async_main())
    #asyncio.run(async_main(), loop_factory=QEventLoop)



if __name__ == "__main__":
    #import cProfile
    #import pyinstrument

    #with pyinstrument.profile():
    #with cProfile.Profile() as pr:
    main()
        #pr.print_stats()
