import luiginlp
from luiginlp.modules.frog import Frog
from luiginlp.engine import Parallel, PassParameters
luiginlp.run(Parallel(component='Frog',inputfiles="test.rst,test2.rst",passparameters=PassParameters(skip='p')))
