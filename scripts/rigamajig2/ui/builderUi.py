"""
This file contains the UI for the main rig builder
"""
import sys
import logging
import os
from collections import OrderedDict

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import rigamajig2.shared.common as common
from rigamajig2.ui.widgets import pathSelector, collapseableWidget, scriptRunner, componentManager, overrideColorer
import rigamajig2.maya.rig.builder as builder
import rigamajig2.maya.data.abstract_data as abstract_data

logger = logging.getLogger(__name__)
logger.setLevel(5)

MAYA_FILTER = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
JSON_FILTER = "Json Files (*.json)"

LARGE_BTN_HEIGHT = 35


class RigamajigBuilderUi(QtWidgets.QDialog):
    WINDOW_TITLE = "Rigamajig2 Builder"

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = RigamajigBuilderUi()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self):
        if sys.version_info.major < 3:
            maya_main_window = wrapInstance(long(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        else:
            maya_main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

        super(RigamajigBuilderUi, self).__init__(maya_main_window)
        self.rig_env = None

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setProperty("saveWindowPref", True)
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(375, 825)

        self.create_actions()
        self.create_menus()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        # FILE
        self.load_rig_file_action = QtWidgets.QAction("Load Rig File", self)
        self.load_rig_file_action.triggered.connect(self.load_rig_file)

        self.save_rig_file_action = QtWidgets.QAction("Save Rig File", self)
        self.save_rig_file_action.triggered.connect(self.save_rig_file)

        # UTILS
        # ...

        # HELP
        self.show_documentation_action = QtWidgets.QAction("Documentation", self)
        self.show_documentation_action.triggered.connect(self.show_documentation)

        self.show_about_action = QtWidgets.QAction("About", self)
        self.show_about_action.triggered.connect(self.show_about)

    def create_menus(self):
        """create menu actions"""
        self.main_menu = QtWidgets.QMenuBar()

        file_menu = self.main_menu.addMenu("File")
        file_menu.addAction(self.load_rig_file_action)
        file_menu.addAction(self.save_rig_file_action)

        utils_menu = self.main_menu.addMenu("Utils")
        tools_menu = self.main_menu.addMenu("Tools")

        help_menu = self.main_menu.addMenu("Help")
        help_menu.addAction(self.show_documentation_action)
        help_menu.addAction(self.show_about_action)

    def create_widgets(self):
        self.rig_path_selector = pathSelector.PathSelector(cap='Select a Rig File', ff="Rig Files (*.rig)", fm=1)

        self.create_rig_env_btn = QtWidgets.QPushButton("Create rig env")
        self.create_rig_env_btn.setToolTip("Create a new rig enviornment from scratch")

        self.clone_rig_env_btn = QtWidgets.QPushButton("Clone rig env")
        self.create_rig_env_btn.setToolTip("Create a new rig enviornment from an existing enviornment")

        # Pre- script section
        self.preScript_wdgt = collapseableWidget.CollapsibleWidget('Pre-Script')
        self.preScript_scriptRunner = scriptRunner.ScriptRunner()

        # Model Section
        self.model_wdgt = collapseableWidget.CollapsibleWidget('Model')
        self.model_path_selector = pathSelector.PathSelector("model:", cap="Select a Model file", ff=MAYA_FILTER, fm=1)
        self.import_model_btn = QtWidgets.QPushButton('Import Model')
        self.open_model_btn = QtWidgets.QPushButton('Open Model')
        self.open_model_btn.setFixedWidth(100)

        # Skeleton Section
        self.skeleton_wdgt = collapseableWidget.CollapsibleWidget('Skeleton')
        self.skel_path_selector = pathSelector.PathSelector("skeleton:", cap="Select a Skeleton file", ff=MAYA_FILTER,
                                                            fm=1)
        self.joint_pos_path_selector = pathSelector.PathSelector("joint pos: ", cap="Select a Skeleton position file",
                                                                 ff=JSON_FILTER, fm=1)
        self.import_skeleton_btn = QtWidgets.QPushButton("Import skeleton")
        self.save_skeleton_btn = QtWidgets.QPushButton("Save skeleton")
        self.load_jnt_pos_btn = QtWidgets.QPushButton("Load joint pos")
        self.save_jnt_pos_btn = QtWidgets.QPushButton("Save joint pos")
        self.import_load_skeleton_btn = QtWidgets.QPushButton("Import and Load Joint Positions")
        self.import_load_skeleton_btn.setFixedHeight(LARGE_BTN_HEIGHT)

        self.skeletonEdit_wdgt = collapseableWidget.CollapsibleWidget('Edit Skeleton')
        self.jnt_to_rot_btn = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Rotation")
        self.jnt_to_ori_btn = QtWidgets.QPushButton(QtGui.QIcon(":orientJoint"), "To Orientation")
        self.jntAxisX_rb = QtWidgets.QRadioButton('x')
        self.jntAxisX_rb.setChecked(True)
        self.jntAxisY_rb = QtWidgets.QRadioButton('y')
        self.jntAxisZ_rb = QtWidgets.QRadioButton('z')

        self.mirrorJntMode_cbox = QtWidgets.QComboBox()
        self.mirrorJntMode_cbox.setFixedHeight(24)
        self.mirrorJntMode_cbox.addItem("rotate")
        self.mirrorJntMode_cbox.addItem("translate")
        self.mirrorJnt_btn = QtWidgets.QPushButton(QtGui.QIcon(":kinMirrorJoint_S"), "Mirror")
        self.mirrorJnt_btn.setFixedHeight(24)

        # Component Section
        self.cmpt_wdgt = collapseableWidget.CollapsibleWidget('Components')
        self.cmpt_manager = componentManager.ComponentManager()
        self.initalize_all_btn = QtWidgets.QPushButton("Initalize All Components ")
        self.initalize_all_btn.setFixedHeight(LARGE_BTN_HEIGHT)

        self.guide_path_selector = pathSelector.PathSelector("guides:", cap="Select a guide file", ff=JSON_FILTER, fm=1)
        self.load_guides_btn = QtWidgets.QPushButton("Load Guides")
        self.save_guides_btn = QtWidgets.QPushButton("Save Guides")

        self.build_rig_btn = QtWidgets.QPushButton("Build")
        self.connect_rig_btn = QtWidgets.QPushButton("Connect")
        self.finalize_rig_btn = QtWidgets.QPushButton("Finalize")
        self.complete_build_btn = QtWidgets.QPushButton("Full Build")
        self.complete_build_btn.setFixedHeight(LARGE_BTN_HEIGHT)

        # Post - script section
        self.postScript_wdgt = collapseableWidget.CollapsibleWidget('Post-Script')
        self.postScript_scriptRunner = scriptRunner.ScriptRunner()

        # Control Shape Section
        self.ctlShape_wdgt = collapseableWidget.CollapsibleWidget('Controls')
        self.ctl_path_selector = pathSelector.PathSelector("Controls:", cap="Select a Control Shape file",
                                                           ff=JSON_FILTER,
                                                           fm=1)
        self.load_color_cb = QtWidgets.QCheckBox()
        self.load_color_cb.setChecked(True)
        self.load_color_cb.setFixedWidth(25)
        self.load_ctl_btn = QtWidgets.QPushButton("Load Controls")
        self.save_ctl_btn = QtWidgets.QPushButton("Save Controls")

        self.controlEdit_wgt = collapseableWidget.CollapsibleWidget('Edit Controls')

        self.ctlAxisX_rb = QtWidgets.QRadioButton('x')
        self.ctlAxisX_rb.setChecked(True)
        self.ctlAxisY_rb = QtWidgets.QRadioButton('y')
        self.ctlAxisZ_rb = QtWidgets.QRadioButton('z')
        self.mirrorCtlMode_cbox = QtWidgets.QComboBox()
        self.mirrorCtlMode_cbox.setFixedHeight(24)
        self.mirrorCtlMode_cbox.addItem("replace")
        self.mirrorCtlMode_cbox.addItem("match")
        self.mirror_control_btn = QtWidgets.QPushButton("Mirror")

        self.ctlColor_ovrcol = overrideColorer.OverrideColorer()

        self.ctlShape_cbox = QtWidgets.QComboBox()
        self.ctlShape_cbox.setFixedHeight(24)
        self.set_ctlShape_items()
        self.setCtlShape_btn = QtWidgets.QPushButton("Set Shape")

        self.replace_ctl_btn = QtWidgets.QPushButton("Replace Control Shape ")

        # Deformation Section
        self.deformations_wdgt = collapseableWidget.CollapsibleWidget('Deformations')
        # Publish Section
        self.publish_wdgt = collapseableWidget.CollapsibleWidget('Publish')
        self.publishScript_scriptRunner = scriptRunner.ScriptRunner()

        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layouts(self):
        rig_env_btn_layout = QtWidgets.QHBoxLayout()
        rig_env_btn_layout.addWidget(self.create_rig_env_btn)
        rig_env_btn_layout.addWidget(self.clone_rig_env_btn)

        rig_env_layout = QtWidgets.QVBoxLayout()
        rig_env_layout.addWidget(self.rig_path_selector)
        rig_env_layout.addLayout(rig_env_btn_layout)

        # prescript
        self.preScript_wdgt.addWidget(self.preScript_scriptRunner)

        # Model
        model_btn_layout = QtWidgets.QHBoxLayout()
        model_btn_layout.setContentsMargins(0, 0, 0, 0)
        model_btn_layout.setSpacing(4)
        model_btn_layout.addWidget(self.import_model_btn)
        model_btn_layout.addWidget(self.open_model_btn)

        self.model_wdgt.addWidget(self.model_path_selector)
        self.model_wdgt.addLayout(model_btn_layout)

        # Skeleton
        save_load_skeleton_layout = QtWidgets.QHBoxLayout()
        save_load_skeleton_layout.addWidget(self.import_skeleton_btn)
        save_load_skeleton_layout.addWidget(self.save_skeleton_btn)

        save_load_jnt_layout = QtWidgets.QHBoxLayout()
        save_load_jnt_layout.addWidget(self.load_jnt_pos_btn)
        save_load_jnt_layout.addWidget(self.save_jnt_pos_btn)

        skeleton_btn_layout = QtWidgets.QVBoxLayout()
        skeleton_btn_layout.setContentsMargins(0, 0, 0, 0)
        skeleton_btn_layout.setSpacing(4)
        skeleton_btn_layout.addLayout(save_load_skeleton_layout)
        skeleton_btn_layout.addLayout(save_load_jnt_layout)

        jointOrientation_layout = QtWidgets.QHBoxLayout()
        jointOrientation_layout.addWidget(self.jnt_to_rot_btn)
        jointOrientation_layout.addWidget(self.jnt_to_ori_btn)

        mirrorJoint_layout = QtWidgets.QHBoxLayout()
        mirrorJoint_layout.setSpacing(4)
        jointMirrorAxis_layout = QtWidgets.QHBoxLayout()
        jointMirrorAxis_layout.addWidget(QtWidgets.QLabel("Axis: "))
        jointMirrorAxis_layout.addWidget(self.jntAxisX_rb)
        jointMirrorAxis_layout.addWidget(self.jntAxisY_rb)
        jointMirrorAxis_layout.addWidget(self.jntAxisZ_rb)

        mirrorJoint_layout.addLayout(jointMirrorAxis_layout)
        mirrorJoint_layout.addWidget(self.mirrorJntMode_cbox)
        mirrorJoint_layout.addWidget(self.mirrorJnt_btn)

        self.skeleton_wdgt.addWidget(self.skel_path_selector)
        self.skeleton_wdgt.addWidget(self.joint_pos_path_selector)
        self.skeleton_wdgt.addLayout(skeleton_btn_layout)
        self.skeleton_wdgt.addWidget(self.import_load_skeleton_btn)
        self.skeleton_wdgt.addWidget(self.skeletonEdit_wdgt)

        self.skeletonEdit_wdgt.addLayout(jointOrientation_layout)
        self.skeletonEdit_wdgt.addLayout(mirrorJoint_layout)

        # Components
        cmpt_btn_layout = QtWidgets.QHBoxLayout()
        cmpt_btn_layout.setSpacing(4)
        cmpt_btn_layout.addWidget(self.initalize_all_btn)

        guide_load_layout = QtWidgets.QHBoxLayout()
        guide_load_layout.addWidget(self.load_guides_btn)
        guide_load_layout.addWidget(self.save_guides_btn)

        self.cmpt_wdgt.addWidget(self.cmpt_manager)
        self.cmpt_wdgt.addLayout(cmpt_btn_layout)
        self.cmpt_wdgt.addWidget(self.guide_path_selector)
        self.cmpt_wdgt.addLayout(guide_load_layout)
        build_step_layout = QtWidgets.QHBoxLayout()
        build_step_layout.addWidget(self.build_rig_btn)
        build_step_layout.addWidget(self.connect_rig_btn)
        build_step_layout.addWidget(self.finalize_rig_btn)
        self.cmpt_wdgt.addLayout(build_step_layout)
        self.cmpt_wdgt.addWidget(self.complete_build_btn)

        # Post Script
        self.postScript_wdgt.addWidget(self.postScript_scriptRunner)

        # Control shapes
        control_btn_layout = QtWidgets.QHBoxLayout()
        control_btn_layout.setSpacing(4)
        load_color_label = QtWidgets.QLabel("Load Color:")
        load_color_label.setFixedWidth(60)

        control_btn_layout.addWidget(load_color_label)
        control_btn_layout.addWidget(self.load_color_cb)
        control_btn_layout.addWidget(self.load_ctl_btn)
        control_btn_layout.addWidget(self.save_ctl_btn)

        mirrorControl_layout = QtWidgets.QHBoxLayout()
        mirrorControl_layout.setSpacing(4)
        controlMirrorAxis_layout = QtWidgets.QHBoxLayout()
        controlMirrorAxis_layout.addWidget(QtWidgets.QLabel("Axis: "))
        controlMirrorAxis_layout.addWidget(self.ctlAxisX_rb)
        controlMirrorAxis_layout.addWidget(self.ctlAxisY_rb)
        controlMirrorAxis_layout.addWidget(self.ctlAxisZ_rb)

        mirrorControl_layout.addLayout(controlMirrorAxis_layout)
        mirrorControl_layout.addWidget(self.mirrorCtlMode_cbox)
        mirrorControl_layout.addWidget(self.mirror_control_btn)

        setControlShape_layout = QtWidgets.QHBoxLayout()
        setControlShape_layout.addWidget(self.ctlShape_cbox)
        setControlShape_layout.addWidget(self.setCtlShape_btn)

        self.ctlShape_wdgt.addWidget(self.ctl_path_selector)
        self.ctlShape_wdgt.addLayout(control_btn_layout)
        self.ctlShape_wdgt.addWidget(self.controlEdit_wgt)
        self.controlEdit_wgt.addLayout(mirrorControl_layout)
        self.controlEdit_wgt.addWidget(self.ctlColor_ovrcol)
        self.controlEdit_wgt.addLayout(setControlShape_layout)
        self.controlEdit_wgt.addWidget(self.replace_ctl_btn)

        # Deformations

        # Publish

        # add the collapseable widgets
        build_layout = QtWidgets.QVBoxLayout()
        build_layout.addWidget(self.preScript_wdgt)
        build_layout.addWidget(self.model_wdgt)
        build_layout.addWidget(self.skeleton_wdgt)
        build_layout.addWidget(self.cmpt_wdgt)
        build_layout.addWidget(self.ctlShape_wdgt)
        build_layout.addWidget(self.deformations_wdgt)
        build_layout.addWidget(self.postScript_wdgt)
        build_layout.addWidget(self.publish_wdgt)
        build_layout.addStretch()

        # groups
        rig_env_grp = QtWidgets.QGroupBox('Rig Enviornment')
        rig_env_grp.setLayout(rig_env_layout)

        build_grp = QtWidgets.QGroupBox('Build')
        build_grp.setLayout(build_layout)

        # lower persistant buttons (AKA close)
        low_buttons_layout = QtWidgets.QHBoxLayout()
        low_buttons_layout.addWidget(self.close_btn)

        # scrollable area
        body_wdg = QtWidgets.QWidget()
        body_layout = QtWidgets.QVBoxLayout(body_wdg)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(rig_env_grp)
        body_layout.addWidget(build_grp)

        body_scroll_area = QtWidgets.QScrollArea()
        body_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        body_scroll_area.setWidgetResizable(True)
        body_scroll_area.setWidget(body_wdg)

        # main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        main_layout.setMenuBar(self.main_menu)
        main_layout.addWidget(body_scroll_area)
        main_layout.addLayout(low_buttons_layout)

    def create_connections(self):
        self.rig_path_selector.select_path_btn.clicked.connect(self.path_selector_load_rig_file)
        self.create_rig_env_btn.clicked.connect(self.create_rig_env)
        self.clone_rig_env_btn.clicked.connect(self.clone_rig_env)

        self.import_model_btn.clicked.connect(self.import_model)

        self.import_load_skeleton_btn.clicked.connect(self.import_load_skeleton)
        self.import_skeleton_btn.clicked.connect(self.import_skeleton)
        self.load_jnt_pos_btn.clicked.connect(self.load_joint_positions)
        self.save_jnt_pos_btn.clicked.connect(self.save_joint_positions)
        self.jnt_to_rot_btn.clicked.connect(self.jnt_to_rotation)
        self.jnt_to_ori_btn.clicked.connect(self.jnt_to_orientation)
        self.mirrorJnt_btn.clicked.connect(self.mirror_joint)

        self.load_guides_btn.clicked.connect(self.load_guides)
        self.save_guides_btn.clicked.connect(self.save_guides)
        self.initalize_all_btn.clicked.connect(self.cmpt_manager.initalize_all_cmpts)

        self.load_ctl_btn.clicked.connect(self.load_controlShapes)
        self.save_ctl_btn.clicked.connect(self.save_controlShapes)
        self.mirror_control_btn.clicked.connect(self.mirror_control)
        self.setCtlShape_btn.clicked.connect(self.set_controlShape)
        self.replace_ctl_btn.clicked.connect(self.replace_controlShape)

        self.close_btn.clicked.connect(self.close)

    # Connections
    def load_rig_file(self):
        new_path = cmds.fileDialog2(ds=2, cap="Select a rig file", ff="Rig Files (*.rig)", fm=1, okc='Select',
                                    dir=self.rig_env)
        if new_path:
            self.set_rig_file(new_path[0])

    def path_selector_load_rig_file(self):
        new_path = self.rig_path_selector.get_abs_path()
        if new_path:
            self.set_rig_file(new_path)

    def save_rig_file(self):
        """
        Save out a rig file
        :return:
        """
        data = abstract_data.AbstractData()
        data.read(self.rig_file)
        new_data = OrderedDict()
        new_data = data.getData()

        # TODO: Keep this updated as we add stuff to the builder
        new_data['model_file'] = self.model_path_selector.get_path()
        new_data['skeleton_file'] = self.skel_path_selector.get_path()
        new_data['skeleton_pos'] = self.joint_pos_path_selector.get_path()
        new_data['guides'] = self.guide_path_selector.get_path()
        new_data['control_shapes'] = self.ctl_path_selector.get_path()

        data.setData(new_data)
        data.write(self.rig_file)

    def show_documentation(self):
        pass

    def show_about(self):
        pass

    def set_rig_file(self, path=None):
        self.rig_path_selector.select_path(path=path)
        file_info = QtCore.QFileInfo(self.rig_path_selector.get_abs_path())
        self.rig_env = file_info.path()
        self.rig_file = file_info.filePath()

        # set all path selectors to be realive to the new rig enviornment
        self.model_path_selector.set_relativeTo(self.rig_env)
        self.skel_path_selector.set_relativeTo(self.rig_env)
        self.joint_pos_path_selector.set_relativeTo(self.rig_env)
        self.guide_path_selector.set_relativeTo(self.rig_env)
        self.ctl_path_selector.set_relativeTo(self.rig_env)

        self.rig_builder = builder.Builder(self.rig_file)
        self.update_ui_with_rig_data()

    def update_ui_with_rig_data(self):
        tmp_builder = builder.Builder()
        if not self.rig_file:
            return

        # clear script runners
        self.preScript_scriptRunner.clear_scripts()
        self.postScript_scriptRunner.clear_scripts()
        self.publishScript_scriptRunner.clear_scripts()

        # load_settings prescripts from file or rig_env
        pre_script_path = os.path.join(self.rig_env, builder.PRE_SCRIPT_PATH)
        if QtCore.QFileInfo(pre_script_path).exists():
            self.preScript_scriptRunner.set_start_dir(pre_script_path)
            self.preScript_scriptRunner.add_scripts_from_dir(pre_script_path)

        # load_settings post scripts from file or rig_env
        post_script_path = os.path.join(self.rig_env, builder.POST_SCRIPT_PATH)
        if QtCore.QFileInfo(post_script_path).exists():
            self.postScript_scriptRunner.set_start_dir(post_script_path)
            self.postScript_scriptRunner.add_scripts_from_dir(post_script_path)

        # load_settings pub scripts from file or rig_env
        pub_script_path = os.path.join(self.rig_env, builder.PUB_SCRIPT_PATH)
        if QtCore.QFileInfo(pub_script_path).exists():
            self.publishScript_scriptRunner.set_start_dir(pub_script_path)
            self.publishScript_scriptRunner.add_scripts_from_dir(pub_script_path)

        mod_file = tmp_builder.get_rig_data(self.rig_file, builder.MODEL_FILE)
        if mod_file: self.model_path_selector.set_path(mod_file)

        skel_file = tmp_builder.get_rig_data(self.rig_file, builder.SKELETON_FILE)
        if skel_file: self.skel_path_selector.set_path(skel_file)

        skel_pos_file = tmp_builder.get_rig_data(self.rig_file, builder.SKELETON_POS)
        if skel_pos_file: self.joint_pos_path_selector.set_path(skel_pos_file)

        guide_file = tmp_builder.get_rig_data(self.rig_file, builder.GUIDES)
        if guide_file: self.guide_path_selector.set_path(guide_file)

        ctl_file = tmp_builder.get_rig_data(self.rig_file, builder.CONTROL_SHAPES)
        if ctl_file: self.ctl_path_selector.set_path(ctl_file)

    # UI FUNCTIONS
    def set_ctlShape_items(self):
        import rigamajig2.maya.rig.control
        control_shapes = rigamajig2.maya.rig.control.getAvailableControlShapes()
        for control_shape in control_shapes:
            self.ctlShape_cbox.addItem(control_shape)

    # UTILITIY FUNCTIONS
    def create_rig_env(self):
        print("TODO : create a rig environment")

    def clone_rig_env(self):
        print("TODO : clone a rig environment")

    # CONNECTIONS
    def mirror_joint(self):
        """ mirror joint"""
        import rigamajig2.maya.joint
        axis = 'x'
        if self.jntAxisY_rb.isChecked(): axis = 'y'
        if self.jntAxisZ_rb.isChecked(): axis = 'z'
        mirrorMode = self.mirrorJntMode_cbox.currentText()
        for joint in cmds.ls(sl=True):
            joints = cmds.listRelatives(cmds.ls(sl=True, type='joint'), ad=True, type='joint') or []
            rigamajig2.maya.joint.mirror(joints + [joint], axis=axis, mode=mirrorMode)

    def jnt_to_rotation(self):
        import rigamajig2.maya.joint
        rigamajig2.maya.joint.toRotation(cmds.ls(sl=True, type='joint'))

    def jnt_to_orientation(self):
        import rigamajig2.maya.joint
        rigamajig2.maya.joint.toOrientation(cmds.ls(sl=True, type='joint'))

    def mirror_control(self):
        import rigamajig2.maya.curve
        axis = 'x'
        if self.ctlAxisY_rb.isChecked(): axis = 'y'
        if self.ctlAxisZ_rb.isChecked(): axis = 'z'
        mirrorMode = self.mirrorCtlMode_cbox.currentText()
        rigamajig2.maya.curve.mirror(cmds.ls(sl=True, type='transform'), axis=axis, mode=mirrorMode)

    # BULDER FUNCTIONS
    def import_model(self):
        self.rig_builder.import_model(self.model_path_selector.get_abs_path())

    def import_load_skeleton(self):
        self.import_skeleton()
        self.load_joint_positions()

    def import_skeleton(self):
        self.rig_builder.import_skeleton(self.skel_path_selector.get_abs_path())

    def load_joint_positions(self):
        self.rig_builder.load_joint_positions(self.joint_pos_path_selector.get_abs_path())

    def save_joint_positions(self):
        self.rig_builder.save_joint_positions(self.joint_pos_path_selector.get_abs_path())

    def load_guides(self):
        self.rig_builder.load_guide_data(self.guide_path_selector.get_abs_path())

    def save_guides(self):
        self.rig_builder.save_guide_data(self.guide_path_selector.get_abs_path())

    def load_controlShapes(self):
        self.rig_builder.load_controlShapes(self.ctl_path_selector.get_abs_path(), self.load_color_cb.isChecked())

    def save_controlShapes(self):
        self.rig_builder.save_controlShapes(self.ctl_path_selector.get_abs_path())

    def set_controlShape(self):
        """Set the control shape of the selected node"""
        import rigamajig2.maya.rig.control
        shape = self.ctlShape_cbox.currentText()
        for node in cmds.ls(sl=True, type='transform'):
            rigamajig2.maya.rig.control.setControlShape(node, shape)

    def replace_controlShape(self):
        """Replace the control shape"""
        import rigamajig2.maya.curve
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) >= 2:
            for dest in selection[1:]:
                if cmds.listRelatives(dest, shapes=True, pa=True):
                    for shape in cmds.listRelatives(dest, shapes=True, pa=True):
                        cmds.delete(shape)
                rigamajig2.maya.curve.copyShape(selection[0], dest)

    def toggle_advanced_proxy(self):
        """ Toggle the advanced proxy attributes """
        if self.show_advanced_proxy_cb.isChecked():
            self.rig_builder.show_advanced_proxy()
        else:
            self.rig_builder.delete_advanced_proxy()


if __name__ == '__main__':
    try:
        rigamajig_builder_dialog.close()
        rigamajig_builder_dialog.deleteLater()
    except:
        pass

    rigamajig_builder_dialog = RigamajigBuilderUi()
    rigamajig_builder_dialog.show()

    rigamajig_builder_dialog.set_rig_file(
        path='/Users/masonsmigel/Documents/dev/maya/rigamajig2/archetypes/biped/biped.rig')
