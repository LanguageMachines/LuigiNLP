from sciluigi import ExternalTask, TargetInfo
from luigi import StringParameter

class FoLiAInput(ExternalTask):
    basename= StringParameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.folia.xml')

class TEIInput(ExternalTask):
    basename= StringParameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.tei.xml')

class PlainTextInput(ExternalTask):
    """Untokenised plain text documents"""
    basename= StringParameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.txt')

class WordInput(ExternalTask):
    basename= StringParameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.docx')

class WordInput_legacy(ExternalTask):
    basename= StringParameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.doc')
