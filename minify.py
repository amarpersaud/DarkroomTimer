from csscompressor import compress
import os
from jsmin import jsmin

dirsToCheck = ["./css", "./js"]

class cd:
  """Context manager for changing the current working directory"""
  def __init__(self, newPath):
    self.newPath = os.path.expanduser(newPath)
  def __enter__(self):
    self.savedPath = os.getcwd()
    os.chdir(self.newPath)
  def __exit__(self, etype, value, traceback):
    os.chdir(self.savedPath)

def checkDir(direct):
    for root, subdirs, files in os.walk(direct):
        if '.git' in subdirs:
            subdirs.remove('.git')
        for filename in files:
            if(filename.endswith(".css") & (".min." not in filename)):
                cssfpath = os.path.join(root, filename)
                g = open(cssfpath, 'r')
                f = g.read()
                d = compress(f)
                with open(os.path.join(root, filename[:filename.rfind(".css")] + ".min.css"), 'w') as a:
                    a.write(d)
                print("Succeeded in compressing: " + filename)
            elif (filename.endswith(".js") & (".min." not in filename)):
                cssfpath = os.path.join(root, filename)
                g = open(cssfpath, 'r')
                f = g.read()
                d = jsmin(f)
                with open(os.path.join(root, filename[:filename.rfind(".js")] + ".min.js"), 'w') as a:
                    a.write(d)
                print("Succeeded in compressing: " + filename)
                
for d in dirsToCheck:
    checkDir(d)