
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
