# brave_ad_clicker
A Python bot to automatically close ads on the Brave browser

`pip install -r requirements.txt`

`python ad_clicker.py`

Algorithm:
1. Take a screen shot
2. Perform a sliding box evaluation comparing sub-frames to a template
3. click on the best match
4. move mouse back to original position

![](last_screen.png)
