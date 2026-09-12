
from core import G
import wavefront
def saveObj(filename):
    wavefront.writeObjFile(filename, G.app.objects[0].mesh)
