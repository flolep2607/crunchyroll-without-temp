import argparse
import requests
import json
import time
from http import cookiejar
from math import floor
from os.path import exists
import m3u8
from Crypto.Cipher import AES
import cloudscraper


class ProgressBar:
    """
    This class allows you to make easily a progress bar.
    """
    def __init__(self, steps, maxbar=100, title='Chargement',blocsize=1000):
        if steps <= 0 or maxbar <= 0 or maxbar > 200:
            raise ValueError
        self.steps = steps
        self.maxbar = maxbar
        self.title = title
        self.perc = 0
        self._completed_steps = 0
        self.blocsize=blocsize
        self.start_time=time.time()
        # self.update(False)
    def update(self, increase=True):
        if increase:
            self._completed_steps += 1
        self.perc = floor(self._completed_steps / self.steps * 100)
        if self._completed_steps > self.steps:
            self._completed_steps = self.steps
        steps_bar = floor(self.perc / 100 * self.maxbar)
        if steps_bar == 0:
            visual_bar = self.maxbar * ' '
        else:
            visual_bar = (steps_bar - 1) * '═' + '>' + (self.maxbar - steps_bar) * ' '
        speedy=(self._completed_steps*self.blocsize)/(time.time()-self.start_time)
        return self.title + ' [' + visual_bar + '] ' + str(self.perc) + '% '


def cookie_remover(cj,name):
    try:cj.clear(domain=".crunchyroll.com",path="/",name=name)
    except:pass

class NotPremiumError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}

def getter(url,cookie_file=None):
    scraper = cloudscraper.create_scraper(browser='chrome')
    if cookie_file:
        cj=cookiejar.MozillaCookieJar(cookie_file)
        cj.load()
        cookie_remover(cj,"OptanonControl")
        cookie_remover(cj,"__cfduid")
        cookie_remover(cj,"c_visitor")
        scraper.cookies=cj
        print("Cookies miam🍪.. Loaded")
    elif exists("cookies.txt"):
        cj=cookiejar.MozillaCookieJar("cookies.txt")
        cj.load()
        cookie_remover(cj,"OptanonControl")
        cookie_remover(cj,"__cfduid")
        cookie_remover(cj,"c_visitor")
        scraper.cookies=cj
        print("Cookies miam🍪.. Loaded")
    wb_page=scraper.get(url)
    if wb_page.ok:
        if "showmedia-trailer-notice" in wb_page.text:
            raise NotPremiumError("Not Premium")
        infos=wb_page.text.split("vilos.config.media = ")[1].split(";")[0]
        infos=json.loads(infos)["streams"]
        best=None
        for i in infos:
            if i["hardsub_lang"]=="frFR" and ".m3u8" in i["url"]:
                tmp=m3u8.load(i["url"])
                if tmp.playlists:
                    for arg in tmp.playlists:
                        if not best or best.stream_info.resolution[0]<arg.stream_info.resolution[0]:
                            best=arg
                        elif best.stream_info.resolution[0]==arg.stream_info.resolution[0]:
                            if best.stream_info.resolution[1]<arg.stream_info.resolution[1]:
                                best=arg
                            elif best.stream_info.resolution[1]==arg.stream_info.resolution[1]:
                                if best.stream_info.frame_rate<arg.stream_info.frame_rate:
                                    best=arg
                                elif best.stream_info.frame_rate==arg.stream_info.frame_rate:
                                    if  best.stream_info.bandwidth<arg.stream_info.bandwidth:
                                        best=arg
        return best
    raise NotPremiumError("Error")


def main(infos,outfile,username=None,password=None):
    if "stream_info" in dir(infos):
        print("\033[1m"+"╔"+"═"*40+"╗")
        print("║"+("Resolution: "+str(infos.stream_info.resolution[0])+"x"+str(infos.stream_info.resolution[1])).ljust(40)+"║")
        print("║"+("Framerate:  "+str(infos.stream_info.frame_rate)).ljust(40)+"║")
        print("║"+("Bandwidth:  "+str(infos.stream_info.bandwidth)).ljust(40)+"║")
        print("╚"+"═"*40+"╝"+ "\033[0m")
        r=m3u8.load(infos.uri)
        key=requests.get(r.keys[0].uri).content
        progress_bar=ProgressBar(len(r.segments))
        with open(outfile,"wb") as output_file:
            for fil in r.segments:
                input_stream=requests.get(fil.uri,stream=True) 
                cipher_encrypt = AES.new(key, AES.MODE_CBC, key)
                for part in input_stream.iter_content(chunk_size=512):
                    output_file.write(cipher_encrypt.decrypt(part))
                print(progress_bar.update(),end="\r")
    else:
        raise Exception("Not Premium")
        

def is_valid_file(parser, arg):
    if not exists(arg):
        parser.error("The cookie file %s does not exist!" % arg)

parser = argparse.ArgumentParser()
parser.add_argument("l", type=str, help="link")
parser.add_argument("o", type=str, help="output file")
parser.add_argument("-c", "--cookies", type=is_valid_file, help="cookie file path", default=None)
args = parser.parse_args()
try:
    main(getter(args.l,args.cookies),args.o)
except NotPremiumError:
    print("\033[1m"+"╔"+"═"*60+"╗")
    print("║"+"Humm something happen do you have Crunchy Premium?".center(60)+"║")
    print("╚"+"═"*60+"╝"+ "\033[0m")
