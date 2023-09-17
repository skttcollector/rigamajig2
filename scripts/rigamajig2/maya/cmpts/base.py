"""
base component
"""
import maya.cmds as cmds
import maya.mel as mel
from collections import OrderedDict

import rigamajig2.maya.container
import rigamajig2.maya.attr
import rigamajig2.maya.meta
import rigamajig2.maya.color
import rigamajig2.maya.data.joint_data as joint_data
import rigamajig2.maya.transform as transform
from rigamajig2.maya.rig.control import CONTROLTAG

import logging

logger = logging.getLogger(__name__)

logger.setLevel(0)

UNBUILT_STEP = 0
INTIALIZE_STEP = 1
GUIDE_STEP = 2
BUILD_STEP = 3
CONNECT_STEP = 4
FINALIZE_STEP = 5
OPTIMIZE_STEP = 6

METADATA_NODE_TYPE = "network"


# pylint:disable=too-many-public-methods
class Base(object):
    """
    Base component all components are subclassed from
    """
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0

    version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
    version = '%i.%i.%i' % version_info
    __version__ = version

    UI_COLOR = (200, 200, 200)

    def __init__(self, name, input, size=1, rigParent=None, componentTag=None, enabled=True):
        """
        constructor of the base class.

        :param name: name of the components
        :type name: str
        :param input: list of input joints.
        :type input: list
        :param size: default size of the controls:
        :type size: float
        :param rigParent: node to parent to connect the component to in the heirarchy
        :type rigParent: str
        :param enabled: If set to false the component will not build
        """
        self._componentParameters = {}

        self.componentType = self.__module__.split('cmpts.')[-1]
        self.name = name
        self.input = input
        self.enabled = enabled
        self.size = size
        self.rigParent = rigParent or str()
        self.componentTag = componentTag or str()

        # important global nodes
        self.container = self.name + '_container'

        # we will always need the container if it does not exist.
        if not cmds.objExists(self.container):
            self.createContainer()
            self.createMetaNode(metaNodeName=self.container + "_metadata")
            logger.debug(f"Component '{name}' container created.")

        self.metadataNode = self.getMetaDataNode()

        # define component parameters
        self.defineParameter(parameter="name", value=self.name, dataType="string")
        self.defineParameter(parameter="type", value=self.componentType, dataType="type")
        self.defineParameter(parameter="input", value=self.input, dataType="list")
        self.defineParameter(parameter="enabled", value=self.enabled, dataType="bool")
        self.defineParameter(parameter="size", value=self.size, dataType="int")
        self.defineParameter(parameter="rigParent", value=self.rigParent, dataType="string")
        self.defineParameter(parameter="componentTag", value=self.componentTag, dataType="string")

    @classmethod
    def fromContainer(cls, container):
        """ Create a component instance from a container"""
        metaNode = rigamajig2.maya.meta.MetaNode(container)
        name = metaNode.getData("name")
        input = metaNode.getData("input")
        enabled = metaNode.getData("enabled")
        size = metaNode.getData("size")
        rigParent = metaNode.getData("rigParent")
        componentTag = metaNode.getData("componentTag")

        componentInstance = cls(name=name,
                                input=input,
                                enabled=enabled,
                                size=size,
                                rigParent=rigParent,
                                componentTag=componentTag)

        return componentInstance

    def _initalizeComponent(self):
        """
        setup all intialize functions for the component

        process order:
            self.createContainer
        """
        if self.getStep() < INTIALIZE_STEP and self.enabled:
            # fullDict = dict(self.metaData, **self.cmptSettings)
            self.setInitalData()
            self.setStep(1)

        else:
            logger.debug('component {} already initalized.'.format(self.name))

    def _guideComponent(self):
        """
        setup the component guides
        process order:
            self.preScript
            self.createJoints
            self.createBuildGuides
        """
        self._loadComponentParametersToClass()

        if self.getStep() < GUIDE_STEP and self.enabled:
            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.createJoints()
                self.createBuildGuides()
            self.setStep(2)

        else:
            logger.debug('component {} already guided.'.format(self.name))

    def _buildComponent(self):
        """
        build the rig

        process order:
            self.initialHierarchy
            self.preRigSetup
            self.rigSetup
            self.postRigSetup
        """
        self._loadComponentParametersToClass()

        if self.getStep() < BUILD_STEP and self.enabled:

            # anything that manages or creates nodes should set the active container
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.initialHierarchy()
                self.preRigSetup()
                self.rigSetup()
                self.postRigSetup()
                self.setupAnimAttrs()
            self.setStep(3)
        else:
            logger.debug('component {} already built.'.format(self.name))

    def _connectComponent(self):
        """ connect components within the rig"""
        self._loadComponentParametersToClass()

        if self.getStep() < CONNECT_STEP and self.enabled:
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.initConnect()
                self.connect()
                self.postConnect()
            self.setStep(4)
        else:
            logger.debug('component {} already connected.'.format(self.name))

    def _finalizeComponent(self):
        """
        finalize component

         process order:
            self.publishNodes
            self.publishAttributes
            self.finalize
            self.postScripts
        """
        # self._loadComponentParametersToClass()

        if self.getStep() < FINALIZE_STEP and self.enabled:
            self.publishNodes()
            self.publishAttributes()
            with rigamajig2.maya.container.ActiveContainer(self.container):
                self.finalize()
                self.setAttrs()

            # if we added a component tag build that now!
            if self.componentTag:
                rigamajig2.maya.meta.tag(self.container, 'component', self.componentTag)

            self.setStep(5)
        else:
            logger.debug('component {} already finalized.'.format(self.name))

    def _optimizeComponent(self):
        """"""
        # self._loadComponentParametersToClass()

        if self.getStep() != OPTIMIZE_STEP:
            self.optimize()
            self.setStep(6)
        else:
            logger.debug('component {} already optimized.'.format(self.name))

    # --------------------------------------------------------------------------------
    # functions
    # --------------------------------------------------------------------------------
    def createJoints(self):
        """build joints required for the component"""
        pass

    def createBuildGuides(self):
        """Add additional guides"""
        pass

    def setInitalData(self):
        """
        Set inital component data.
        This allows you to set component data within subclasses.
        """
        pass

    def createContainer(self):
        """Create a Container for the component"""
        if not cmds.objExists(self.container):
            self.container = rigamajig2.maya.container.create(self.container)
            rigamajig2.maya.meta.tag(self.container, 'component')

            # tag the container with the proper component version
            rigamajig2.maya.attr.createAttr(self.container, "__version__", "string",
                                            value=self.__version__,
                                            keyable=False,
                                            locked=True
                                            )

    def createMetaNode(self, metaNodeName):
        """Create the metadata node. This will store any data we need to transfer across steps"""
        if not cmds.objExists(metaNodeName):
            self.metadataNode = cmds.createNode(METADATA_NODE_TYPE, name=metaNodeName)
            rigamajig2.maya.meta.createMessageConnection(self.container, self.metadataNode,
                                                         sourceAttr="metaDataNetworkNode")

            rigamajig2.maya.container.addNodes(self.metadataNode, self.container, force=True)

    def initialHierarchy(self):
        """Setup the inital Hirarchy. implement in subclass"""
        self.rootHierarchy = cmds.createNode('transform', n=self.name + '_cmpt')
        self.paramsHierarchy = cmds.createNode('transform', n=self.name + '_params',
                                               parent=self.rootHierarchy)
        self.controlHierarchy = cmds.createNode('transform', n=self.name + '_control',
                                                parent=self.rootHierarchy)
        self.spacesHierarchy = cmds.createNode('transform', n=self.name + '_spaces',
                                               parent=self.rootHierarchy)

        rigamajig2.maya.color.setOutlinerColor(self.rootHierarchy, [255, 255, 153])

        # lock and hide the attributes
        for hierarchy in [self.paramsHierarchy, self.controlHierarchy, self.spacesHierarchy]:
            rigamajig2.maya.attr.lockAndHide(hierarchy, rigamajig2.maya.attr.TRANSFORMS + ['v'])

    def preRigSetup(self):
        """Pre rig setup. implement in subclass"""
        pass

    def rigSetup(self):
        """Add the rig setup. implement in subclass"""
        pass

    def postRigSetup(self):
        """Add the post setup. implement in subclass"""
        pass

    def setupAnimAttrs(self):
        """Setup animation attributes. implement in subclass"""
        pass

    def initConnect(self):
        """initalize the connection. implement in subclass"""
        pass

    def connect(self):
        """create the connection. implement in subclass"""
        pass

    def postConnect(self):
        """any final cleanup after the connection. implement in subclass"""
        pass

    def publishNodes(self):
        """Publush nodes. implement in subclass"""
        rigamajig2.maya.container.addParentAnchor(self.rootHierarchy, container=self.container)
        rigamajig2.maya.container.addChildAnchor(self.rootHierarchy, container=self.container)

        # for the containers we need to publish all controls within a container.
        allNodes = rigamajig2.maya.container.getNodesInContainer(self.container, getSubContained=True)
        for currentNode in allNodes:
            if rigamajig2.maya.meta.hasTag(currentNode, CONTROLTAG):
                rigamajig2.maya.container.addPublishNodes(currentNode)

    def publishAttributes(self):
        """publish attributes. implement in subclass"""
        pass

    def finalize(self):
        """Finalize a component. implement in subclass"""
        pass

    def setAttrs(self):
        """Set attributes. implement in subclass"""
        pass

    def optimize(self):
        """Optimize a component. implement in subclass"""
        pass

    def deleteSetup(self):
        """ delete the rig setup"""
        logger.info("deleting component {}".format(self.name))
        cmds.select(self.container, r=True)
        mel.eval("doDelete;")

        for input in self.input:
            if cmds.objExists(input):
                rigamajig2.maya.attr.unlock(input, rigamajig2.maya.attr.TRANSFORMS + ['v'])

    def setStep(self, step=0):
        """
        set the pipeline step.

        step 0 - unbuilt
        step 1 - initalize component
        step 2 - guide component
        step 3 - build component
        step 4 - connect component
        step 5 - finalize component
        step 6 - optimize component

        :param step:
        :return:
        """
        if not cmds.objExists("{}.{}".format(self.container, 'build_step')):
            rigamajig2.maya.attr.createEnum(self.container, 'build_step', value=0,
                                            enum=['unbuilt', 'initalize', 'guide', 'build', 'connect', 'finalize',
                                                  'optimize'],
                                            keyable=False, channelBox=False)

        cmds.setAttr("{}.{}".format(self.container, 'build_step'), step)

    def getStep(self):
        """
        get the pipeline step
        :return:
        """
        if self.container and cmds.objExists("{}.{}".format(self.container, 'build_step')):
            return cmds.getAttr("{}.{}".format(self.container, 'build_step'))
        return 0

    def defineParameter(self, parameter, value, dataType=None, hide=True, lock=False):
        """
        Define a parameter component. This makes up the core data structure of a component.
        This defines parameters and behaviors and is used to build the rest of the functionality but should NOT define the structre.

        :param str parameter: name of the parameter, This will be accessible through self.parameter in the class
        :param any value: the value of the parameter
        :param dataType: the type of data stored in the value. Default is derived from the value.
        :param bool hide: hide the added parameter from the channel box
        :param bool lock: lock the added parameter
        """

        if not dataType:
            dataType = rigamajig2.maya.meta.validateDataType(value)

        logger.debug(f"adding component parameter {parameter}, {value} ({dataType})")
        self._componentParameters[parameter] = {"value": value, "dataType": dataType}

        metaData = rigamajig2.maya.meta.MetaNode(self.container)
        metaData.setData(attr=parameter, value=value, attrType=dataType, hide=hide, lock=lock)

        setattr(self.__class__, parameter, value)

    def _getLocalComponentVariables(self):
        """Get a list of class variables"""

        localComponentVariables = list()
        allClassVariables = self.__dict__.keys()

        for var in allClassVariables:
            # ensure the variable is valid.
            if var in self._componentParameters: continue
            if var.startswith("_"): continue
            if var in ["container", "metadataNode", "metaDataNetworkNode", "componentType"]: continue

            localComponentVariables.append(var)

        return localComponentVariables

    def _stashLocalVariablesToMetadata(self):
        localComponentVariables = self._getLocalComponentVariables()

        localComponentDataDict = {}

        for localVariable in localComponentVariables:
            localComponentDataDict[localVariable] = self.__getattribute__(localVariable)

        metaNode = rigamajig2.maya.meta.MetaNode(self.metadataNode)
        metaNode.setDataDict(localComponentDataDict)

    def _retreiveLocalVariablesFromMetadata(self):
        """
        This function will rebuild the properties based on the data added to the metanode.
        :return:
        """
        metaNode = rigamajig2.maya.meta.MetaNode(self.metadataNode)
        dataDict = metaNode.getAllData()

        for key in dataDict.keys():
            if key in ["metaDataNetworkNode"]:
                continue
            attrPlug = f"{self.metadataNode}.{key}"

            # # TODO: come back to this
            setattr(self.__class__, key, dataDict[key])

    def loadSettings(self, data):
        """
        Load setting data onto the self.metaNode
        :param data: data to store on the self.metaNode
        :return:
        """
        keysToRemove = ['name', 'type', 'input']
        newDict = {key: val for key, val in data.items() if key not in keysToRemove}

        metaNode = rigamajig2.maya.meta.MetaNode(self.container)
        metaNode.setDataDict(newDict)

    def _loadComponentParametersToClass(self):
        """
        loadSettings meta data from the settings node into a dictionary
        """
        newComponentData = OrderedDict()
        for key in self._componentParameters.keys():

            metaNode = rigamajig2.maya.meta.MetaNode(self.container)
            data = metaNode.getAllData()

            if not data:
                data = self._componentParameters

            if key in data.keys():
                setattr(self, key, data[key])
                newComponentData[key] = data[key]

        self._componentParameters.update(newComponentData)

    # GET
    def getContainer(self):
        """
        get the component container
        """
        if cmds.objExists(self.container):
            return self.container
        return None

    def getName(self):
        """Get component name"""
        return self.name

    def getMetaDataNode(self):
        return rigamajig2.maya.meta.getMessageConnection(f"{self.container}.metaDataNetworkNode")

    def getComponentData(self):
        """Get all component Data """
        # create an info dictionary with the important component settings.
        # This is used to save the component to a file
        infoDict = OrderedDict()
        data = self._componentParameters

        for key in list(self._componentParameters.keys()):
            infoDict[key] = data[key]["value"]

        logger.debug(infoDict)
        return infoDict

    def getComponenetType(self):
        """Get the component type"""
        return self.componentType

    # SET
    def setName(self, value):
        """Set the component name"""
        self.name = value

    def setContainer(self, value):
        """Set the component container"""
        self.container = value

    # @staticmethod
    # def __getPropertyValue(propertyPlug):
    #     """used to dynamically get the value of a property"""
    #     propertyHolderNode, propertyAttr = propertyPlug.split(".")
    #
    #     def getter(self):
    #         metaNode = rigamajig2.maya.meta.MetaNode(propertyHolderNode)
    #         return metaNode.getData(propertyAttr)
    #
    #     return getter
    #
    # @staticmethod
    # def __setPropertyValue(propertyPlug):
    #     """Used to dynamically set the value of a propery"""
    #     propertyHolderNode, propertyAttr = propertyPlug.split(".")
    #
    #     def setter(self, value):
    #         metaNode = rigamajig2.maya.meta.MetaNode(propertyHolderNode)
    #         return metaNode.setData(propertyAttr, value=value)
    #
    #     return setter

    @classmethod
    def testBuild(cls, cmpt):
        """
        Static method to run the initialize, build, connect, finalize and optimize steps
        :param cmpt: component to test the build.
        :return:
        """
        cmpt._initalizeComponent()
        cmpt._guideComponent()
        cmpt._buildComponent()
        cmpt._connectComponent()
        cmpt._finalizeComponent()
        cmpt._optimizeComponent()
