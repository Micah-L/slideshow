#!/usr/bin/env py

import os
import platform
import sys
from collections import deque
from itertools import cycle
import random
import time
import subprocess

### config ###
#
# List some folders here for the slide show to pick from
image_folders = ['C:\\Data\\Photo\\Random Wallpaper']


# Set to True to show images in random order. Set to False to show images in order by path name.
random_order = True

# Set image_delay to the number of seconds to wait between images. Can be changed after the app starts.
image_delay = 5

### end config ###


try:
    import tkinter as tk
except ImportError:  # Python 2
    import Tkinter as tk  # $ sudo apt-get install python-tk

from PIL import Image  # $ pip install pillow
from PIL import ImageTk

psutil = None  # avoid "redefinition of unused 'psutil'" warning
try:
    import psutil
except ImportError:
    pass



class Slideshow(object):

    def __init__(self, parent, filenames, slideshow_delay=5, history_size=20, min_W = float('Inf'), min_H = float('Inf')):
        self._history_size = history_size
        self.ma = parent.winfo_toplevel()
        self.filenames = cycle(filenames)  # loop forever
        self._last_changed = 0
        self._files = deque(maxlen=2*history_size)  # for prev/next files
        for _ in range(2*history_size):
            self._files.append(next(self.filenames))
        self._photo_image = None  # must hold reference to PhotoImage
        self._id = None  # used to cancel pending show_image() callbacks
        self.imglbl = tk.Label(parent, bg="black")  # it contains current image
        # label occupies all available space
        self.imglbl.pack(fill=tk.BOTH, expand=True)
        self.slideshow_delay = slideshow_delay
        self.paused = False

        # start slideshow on the next tick
        self.imglbl.after(1, self._slideshow)

    def _slideshow(self):
        print("in _slideshow")
        print("self._id: \t {}".format(self._id))
        now = time.time()
        print("time now:\t{}\tlast:\t{}\tdiff:\t{}".format(now,self._last_changed,now-self._last_changed))
        if self.paused:
            if self._id is not None:
                self.imglbl.after_cancel(self._id)
            self._id = self.imglbl.after(self.slideshow_delay*1000, self._slideshow)
            
        elif now - self._last_changed < self.slideshow_delay:
            t = int(max(0,self.slideshow_delay - now + self._last_changed)*1000)
            print("Calling again after {} ms".format(t))
            if self._id is not None:
                self.imglbl.after_cancel(self._id)
            self._id = self.imglbl.after(t, self._slideshow)       
            return
        else:
            self._files.append(next(self.filenames))
            #self._files.rotate(-1)
            self.show_image()
            self._last_changed = time.time()
            if self._id is not None:
                self.imglbl.after_cancel(self._id)
            self._id = self.imglbl.after(self.slideshow_delay*1000, self._slideshow)

    def show_image(self):
        filename = self._files[self._history_size]
        print("load {}".format(str(filename)))
        image = Image.open(filename)  # note: let OS manage file cache

        # shrink image inplace to fit in the application window
        w, h = self.ma.winfo_width(), self.ma.winfo_height()
        if image.size[0] > w or image.size[1] > h:
            # note: ImageOps.fit() copies image
            # preserve aspect ratio
            if w < 3 or h < 3:  # too small
                return  # do nothing
            image.thumbnail((w - 2, h - 2), Image.ANTIALIAS)

        # note: pasting into an RGBA image that is displayed might be slow
        # create new image instead
        self._photo_image = ImageTk.PhotoImage(image)
        self.imglbl.configure(image=self._photo_image)

        # set application window title
        self.ma.wm_title(filename)

    def _show_image_on_next_tick(self):
        # cancel previous callback schedule a new one
        if self._id is not None:
            self.imglbl.after_cancel(self._id)
        self._id = self.imglbl.after(1, self.show_image)
        
    def pause(self, event_unused = None):
        self.paused = not self.paused
        print("Paused: {}".format(self.paused))

    def next_image(self, event_unused=None):
        self._files.append(next(self.filenames))
        self._show_image_on_next_tick()
        self._last_changed = time.time()
        self.imglbl.after(self.slideshow_delay * 1000, self._slideshow)

    def prev_image(self, event_unused=None):
        self._files.rotate(1)
        self._show_image_on_next_tick()
        self._last_changed = time.time()
        self.imglbl.after(self.slideshow_delay * 1000, self._slideshow)
    def full_screen(self, event_unused=None):
        parent.attributes("-fullscreen", True)			

    def fit_image(self, event=None, _last=[None] * 2):
        """Fit image inside application window on resize."""
        if event is not None and event.widget is self.ma and (
                _last[0] != event.width or _last[1] != event.height):
            # size changed; update image
            _last[:] = event.width, event.height
            self._show_image_on_next_tick()
    
            
    def change_speed(self, event = None, delay = None):
        if delay is not None:
            self.slideshow_delay = delay
            return
        def ok(event=None):
            print(event)
            val = int(e.get())
            if isinstance(val, int) and val > 0:
                self.slideshow_delay = val
                print("Setting image delay to {}".format(val))
            else:
                print("You must enter a positive integer")
            top.destroy()
            
        def cancel(event=None):
            top.destroy()

        print("Slideshow delay is currently set to {}".format(self.slideshow_delay))

        top = tk.Toplevel(self.ma)
        tk.Label(top, text="Set the delay (in seconds)\nCurrent delay is {}".format(self.slideshow_delay)).pack()
        e = tk.Entry(top)
        e.pack(padx=5)
        e.focus_set()
        b = tk.Button(top, text="OK", command=ok)
        b.pack(pady=5)
        e.bind('<Return>',ok)
        e.bind('<Escape>',cancel)
        
    def quit(self, event=None):
        self.ma.quit()
    
    def move_image(self, event=None):
        print("Moving image to trash: {}".format(self._files[self._history_size]))
        with open("deleted_files.txt", "a") as f:
            f.write(self._files[self._history_size] + '\n')

        target = "Trash"

        try:
            os.mkdir(target)
        except FileExistsError:
            pass

        file_path = self._files[self._history_size]
    
        try:
            os.rename(file_path, target + slash + get_filename(file_path))
        except FileNotFoundError:
            pass

            
    def make_favorite(self, event=None):
        print("Favoriting {}".format(self._files[self._history_size]))
        with open("favorites.txt", "a") as f:
            f.write(self._files[self._history_size] + '\n')            
        
### end Slideshow class ###
            
def get_image_files(rootdir):
    for path, dirs, files in os.walk(rootdir):
        dirs.sort()  # traverse directory in sorted order (by name)
        files.sort()  # show images in sorted order
        for filename in files:
            if any(filename.lower().endswith(x) for x in ['.jpg','.jpeg','.gif','.png']):
                yield os.path.join(path, filename)

def get_filename(s):
    return s.split(slash)[-1]



def main():

    root = tk.Tk()
    def alt_full_screen():
        subprocess.Popen([r"SwitchPrimaryDisplays.exe"])
        time.sleep(2)
        root.attributes("-fullscreen", True)
        subprocess.Popen([r"SwitchPrimaryDisplays.exe"])

    ### get image filenames ###
    # image_folders is from config.py
    image_filenames = [x for imagedir in image_folders for x in get_image_files(imagedir)]
    if random_order: 
        random.shuffle(image_filenames)

    ### configure initial size ###
    if platform.system() == "Windows":
        root.wm_state('zoomed')  # start maximized
        slash = '\\' #windows
    else:
        width, height, xoffset, yoffset = 400, 300, 0, 0
        # double-click the title bar to maximize the app
        # or uncomment:

        # # remove title bar
        # root.overrideredirect(True) # <- this makes it hard to kill
        # width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))
        slash = '/' 

    ### start slideshow ###
    try:  
        app = Slideshow(root, image_filenames, slideshow_delay = image_delay)
    except StopIteration:
        sys.exit("no image files found in %r" % (imagedir, ))

    ### configure keybindings ###
    root.bind("<Escape>", lambda _: root.attributes("-fullscreen", False))  
    root.bind('<Down>', lambda _: root.attributes("-fullscreen", False))
    root.bind('<Alt-Key-Up>', lambda _: alt_full_screen() )
    root.bind('<Up>', lambda _: root.attributes("-fullscreen", True))
    root.bind('<Prior>', app.prev_image)
    root.bind('<Left>', app.prev_image)
    root.bind('<Next>', app.next_image)
    root.bind('<Right>', app.next_image)
    root.bind('<space>', app.pause)
    root.bind('<Control-Key-s>', app.change_speed)
    root.bind('<Control-Key-q>', app.quit)
    root.bind('<Control-Key-c>', app.quit)
    root.bind('<Control-Shift-Key-d>',app.move_image)
    root.bind('<Control-Key-f>',app.make_favorite)
    
    # root.bind("<Configure>", app.fit_image)  # fit image on resize
    root.focus_set()
    root.mainloop()
    



if __name__ == '__main__':
    main()
