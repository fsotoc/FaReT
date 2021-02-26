# makehuman client
# Jason Hays
from . import communicator
from . import commons
import log
import numpy as np

def do_tweak(similarity_score, curr_params, special_key, out_path, settings, image_count):
    # if they somehow perfectly match, then stop
    if similarity_score == 1:
        return None
    # if they are highly similar, make smaller changes
    dissimilarity = 1.0 - similarity_score
    
    params = {}
    for param in curr_params:
        if param == special_key:
            params[param] = curr_params[param] + np.random.normal(0, dissimilarity)
        else:
            params[param] = curr_params[param]
    commons.updateModelingParameters(params)
    path = commons.render(out_path, settings, image_count)
    return path, params

# save the model using curr_params
def save_model_and_stop(out_path, name):
    commons.updateModelingParameters(curr_params)
    out_name = os.path.join(outpath, name)
    commons.save_model(out_name)
    return out_name+".mhm"

def do_op(out_path, name, settings):  
    image_count = 0
    
    # message constants
    CHOICE_ONE = '1'
    CHOICE_TWO = '2'
    CHOICE_NEITHER = '3'
    TWEAK_IMAGES = '4'
    CHANGE_KEY = '5'
    NO_OP = '7'
    STOP_SAVE = '8'

    # open a clientside connection
    com = communicator.Communicator(server = False)
    # get the current parameters of the face shape
    curr_params = commons.get_shape_params()
    # save a render of the current model
    initial_path = commons.render(out_path, settings, image_count)
    image_count+=1
    # send the average render so the server can compute similarity scores
    log.message("Sending initial rendered image")
    com.send(initial_path)
    log.message("Receiving Initial Request")
    request_type = com.get_message()
    log.message("Received request "+ request_type)
    face_param_names = np.unique(["cheek/r-cheek-bones-decr|incr", "cheek/r-cheek-inner-decr|incr", "cheek/r-cheek-trans-down|up", "cheek/r-cheek-volume-decr|incr", "cheek/r-cheek-bones-decr|incr", "cheek/r-cheek-inner-decr|incr", "cheek/r-cheek-trans-down|up", "cheek/r-cheek-volume-decr|incr", "chin/chin-bones-decr|incr", "chin/chin-cleft-decr|incr", "chin/chin-height-decr|incr", "chin/chin-jaw-drop-decr|incr", "chin/chin-prognathism-decr|incr", "chin/chin-prominent-decr|incr", "chin/chin-width-decr|incr", "ears/r-ear-flap-decr|incr", "ears/r-ear-lobe-decr|incr", "ears/r-ear-rot-backward|forward", "ears/r-ear-scale-decr|incr", "ears/r-ear-scale-depth-decr|incr", "ears/r-ear-scale-vert-decr|incr", "ears/r-ear-shape-pointed|triangle", "ears/r-ear-shape-square|round", "ears/r-ear-trans-backward|forward", "ears/r-ear-trans-down|up", "ears/r-ear-wing-decr|incr", "ears/r-ear-flap-decr|incr", "ears/r-ear-lobe-decr|incr", "ears/r-ear-rot-backward|forward", "ears/r-ear-scale-decr|incr", "ears/r-ear-scale-depth-decr|incr", "ears/r-ear-scale-vert-decr|incr", "ears/r-ear-shape-pointed|triangle", "ears/r-ear-shape-square|round", "ears/r-ear-trans-backward|forward", "ears/r-ear-trans-down|up", "ears/r-ear-wing-decr|incr", "eyebrows/eyebrows-angle-down|up", "eyebrows/eyebrows-trans-backward|forward", "eyebrows/eyebrows-trans-down|up", "eyes/r-eye-bag-decr|incr", "eyes/r-eye-bag-height-decr|incr", "eyes/r-eye-bag-in|out", "eyes/r-eye-corner1-down|up", "eyes/r-eye-corner2-down|up", "eyes/r-eye-epicanthus-in|out", "eyes/r-eye-eyefold-angle-down|up", "eyes/r-eye-eyefold-concave|convex", "eyes/r-eye-eyefold-down|up", "eyes/r-eye-height1-decr|incr", "eyes/r-eye-height2-decr|incr", "eyes/r-eye-height3-decr|incr", "eyes/r-eye-push1-in|out", "eyes/r-eye-push2-in|out", "eyes/r-eye-scale-decr|incr", "eyes/r-eye-trans-down|up", "eyes/r-eye-trans-in|out", "eyes/r-eye-bag-decr|incr", "eyes/r-eye-bag-height-decr|incr", "eyes/r-eye-bag-in|out", "eyes/r-eye-corner1-down|up", "eyes/r-eye-corner2-down|up", "eyes/r-eye-epicanthus-in|out", "eyes/r-eye-eyefold-angle-down|up", "eyes/r-eye-eyefold-concave|convex", "eyes/r-eye-eyefold-down|up", "eyes/r-eye-height1-decr|incr", "eyes/r-eye-height2-decr|incr", "eyes/r-eye-height3-decr|incr", "eyes/r-eye-push1-in|out", "eyes/r-eye-push2-in|out", "eyes/r-eye-scale-decr|incr", "eyes/r-eye-trans-down|up", "eyes/r-eye-trans-in|out", "forehead/forehead-nubian-decr|incr", "forehead/forehead-scale-vert-decr|incr", "forehead/forehead-temple-decr|incr", "forehead/forehead-trans-backward|forward", "head/head-age-decr|incr", "head/head-angle-in|out", "head/head-back-scale-depth-decr|incr", "head/head-diamond", "head/head-fat-decr|incr", "head/head-invertedtriangular", "head/head-oval", "head/head-rectangular", "head/head-round", "head/head-scale-depth-decr|incr", "head/head-scale-horiz-decr|incr", "head/head-scale-vert-decr|incr", "head/head-square", "head/head-trans-backward|forward", "head/head-trans-down|up", "head/head-trans-in|out", "head/head-triangular", "macrodetails-universal/Muscle", "macrodetails-universal/Weight", "macrodetails/African", "macrodetails/Age", "macrodetails/Asian", "macrodetails/Caucasian", "macrodetails/Gender", "mouth/mouth-angles-down|up", "mouth/mouth-cupidsbow-decr|incr", "mouth/mouth-cupidsbow-width-decr|incr", "mouth/mouth-dimples-in|out", "mouth/mouth-laugh-lines-in|out", "mouth/mouth-lowerlip-ext-down|up", "mouth/mouth-lowerlip-height-decr|incr", "mouth/mouth-lowerlip-middle-down|up", "mouth/mouth-lowerlip-volume-decr|incr", "mouth/mouth-lowerlip-width-decr|incr", "mouth/mouth-philtrum-volume-decr|incr", "mouth/mouth-scale-depth-decr|incr", "mouth/mouth-scale-horiz-decr|incr", "mouth/mouth-scale-vert-decr|incr", "mouth/mouth-trans-backward|forward", "mouth/mouth-trans-down|up", "mouth/mouth-trans-in|out", "mouth/mouth-upperlip-ext-down|up", "mouth/mouth-upperlip-height-decr|incr", "mouth/mouth-upperlip-middle-down|up", "mouth/mouth-upperlip-volume-decr|incr", "mouth/mouth-upperlip-width-decr|incr", "neck/neck-back-scale-depth-decr|incr", "neck/neck-double-decr|incr", "neck/neck-scale-depth-decr|incr", "neck/neck-scale-horiz-decr|incr", "neck/neck-scale-vert-decr|incr", "neck/neck-trans-backward|forward", "neck/neck-trans-down|up", "neck/neck-trans-in|out", "nose/nose-base-down|up", "nose/nose-compression-compress|uncompress", "nose/nose-curve-concave|convex", "nose/nose-flaring-decr|incr", "nose/nose-greek-decr|incr", "nose/nose-hump-decr|incr", "nose/nose-nostrils-angle-down|up", "nose/nose-nostrils-width-decr|incr", "nose/nose-point-down|up", "nose/nose-point-width-decr|incr", "nose/nose-scale-depth-decr|incr", "nose/nose-scale-horiz-decr|incr", "nose/nose-scale-vert-decr|incr", "nose/nose-septumangle-decr|incr", "nose/nose-trans-backward|forward", "nose/nose-trans-down|up", "nose/nose-trans-in|out", "nose/nose-volume-decr|incr", "nose/nose-width1-decr|incr", "nose/nose-width2-decr|incr", "nose/nose-width3-decr|incr"])
    special_key = np.random.choice(face_param_names)
    while True:
        #try:
        
        if request_type == TWEAK_IMAGES:
            log.message("Receiving Similarity")
            similarity = com.get_message()
            log.message("Similarity score "+ similarity)
            
            
            img_path1, params1 = do_tweak(float(similarity), curr_params, special_key, out_path, settings, image_count)
            image_count+=1
            img_path2, params2 = do_tweak(float(similarity), curr_params, special_key, out_path, settings, image_count)
            image_count+=1
            # send the paths to the images
            log.message("Sending rendered image paths")
            com.send(img_path1, img_path2)

            choice = com.get_message()
            while choice == NO_OP:
                choice = com.get_message()
            if choice == CHOICE_ONE:
                curr_params = params1
            elif choice == CHOICE_TWO:
                curr_params = params2
            elif choice == CHOICE_NEITHER:
                pass    
            elif choice == CHANGE_KEY:
                special_key = np.random.choice(face_param_names)
            elif choice == STOP_SAVE:
                com.send(save_model_and_stop(out_path, name))
                break
            else:
                com.close()
                raise(Exception("ERROR -- invalid choice message", choice))
        else:
            com.close()
            raise(Exception("ERROR -- invalid request message", request_type))
        log.message("Receiving Request")
        request_type = com.get_message()
        log.message("Received request "+ request_type)
        #except:
        #    break
    com.close()