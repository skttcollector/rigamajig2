#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: model.py
    author: masonsmigel
    date: 07/2022
    discription: This module contains our rig builder.
                 It acts as a wrapper to manage all functions of the rig_builder.
"""

# PYTHON
import os
import time
import inspect
import logging
from collections import OrderedDict

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
import rigamajig2.shared.common as common
import rigamajig2.shared.path as rig_path
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta

# BUILDER
import rigamajig2.maya.rig_builder.model as model
import rigamajig2.maya.rig_builder.guides as guides
import rigamajig2.maya.rig_builder.controlShapes as controlShapes
import rigamajig2.maya.rig_builder.deform as deform
import rigamajig2.maya.rig_builder.builderUtils as builderUtils

logger = logging.getLogger(__name__)

CMPT_PATH = os.path.abspath(os.path.join(__file__, '../../cmpts'))

_EXCLUDED_FOLDERS = ['face']
_EXCLUDED_FILES = ['__init__.py', 'base.py']

# BUILD ENVIORNMENT GLOBLALS
PRE_SCRIPT = 'pre_script'
POST_SCRIPT = 'post_script'
PUB_SCRIPT = 'pub_script'

# RIG FILE KEYS
RIG_NAME = 'rig_name'
MODEL_FILE = "model_file"
SKELETON_FILE = "skeleton_file"
SKELETON_POS = "skeleton_pos"
CONTROL_SHAPES = "control_shapes"
GUIDES = "guides"
COMPONENTS = "components"
SKINS = 'skins'
PSD = 'psd'
OUTPUT_RIG = 'output_file'
OUTPUT_RIG_FILE_TYPE = 'output_file_type'


class Builder(object):
    def __init__(self, rigFile=None):
        """
        Initalize the builder
        :param rigFile: path to the rig file
        """
        self.path = None
        self.set_rig_file(rigFile)
        self.cmpt_list = list()

        self._available_cmpts = builderUtils._lookForComponents(CMPT_PATH, _EXCLUDED_FOLDERS, _EXCLUDED_FILES)
        # self.__lookForComponents(CMPT_PATH)

        # varibles we need
        self.top_skeleton_nodes = list()
        self.load_cmpts_from_file = False

    def getComponents(self):
        return self._available_cmpts

    def _absPath(self, path):
        if path:
            path = common.getFirstIndex(path)
            return os.path.realpath(os.path.join(self.path, path))

    # --------------------------------------------------------------------------------
    # RIG BUILD STEPS
    # --------------------------------------------------------------------------------
    def import_model(self, path=None):
        path = path or self._absPath(self.get_rig_data(self.rig_file, MODEL_FILE))
        model.import_model(path)
        logger.info("Model loaded")

    def load_joints(self, path=None):
        path = path or self._absPath(self.get_rig_data(self.rig_file, SKELETON_POS))
        guides.load_joints(path)
        logger.info("Joints loaded")

    def save_joints(self, path=None):
        path = path or self._absPath(self.get_rig_data(self.rig_file, SKELETON_POS))
        guides.save_joints(path)
        logger.info("Joint positions saved to: {}".format(path))

    def initalize(self):
        """Initalize rig (this is where the user can make changes)"""
        for cmpt in self.cmpt_list:
            logger.info('Initalizing: {}'.format(cmpt.name))
            cmpt._intialize_cmpt()
        self.load_guide_data()
        logger.info("initalize -- complete")

    def build(self):
        """build rig"""
        for cmpt in self.cmpt_list:
            logger.info('Building: {}'.format(cmpt.name))
            cmpt._build_cmpt()
            # if the component is not a main parent the cmpt.root_hrc to the rig
            if cmds.objExists('rig') and cmpt.getComponenetType() != 'main.Main':
                if hasattr(cmpt, "root_hrc"):
                    if not cmds.listRelatives(cmpt.root_hrc, p=True):
                        cmds.parent(cmpt.root_hrc, 'rig')

        # parent the bind joints to the bind group. if one exists
        if cmds.objExists('bind'):
            top_skeleton_nodes = meta.getTagged('skeleton_root')
            if not cmds.listRelatives(top_skeleton_nodes, p=True):
                cmds.parent(top_skeleton_nodes, 'bind')

        # if the model group exists. parent the model
        if cmds.objExists('model'):
            top_model_nodes = meta.getTagged('model_root')
            if not cmds.listRelatives(top_model_nodes, p=True):
                cmds.parent(top_model_nodes, 'model')

        logger.info("build -- complete")

    def connect(self):
        """connect rig"""
        for cmpt in self.cmpt_list:
            logger.info('Connecting: {}'.format(cmpt.name))
            cmpt._connect_cmpt()
        logger.info("connect -- complete")

    def finalize(self):
        """finalize rig"""
        for cmpt in self.cmpt_list:
            logger.info('Finalizing: {}'.format(cmpt.name))
            cmpt._finalize_cmpt()
        logger.info("finalize -- complete")

    def optimize(self):
        """optimize rig"""
        for cmpt in self.cmpt_list:
            logger.info('Optimizing {}'.format(cmpt.name))
            cmpt._optimize_cmpt()
        logger.info("optimize -- complete")

    def save_components(self, path=None):
        """
        Save out components to a file. This only saves compoonent settings such as name, inputs, spaces and names.
        :param path: path to components
        :return:
        """
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, COMPONENTS))

        cmpt_data = OrderedDict()
        cd = abstract_data.AbstractData()
        for cmpt in self.cmpt_list:
            cmpt_data[cmpt.name] = cmpt.getComponentData()

        cd.setData(cmpt_data)
        cd.write(path)
        logger.info("Components saved to: {}".format(path))

    def load_components(self, path=None):
        """
        Load components
        :param path:
        :return:
        """
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, COMPONENTS))
        cd = abstract_data.AbstractData()
        cd.read(path)
        cmpt_data = cd.getData()

        self.set_cmpts(list())
        for cmpt in list(cmpt_data.keys()):
            # dynamically load component module into python
            module_name, class_name = cmpt_data[cmpt]['type'].split(".")
            modulesPath = 'rigamajig2.maya.cmpts.{}'
            module_name = modulesPath.format(module_name)
            module_object = __import__(module_name, globals(), locals(), ["*"], 0)

            cmpt_class = getattr(module_object, class_name)
            instance = cmpt_class(cmpt_data[cmpt]['name'], cmpt_data[cmpt]['input'])
            self.append_cmpts(instance)
            self.load_cmpts_from_file = True

        logger.info("components loaded -- complete")

    def load_component_settings(self, path=None):
        """
        loadSettings component settings from the rig builder
        :param path:
        :return:
        """
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, COMPONENTS))

        if self.load_cmpts_from_file:
            cd = abstract_data.AbstractData()
            cd.read(path)
            cmpt_data = cd.getData()
            for cmpt in self.cmpt_list:
                cmpt.loadSettings(cmpt_data[cmpt.name])

    def load_controlShapes(self, path=None, applyColor=True):
        """
        Load the control shapes
        :param path: path to control shape
        :param applyColor: Apply the control colors.
        :return:
        """
        path = path or self._absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))
        controlShapes.load_controlShapes(path, applyColor=applyColor)
        logger.info("control shapes -- complete")

    def save_controlShapes(self, path=None):
        path = path or self._absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))
        controlShapes.save_controlShapes(path)
        logger.info("control shapes saved to: {}".format(path))

    def load_guide_data(self, path=None):
        """
        Load guide data
        :return:
        """
        path = path or self._absPath(self.get_rig_data(self.rig_file, GUIDES))
        if guides.load_guide_data(path):
            logger.info("guides loaded")

    def save_guide_data(self, path=None):
        """
        Save guides data
        :param path:
        :return:
        """
        path = path or self._absPath(self.get_rig_data(self.rig_file, GUIDES))
        guides.save_guide_data(path)
        logger.info("guides saved to: {}".format(path))

    def load_poseReaders(self, path=None, replace=True):
        """ Load pose readers"""

        path = path or self._absPath(self.get_rig_data(self.rig_file, PSD)) or ''
        if deform.load_poseReaders(path, replace=replace):
            logger.info("pose readers loaded")

    def save_poseReaders(self, path=None):
        """Save out pose readers"""
        path = path or self._absPath(self.get_rig_data(self.rig_file, PSD))
        deform.save_poseReaders(path)
        logger.info("pose readers saved to: {}".format(path))

    def load_deform_data(self):
        """
        Load other data, this is stuff like skinweights, blendshapes, clusters etc.
        :return:
        """
        self.load_skin_weights()
        logger.info("data loading -- complete")

    def load_skin_weights(self, path=None):
        path = path or self._absPath(self.get_rig_data(self.rig_file, SKINS)) or ''
        if deform.load_skin_weights(path):
            logger.info("skin weights loaded")

    def save_skin_weights(self, path=None):
        path = path or self._absPath(self.get_rig_data(self.rig_file, SKINS)) or ''
        deform.save_skin_weights(path)

    def delete_cmpts(self, clear_list=True):
        main_cmpt = None
        for cmpt in self.cmpt_list:
            if cmds.objExists(cmpt.container):
                if cmpt.getComponenetType() == 'main.Main':
                    main_cmpt = cmpt
                else:
                    cmpt.deleteSetup()
        if main_cmpt:
            main_cmpt.deleteSetup()
        if clear_list:
            self.cmpt_list = list()

    def build_single_cmpt(self, name, type):
        """
        Build a single component based on the name and component type.
        If a component with the given name and type exists within the self.cmpt_list build that component.

        Warning: Building a single component without nesseary connection nodes in the scene may lead to
                 unpredicable results. ONLY USE THIS FOR RND!
        :param name:
        :param type:
        :return:
        """
        cmpt = self.find_cmpt(name=name, type=type)

        if cmpt:
            cmpt._intialize_cmpt()
            cmpt._build_cmpt()
            cmpt._connect_cmpt()
            cmpt._finalize_cmpt()

            if cmds.objExists('rig') and cmpt.getComponenetType() != 'main.Main':
                if hasattr(cmpt, "root_hrc"):
                    if not cmds.listRelatives(cmpt.root_hrc, p=True):
                        cmds.parent(cmpt.root_hrc, 'rig')

            logger.info("build: {} -- complete".format(cmpt.name))

    # --------------------------------------------------------------------------------
    # RUN SCRIPTS UTILITIES
    # --------------------------------------------------------------------------------
    def pre_script(self):
        """ Run pre scripts. use  through the PRE SCRIPT path"""
        builderUtils.runAllScripts(self._absPath(self.get_rig_data(self.rig_file, PRE_SCRIPT)))
        logger.info("pre scripts -- complete")

    def post_script(self):
        """ Run pre scripts. use  through the POST SCRIPT path"""
        builderUtils.runAllScripts(self._absPath(self.get_rig_data(self.rig_file, POST_SCRIPT)))
        logger.info("pre scripts -- complete")

    def pub_script(self):
        """ Run pre scripts. use  through the PUB SCRIPT path"""
        builderUtils.runAllScripts(self._absPath(self.get_rig_data(self.rig_file, PUB_SCRIPT)))
        logger.info("publish scripts -- complete")

    # ULITITY FUNCTION TO BUILD THE ENTIRE RIG
    def run(self, publish=False, outputfile=None, assetName=None, fileType=None, versioning=True):
        if not self.path:
            logger.error('you must provide a build enviornment path. Use Bulder.set_rig_file()')
            return

        start_time = time.time()
        print('\nBegin Rig Build\n{0}\nbuild env: {1}\n'.format('-' * 70, self.path))
        builderUtils.load_required_plugins()
        self.pre_script()
        self.import_model()
        self.load_joints()
        self.load_components()
        self.initalize()
        self.load_component_settings()
        self.build()
        self.connect()
        self.finalize()
        self.load_poseReaders()
        self.post_script()
        self.load_controlShapes()
        self.load_deform_data()
        if publish:
            self.pub_script()
            self.publish(outputfile=outputfile, assetName=assetName, fileType=fileType, versioning=versioning)
        end_time = time.time()
        final_time = end_time - start_time

        print('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}\n'.format(final_time, '-' * 70))

    # UTILITY FUNCTION TO PUBLISH THE RIG
    def publish(self, outputfile=None, assetName=None, fileType=None, versioning=True):

        outputfile = outputfile or self._absPath(self.get_rig_data(self.rig_file, OUTPUT_RIG))
        assetName = assetName or self._absPath(self.get_rig_data(self.rig_file, RIG_NAME))
        fileType = fileType or self._absPath(self.get_rig_data(self.rig_file, OUTPUT_RIG_FILE_TYPE))

        # check if the provided path is a file path.
        # if so use the file naming and extension from the provided path
        if rig_path.isFile(outputfile):
            file_name = outputfile.split(os.sep)[-1]
            dir_name = '/'.join(outputfile.split(os.sep)[:-1])

        # if only a directory is provided than generate a filename using the rig name and file extension
        else:
            dir_name = outputfile
            if assetName:
                rig_name = self.get_rig_data(self.rig_file, RIG_NAME)
                file_name = "{}_{}.{}".format(rig_name, 'rig', fileType)
            else:
                raise RuntimeError("Must select an output path or character name to publish a rig")

        # create output directory and save
        rig_path.make_dir(dir_name)
        publish_path = os.path.join(dir_name, file_name)
        file.saveAs(publish_path, log=False)
        logger.info("out rig published: {}".format(publish_path))

        # if we want to save a version as well
        if versioning:
            # get the version directory, file
            version_dir = os.path.join(dir_name, 'versions')
            filebase = ".".join(file_name.split('.')[:-1])
            fileext = file_name.split('.')[-1]

            # format the new file name and file path
            version_file = "{}_{}.{}".format(filebase, 'v000', fileext)
            version_path = os.path.join(version_dir, version_file)

            # make the output directory and save the file
            rig_path.make_dir(version_dir)
            version_path = file.incrimentSave(version_path, log=False)
            logger.info("out rig archived: {}".format(version_path))

    # --------------------------------------------------------------------------------
    # GET
    # --------------------------------------------------------------------------------
    def get_rig_env(self):
        return self.path

    def get_rig_file(self):
        return self.rig_file

    def get_cmpt_list(self):
        return self.cmpt_list

    def get_cmpt_obj_from_container(self, container):
        name = cmds.getAttr("{}.name".format(container))
        cmpt_type = cmds.getAttr("{}.type".format(container))

        return self.find_cmpt(name, cmpt_type)

    def find_cmpt(self, name, type):
        for cmpt in self.cmpt_list:
            _name = cmpt.name
            _type = cmpt.cmpt_type
            if name == _name:
                if type == _type:
                    return cmpt
        logger.warning("No component: {} with type: {} found within current build".format(name, cmpt_type))
        return None

    # --------------------------------------------------------------------------------
    # SET
    # --------------------------------------------------------------------------------
    def set_cmpts(self, cmpts):
        """
        Set the self.cmpt_list
        :param cmpts: list of components to set
        """
        cmpts = common.toList(cmpts)
        self.cmpt_list = cmpts

    def append_cmpts(self, cmpts):
        """
        append a component
        :param cmpts: list of components to append
        :return:
        """
        cmpts = common.toList(cmpts)
        for cmpt in cmpts:
            self.cmpt_list.append(cmpt)

    def set_rig_file(self, rigFile):
        if not rigFile:
            self.rig_file = None
            return

        if not os.path.exists(rigFile):
            # TODO: give the user the option to create a rig file somewhere
            raise RuntimeError("'{0}' does not exist".format(rigFile))
        self.rig_file = rigFile

        rig_data = abstract_data.AbstractData()
        rig_data.read(self.rig_file)
        data = rig_data.getData()
        if "rig_env" not in data:
            rig_env_path = '../'
        else:
            rig_env_path = data["rig_env"]
        self.path = os.path.abspath(os.path.join(self.rig_file, rig_env_path))
        logger.info('\n\nRig Enviornment path: {0}'.format(self.path))

    @staticmethod
    def get_rig_data(rig_file, key):
        """
        read the data from the self.rig_file
        :param rig_file:
        :param key:
        :return:
        """
        if not rig_file:
            return None

        if not os.path.exists(rig_file):
            raise RuntimeError('rig file at {} does not exist'.format(rig_file))

        data = abstract_data.AbstractData()
        data.read(rig_file)
        if key in data.getData():
            return data.getData()[key]
        return None
