# -*- coding: utf-8 -*-
#
# FirstObserver
# Author: Peter Ersts (ersts@amnh.org)
#
# --------------------------------------------------------------------------
#
# This file is part of the FirstObserver application.
#
# FirstObserver is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FirstObserver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
import sys
from shutil import copyfile
from PyQt5 import QtWidgets
from fobs import __version__, CentralWidget

if __name__ == '__main__':
    copyfile('_template.accdb', 'sandbox.accdb')
    app = QtWidgets.QApplication(sys.argv)
    main = QtWidgets.QMainWindow()
    main.setWindowTitle('FirstObserver [v {}]'.format(__version__))
    main.setCentralWidget(CentralWidget())
    main.show()
    sys.exit(app.exec_())
