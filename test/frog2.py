import luiginlp
from luiginlp.modules.frog import Frog
luiginlp.run(Frog(inputfile="test.rst"), Frog(inputfile="test2.rst"))
