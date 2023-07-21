#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: actions.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# PYTHON
import sys
import os
from functools import partial

# MAYA
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from shiboken2 import wrapInstance

# RIGAMJIG
from rigamajig2.maya.builder import constants
import rigamajig2.maya.qc as qc
from rigamajig2.maya import loggers
import rigamajig2.maya.data.abstract_data as abstract_data
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner
import rigamajig2.maya.builder
import rigamajig2.maya.builder.builder as builder
import rigamajig2.ui.builder_ui.recent_files as recent_files


class Actions(object):
    """ Setup the actions for the builder dialog"""

    def __init__(self, dialog):
        """
        This class will setup the actions for the the builder Dialog.
        You must pass in the dialog as the self.dialog parameter

        :param dialog: dialog to connect the actions to
        """
        self.dialog = dialog
        self.createActions()

    def createActions(self):
        """ Create the Actions"""
        # FILE
        self.newRigFileAction = QtWidgets.QAction("New Rig File", self.dialog)
        self.newRigFileAction.setIcon(QtGui.QIcon(":fileNew.png"))
        self.newRigFileAction.triggered.connect(self.createRigEnviornment)

        self.loadRigFileAction = QtWidgets.QAction("Load Rig File", self.dialog)
        self.loadRigFileAction.setIcon(QtGui.QIcon(":folder-open.png"))
        self.loadRigFileAction.triggered.connect(self.loadRigFile)

        self.saveRigFileAction = QtWidgets.QAction("Save Rig File", self.dialog)
        self.saveRigFileAction.setIcon(QtGui.QIcon(":save.png"))
        self.saveRigFileAction.triggered.connect(self.saveRigFile)

        # add a submenu to load recent rigFiles
        self.recentRigFileMenu = QtWidgets.QMenu("Recent Rig Files ...", self.dialog)
        self.recentRigFileMenu.setIcon(QtGui.QIcon(":out_time.png"))
        self.updateRecentFiles()

        self.reloadRigFileAction = QtWidgets.QAction("Reload Rig File", self.dialog)
        self.reloadRigFileAction.setIcon(QtGui.QIcon(":refresh.png"))
        self.reloadRigFileAction.triggered.connect(self.reloadRigFile)

        # UTILS
        self.reloadRigamajigModulesAction = QtWidgets.QAction("Reload Rigamajig2 Modules", self.dialog)
        self.reloadRigamajigModulesAction.triggered.connect(self.reloadRigamajigModules)

        self.mergeRigFilesAction = QtWidgets.QAction("Merge Rig Files", self.dialog)
        self.mergeRigFilesAction.triggered.connect(self.showMergeRigFilesDialog)

        self.setLoggingLevelMenu = QtWidgets.QMenu("Set Logging Level", self.dialog)

        # Add actions to the menu to set the logging level to each stage
        level = 10
        for levels in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            loggingLevelAction = QtWidgets.QAction(levels, self.setLoggingLevelMenu)
            loggingLevelAction.triggered.connect(partial(loggers.setLoggingLevel, level))
            self.setLoggingLevelMenu.addAction(loggingLevelAction)
            level += 10

        self.devModeAction = QtWidgets.QAction("Dev Mode", self.dialog)
        self.devModeAction.setCheckable(True)

        # TOOLS
        self.runPerformanceTestAction = QtWidgets.QAction("Run Performance Test", self.dialog)
        self.runPerformanceTestAction.triggered.connect(self.runPerformanceTest)

        self.generateRandomAnimationAction = QtWidgets.QAction("Generate Random Animation", self.dialog)
        self.generateRandomAnimationAction.triggered.connect(self.generateRandomAnimation)

        self.openProfilerAction = QtWidgets.QAction("Profiler", self.dialog)
        self.openProfilerAction.triggered.connect(self.openProfiler)

        self.openEvaluationToolkitAction = QtWidgets.QAction("Evaluation Toolkit", self.dialog)
        self.openEvaluationToolkitAction.triggered.connect(self.openEvaluationToolkit)

        # HELP
        self.showDocumentationAction = QtWidgets.QAction("Documentation", self.dialog)
        self.showDocumentationAction.triggered.connect(self.showDocumentation)

        self.showAboutAction = QtWidgets.QAction("About", self.dialog)
        self.showAboutAction.triggered.connect(self.showAbout)

    def createRigEnviornment(self):
        """ Create Rig Enviornment"""
        createDialog = CreateRigEnvDialog()
        createDialog.newRigEnviornmentCreated.connect(self.dialog.setRigFile)
        createDialog.showDialog()

    def loadRigFile(self):
        """ Load a rig file"""
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
        fileDialog.setNameFilters(["Rig Files (*.rig)"])

        result = fileDialog.exec_()

        if result:
            rigfile = fileDialog.selectedFiles()[0]
            self.dialog.setRigFile(rigfile)
            recent_files.addRecentFile(rigfile)
            self.updateRecentFiles()

    def loadRecentRigFile(self, rigfile):
        self.dialog.setRigFile(rigfile)

        # lets re-add the recent file. This will just move it to the top of the list. Then update the list
        recent_files.addRecentFile(rigfile)
        self.updateRecentFiles()

    def saveRigFile(self):
        """ Save out a rig file """
        data = abstract_data.AbstractData()
        data.read(self.dialog.rigFile)
        newData = data.getData()

        # Save the main feilds
        newData[constants.RIG_NAME] = self.dialog.assetNameLineEdit.text()

        newData[constants.MODEL_FILE] = self.dialog.modelWidget.modelPathSelector.getPath(absoultePath=False)
        newData[constants.SKELETON_POS] = self.dialog.jointWidget.jointPositionDataLoader.getFileList()
        newData[constants.GUIDES] = self.dialog.intalizeWidget.guideDataLoader.getFileList()
        newData[constants.COMPONENTS] = self.dialog.intalizeWidget.componentsDataLoader.getFileList()
        newData[constants.PSD] = self.dialog.buildWidget.psdDataLoader.getFileList()
        newData[constants.CONTROL_SHAPES] = self.dialog.controlsWidget.controlDataLoader.getFileList()
        newData[constants.DEFORM_LAYERS] = self.dialog.deformationWidget.deformLayerPathSelector.getPath(
            absoultePath=False)
        newData[constants.SKINS] = self.dialog.deformationWidget.skinPathSelector.getPath(absoultePath=False)
        newData[constants.SHAPES] = self.dialog.deformationWidget.SHAPESPathSelector.getPath(absoultePath=False)
        newData[constants.OUTPUT_RIG] = self.dialog.publishWidget.outPathSelector.getPath(absoultePath=False)
        newData[constants.OUTPUT_RIG_FILE_TYPE] = self.dialog.publishWidget.outFileTypeComboBox.currentText()
        newData[constants.OUTPUT_FILE_SUFFIX] = self.dialog.publishWidget.outFileSuffix.text()

        # setup new data for the scripts
        preScripts = self.dialog.modelWidget.preScriptRunner.getCurrentScriptList(
            relativePath=self.dialog.rigEnviornment)
        postScripts = self.dialog.buildWidget.postScriptRunner.getCurrentScriptList(
            relativePath=self.dialog.rigEnviornment)
        pubScripts = self.dialog.publishWidget.pubScriptRunner.getCurrentScriptList(
            relativePath=self.dialog.rigEnviornment)
        newData[constants.PRE_SCRIPT] = preScripts
        newData[constants.POST_SCRIPT] = postScripts
        newData[constants.PUB_SCRIPT] = pubScripts

        data.setData(newData)
        data.write(self.dialog.rigFile)
        builder.logger.info("data saved to : {}".format(self.dialog.rigFile))

    def reloadRigFile(self):
        """ Reload rig file"""
        self.dialog.setRigFile(self.dialog.rigFile)

    def updateRecentFiles(self):
        """Update the recent file menu based on our recent file list"""

        # clear the recent file menu
        self.recentRigFileMenu.clear()

        # add any new recent files to the submenu
        for recentFile in recent_files.getRecentFileList():
            openRecentFileAction = QtWidgets.QAction(recentFile, self.recentRigFileMenu)
            openRecentFileAction.triggered.connect(partial(self.loadRecentRigFile, recentFile))

            self.recentRigFileMenu.addAction(openRecentFileAction)

    # TOOLS MENU
    def runPerformanceTest(self):
        """ Run Performance tests"""
        qc.runPerformanceTest()

    def generateRandomAnimation(self):
        """ Generate Random animation"""
        qc.generateRandomAnim()

    def openProfiler(self):
        mel.eval("ProfilerTool;")

    def openEvaluationToolkit(self):
        mel.eval("openEvaluationToolkit;")

    def reloadRigamajigModules(self):
        """ Reload riamajig modules"""
        import rigamajig2
        rigamajig2.reloadModule(log=True)

    def showMergeRigFilesDialog(self):
        """ Show the merge rig files dialog"""
        from rigamajig2.ui.builder_ui import mergeRigs_dialog

        mergeRigs_dialog.MergeRigsDialog.showDialog()

    # SHOW HELP
    def showDocumentation(self):
        """ Open Documentation"""
        pass

    def showAbout(self):
        """ Show about"""
        pass


class CreateRigEnvDialog(QtWidgets.QDialog):
    """ Create new rig environment dialog"""
    WINDOW_TITLE = "Create Rig Enviornment"

    newRigEnviornmentCreated = QtCore.Signal(str)

    rigFileResult = None

    def showDialog(self):
        """ Show the dialog"""
        self.exec_()

    def __init__(self):
        """ Constructor for the rig file creation"""
        if sys.version_info.major < 3:
            mayaMainWindow = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            mayaMainWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(CreateRigEnvDialog, self).__init__(mayaMainWindow)
        self.rigEnviornment = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedSize(375, 135)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.updateCreateMethod()

    def createWidgets(self):
        """ Create Widgets"""
        self.fromArchetypeRadioButton = QtWidgets.QRadioButton("New From Archetype")
        self.fromExistingRadioButton = QtWidgets.QRadioButton("Clone Existing")
        self.fromArchetypeRadioButton.setChecked(True)

        self.archetypeRadioButtonWidget = QtWidgets.QWidget()
        self.archetypeRadioButtonWidget.setFixedHeight(25)
        self.archetypeComboBox = QtWidgets.QComboBox()
        for archetype in rigamajig2.maya.builder.core.getAvailableArchetypes():
            self.archetypeComboBox.addItem(archetype)

        self.sourcePath = pathSelector.PathSelector("Source:", fileMode=2)
        self.destinationPath = pathSelector.PathSelector("New Env:", fileMode=2)
        self.rigNameLineEdit = QtWidgets.QLineEdit()
        self.rigNameLineEdit.setPlaceholderText("rig_name")

        self.createButton = QtWidgets.QPushButton("Create")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

    def createLayouts(self):
        """ Create Layouts"""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(6, 6, 6, 6)
        mainLayout.setSpacing(4)

        radioButtonLayout = QtWidgets.QHBoxLayout()
        radioButtonLayout.addSpacing(15)
        radioButtonLayout.addWidget(self.fromArchetypeRadioButton)
        radioButtonLayout.addWidget(self.fromExistingRadioButton)

        archetypeRadioButtonLayout = QtWidgets.QHBoxLayout(self.archetypeRadioButtonWidget)
        archetypeRadioButtonLayout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel("Archetype:")
        label.setFixedWidth(60)
        archetypeRadioButtonLayout.addWidget(label)
        archetypeRadioButtonLayout.addWidget(self.archetypeComboBox)

        rigNameLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Rig Name:")
        label.setFixedWidth(60)
        rigNameLayout.addWidget(label)
        rigNameLayout.addWidget(self.rigNameLineEdit)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.createButton)

        mainLayout.addLayout(radioButtonLayout)
        mainLayout.addWidget(self.archetypeRadioButtonWidget)
        mainLayout.addWidget(self.sourcePath)
        mainLayout.addWidget(self.destinationPath)
        mainLayout.addLayout(rigNameLayout)
        mainLayout.addLayout(buttonLayout)

    def createConnections(self):
        """ Create Connections"""
        self.fromArchetypeRadioButton.toggled.connect(self.updateCreateMethod)
        self.fromExistingRadioButton.toggled.connect(self.updateCreateMethod)

        self.cancelButton.clicked.connect(self.close)
        self.createButton.clicked.connect(self.createNewRigEnviornment)

    def updateCreateMethod(self):
        """
        Update the UI creation method
        :return:
        """
        if self.fromArchetypeRadioButton.isChecked():
            self.archetypeRadioButtonWidget.setVisible(True)
            self.sourcePath.setVisible(False)
        else:
            self.archetypeRadioButtonWidget.setVisible(False)
            self.sourcePath.setVisible(True)

    def createNewRigEnviornment(self):
        """
        Create a new rig enviornment
        """

        destinationRigEnviornment = self.destinationPath.getPath()
        rigName = self.rigNameLineEdit.text()
        if self.fromArchetypeRadioButton.isChecked():
            archetype = self.archetypeComboBox.currentText()
            rigFile = rigamajig2.maya.builder.core.newRigEnviornmentFromArchetype(
                newEnv=destinationRigEnviornment,
                archetype=archetype,
                rigName=rigName)
        else:
            sourceEnviornment = self.sourcePath.getPath()
            rigFile = rigamajig2.maya.builder.core.createRigEnviornment(
                sourceEnviornment=sourceEnviornment,
                targetEnviornment=destinationRigEnviornment,
                rigName=rigName)
        self.newRigEnviornmentCreated.emit(rigFile)

        self.close()
