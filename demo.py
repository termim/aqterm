
import asyncio
import sys
from typing import Optional

import qasync
from qasync import QEventLoop, asyncClose, asyncSlot

from qtpy import QtGui, QtCore, QtWidgets

from aqterm.asyncsshsession import SSHClientSession
from aqterm.terminal import TerminalWidget
from aqterm.schemes import ColorScheme

#ColorScheme.loadSchemes(os.path.abspath("schemes"))


class TabbedTerminal(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabbedTerminal, self).__init__(parent)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        self._new_button = QtWidgets.QPushButton(self)
        self._new_button.setText("New")
        self._new_button.clicked.connect(self.new_terminal)
        self.setCornerWidget(self._new_button)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setWindowTitle("Terminal")
        self._terms = []
        self.tabCloseRequested[int].connect(self._on_close_request)
        self.currentChanged[int].connect(self._on_current_changed)

    @asyncClose
    async def closeEvent(self, event):  # noqa:N802
        self.session.close()

    def _on_close_request(self, idx):
        term = self.widget(idx)
        term.stop()

    def _on_current_changed(self, idx):
        term = self.widget(idx)
        self._update_title(term)

    @asyncSlot()
    async def new_terminal(self):
        # Create session
        self.session = await SSHClientSession.create_session(
                host='localhost',
                program='/usr/bin/bash',
                term_type='xterm-color',
                term_size=(80, 24)
            )
        term = TerminalWidget(self.session, parent = self)
        term.sessionClosed.connect(self.on_session_closed)
        self.addTab(term, "Terminal")
        self._terms.append(term)
        self.setCurrentWidget(term)
        term.setFocus()

    def timerEvent(self, event):
        self._update_title(self.currentWidget())

    def _update_title(self, term):
        if term is None:
            self.setWindowTitle("Terminal")
            return
        idx = self.indexOf(term)
        title = "Terminal"
        self.setTabText(idx, title)
        self.setWindowTitle(title)

    def on_session_closed(self):
        term = self.sender()
        try:
            self._terms.remove(term)
        except:
            pass
        self.removeTab(self.indexOf(term))
        widget = self.currentWidget()
        if widget:
            widget.setFocus()
        #if self.count() == 0:
            #self.new_terminal()


def main():

    app = QtWidgets.QApplication(sys.argv)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    win = TabbedTerminal()
    win.resize(800, 600)
    win.show()

    async def async_main():
        #asyncio.create_task(win.new_terminal())
        await win.new_terminal()
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
