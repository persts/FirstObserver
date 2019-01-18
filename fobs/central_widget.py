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
import pyodbc
import json
import datetime
from PIL import Image, ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from andenet.gui import AnnotatorDialog #pylint: disable=E0401

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS # pylint: disable=E1101
else:
    bundle_dir = os.path.dirname(__file__)
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(bundle_dir, 'central_widget.ui'))


class CentralWidget(QtWidgets.QWidget, CLASS_DIALOG):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.connection = None
        self.cursor = None
        self.observers = {}
        self.visits = {}
        self.species = {}
        self.image_directory = ''
        self.image_list = []
        self.observer_id = None
        self.visit_id = None
        self.annotator = None
        self.annotator_dialog = AnnotatorDialog()
        self.annotator_dialog.selected.connect(self.set_annotator)

        self.graphics_scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.graphics_scene)

        self.pushButtonAnnotator.clicked.connect(self.annotator_dialog.show)
        self.pushButtonDatabase.clicked.connect(self.select_database)
        self.pushButtonImport.clicked.connect(self.prep_import)

    def annotator_finished(self):
        self.textBrowser.append('Import Complete.')

    def display_image(self, image, record):
        img = Image.open(image)
        width, height = img.size
        self.graphics_scene.clear()
        self.qImage = ImageQt.ImageQt(img)
        self.graphics_scene.addPixmap(QtGui.QPixmap.fromImage(self.qImage))
        self.graphicsView.fitInView(self.graphics_scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        self.graphicsView.setSceneRect(self.graphics_scene.itemsBoundingRect())

        pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.yellow, QtCore.Qt.SolidPattern), 3)
        font = QtGui.QFont()
        for a in record['annotations']:
            bbox = a['bbox']
            top_left = QtCore.QPointF(bbox['xmin'] * width, bbox['ymin'] * height)
            bottom_right = QtCore.QPointF(bbox['xmax'] * width, bbox['ymax'] * height)
            rect = QtCore.QRectF(top_left, bottom_right)
            graphics_item = self.graphics_scene.addRect(rect, pen)
            font.setPointSize(int(rect.width() * 0.065))
            text = QtWidgets.QGraphicsTextItem(a['label'])
            text.setFont(font)
            text.setPos(rect.topLeft().toPoint())
            text.setDefaultTextColor(QtCore.Qt.yellow)
            x_offset = text.boundingRect().width() / 2.0
            y_offset = text.boundingRect().height() / 2.0
            text.moveBy((rect.width() / 2.0) - x_offset, (rect.height() / 2.0) - y_offset)
            text.setParentItem(graphics_item)

    def prep_import(self):
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

            self.observer_id = float(self.observers[observer])
            self.visit_id = float(self.visits[visit])

            # Start the Annotator
            self.annotator.image_directory = self.image_directory
            self.annotator.image_list = self.image_list
            self.annotator.start()

    def select_database(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Database', '.', 'Microsoft Access Database (*.accdb)')
        if file_name[0] != '':
            self.connection = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + file_name[0])
            self.cursor = self.connection.cursor()

            # Build a simple lookup table
            self.species = {}
            results = self.cursor.execute('SELECT * FROM Species').fetchall()
            for s in results:
                self.species[s[1]] =float(s[0])

            # Build lookup keys and tables for observer and visit id
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
            self.pushButtonImport.setDisabled(False)

    def set_annotator(self, annotator):
        self.annotator = annotator
        self.annotator.progress.connect(self.update_database)
        self.pushButtonDatabase.setDisabled(False)
        self.annotator.finished.connect(self.annotator_finished)
    
    def update_database(self, count, image, rec):
        image_dir = QtCore.QDir.toNativeSeparators(self.image_directory + "/")
        self.textBrowser.append(os.path.join(image_dir, image))
        self.display_image(os.path.join(image_dir, image), rec)
        # Store image
        timestamp = os.path.getctime(os.path.join(self.image_directory, image))
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        self.cursor.execute('INSERT INTO Photos (ImageNum, FileName, ImageDate, FilePath, VisitID) VALUES (?, ?, ?, ?, ?)', (count + 1.0, image, timestamp, image_dir, self.visit_id))
        self.connection.commit()
        id = float(self.cursor.execute('SELECT @@Identity').fetchone()[0])

        # Add species identifications and bounding boxes
        detections = {}
        for a in rec['annotations']:
            bbox = a['bbox']
            XLen = (bbox['xmax'] - bbox['xmin'])
            YLen = (bbox['ymax'] - bbox['ymin'])
            TagX = bbox['xmin'] + (XLen / 2.0)
            TagY = bbox['ymin'] + (YLen / 2.0)
            self.cursor.execute('INSERT INTO PhotoTags (TagX, TagY, XLen, YLen, ImageID, ObsID) values (?, ?, ?, ?, ?, ?)', (TagX, TagY, XLen, YLen, id, self.observer_id))
            if a['label'] not in detections:
                detections[a['label']] = 1.0
            else:
                detections[a['label']] += 1.0
        
        for d in detections.keys():
            self.textBrowser.append("\t{} - {}".format(detections[d], d))
            self.cursor.execute('INSERT INTO Detections (SpeciesID, Individuals, ObsID, ImageID) values (?, ?, ?, ?)', (self.species[d], detections[d], self.observer_id, id))
        self.connection.commit()
        self.textBrowser.append("\n")
            
