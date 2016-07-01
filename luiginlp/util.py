import os
import shutil
import glob
import fnmatch
import logging

DISALLOWINSHELLSAFE = ('|','&',';','!','<','>','{','}','`','\n','\r','\t')

def getlog():
    return logging.getLogger('sciluigi-interface')

log = getlog()

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

    def __init__(self, destinationdir, persist=False):
        self.destinationdir = destinationdir
        self.usetmp = not os.path.exists(self.destinationdir)
        if self.usetmp:
            self.directory = self.destinationdir + '.tmp'
        else:
            self.directory = self.destinationdir
        self.persist=persist



    def __enter__(self):
        log.info("Setting up directory handler " + self.directory + " -> "  + self.destinationdir)
        if self.usetmp and os.path.exists(self.directory) and not self.persist:
            shutil.rmtree(self.directory)
        os.mkdir(self.directory)
        return self

    def __exit__(self, type, value, traceback):
        if self.usetmp:
            if not isinstance(value, Exception):
                log.info("Cleaning up directory handler " + self.destinationdir + " after success")
                os.rename(self.directory,self.destinationdir)
            elif not self.persist:
                log.info("Removing directory handler " + self.directory + " after failure")
                shutil.rmtree(self.directory)

    def collectoutput(self, mask):
        for file in glob.glob(mask):
            shutil.move(file, self.directory)

def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results


def waitforbatch(pids, threads):
    while len(pids) == threads:
        newpids = []
        for pid in pids:
            try:
                os.kill(pid, 0) #checks if process still running, does not kill
            except:
                newpids.append(pid)
        pids = newpids
