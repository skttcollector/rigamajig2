#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: joint_widget.py
    author: masonsmigel
    date: 07/2022
    discription: 

"""


# PYTHON
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

# MAYA
import maya.cmds as cmds

# RIGAMAJIG2
import rigamajig2.maya.joint
import rigamajig2.maya.rig.live as live
import rigamajig2.maya.meta as meta
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, sliderGrp
from rigamajig2.ui.builder_ui import constants
from rigamajig2.maya.builder.builder import SKELETON_POS

# pylint: disable= too-many-instance-attributes
class JointWidget(QtWidgets.QWidget):
    """ Joint layout for the builder UI """

    def __init__(self, builder=None):
        """
        Constructor for the joint widget
        :param builder: builder to connect to the ui
        """
        super(JointWidget, self).__init__()

        self.builder = builder

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        """ Create Widgets"""
        self.mainCollapseableWidget  = collapseableWidget.CollapsibleWidget('Skeleton', addCheckbox=True)

        self.jointPositionPathSelector = pathSelector.PathSelector(
            "joint pos: ",
            caption="Select a Skeleton position file",
            fileFilter=constants.JSON_FILTER,
            fileMode=1
            )
        self.loadJointPositionButton = QtWidgets.QPushButton("Load joints")
        self.saveJointPositionButton = QtWidgets.QPushButton("Save joints")

        self.skeletonEditWidget = collapseableWidget.CollapsibleWidget('Edit Skeleton')
        self.skeletonEditWidget.setHeaderBackground(constants.EDIT_BG_HEADER_COLOR)
        self.skeletonEditWidget.setWidgetBackground(constants.EDIT_BG_WIDGET_COLOR)

        self.jointToRotationButton = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Rotation")
        self.jointToOrientationButton = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Orientation")
        self.cleanSkeletonButton = QtWidgets.QPushButton("Clean Skeleton")
        self.jointAxisXRadioButton = QtWidgets.QRadioButton('x')
        self.jointAxisYRadioButton = QtWidgets.QRadioButton('y')
        self.jointAxisZRadioButton = QtWidgets.QRadioButton('z')
        self.jointAxisXRadioButton.setChecked(True)

        self.mirrorJointModeCheckbox = QtWidgets.QComboBox()
        self.mirrorJointModeCheckbox.setFixedHeight(24)
        self.mirrorJointModeCheckbox.addItem("rotate")
        self.mirrorJointModeCheckbox.addItem("translate")
        self.mirrorJointsButton = QtWidgets.QPushButton(QtGui.QIcon(":kinMirrorJoint_S"), "Mirror")
        self.mirrorJointsButton.setFixedHeight(24)

        self.pinJointsButton = QtWidgets.QPushButton("Pin Joints")
        self.pinJointsButton.setIcon(QtGui.QIcon(":pinned"))
        self.unpinJointsButton = QtWidgets.QPushButton("Un-Pin Joints")
        self.unpinJointsButton.setIcon(QtGui.QIcon(":unpinned"))

        self.unpinAllJointsButton = QtWidgets.QPushButton("Un-Pin All Joints")
        self.unpinAllJointsButton.setIcon(QtGui.QIcon(":unpinned"))

        self.insertJointsAmountSlider = sliderGrp.SliderGroup()
        self.insertJointsAmountSlider.setValue(1)
        self.insertJointsAmountSlider.setRange(1, 10)
        self.insertJointsButton = QtWidgets.QPushButton("Insert Joints")

        self.prepareJointsButton = QtWidgets.QPushButton("Prep Skeleton")

    def createLayouts(self):
        """ Create Layouts"""
        # setup the main layout.
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        saveLoadJointLayout = QtWidgets.QHBoxLayout()
        saveLoadJointLayout.setContentsMargins(0, 0, 0, 0)
        saveLoadJointLayout.setSpacing(4)
        saveLoadJointLayout.addWidget(self.loadJointPositionButton)
        saveLoadJointLayout.addWidget(self.saveJointPositionButton)

        # setup the joint orientation Layout
        jointOrientationLayout = QtWidgets.QHBoxLayout()
        jointOrientationLayout.addWidget(self.jointToRotationButton)
        jointOrientationLayout.addWidget(self.jointToOrientationButton)

        # setup the main mirroe axis joint Layout
        jointMirrorAxisLayout = QtWidgets.QHBoxLayout()
        jointMirrorAxisLayout.addWidget(QtWidgets.QLabel("Axis: "))
        jointMirrorAxisLayout.addWidget(self.jointAxisXRadioButton)
        jointMirrorAxisLayout.addWidget(self.jointAxisYRadioButton)
        jointMirrorAxisLayout.addWidget(self.jointAxisZRadioButton)

        # setup the main mirrr joint Layout
        mirrorJointLayout = QtWidgets.QHBoxLayout()
        mirrorJointLayout.setSpacing(4)
        mirrorJointLayout.addLayout(jointMirrorAxisLayout)
        mirrorJointLayout.addWidget(self.mirrorJointModeCheckbox)
        mirrorJointLayout.addWidget(self.mirrorJointsButton)

        # setup the pin joints layout
        pinJointsLayout = QtWidgets.QHBoxLayout()
        pinJointsLayout.addWidget(self.pinJointsButton)
        pinJointsLayout.addWidget(self.unpinJointsButton)
        pinJointsLayout.addWidget(self.unpinAllJointsButton)

        # setup the insert joints layout
        insertJointLayout = QtWidgets.QHBoxLayout()
        insertJointLayout.addWidget(self.insertJointsAmountSlider)
        insertJointLayout.addWidget(self.insertJointsButton)

        # add widgets to the skeletonEdit widget.
        self.skeletonEditWidget.addWidget(self.cleanSkeletonButton)
        self.skeletonEditWidget.addLayout(jointOrientationLayout)
        self.skeletonEditWidget.addLayout(mirrorJointLayout)
        self.skeletonEditWidget.addLayout(pinJointsLayout)
        self.skeletonEditWidget.addLayout(insertJointLayout)
        self.skeletonEditWidget.addWidget(self.prepareJointsButton)
        self.skeletonEditWidget.addSpacing(3)

        # add widgets to the main skeleton widget.
        self.mainCollapseableWidget .addWidget(self.jointPositionPathSelector)
        self.mainCollapseableWidget .addLayout(saveLoadJointLayout)
        self.mainCollapseableWidget .addWidget(self.skeletonEditWidget)

        # add the widget to the main layout
        self.mainLayout.addWidget(self.mainCollapseableWidget)

    def createConnections(self):
        """ Create Connections"""
        self.loadJointPositionButton.clicked.connect(self.loadJointsPositions)
        self.saveJointPositionButton.clicked.connect(self.saveJointPositions)
        self.jointToRotationButton.clicked.connect(self.jointToRotation)
        self.jointToOrientationButton.clicked.connect(self.jointToOrientation)
        self.mirrorJointsButton.clicked.connect(self.mirrorJoint)
        self.pinJointsButton.clicked.connect(self.pinJoints)
        self.unpinJointsButton.clicked.connect(self.unpinJoints)
        self.unpinAllJointsButton.clicked.connect(self.unpinAllJoints)
        self.insertJointsButton.clicked.connect(self.insertJoints)
        self.prepareJointsButton.clicked.connect(self.prepareSkeleton)

    def setBuilder(self, builder):
        """ Set a builder for widget"""
        rigEnv = builder.getRigEnviornment()
        self.builder = builder
        self.jointPositionPathSelector.setRelativePath(rigEnv)

        # update data within the rig
        jointFile = self.builder.getRigData(self.builder.getRigFile(), SKELETON_POS)
        if jointFile:
            self.jointPositionPathSelector.setPath(jointFile)

    def runWidget(self):
        """ Run this widget from the builder breakpoint runner"""
        self.loadJointsPositions()

    @property
    def isChecked(self):
        """ Check it the widget is checked"""
        return self.mainCollapseableWidget .isChecked()

    # CONNECTIONS
    def loadJointsPositions(self):
        """ load joints and positions"""
        self.builder.loadJoints(self.jointPositionPathSelector.getPath())

    def saveJointPositions(self):
        """ save the joint positions"""
        # TODO add a check about saving a blank scene.
        self.builder.saveJoints(self.jointPositionPathSelector.getPath())

    def pinJoints(self):
        """ Pin selected joints"""
        live.pin()

    def unpinJoints(self):
        """ Unpin selected joints"""
        live.unpin()

    def unpinAllJoints(self):
        """ Unpin all joints"""
        pinnedNodes = meta.getTagged("isPinned")
        live.unpin(pinnedNodes)

    def insertJoints(self):
        """ insert joints between two selected joints"""
        jointAmount = self.insertJointsAmountSlider.getValue()
        selection = cmds.ls(sl=True)
        assert len(selection) == 2, "Must select two joints!"
        rigamajig2.maya.joint.insertJoints(selection[0], selection[-1], amount=jointAmount)

    def prepareSkeleton(self):
        """
        Prepare the skeleton for rig build.
        This ensures channels are all visable and zero out the rotations
        """
        joint.addJointOrientToChannelBox(cmds.ls(sl=True))
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True))

    def mirrorJoint(self):
        """ mirror joint"""
        axis = 'x'
        if self.jointAxisYRadioButton.isChecked():
            axis = 'y'
        if self.jointAxisZRadioButton.isChecked():
            axis = 'z'

        mirrorMode = self.mirrorJointModeCheckbox.currentText()
        for joint in cmds.ls(sl=True):
            joints = cmds.listRelatives(cmds.ls(sl=True, type='joint'), ad=True, type='joint') or []
            rigamajig2.maya.joint.mirror(joints + [joint], axis=axis, mode=mirrorMode)

    def jointToRotation(self):
        """ Convert joint transformation to rotation"""
        rigamajig2.maya.joint.toRotation(cmds.ls(sl=True, type='joint'))

    def jointToOrientation(self):
        """ Convert joint transformation to orientation"""
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True, type='joint'))