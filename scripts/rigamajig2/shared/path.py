"""
This module contains path utilities
"""
import os
import pathlib


def cleanPath(path):
    """
    Cleanup a given path to work how it should.
    :param path: path to clean
    :returns: cleanup up path
    :rtype: str
    """

    myPath = pathlib.Path(path)
    resolvedPath = myPath.absolute()

    return str(resolvedPath)


def isFile(path):
    """Check if the path is a file"""
    if isinstance(path, (list, tuple)):
        path = path[0]

    if not path: return False
    root, ext = os.path.splitext(path)
    if ext:
        return True
    else:
        return False


def isDir(path):
    """Check if the path is a directory"""
    if isinstance(path, (list, tuple)):
        path = path[0]

    if not path: return False
    root, ext = os.path.splitext(path)
    if ext:
        return False
    else:
        return True


def getRelativePath(path, start):
    """
    :param path:
    :param start:
    :return:
    """
    return os.path.relpath(path, start)


def getAbsoultePath(rel, start):
    """
    :param rel: relative path
    :param start: path to start from
    :return: abs path
    """

    absoultePath = os.path.join(start, rel)
    normalizedPath = os.path.normpath(absoultePath)

    return normalizedPath

def validatePathExists(filepath:str) -> bool:
    """
    Check to see if a file path is passed in and exists

    :param filepath: name of the file path to check.
    :return: boolean if the filepath is real and exists or not.
    """
    if not filepath:
        return False
    if not os.path.exists(filepath):
        return False

    return True