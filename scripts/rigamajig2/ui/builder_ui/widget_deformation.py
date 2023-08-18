#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: widget_deformation.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""
# MAYA
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# RIGAMAJIG2
import rigamajig2.maya.builder.constants
from rigamajig2.shared import common
from rigamajig2.ui.builder_ui.widgets import pathSelector, collapseableWidget
from rigamajig2.ui.builder_ui import style
from rigamajig2.maya.builder.constants import SKINS, PSD, SHAPES, DEFORM_LAYERS
from rigamajig2.maya.rig import deformLayer
from rigamajig2.maya import skinCluster


class DeformationWidget(QtWidgets.QWidget):
    """ Deformation layout for the builder UI """

    def __init__(self, builder=None):
        """
       Constructor for the deformation widget
       :param builder: builder to connect to the ui
       """
        super(DeformationWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets"""
        self.mainCollapseableWidget = collapseableWidget.CollapsibleWidget('Deformations', addCheckbox=True)

        self.deformLayerPathSelector = pathSelector.PathSelector(
            "layers:",
            caption='Select a deformationLayer file',
            fileFilter=common.JSON_FILTER,
            fileMode=1)

        self.loadDeformLayersButton = QtWidgets.QPushButton("Load Deform Layers")
        self.loadDeformLayersButton.setIcon(QtGui.QIcon(common.getIcon("loadDeformLayers.png")))
        self.saveDeformLayersButton = QtWidgets.QPushButton("Save Deform Layers")
        self.saveDeformLayersButton.setIcon(QtGui.QIcon(common.getIcon("saveDeformLayers.png")))

        self.addDeformLayersWidget = collapseableWidget.CollapsibleWidget('Add deformation Layers')
        self.addDeformLayersWidget.setHeaderBackground(style.EDIT_BG_HEADER_COLOR)
        self.addDeformLayersWidget.setDarkPallete()
        self.suffixLineEdit = QtWidgets.QLineEdit()
        self.suffixLineEdit.setPlaceholderText("suffix")

        self.combineMthodComboBox = QtWidgets.QComboBox()
        for item in deformLayer.CONNECTION_METHOD_LIST:
            self.combineMthodComboBox.addItem(item)
        self.addDeformLayerButton = QtWidgets.QPushButton("Add Deform Layer")
        self.connectToMainMeshButton = QtWidgets.QPushButton("Connect to Model")

        self.skinPathSelector = pathSelector.PathSelector(
            "skin:",
            caption="Select the skin weight folder",
            fileFilter=common.JSON_FILTER,
            fileMode=2)
        self.loadAllSkinButton = QtWidgets.QPushButton("Load All Skins")
        self.loadAllSkinButton.setIcon(QtGui.QIcon(common.getIcon("loadSkincluster.png")))
        self.loadSingleSkinButton = QtWidgets.QPushButton("Load Skin")
        self.loadSingleSkinButton.setIcon(QtGui.QIcon(common.getIcon("loadSkincluster.png")))
        self.saveSkinsButton = QtWidgets.QPushButton("Save Skin")
        self.saveSkinsButton.setIcon(QtGui.QIcon(common.getIcon("saveSkincluster.png")))

        self.loadDeformLayersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveDeformLayersButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadAllSkinButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadSingleSkinButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveSkinsButton.setFixedHeight(style.LARGE_BTN_HEIGHT)

        self.loadAllSkinButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.loadSingleSkinButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveSkinsButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.loadDeformLayersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.saveDeformLayersButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

        self.skinEditWidget = collapseableWidget.CollapsibleWidget('Edit Skin Cluster')
        self.skinEditWidget.setHeaderBackground(style.EDIT_BG_HEADER_COLOR)
        self.skinEditWidget.setDarkPallete()

        self.copySkinWeightsButton = QtWidgets.QPushButton("Copy Skin Weights and Influences")
        self.copySkinWeightsButton.setIcon(QtGui.QIcon(":copySkinWeight"))
        self.connectBpmsButton = QtWidgets.QPushButton("Connect BPMs on Skins")


        self.SHAPESPathSelector = pathSelector.PathSelector(
            "SHAPES:",
            caption="Select a SHAPES Node Setup",
            fileFilter=rigamajig2.shared.common.MEL_FILTER,
            fileMode=2)
        self.saveSHAPESButton = QtWidgets.QPushButton("Save SHAPES Setup")
        self.saveSHAPESButton.setIcon(QtGui.QIcon(common.getIcon("saveShapesSetup.png")))
        self.loadSHAPESButton = QtWidgets.QPushButton("Load SHAPES Setup")
        self.loadSHAPESButton.setIcon(QtGui.QIcon(common.getIcon("loadShapesSetup.png")))

        self.saveSHAPESButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.saveSHAPESButton.setIconSize(style.LARGE_BTN_ICON_SIZE)
        self.loadSHAPESButton.setFixedHeight(style.LARGE_BTN_HEIGHT)
        self.loadSHAPESButton.setIconSize(style.LARGE_BTN_ICON_SIZE)

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        deformLayerLayout = QtWidgets.QHBoxLayout()
        deformLayerLayout.setContentsMargins(0, 0, 0, 0)
        deformLayerLayout.setSpacing(4)
        deformLayerLayout.addWidget(self.loadDeformLayersButton)
        deformLayerLayout.addWidget(self.saveDeformLayersButton)

        # add the deformation layers back to the collapseable widget
        self.mainCollapseableWidget.addWidget(self.deformLayerPathSelector)
        self.mainCollapseableWidget.addLayout(deformLayerLayout)
        self.mainCollapseableWidget.addWidget(self.addDeformLayersWidget)

        addDeformLayersLayout = QtWidgets.QHBoxLayout()
        addDeformLayersLayout.addWidget(self.suffixLineEdit)
        addDeformLayersLayout.addWidget(self.combineMthodComboBox)
        addDeformLayersLayout.addWidget(self.addDeformLayerButton)

        self.addDeformLayersWidget.addLayout(addDeformLayersLayout)
        self.addDeformLayersWidget.addWidget(self.connectToMainMeshButton)
        self.addDeformLayersWidget.addSpacing(4)

        self.mainCollapseableWidget.addSpacing(10)

        skinButtonLayout = QtWidgets.QHBoxLayout()
        skinButtonLayout.setContentsMargins(0, 0, 0, 0)
        skinButtonLayout.setSpacing(4)
        skinButtonLayout.addWidget(self.loadAllSkinButton)
        skinButtonLayout.addWidget(self.loadSingleSkinButton)
        skinButtonLayout.addWidget(self.saveSkinsButton)

        # add the skin layers back to the collapseable widget
        self.mainCollapseableWidget.addWidget(self.skinPathSelector)
        self.mainCollapseableWidget.addLayout(skinButtonLayout)

        self.mainCollapseableWidget.addWidget(self.skinEditWidget)
        self.skinEditWidget.addWidget(self.copySkinWeightsButton)
        self.skinEditWidget.addWidget(self.connectBpmsButton)
        self.skinEditWidget.addSpacing(4)

        self.mainCollapseableWidget.addSpacing(10)
        self.mainCollapseableWidget.addWidget(self.SHAPESPathSelector)

        # SHAPES layout
        SHAPESButtonLayout = QtWidgets.QHBoxLayout()
        SHAPESButtonLayout.setContentsMargins(0, 0, 0, 0)
        SHAPESButtonLayout.setSpacing(4)
        SHAPESButtonLayout.addWidget(self.loadSHAPESButton)
        SHAPESButtonLayout.addWidget(self.saveSHAPESButton)
        self.mainCollapseableWidget.addLayout(SHAPESButtonLayout)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections"""
        self.loadDeformLayersButton.clicked.connect(self.loadDeformLayers)
        self.saveDeformLayersButton.clicked.connect(self.saveDeformLayers)
        self.addDeformLayerButton.clicked.connect(self.addDeformLayer)
        self.connectToMainMeshButton.clicked.connect(self.connectDeformMesh)

        self.loadAllSkinButton.clicked.connect(self.loadAllSkins)
        self.loadSingleSkinButton.clicked.connect(self.loadSingleSkin)
        self.saveSkinsButton.clicked.connect(self.saveSkin)
        self.copySkinWeightsButton.clicked.connect(self.copySkinWeights)
        self.connectBpmsButton.clicked.connect(self.connectBindPreMatrix)
        self.saveSHAPESButton.clicked.connect(self.saveSHAPESData)
        self.loadSHAPESButton.clicked.connect(self.loadSHAPESData)

    def setBuilder(self, builder):
        """ Set a builder for intialize widget"""
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.deformLayerPathSelector.setRelativePath(rigEnv)
        self.skinPathSelector.setRelativePath(rigEnv)
        self.SHAPESPathSelector.setRelativePath(rigEnv)

        # update data within the rig
        deformLayerFile = self.builder.getRigData(self.builder.getRigFile(), DEFORM_LAYERS)
        self.deformLayerPathSelector.selectPath(deformLayerFile)

        skinFile = self.builder.getRigData(self.builder.getRigFile(), SKINS)
        self.skinPathSelector.selectPath(skinFile)

        SHAPESFile = self.builder.getRigData(self.builder.getRigFile(), SHAPES)
        self.SHAPESPathSelector.selectPath(SHAPESFile)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.loadDeformLayers()
        self.loadAllSkins()
        self.loadSHAPESData()

    @property
    def isChecked(self):
        """ Check it the widget is checked"""
        return self.mainCollapseableWidget.isChecked()

    # CONNECTIONS
    def loadDeformLayers(self):
        """ Save load pose reader setup from json using the builder """
        self.builder.loadDeformationLayers(self.deformLayerPathSelector.getPath())

    def saveDeformLayers(self):
        """ Save pose reader setup to json using the builder """
        self.builder.saveDeformationLayers(self.deformLayerPathSelector.getPath())

    def loadAllSkins(self):
        """Load all skin weights in the given folder"""
        self.builder.loadSkinWeights(self.skinPathSelector.getPath())

    def loadSingleSkin(self):
        """Load a single skin file"""
        import rigamajig2.maya.builder.data
        path = cmds.fileDialog2(dialogStyle=2,
                                caption="Select a skin file",
                                fileFilter=common.JSON_FILTER,
                                okc="Select",
                                dir=self.skinPathSelector.getPath())
        if path:
            rigamajig2.maya.builder.data.loadSingleSkin(path[0])

    def saveSkin(self):
        """Save the skin weights"""
        self.builder.saveSkinWeights(path=self.skinPathSelector.getPath())

    def copySkinWeights(self):
        """ Copy Skin weights"""
        src = cmds.ls(sl=True)[0]
        dst = cmds.ls(sl=True)[1:]
        skinCluster.copySkinClusterAndInfluences(src, dst)

    def connectBindPreMatrix(self):
        """
        Connect influence joints to their respective bindPreMatrix
        """
        for mesh in cmds.ls(sl=True):
            sc = skinCluster.getSkinCluster(mesh)
            skinCluster.connectExistingBPMs(sc)

    def loadSHAPESData(self):
        self.builder.loadSHAPESData(self.SHAPESPathSelector.getPath())

    def saveSHAPESData(self):
        self.builder.saveSHAPESData(self.SHAPESPathSelector.getPath())

    def addDeformLayer(self):
        """
        add a new deformation layer to the selected object
        :return:
        """
        suffix = self.suffixLineEdit.text()
        connectionMethod = self.combineMthodComboBox.currentText()

        # create a new deformation layer
        for node in cmds.ls(sl=True):
            layers = deformLayer.DeformLayer(node)
            layers.createDeformLayer(suffix=suffix, connectionMethod=connectionMethod)

    def connectDeformMesh(self):
        """
        Connect deformation layers to the main deform layer
        :return:
        """
        for s in cmds.ls(sl=True):
            layer = deformLayer.DeformLayer(s)
            layer.connectToModel()
