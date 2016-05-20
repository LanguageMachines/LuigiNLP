from sciluigi import ExternalTask, TargetInfo
from luigi import Parameter
from piccl.engine import InputFormat, registerformat

class FoLiAInput(InputFormat):
    id='folia'
    extension='folia.xml'
    basename= Parameter()

    def out_folia(self):
        return self.target()

registerformat(FoLiAInput)

class TEIInput(InputFormat):
    id='tei'
    extension='tei.xml'
    basename= Parameter()

    def out_tei(self):
        return self.target()

registerformat(TEIInput)

class PlainTextInput(InputFormat):
    """Untokenised plain text documents"""
    id='txt'
    extension = 'txt'
    basename= Parameter()

    def out_txt(self):
        return self.target()

registerformat(PlainTextInput)

class ReStructuredTextInput(InputFormat):
    """ReStructuredText plain text documents"""
    id='rst'
    extension='rst'
    basename= Parameter()

    def out_rst(self):
        return self.target()

registerformat(ReStructuredTextInput)

class WordInput(InputFormat):
    id='docx'
    extension='docx'
    basename= Parameter()

    def out_docx(self):
        return self.target()

registerformat(WordInput)

class AlpinoDocDirInput(InputFormat):
    """Represents a directory, corresponding to a document, with Alpino XML files, one per sentence, numbered"""
    id='alpinodocdir'
    extension='alpinodocdir'
    basename = Parameter()
    directory=True

    def out_alpinodocdir(self):
        return self.target()
