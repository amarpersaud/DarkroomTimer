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
                    
    #Parse HTML file and insert included HTML files
    def ParseHTML(self, root, filename):
        file_path = os.path.join(root, filename)
        html = "<html><body><include href=\"/nav.html\"/></body></html>"
        
        #open and read the html file
        with open(file_path, 'rb') as f:
            html = f.read()
        
        print("Opened file and read text")
        
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
                print("Relative to file")
                includefilepath = os.path.join(root, href)
            else:   
                #else relative to root / 
                print("Relative to root")
                includefilepath = os.path.join(href)
            
            print("\tInclude filepath: {}".format(includefilepath))
            
            replacementText = ""
            with open(includefilepath, 'rb') as incf:
                replacementText = incf.read()
                
            inc.replace_with(BeautifulSoup(replacementText, "html.parser"))
        
        return soup.prettify().encode('utf-8')
    
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
        
        #Handle the files.
        for f in files: 
            #Make sure the modified event is for the file and not the parent directory.
            if(os.path.isfile(f) and (".git" not in f)): # Also ensure not a git file
                print(f"File is {f}")   
                #ignore python files. Case not necessary but nice to know
                if(f.endswith(".py")):
                    print("python file, ignoring")
                #Minify css and js files
                if( (f.endswith(".css") and not f.endswith(".min.css")) or (f.endswith(".js") and not f.endswith(".min.js"))):
                    print(f"css or js file changed, recompile: {f}")
                    for d in MinifyDirectories:
                        self.CheckDirectory(d)
                #Compile html files if they are part of the inc or 
                if(f.endswith(".html")):
                    #Only recompile if source or included html has changed.
                    if(f.startswith(HTML_SRC_LOCATION) or f.startswith(HTML_INC_LOCATION)):
                        for root, subdirs, files in os.walk(HTML_SRC_LOCATION):
                            if '.git' in subdirs:
                                subdirs.remove('.git')
                            for filename in files:
                                if(filename.endswith(".html")):
                                    print("Found html file: {} {}".format(root, filename))
                                    parsedHTML = self.ParseHTML(root, filename)
                                    newFilepath = os.path.join("./", root[len(HTML_SRC_LOCATION)+1:], filename)
                                    print("New filepath: {}".format(newFilepath))
                                    with open(newFilepath, 'wb') as nf:
                                        nf.write(parsedHTML)
                    else:
                        print("Not SRC or INC file. Ignoring")
                handledFiles = handledFiles + 1
        print(f"Handled {handledFiles} events at t={datetime.now()}")

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

