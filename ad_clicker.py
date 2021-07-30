import os
import time
import platform
import argparse
import datetime

import mss
import mss.tools
import pyautogui
import numpy as np
import soundfile as sf
import sounddevice as sd
import matplotlib.pyplot as plt
from skimage.util import view_as_windows
from skimage import color
from skimage import io

# detect the operating system
if platform.system() == 'Windows':
    my_computer = 'windows'
elif platform.system() == 'Linux':
    raise('This program is not made for Linux... TO DO')
elif platform.system() == 'Darwin':
    my_computer = 'mac'

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Script to close brave ads')
    parser.add_argument('-c','--cadence', action='store', type=float, default=5, help="Operating cadence in seconds")
    parser.add_argument('-t','--template', action='store', type=str, default="brave_template.png", help="Template Image to lock onto")
    parser.add_argument('-s','--stride', action='store', type=int, default=1, help="Stride of the search")
    parser.add_argument('--size', action='store', type=int, default=256, help="Size of the window")
    parser.add_argument('--test', action='store', type=str, default="", help="Test Image")

    args = parser.parse_args()

    print(my_computer)

    # load the image to lock onto
    template = io.imread(os.path.join(my_computer, args.template), as_gray=True)
    tr = template.astype(np.float32)
    tr -= tr.min() # lil preprocessing

    ad_count = 0

    while True:

        with mss.mss() as sct:
            # Use the 1st monitor
            monitor = sct.monitors[0]
            ad_bool = False

            # Capture a bbox
            #bbox = (left, top, right, lower)
            if my_computer == 'windows':
                bbox = (monitor["width"]-args.size, monitor["height"]-args.size,  monitor["width"], monitor["height"])
            elif my_computer == 'mac':
                bbox = (monitor["width"]-args.size, 0,  monitor["width"], args.size)

            # Grab the picture
            print("taking screen shot...")
            if args.test:
                im = io.imread(os.path.join(my_computer,args.test), as_gray=True).astype(np.float32)
            else:
                im = color.rgb2gray(color.rgba2rgb(np.array(sct.grab(bbox)))).astype(np.float32)

            # view as windows
            print("reshaping into windows...")
            im_windows = view_as_windows(im, tr.shape, step=args.stride)  # 4d array
            im_windows_r = im_windows.reshape(-1, tr.shape[0], tr.shape[1]) # 3d array
            im_min = np.min(im_windows_r,axis=(1,2)) # lil preprocessing
            for j in range(im_windows_r.shape[0]):
                im_windows_r[j] -= im_min[j]

            # find the best match
            print('evaluating best match...')
            diff = np.mean((im_windows_r - tr)**2, axis=(1,2)) # 1d array
            diff_map = diff.reshape(im_windows.shape[0], im_windows.shape[1]) # 2d array
            best_match = np.argmin(diff)

            print(f"best match: {diff[best_match]:.2f}")

            # get the coordinates of minimum
            xygrid = np.arange(im_windows_r.shape[0]).reshape(im_windows.shape[0], im_windows.shape[1])
            xycoord = np.argwhere(xygrid == best_match)[0]

            # click the best match
            if diff[best_match] < 0.01:
                ad_count += 1
                ad_bool = True
                print(f"clicking on ad {ad_count}")

                # alert user
                try:
                    data, fs = sf.read("click_tone.wav", dtype='float32')
                    sd.play(data, fs, device=0)
                except:
                    print("error playing click_tone.wav, check device number")
                    pass

                # current mouse position
                mx, my = pyautogui.position()
                
                # move mouse to the best match
                newx = monitor["width"]-im.shape[1] + xycoord[1]*args.stride+tr.shape[1]*0.5
                newy = xycoord[0]*args.stride+tr.shape[0]*0.5
                print(f"ad: {newx}, {newy}")

                pyautogui.moveTo(newx, newy, _pause=False, duration=0.01)

                # click on the best match
                pyautogui.click()

                # move back to original position
                pyautogui.moveTo(mx, my, _pause=False, duration=0.01)

                print("generating image...")
                fig, ax = plt.subplots(2,2,figsize=(7,10))
                fig.suptitle(f"Ad detected: {ad_bool}", fontsize=20)
                ax[0,0].set_title(datetime.datetime.now().isoformat().split('.')[0])
                ax[0,0].imshow(im,vmin=0,vmax=1,cmap='binary_r')
                ax[0,0].plot(xycoord[1]*args.stride+tr.shape[1]*0.5, 
                            xycoord[0]*args.stride+tr.shape[0]*0.5,'rx')
                ax[1,0].set_title("Best Match")
                ax[1,0].imshow(im_windows_r[best_match],vmin=0,vmax=1,cmap='binary_r')

                ax[1,1].set_title("Template")
                ax[1,1].imshow(tr,vmin=0,vmax=1,cmap='binary_r')

                ax[0,1].set_title("Heat Map")
                ax[0,1].imshow(diff_map,vmin=diff.min(),vmax=diff.max(), cmap='jet_r')

                plt.tight_layout()
                plt.savefig("last_screen.png")
                plt.close()

            del im, im_windows, im_windows_r, bbox
            del diff, diff_map, best_match, xycoord, xygrid
        print("sleeping...")
        time.sleep(args.cadence)