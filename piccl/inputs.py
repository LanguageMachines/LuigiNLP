from sciluigi import ExternalTask, TargetInfo
from luigi import Parameter
from piccl.engine import InputFormat, registerformat

@registerformat
class FoLiAInput(InputFormat):
    id='folia'
    extension='folia.xml'
    basename= Parameter()

    def out_folia(self):
        return self.target()

@registerformat
class TEIInput(InputFormat):
    id='tei'
    extension='tei.xml'
    basename= Parameter()

    def out_tei(self):
        return self.target()


@registerformat
class PlainTextInput(InputFormat):
    """Untokenised plain text documents"""
    id='txt'
    extension = 'txt'
    basename= Parameter()

    def out_txt(self):
        return self.target()


@registerforamt
class ReStructuredTextInput(InputFormat):
    """ReStructuredText plain text documents"""
    id='rst'
    extension='rst'
    basename= Parameter()

    def out_rst(self):
        return self.target()


@registerformat
class WordInput(InputFormat):
    id='docx'
    extension='docx'
    basename= Parameter()

    def out_docx(self):
        return self.target()


@registerformat
class PdfInput(InputFormat):
    id='pdf'
    extension='pdf'
    basename= Parameter()

    def out_pdf(self):
        return self.target()


@registerformat
class TiffInput(InputFormat):
    """A collection of TIFF images for document pages"""
    id='tiff'
    extension='tif'
    basename= Parameter()

    def out_tiff(self):
        return self.target()

@registerformat
class TiffDocDirInput(InputFormat):
    """A collection of TIFF images for document pages"""
    id='tiffdocdir'
    extension='tiffdocdir'
    basename= Parameter()

    def out_tiffdir(self):
        return self.target()


@registerformat
class AlpinoDocDirInput(InputFormat):
    """Represents a directory, corresponding to a document, with Alpino XML files, one per sentence, numbered"""
    id='alpinodocdir'
    extension='alpinodocdir'
    basename = Parameter()
    directory=True

    def out_alpinodocdir(self):
        return self.target()
