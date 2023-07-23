#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: guides.py
    author: masonsmigel
    date: 07/2022
    discription:

"""
# PYTHON
import os

# MAYA
import maya.cmds as cmds

# RIGAMJIG
import rigamajig2.shared.common as common
import rigamajig2.maya.data.joint_data as joint_data
import rigamajig2.maya.data.guide_data as guide_data
import rigamajig2.maya.meta as meta
import rigamajig2.maya.joint as joint
import rigamajig2.maya.attr as attr


def loadJoints(path=None):
    """
    Load all joints for the builder
    :param path: path to joint file
    :return:
    """
    if not path:
        return

    if not os.path.exists(path):
        return

    dataObj = joint_data.JointData()
    dataObj.read(path)
    dataObj.applyData(dataObj.getKeys())

    # tag all bind joints
    for jnt in cmds.ls(f"*_{common.BINDTAG}", type='joint'):
        meta.tag(jnt, common.BINDTAG)

    dataObj.getData().keys()
    for node in cmds.ls(dataObj.getKeys(), l=True):
        # add the joint orient to all joints in the file.
        joint.addJointOrientToChannelBox(node)

        # find joints without a parent and make them a root
        if not len(node.split('|')) > 2:
            meta.tag(node, 'skeleton_root')


def saveJoints(path=None):
    """
    save the joints
    :param path: path to save joints
    """

    # find all skeleton roots and get the positions of their children
    skeletonRoots = common.toList(meta.getTagged('skeleton_root'))

    if not skeletonRoots:
        skeletonRoots = cmds.ls(sl=True)

    if skeletonRoots:
        dataObj = joint_data.JointData()
        for root in skeletonRoots:
            dataObj.gatherData(root)
            childJoints = cmds.listRelatives(root, allDescendents=True, type='joint') or list()
            dataObj.gatherDataIterate(childJoints)
        dataObj.write(path)
    else:
        raise RuntimeError(
            "the rootHierarchy joint {} does not exists. Please select some joints.".format(skeletonRoots))


def gatherJoints():
    """
    gather all joints in the scene to save.
    :return: list of all joints in the scene that should be saved.
    """

    # find all skeleton roots and get the positions of their children
    skeletonRoots = common.toList(meta.getTagged('skeleton_root'))

    if not skeletonRoots:
        skeletonRoots = cmds.ls(sl=True)

    allJoints = list()
    if skeletonRoots:
        for root in skeletonRoots:
            childJoints = cmds.listRelatives(root, allDescendents=True, type='joint') or list()
            allJoints.append(root)
            for eachJoint in childJoints:
                allJoints.append(eachJoint)
    else:
        raise RuntimeError(
            "the rootHierarchy joint {} does not exists. Please select some joints.".format(skeletonRoots))

    return allJoints


def loadGuideData(path=None):
    """
    Load guide data
    :param path: path to guide data to save
    :return:
    """
    if not path:
        return

    if path and not os.path.exists(path):
        return

    try:
        dataObj = guide_data.GuideData()
        dataObj.read(path)
        dataObj.applyData(nodes=dataObj.getKeys())
        return True
    except Exception as e:
        raise e
        # return False


def saveGuideData(path=None):
    """
    Save guides data
    :param path: path to guide data to save
    :return:
    """
    dataObj = guide_data.GuideData()
    dataObj.gatherDataIterate(meta.getTagged("guide"))
    dataObj.write(path)


def gatherGuides():
    """
    Gather all guides in the scene
    :return: a list of all guides in the scene
    """
    return meta.getTagged("guide")
