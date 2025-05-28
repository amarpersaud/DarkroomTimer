#!/usr/bin/python

### Watches directories for changes to .css, .js and .html files and automatically recompiles the file.
###

import os
import time 

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

MinifyDirectories = ["./css", "./js", "./fonts"]

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        #print(f'event type: {event.event_type}  path : {event.src_path}')
        if(event.src_path.endswith(".py")):
            print("python file, ignoring")
        if( (event.src_path.endswith(".css") and not event.src_path.endswith(".min.css")) or (event.src_path.endswith(".js") and not event.src_path.endswith(".min.js"))):
            print(f"css or js file changed, recompile: {event.src_path}")
            for d in MinifyDirectories:
                self.CheckDirectory(d)
        if(event.src_path.endswith(".html")):
            s = event.src_path.replace("\\", "/")
            if(s.count("/") > 1):   #Only if change is in a subdirectory
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
        
if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    
    #Move up a directory
    os.chdir("../")
    observer.schedule(event_handler, path='./', recursive=True) #watch parent directory
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

