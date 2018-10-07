# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2016-2018 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""QtWebEngine specific p2p://* handlers and glue code."""

from PyQt5.QtCore import QBuffer, QIODevice, QUrl, QByteArray
from PyQt5.QtWebEngineCore import (QWebEngineUrlSchemeHandler,
                                   QWebEngineUrlRequestJob)

from qutebrowser.browser import qutescheme
from qutebrowser.utils import log, qtutils

import ipfsapi
import magic
import traceback

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever

class IPFSSchemeHandler(QWebEngineUrlSchemeHandler):

    """Handle p2p://* requests on QtWebEngine."""

    def install(self, profile):
        """Install the handler for p2p:// URLs on the given profile."""
        profile.installUrlSchemeHandler(b'p2p', self)

    def _check_initiator(self, job):
        """Check whether the initiator of the job should be allowed.

        Only the browser itself or p2p:// pages should access any of those
        URLs.

        Args:
            job: QWebEngineUrlRequestJob

        Return:
            True if the initiator is allowed, False if it was blocked.
        """
        try:
            initiator = job.initiator()
        except AttributeError:
            # Added in Qt 5.11
            return True

        if initiator == QUrl('null') and not qtutils.version_check('5.12'):
            # WORKAROUND for https://bugreports.qt.io/browse/QTBUG-70421
            return True

        print("scheme: " + initiator.scheme())
        if initiator.isValid() and initiator.scheme() != 'p2p':
            log.misc.warning("Blocking malicious request from {} to {}".format(
                initiator.toDisplayString(),
                job.requestUrl().toDisplayString()))
            job.fail(QWebEngineUrlRequestJob.RequestDenied)
            return False

        return True

    def requestStarted(self, job):
        """Handle a request for a p2p: scheme.

        This method must be reimplemented by all custom URL scheme handlers.
        The request is asynchronous and does not need to be handled right away.

        Args:
            job: QWebEngineUrlRequestJob
        """
        url = job.requestUrl()

        ipfsPath = remove_prefix(url.toDisplayString(), 'p2p:/')

        # TODO should check if it's a directory before trying to CAT it
        # TODO if it is a directory, and there is a index.html, CAT index.html

        try:
            api = ipfsapi.connect('127.0.0.1', 5001)
            catData = api.cat(ipfsPath)
        except Exception as e:
            print(e)
            catData = bytes("Could not load content. Make sure you have your IPFS daemon running\n\n", "utf8")
            # catData = catData + bytes(str(e), 'utf8')
            catData = catData + bytes(traceback.format_exc(), 'utf8')

        mimetype = magic.from_buffer(catData, mime=True)

        buf = QBuffer(parent=self)
        buf.open(QIODevice.WriteOnly)
        buf.write(catData)
        buf.seek(0)
        buf.close()
        job.reply(mimetype.encode('ascii'), buf)
