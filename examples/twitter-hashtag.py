#!/usr/bin/env python

#made by @mrglennjones with help from @pimoroni & pb

import time
import unicodedata
try:
    import queue
except ImportError:
    import Queue as queue
from sys import exit

try:
    import tweepy
except ImportError:
    exit("This script requires the tweepy module\nInstall with: sudo pip install tweepy")

import scrollphathd
from scrollphathd.fonts import font5x7


# adjust the tracked keyword below to your keyword or #hashtag
keyword = '#bilgetank'

# enter your twitter app keys here
# you can get these at apps.twitter.com
consumer_key = ''
consumer_secret = ''

access_token = ''
access_token_secret = ''

if consumer_key == '' or consumer_secret == '' or access_token == '' or access_token_secret == '':
    print("You need to configure your Twitter API keys! Edit this file for more information!")
    exit(0)

# make FIFO queue
q = queue.Queue()

# Display a progress bar for seconds
# Displays a dot if False
DISPLAY_BAR = False

# define main loop to fetch formatted tweet from queue
def mainloop():
    scrollphathd.rotate(degrees=180)
    scrollphathd.clear()
    scrollphathd.show()

    while True:
        # grab the tweet string from the queue
        try:
            scrollphathd.clear()
            status = q.get(False)

            if not status:
                # Grab the "seconds" component of the current time
                # and convert it to a range from 0.0 to 1.0
                float_sec = (time.time() % 60) / 59.0

                # Multiply our range by 15 to spread the current
                # number of seconds over 15 pixels.
                #
                # 60 is evenly divisible by 15, so that
                # each fully lit pixel represents 4 seconds.
                #
                # For example this is 28 seconds:
                # [x][x][x][x][x][x][x][ ][ ][ ][ ][ ][ ][ ][ ]
                #  ^ - 0 seconds                59 seconds - ^
                seconds_progress = float_sec * 15

                if DISPLAY_BAR:
                    # Step through 15 pixels to draw the seconds bar
                    for y in range(15):
                        # For each pixel, we figure out its brightness by
                        # seeing how much of "seconds_progress" is left to draw
                        # If it's greater than 1 (full brightness) then we just display 1.
                        current_pixel = min(seconds_progress, 1)

                        # Multiply the pixel brightness (0.0 to 1.0) by our global brightness value
                        scrollphathd.set_pixel(y + 1, 6, current_pixel * BRIGHTNESS)

                        # Subtract 1 now we've drawn that pixel
                        seconds_progress -= 1

                        # If we reach or pass 0, there are no more pixels left to draw
                        if seconds_progress <= 0:
                            break

                else:
                    # Just display a simple dot
                    scrollphathd.set_pixel(int(seconds_progress), 6, BRIGHTNESS)

                # Display the time (HH:MM) in a 5x5 pixel font
                scrollphathd.write_string(
                    time.strftime("%H:%M"),
                    x=0, # Align to the left of the buffer
                    y=0, # Align to the top of the buffer
                    font=font5x5, # Use the font5x5 font we imported above
                    brightness=BRIGHTNESS # Use our global brightness value
                )

                # int(time.time()) % 2 will tick between 0 and 1 every second.
                # We can use this fact to clear the ":" and cause it to blink on/off
                # every other second, like a digital clock.
                # To do this we clear a rectangle 8 pixels along, 0 down,
                # that's 1 pixel wide and 5 pixels tall.
                if int(time.time()) % 2 == 0:
                    scrollphathd.clear_rect(8, 0, 1, 5)

                # Display our time and sleep a bit. Using 1 second in time.sleep
                # is not recommended, since you might get quite far out of phase
                # with the passing of real wall-time seconds and it'll look weird!
                #
                # 1/10th of a second is accurate enough for a simple clock though :D
                scrollphathd.show()
                time.sleep(0.1)
            else:
                scrollphathd.write_string(status,font=font5x7, brightness=0.1)
                status_length = scrollphathd.write_string(status, x=0, y=0,font=font5x7, brightness=0.1)
                time.sleep(0.25)

                while status_length > 0:
                    scrollphathd.show()
                    scrollphathd.scroll(1)
                    status_length -= 1
                    time.sleep(0.02)


                scrollphathd.clear()
                scrollphathd.show()
                time.sleep(0.25)

                q.task_done()

        except queue.Empty:
            time.sleep(1)

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        if not status.text.startswith('RT'):
            # format the incoming tweet string
            status = u'     >>>>>     @{name}: {text}     '.format(name=status.user.screen_name.upper(), text=status.text.upper())
            try:
                status = unicodedata.normalize('NFKD', status).encode('ascii', 'ignore')
            except BaseException as e:
                print(e)

            # put tweet into the fifo queue
            q.put(status)

    def on_error(self, status_code):
        print("Error: {}".format(status_code))
        if status_code == 420:
            return False


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)

myStream.filter(track=[keyword], stall_warnings=True, async=True)


try:
    mainloop()

except KeyboardInterrupt:
    myStream.disconnect()
    del myStream
    print("Exiting!")
