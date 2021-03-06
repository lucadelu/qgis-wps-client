# -*- coding: latin1 -*-
"""
 /***************************************************************************
   QGIS Web Processing Service Plugin
  -------------------------------------------------------------------
 Date                 : 09 November 2009
 Copyright            : (C) 2009 by Dr. Horst Duester
 email                : horst dot duester at kappasys dot ch

  ***************************************************************************
  *                                                                         *
  *   This program is free software; you can redistribute it and/or modify  *
  *   it under the terms of the GNU General Public License as published by  *
  *   the Free Software Foundation; either version 2 of the License, or     *
  *   (at your option) any later version.                                   *
  *                                                                         *
  ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qgis.core import *
from __init__ import version
from wpslib.wpsserver import WpsServer
from Ui_qgswpsgui import Ui_QgsWps
from qgswpsbookmarks import Bookmarks
from doAbout import DlgAbout
import os
import sys
import string


class QgsWpsGui(QDialog, QObject, Ui_QgsWps):
    MSG_BOX_TITLE = "WPS"

    getDescription = pyqtSignal(str, QTreeWidgetItem)
    newServer = pyqtSignal()
    editServer = pyqtSignal(str)
    deleteServer = pyqtSignal(str)
    connectServer = pyqtSignal()
    addDefaultServer = pyqtSignal()
    requestDescribeProcess = pyqtSignal(str, str)

    def __init__(self, parent, fl):
        QDialog.__init__(self, parent, fl)
        self.setupUi(self)
        self.fl = fl
        self.setWindowTitle('QGIS WPS-Client ' + version())
        self.dlgAbout = DlgAbout(parent)

    def initQgsWpsGui(self):
##      self.btnOk.setEnabled(False)
        self.btnConnect.setEnabled(False)
        settings = QSettings()
        settings.beginGroup("WPS")
        connections = settings.childGroups()
        self.cmbConnections.clear()
        self.cmbConnections.addItems(connections)
        self.treeWidget.clear()

        if self.cmbConnections.size() > 0:
            self.btnConnect.setEnabled(True)
            self.btnEdit.setEnabled(True)
            self.btnDelete.setEnabled(True)
        return 1

    def getBookmark(self, item):
        self.requestDescribeProcess.emit( item.text(0), item.text(1) )

    def on_buttonBox_rejected(self):
        self.close()

    # see http://www.riverbankcomputing.com/Docs/PyQt4/pyqt4ref.html#connecting-signals-and-slots
    # without this magic, the on_btnOk_clicked will be called two times: one clicked() and one clicked(bool checked)
    @pyqtSignature("on_buttonBox_accepted()")          
    def on_buttonBox_accepted(self):
        if  self.treeWidget.topLevelItemCount() == 0:
            QMessageBox.warning(None, 'WPS Warning','No Service connected!')
        else:
            self.getDescription.emit(self.cmbConnections.currentText(),
                                     self.treeWidget.currentItem())
    
    # see http://www.riverbankcomputing.com/Docs/PyQt4/pyqt4ref.html#connecting-signals-and-slots
    # without this magic, the on_btnOk_clicked will be called two times: one clicked() and one clicked(bool checked)
    @pyqtSignature("on_btnConnect_clicked()")       
    def on_btnConnect_clicked(self):
        self.treeWidget.clear()
        selectedWPS = self.cmbConnections.currentText()
        self.server = WpsServer.getServer(selectedWPS)
        self.server.capabilitiesRequestFinished.connect(self.createCapabilitiesGUI)
        self.server.requestCapabilities()

    @pyqtSignature("on_btnBookmarks_clicked()")
    def on_btnBookmarks_clicked(self):
        self.dlgBookmarks = Bookmarks(self.fl)
        QObject.connect(self.dlgBookmarks,
                        SIGNAL("getBookmarkDescription(QTreeWidgetItem)"),
                        self.getBookmark)
        QObject.connect(self.dlgBookmarks,
                        SIGNAL("bookmarksChanged()"), self,
                        SIGNAL("bookmarksChanged()"))
        self.dlgBookmarks.show()

    @pyqtSignature("on_btnNew_clicked()")
    def on_btnNew_clicked(self):
        self.newServer.emit()

    @pyqtSignature("on_btnEdit_clicked()")
    def on_btnEdit_clicked(self):
        self.editServer.emit(self.cmbConnections.currentText())

    @pyqtSignature("on_cmbConnections_currentIndexChanged()")
    def on_cmbConnections_currentIndexChanged(self):
        pass

    @pyqtSignature("on_btnDelete_clicked()")
    def on_btnDelete_clicked(self):
        self.deleteServer.emit(self.cmbConnections.currentText())

    @pyqtSignature("on_pushDefaultServer_clicked()")
    def on_pushDefaultServer_clicked(self):
        self.addDefaultServer.emit()

    def initTreeWPSServices(self, taglist):
        self.treeWidget.setColumnCount(self.treeWidget.columnCount())
        itemList = []
        for items in taglist:
            item = QTreeWidgetItem()
            ident = items[0]
            title = items[1]
            abstract = items[2]
            item.setText(0, ident.strip())
            item.setText(1, title.strip())
            item.setText(2, abstract.strip())
            itemList.append(item)
        self.treeWidget.addTopLevelItems(itemList)

    @pyqtSignature("on_btnAbout_clicked()")
    def on_btnAbout_clicked(self):
        self.dlgAbout.show()
        pass

    @pyqtSignature("QTreeWidgetItem*, int")
    def on_treeWidget_itemDoubleClicked(self, item, column):
        self.getDescription.emit(self.cmbConnections.currentText(),
                                 self.treeWidget.currentItem())

    def createCapabilitiesGUI(self):
        try:
            self.treeWidget.clear()
            itemListAll = self.server.parseCapabilitiesXML()
            self.initTreeWPSServices(itemListAll)
        except:
            pass
