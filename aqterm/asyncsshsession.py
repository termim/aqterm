
import asyncio
import logging
from typing import Optional

import asyncssh
from qtpy import QtCore


class SSHClientSession(QtCore.QObject, asyncssh.SSHClientSession):

    dataReceived = QtCore.Signal(object)
    connectionLost = QtCore.Signal(object)
    sendData = QtCore.Signal(object)

    def __init__(self, **kw):
        super().__init__(**kw)

        self.sendData.connect(self.write)


    @classmethod
    async def create_session(cls, host=None, program=None, term_type=None, term_size=None):

        conn = await asyncssh.connect('localhost')
        chan, session = await conn.create_session(
                                    cls,
                                    program or '/usr/bin/bash',
                                    term_type=term_type or 'xterm-color',
                                    term_size=term_size or (80, 24),
                                    encoding=None,
                                    )
        return session


    def connection_made(self, chan: asyncssh.SSHTCPChannel) -> None:
        self._chan = chan

    def data_received(self, data: str, datatype: asyncssh.DataType) -> None:
        #print(f"{data=} {datatype=}")
        self.dataReceived.emit(data)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            logging.error(f'SSH session error: {exc}')
        self.connectionLost.emit(exc)

    def write(self, data):
        self._chan.write(data)#.encode())

    def resize(self, width: int, height: int, pixwidth: int = 0, pixheight: int = 0):
        self._chan.change_terminal_size(width, height, pixwidth, pixheight)

    def close(self) -> None:
        self._chan.close()
