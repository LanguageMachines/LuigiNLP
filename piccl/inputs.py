from sciluigi import ExternalTask, TargetInfo
from luigi import Parameter
from piccl.engine import InputFormat

class FoLiAInput(InputFormat):
    id='folia'
    extension='folia.xml'
    basename= Parameter()

    def out_folia(self):
        return self.target()

class TEIInput(InputFormat):
    id='tei'
    extension='tei.xml'
    basename= Parameter()

    def out_tei(self):
        return self.target()

class PlainTextInput(InputFormat):
    """Untokenised plain text documents"""
    id='txt'
    extension = 'txt'
    basename= Parameter()

    def out_txt(self):
        return self.target()

class ReStructuredTextInput(InputFormat):
    """ReStructuredText plain text documents"""
    id='rst'
    extension='rst'
    basename= Parameter()

    def out_rst(self):
        return self.target()

class WordInput(InputFormat):
    id='docx'
    extension='docx'
    basename= Parameter()

    def out_docx(self):
        return self.target()

