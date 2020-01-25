from py_client import PythonMHC
makehuman = PythonMHC()
import atexit
# when the session ends (even by error), close the link, but keep the server alive, waiting for the next PsychoPy run.
# at the end of a run, makehuman.close() will send the string, 'exit', 
#  to tell MakeHuman's server to wait for another connection from PsychoPy.
atexit.register(makehuman.close)

# retrieve the shape parameter dictionary
# makehuman.get_model_params() has all of the shape parameters as keys
params = makehuman.get_model_params()
# change the camera target to the face.
makehuman.setFaceCamera()
# zoom out by "10"
makehuman.zoom(10)
# zooming in uses negative numbers.
#makehuman.zoom(-10)
# orbit the camera to the left.
makehuman.rotateCamera(0,45)
#makehuman.setCamera(0,45)

# rotate camera is relative to the current position,
# but set camera takes the current position into account to negate it.
'''
# doing:
makehuman.setCamera(0,0)
makehuman.rotateCamera(0,45)
makehuman.rotateCamera(0,45)
# is the same as:
makehuman.setCamera(0,90)
'''

# alter the params so that they have a large forehead
params['forehead/forehead-scale-vert-decr|incr'] = 1.0
params['nose/nose-scale-vert-decr|incr'] = 1.0
# set and update the model's shape parameters
makehuman.set_model_params(params)

# expression parameters are separate from shape parameters.
# if you do not want to load mhpose files, neutral always uses 0's
neutral = dict(RightInnerBrowUp=0)
# however, you don't _have_ to use neutral as a starting point,
#  so you can change what the interpolation percentages
#  mean by altering the starting point.
# other = dict(RightInnerBrowUp=.5)
brow_expression = dict(RightInnerBrowUp=1)
# the arguments are: starting point, ending point, percentage.
makehuman.set_expression(neutral, brow_expression, 75)
# if you just want to set an expression without interpolating, 
# you can use the same one twice at 100 percent.
# makehuman.set_expression(brow_expression, brow_expression, 100)

makehuman.send('shutdown')