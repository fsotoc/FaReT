from py_client import PythonMHC
makehuman = PythonMHC()
import atexit
# when the session ends, close the link, but keep the server alive, waiting for the next PsychoPy run.
# at the end of a run, makehuman.close() will send the string, 'exit', 
#  to tell MakeHuman's server to wait for another connection from PsychoPy.
atexit.register(makehuman.close)

# retrieve the shape parameter dictionary
params = makehuman.get_model_params()

# alter the params so that they have a large forehead
params['forehead/forehead-scale-vert-decr|incr'] = 1
# set and update the model's shape parameters
makehuman.set_model_params(params)
#makehuman.send('exit')
makehuman.send('shutdown')