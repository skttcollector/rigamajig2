#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: scripts.py
    author: masonsmigel
    date: 07/2022
    discription: This module contains utilities for the builder

"""
# PYTHON
import os
import sys
import glob
import shutil
import logging
import inspect

# MAYA
import maya.cmds as cmds

# RIGAMAJIG
from rigamajig2.maya.builder import constants
from rigamajig2.shared.logger import Logger
from rigamajig2.shared import common
from rigamajig2.shared import path as rig_path
from rigamajig2.shared import runScript
from rigamajig2.maya.data import abstract_data as abstract_data

logger = logging.getLogger(__name__)

CMPT_ROOT_MODULE = 'cmpts'


# def _lookForComponents(path, excludedFolders, excludedFiles):
#     res = os.listdir(path)
#     toReturn = dict()
#     for r in res:
#         fullList = os.path.join(path, r)
#         if r not in excludedFolders and os.path.isdir(path + '/' + r):
#             subDict = _lookForComponents(fullList, excludedFolders, excludedFiles)
#             toReturn.update(subDict)
#         if r.find('.py') != -1 and r.find('.pyc') == -1 and r not in excludedFiles:
#             if r.find('reload') == -1:
#
#                 # find classes in the file path
#                 moduleFile = r.split('.')[0]
#                 pathSplit = fullList.split('/')[:-1]
#                 cmptsIndex = pathSplit.index(CMPT_ROOT_MODULE)
#
#                 localPath = '.'.join(pathSplit[cmptsIndex:])
#                 componentName = '{}.{}'.format(localPath, moduleFile)
#
#                 moduleName = 'rigamajig2.maya.{}'.format(componentName)
#
#                 # module_name = modulesPath.format(module_file)
#                 moduleObject = __import__(moduleName, globals(), locals(), ["*"], 0)
#                 for cls in inspect.getmembers(moduleObject, inspect.isclass):
#                     component = '.'.join(componentName.rsplit('.')[1:])
#                     toReturn[component] = [moduleName, cls[0]]
#
#     return toReturn


def findComponents(path, excludedFolders, excludedFiles):
    """
    Find all valid components within a folder
    :param path: path to search for components
    :param excludedFolders: names of folders to exclude from the search
    :param excludedFiles: names of files to exclude from the search
    :return:
    """
    path = rig_path.cleanPath(path)
    items = os.listdir(path)

    toReturn = dict()
    for item in items:
        itemPath = os.path.join(path, item)

        # ensure the item should not be excluded
        if item not in excludedFolders and os.path.isdir(itemPath):
            res = findComponents(itemPath, excludedFolders, excludedFiles)
            toReturn.update(res)

        # check if the item is a python file
        if item.find('.py') != -1 and item.find('.pyc') == -1 and item not in excludedFiles:
            singleComponentDict = validateComponent(itemPath)
            if singleComponentDict:
                toReturn.update(singleComponentDict)

    return toReturn


def validateComponent(filePath):
    """
    Check if a file is a valid rigamajig component
    :param filePath: file path to check
    :return tuple: component class name, instance of the class
    """
    # first check to make sure the filepath exists
    if not os.path.exists(filePath):
        return False

    if not rig_path.isFile(filePath):
        return False

    # add the path to sys.path
    pathName = os.path.dirname(filePath)
    fileName = os.path.basename(filePath)

    # find the system path that is imported into python
    pythonPaths = list()
    for sysPath in sys.path:
        if sysPath in pathName:
            pythonPaths.append(sysPath)

    # Get the longest found python path.
    # We should never add a path closer than the python root, so it should always be the longest in the file.
    pythonPath = max(pythonPaths, key=len)

    # convert the path into a python module path (separated by ".")
    # ie: path/to/module --> path.to.module
    pythonPathName = pathName.replace(pythonPath, "")
    pythonModulesSplit = pythonPathName.split(os.path.sep)

    moduleName = fileName.split(".")[0]
    modulePath = ".".join(pythonModulesSplit[1:])

    fullModulename = ".".join([modulePath, moduleName])

    # import the module object to verify it is a component.
    moduleObject = __import__(fullModulename, globals(), locals(), ["*"], 0)
    classesInModule = inspect.getmembers(moduleObject, inspect.isclass)

    for class_ in classesInModule:
        # component name must be a PascalCase version of the modulename.
        predictedName = moduleName[0].upper() + moduleName[1:]
        componentClassName = class_[0]
        if componentClassName == predictedName:
            resultDict = dict()
            componentName = '.'.join([modulePath.rsplit('.')[-1], moduleName])
            resultDict[componentName] = [fullModulename, componentClassName]
            return resultDict

    return False


def loadRequiredPlugins():
    """
    loadSettings required plugins
    NOTE: There are plugins REQUIRED for rigamajig such as matrix and quat nodes.
          loading other plug-ins needed in production should be added into a pre-script file
    """
    loadedPlugins = cmds.pluginInfo(query=True, listPlugins=True)

    for plugin in common.REQUIRED_PLUGINS:
        if plugin not in loadedPlugins:
            cmds.loadPlugin(plugin)


def validateScriptList(scriptsList=None):
    """
    Validate the script list.
    This will filter all the items in the script into a script type.
    If the item is a directory then get scripts within the directory.
    :param scriptsList: list of directories and/or scripts to check and add to the list
    :return:
    """
    resultList = list()

    scriptsList = common.toList(scriptsList)

    # add all scripts and directories in the script list to the builder
    for item in scriptsList:
        if not item:
            continue

        if rig_path.isFile(item):
            resultList.append(item)

        if rig_path.isDir(item):
            for script in runScript.findScripts(item):
                resultList.append(script)

    return resultList


def runAllScripts(scripts=None):
    """
    Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
    :param scripts: path to scripts to run
    """
    if scripts is None:
        scripts = list()

    fileScripts = validateScriptList(scripts)
    for script in fileScripts:
        runScript.runScript(script)


def getAvailableArchetypes():
    """
    get a list of avaible archetypes. Archetypes are defined as a folder containng a .rig file.
    :return: list of archetypes
    """
    archetypeList = list()

    pathContents = os.listdir(common.ARCHETYPES_PATH)
    for archetype in pathContents:
        archetypePath = os.path.join(common.ARCHETYPES_PATH, archetype)
        if archetype.startswith("."):
            continue
        if findRigFile(archetypePath):
            archetypeList.append(archetype)
    return archetypeList


class GetCompleteScriptList():
    """
    This class will get a list of all scripts for a given rigfile
    Including any upstream archetype parents script contents.
    """
    scriptList = list()

    @classmethod
    def getScriptList(cls, rigFile, scriptType=None):
        """
        This function will get a list of all scripts for a given rigfile including any upstream archetype parents.

        The list is reversed to provide scripts at the lowest level of inheritance first.

        :param rigFile: rig file to get scripts for
        :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
        :return: list of scripts
        """
        cls.scriptList = list()
        cls.findScripts(rigFile=rigFile, scriptType=scriptType)

        return list(reversed(cls.scriptList))

    @classmethod
    def findScripts(cls, rigFile, scriptType=None):
        """

        :param rigFile: directories at the current rig file level of the rig
        :param scriptType: key of scripts to get. Typical values are pre_script, post_script or pub_script.
        """
        scriptType = scriptType or constants.PRE_SCRIPT

        localScriptPaths = getRigData(rigFile, scriptType)
        rigEnviornmentPath = os.path.abspath(os.path.join(rigFile, "../"))

        # for each item in the prescript path append the scripts within that directory
        for localScriptPath in localScriptPaths:
            fullScriptPath = os.path.join(rigEnviornmentPath, localScriptPath)
            builderScripts = validateScriptList(fullScriptPath)
            cls.scriptList += (builderScripts)

        baseArchetype = getRigData(rigFile, constants.BASE_ARCHETYPE)
        if baseArchetype:
            if baseArchetype in getAvailableArchetypes():
                archetypePath = os.sep.join([common.ARCHETYPES_PATH, baseArchetype])
                archetypeRigFile = findRigFile(archetypePath)

                cls.findScripts(archetypeRigFile, scriptType=scriptType)


def findRigFile(path):
    """ find a rig file within the path"""
    if rig_path.isFile(path):
        return False

    pathContents = os.listdir(path)
    for f in pathContents:
        if f.startswith("."):
            continue
        if not rig_path.isDir(path):
            continue
        fileName, fileExt = os.path.splitext(os.path.join(path, f))
        if fileExt != '.rig':
            continue
        return os.path.join(path, f)
    return False


def newRigEnviornmentFromArchetype(newEnv, archetype, rigName=None):
    """
    Create a new rig envirnment from and archetype
    :param newEnv: target driectory for the new rig enviornment
    :param rigName: name of the new rig enviornment
    :param archetype: archetype to copy
    :return: path to the rig file
    """
    if archetype not in getAvailableArchetypes():
        raise RuntimeError("{} is not a valid archetype".format(archetype))

    archetypePath = os.path.join(common.ARCHETYPES_PATH, archetype)
    rigFile = createRigEnviornment(sourceEnviornment=archetypePath, targetEnviornment=newEnv, rigName=rigName)

    data = abstract_data.AbstractData()
    data.read(rigFile)

    newData = data.getData()
    newData[constants.BASE_ARCHETYPE] = archetype
    data.setData(newData)
    data.write(rigFile)

    # delete the contents of the scripts folders as they should be constructed from
    # previous inheritance. Keeping them here will duplicate the execution.
    for scriptType in [constants.PRE_SCRIPT, constants.POST_SCRIPT, constants.PUB_SCRIPT]:
        path = os.sep.join([newEnv, rigName, data.getData()[scriptType][0]])
        files = glob.glob('{}/*'.format(path))
        for f in files:
            os.remove(f)

    return rigFile


def createRigEnviornment(sourceEnviornment, targetEnviornment, rigName):
    """
    create a new rig enviornment from an existing rig enviornment.
    :param sourceEnviornment: source rig enviornment
    :param targetEnviornment: target rig direction
    :param rigName: new name of the rig enviornment and .rig file
    :return: path to the rig file
    """

    tgtEnvPath = os.path.join(targetEnviornment, rigName)
    shutil.copytree(sourceEnviornment, tgtEnvPath)

    srcRigFile = findRigFile(tgtEnvPath)
    rigFile = os.path.join(tgtEnvPath, "{}.rig".format(rigName))

    # rename the .rig file and the rig_name within the .rig file
    os.rename(srcRigFile, rigFile)

    data = abstract_data.AbstractData()
    data.read(rigFile)

    newData = data.getData()
    newData[constants.RIG_NAME] = rigName
    data.setData(newData)
    data.write(rigFile)

    logger.info("New rig environment created: {}".format(tgtEnvPath))
    return os.path.join(tgtEnvPath, rigFile)


def getRigData(rigFile, key):
    """
    read the data from the self.rig_file
    :param rigFile:
    :param key:
    :return:
    """
    if not rigFile:
        return None

    if not os.path.exists(rigFile):
        raise RuntimeError('rig file at {} does not exist'.format(rigFile))

    data = abstract_data.AbstractData()
    data.read(rigFile)
    if key in data.getData():
        return data.getData()[key]
    return None
