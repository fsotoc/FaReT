import communicator

def add(a, change):
    # just numbers
    if isinstance(a, Number):
        return a + change
    
    summed = {}
    for key in a:
        summed[key] = a[key] + change[key]
    return summed

from numbers import Number
def difference(b, a, bPercent):
    # get the difference between the values
    # if the values are dictionaries, make sure to assign values of 0 when the keys do not exist
    if isinstance(a, Number):
        return b-a

    diff = {}
    for key in b:
        if not key in a:
            a[key] = 0
    for key in a:
        if not key in b:
            b[key] = 0
        
        diff[key] = (b[key] - a[key])*(bPercent/100.)
    return diff
# opens a connection to MH
class PythonMHC(communicator.Communicator):
    def __init__(self, server = False, host='localhost', port=55250, amount=1024, sep="|||"):
        super(PythonMHC, self).__init__(server, host, port, amount, sep)

    # make MakeHuman do arbitrary things with the execute message:
    # funcName -- the string name of the function.
    # feedback (True/False) -- do you expect returned output data?
    # block (True/False): should you get the return message right away, even if it means PsychoPy has to wait?
    #   if block is False and feedback is True,
    #    that means that you need to get the message manually later,
    #    but before getting any other messages!!!
    #   if you have a slow operation and want to do other things in 
    #   PsychoPy in the meantime, then you may not want to block.
    # (args,) -- what is passed to the makehuman function?

    def execute_MH(self, funcName, feedback, block, *args):
        try:
            # pass args as a single message, not multiples as with *
            self.send("execute", funcName, feedback, args)
            if feedback and block:
                return self.get_message()
        except:
            self.send("exit")
        return None

    def close(self):
        self.send("exit")
        super(PythonMHC, self).close()
        
    # these are both examples and helpers: how to use execute_MH()
    def get_render(self, out_path, settings, image_count):
        '''
        settings['scene'] = G.app.scene # this will get set automatically in render if unset
        settings['AA'] = True/False #anti-aliasing -- smoothing by rendering at a larger scale and then downscaling
        settings['dimensions'] = (renderWidth, renderHeight) # how big is the image
        settings['lightmapSSS'] = True/False # do you want cool lighting effects?
        '''
        # commons.render(out_path, settings, image_count)
        img_path = self.execute_MH("commons.render", True, True, out_path, settings, image_count)
        return img_path

    def load_expression(self, emotion_file):
        # load the neutral expression and the expression so you can later get the difference between the two
        neutral_modifiers, _ = self.execute_MH("commons.get_blank_pose", True,True, True)
        emotion_modifiers = self.execute_MH("commons.load_pose_modifiers", True, True,emotion_file)
        return neutral_modifiers, emotion_modifiers

    def set_expression(self, neutral_modifiers, emotion_modifiers, bPercent):
        # compute the appropriate contrast by percentage.
        change = difference(emotion_modifiers, neutral_modifiers, bPercent)
        # add the contrast to the base point.
        expression_dict = add(neutral_modifiers, change)
        # we don't need to get anything from set pose, so just set it.
        self.execute_MH("commons.set_pose", False,False, expression_dict)

    def set_model_params(self, params):
        self.execute_MH("commons.updateModelingParameters", False, False, params)

    def get_model_params(self):
        return self.execute_MH("commons.get_shape_params", True, True)
    def load_model(self, filename):
        self.execute_MH("gui3d.app.loadHumanMHM", False, False, filename)
    def setFaceCamera(self):
        self.execute_MH("gui3d.app.setFaceCamera", False, False)
'''
test = PythonMHC(False, sep="|||")
settings = dict(AA=True, dimensions=(256,256), lightmapSSS=True)
image_number = 0
try:
    #model_params = test.get_model_params()
    neutral, anger = test.load_expression("C:/Users/jason/Documents/_Research/makehuman/expressions/Anger.mhpose")
    test.set_expression(neutral, anger, 50)
    image_path = test.get_render("C:/Users/jason/Documents/_PythonTools/MakeHuman/4_socket_psychopy/", settings, image_number)
except Exception as e:
    print(e)
    test.send("shutdown")
finally:
    test.send("shutdown")
    test.close()
'''