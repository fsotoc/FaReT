# it makes more sense for MakeHuman
# to host because it is more convenient 
# to start MH and leave it running.
from . import communicator
from socket import error as socketError

# commons.load_pose_modifiers(filename)
# commons.set_pose(modifiers)
# commons.render(out_path, settings, image_count=0)
# commons.get_shape_params()
# commons.updateModelingParameters(dict)
from . import commons

#gui3d.app.loadHumanMHM(value)
import gui3d

def execute(connection):
    funcName, feedback, args = connection.get_message(3)
    func = eval(funcName)
    out = func(*args)
    if feedback:
        connection.send(out)

def wait_for_input():
    shutdown = False
    while not shutdown:
        # accept a connection
        client = communicator.Communicator(sep="|||")
        pass
        # get messages:
        while True:
            try:
                # i.e., exit, execute
                message = client.get_message()
                if message == 'exit':
                    break
                elif message == 'shutdown':
                    shutdown = True
                    break
                elif message == 'execute':
                    execute(client)
                pass
            except socketError as e:
                print(e)
                break
        client.close()

def do_op():
    wait_for_input()