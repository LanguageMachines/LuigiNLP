from sciluigi import ExternalTask, TargetInfo
from luigi import Parameter

class FoLiAInput(ExternalTask):
    basename= Parameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.folia.xml')

class TEIInput(ExternalTask):
    basename= Parameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.tei.xml')

class PlainTextInput(ExternalTask):
    """Untokenised plain text documents"""
    basename= Parameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.txt')

class ReStructuredTextInput(ExternalTask):
    """ReStructuredText plain text documents"""
    basename= Parameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.rst')

class WordInput(ExternalTask):
    basename= Parameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.docx')

class WordInput_legacy(ExternalTask):
    basename= Parameter()
    def out_default(self):
        return TargetInfo(self, self.basename + '.doc')
