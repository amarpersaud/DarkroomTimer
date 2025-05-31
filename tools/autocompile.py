#!/usr/bin/python

### Watches directories for changes to .css, .js and .html files and automatically recompiles the file.
###

import os
import time 
from datetime import datetime

# File watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#CSS and JS minify
from csscompressor import compress
from jsmin import jsmin

#HTML 
from bs4 import BeautifulSoup
import os
import re

HTML_SRC_LOCATION = "./SRC"
HTML_INC_LOCATION = "./INC"

MinifyDirectories = ["./css", "./js", "./fonts"]

class MyHandler(FileSystemEventHandler):
    EventsList = []
    def on_modified(self, event):
        self.EventsList.append(event)
    def CheckDirectory(self, direct):
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
    def CompressCSSFile(self, filename):
        if(filename.endswith(".css") & (".min." not in filename)):
            with open(filename, 'r') as g:
                f = g.read()
                d = compress(f)
                with open(filename[:filename.rfind(".css")] + ".min.css", 'w') as a:
                    a.write(d)     
                    print("Succeeded in compressing: " + filename)
    def CompressJSFile(self, filename):
        if(filename.endswith(".js") & (".min." not in filename)):
            with open(filename, 'r') as g:
                f = g.read()
                d = jsmin(f)
                with open(filename[:filename.rfind(".js")] + ".min.js", 'w') as a:
                    a.write(d)
                    print("Succeeded in compressing: " + filename)
    #Parse HTML file and insert included HTML files
    def ParseHTML(self, filename):
        html = "<html><body><include href=\"/nav.html\"/></body></html>"
        
        #open and read the html file
        with open(filename, 'rb') as f:
            html = f.read()
            
        #make soup
        soup = BeautifulSoup(html, "html.parser")
        
        #Find all included html files
        includes = soup.find_all('include')
        
        print("Number of include tags: {}".format(len(includes)))
        
        for inc in includes:
            href = inc['href'] #get target file to insert
            includefilepath = ""
            
            print("Include href: {}".format(href))
            
            #relative to the html file
            if(href.startswith(".")):
                includefilepath = os.path.join(os.path.dirname(filename),href)
            else:   
                #else relative to root / 
                includefilepath = "./" + href
            
            replacementText = ""
            with open(includefilepath, 'rb') as incf:
                replacementText = incf.read()
                
            inc.replace_with(BeautifulSoup(replacementText, "html.parser"))
        
        return soup.prettify().encode('utf-8')
    
    def CompileHTMLSRCFile(self, filename):
        print("Found html file: {}".format(filename))
        parsedHTML = self.ParseHTML(filename)
        newFilepath = "." + filename.replace(HTML_SRC_LOCATION, "")
        print("New filepath: {}".format(newFilepath))
        with open(newFilepath, 'wb') as nf:
            nf.write(parsedHTML) 
    def CompileAllHTML(self):
        for root, subdirs, files in os.walk(HTML_SRC_LOCATION):
            if '.git' in subdirs:
                subdirs.remove('.git')
            for filename in files:
                if(filename.endswith(".html")):
                    print("Found html file: {} {}".format(root, filename))
                    parsedHTML = self.ParseHTML(os.path.join(root,filename))
                    newFilepath = os.path.join("./", root[len(HTML_SRC_LOCATION)+1:], filename)
                    print("New filepath: {}".format(newFilepath))
                    with open(newFilepath, 'wb') as nf:
                        nf.write(parsedHTML)     
    def HandleEvents(self): # batch events
        # Deduplicate events
        files = []
        #Loop over queued filemodifiedevents and get the paths. Remove them from the queue.
        initialLength = len(self.EventsList) # use the current length to avoid getting stuck in loop if queue keeps expanding.
        for i in range(initialLength):
            #start from end and work back towards front to modify list in place
            event = self.EventsList.pop(0)
            if not (event.src_path.replace("\\", "/") in files):
                files.append(event.src_path.replace("\\", "/"))
        handledFiles = 0
        
        #If ANY include html file has changed, recompile all HTML Files.
        #If just source files have changed, only recompile changed source files.
        recompileAllHTML = False
        for f in files:
            if(f.startswith(HTML_INC_LOCATION) and f.endswith(".html")):
                recompileAllHTML = True
        if recompileAllHTML:
            print("HTML INC file changed; recompiling all HTML files")
            self.CompileAllHTML()  
        
        #Handle the files.
        for f in files: 
            #Make sure the modified event is for the file and not the parent directory.
            if(os.path.isfile(f) and (".git" not in f)): # Also ensure not a git file
                print(f"Change to file {f}")   
                
                #ignore python files. Case not necessary but nice to know
                if(f.endswith(".py")):
                    print("python file, ignoring")
                    
                #Minify css and js files
                if(f.endswith(".css") and (not f.endswith(".min.css"))):
                    self.CompressCSSFile(f)
                    
                if(f.endswith(".js") and (not f.endswith(".min.js"))):
                    self.CompressJSFile(f)
                    
                #Compile html files if they are part of the inc or 
                if(f.endswith(".html") and f.startswith(HTML_SRC_LOCATION) and not recompileAllHTML):
                    self.CompileHTMLSRCFile(f)
 
        print(f"Handled {len(files)} events at t={datetime.now()}")

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    
    #Move up a directory
    os.chdir("../")
    observer.schedule(event_handler, path='./', recursive=True) #watch parent directory
    observer.start()

    try:
        while True:
            time.sleep(3)
            #process queued files every 3 seconds to avoid repeated filemodiified evnts
            event_handler.HandleEvents()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

