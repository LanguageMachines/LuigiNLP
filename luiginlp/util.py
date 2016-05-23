import os
import shutil
import glob

DISALLOWINSHELLSAFE = ('|','&',';','!','<','>','{','}','`','\n','\r','\t')

def replaceextension(filename, oldextensions, newextension):
    if newextension[0] != '.':
        newextension = '.' + newextension
    if isinstance(oldextensions, str): oldextensions = (oldextensions,)
    for oldextension in oldextensions:
        oldextension = oldextension.lower()
        if oldextension[0] != '.':
            oldextension = '.' + oldextension
        if filename.lower().endswith(oldextension):
            filename = filename[:-len(oldextension)]
    return filename + newextension

def escape(s, quote):
    s2 = ""
    for i, c in enumerate(s):
        if c == quote:
            escapes = 0
            j = i - 1
            while j > 0:
                if s[j] == "\\":
                    escapes += 1
                else:
                    break
                j -= 1
            if escapes % 2 == 0: #even number of escapes, we need another one
                s2 += "\\"
        s2 += c
    return s2

def shellsafe(s, quote="'", doescape=True):
    """Returns the value string, wrapped in the specified quotes (if not empty), but checks and raises an Exception if the string is at risk of causing code injection"""
    if len(s) > 1024:
        raise ValueError("Variable value rejected for security reasons: too long")
    if quote:
        if quote in s:
            if doescape:
                s = escape(s,quote)
            else:
                raise ValueError("Variable value rejected for security reasons: " + s)
        return quote + s + quote
    else:
        for c in s:
            if c in DISALLOWINSHELLSAFE:
                raise ValueError("Variable value rejected for security reasons: " + s)
        return s

class DirectoryHandler:
    """DirectoryHandler abstracts for a process that output to a directory. It uses a temporary directory and renames it to the final result only when all is completed successfully"""

    def __init__(self, destinationdir):
        self.destinationdir = destinationdir
        self.directory = destinationdir + '.tmp'

    def __enter__(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        os.mkdir(self.directory)
        return self

    def __exit__(self, type, value, traceback):
        if not isinstance(value, Exception):
            os.rename(self.directory,self.destinationdir)
        else:
            shutil.rmtree(self.directory)

    def collectoutput(self, mask):
        for file in glob.glob(mask):
            shutil.move(file, self.directory)



