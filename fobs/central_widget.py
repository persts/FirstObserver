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
import os
import sys
import glob
from PyQt5 import QtCore, QtWidgets, uic
import pyodbc

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(__file__)
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(bundle_dir, 'central_widget.ui'))


class CentralWidget(QtWidgets.QWidget, CLASS_DIALOG):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.cursor = None
        self.observers = {}
        self.visits = {}
        self.database_selected = False
        self.image_directory = ''
        self.image_list = []

        self.pushButtonAnnotator.clicked.connect(self.select_annotator)
        self.pushButtonDatabase.clicked.connect(self.select_database)
        self.pushButtonImport.clicked.connect(self.prep_import)

    def prep_import(self):
        if self.database_selected:
            # Select image directory
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Image Folder')
            if directory != '':
                # Get image file names
                self.image_list = []
                self.image_directory = directory
                files = glob.glob(os.path.join(self.image_directory, '*'))
                image_format = [".jpg", ".jpeg", ".png"]
                self.image_list = list(filter(lambda x: os.path.splitext(x)[1].lower() in image_format, files))
                self.image_list = [os.path.basename(x) for x in self.image_list]
                sorted(self.image_list)

                # Get the observer and visit id
                observer = self.comboBoxObservers.currentText()
                visit = self.comboBoxVisits.currentText()

                observer_id = self.observers[observer]
                visit_id = self.visits[visit]

                #Print
                print(self.image_directory)
                print(observer, observer_id)
                print(visit, visit_id)
                print(self.image_list)
    def select_annotator(self):
        print('Not implemented')

    def select_database(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Database', '.', 'Microsoft Access Database (*.accdb)')
        if file_name[0] != '':
            self.connection = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + file_name[0])
            self.cursor = self.connection.cursor()

            self.comboBoxObservers.clear()
            results = self.cursor.execute('SELECT * FROM Observers').fetchall()
            self.observers = {}
            for row in results:
                observer = '{}_{}'.format(row[2], row[1])
                self.comboBoxObservers.addItem(observer)
                self.observers[observer] = row[0]
            study_areas = {}
            results = self.cursor.execute('SELECT StudyAreaID, StudyAreaName FROM StudyAreas')
            for row in results:
                study_areas[row[0]] = row[1]
            locations = {}
            results = self.cursor.execute('SELECT LocationID, StudyAreaID, LocationName FROM CameraLocations')
            for row in results:
                locations[row[0]] = '{}#{}'.format(study_areas[row[1]], row[2])
            types = {}
            results = self.cursor.execute('SELECT ID, VisitType FROM LkupVisitTypes')
            for row in results:
                types[row[0]] = row[1]
            self.visits = {}
            visit_list = []
            results = self.cursor.execute('SELECT VisitID, LocationID, VisitTypeID, VisitDate FROM Visits')
            for row in results:
                visit = '{}#{}#{}'.format(locations[row[1]], types[row[2]], row[3])
                visit_list.append(visit)
                self.visits[visit] = row[0]
            self.comboBoxVisits.clear()
            sorted(visit_list)
            self.comboBoxVisits.addItems(visit_list)
            self.database_selected = True

            
