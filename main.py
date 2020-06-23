import argparse
import re
import youtube_dl
import requests
import json
import m3u8
from Crypto.Cipher import AES
import cloudscraper

def getter(url):
    scraper = cloudscraper.create_scraper()
    wb_page=scraper.get(url)#"https://www.crunchyroll.com/fr/tower-of-god/episode-11-underwater-hunt-part-one-794529").text
    if wb_page.ok:
        infos=wb_page.text.split("vilos.config.media = ")[1].split(";")[0]
        infos=json.loads(infos)["streams"]
        best=None
        for i in infos:
            if i["hardsub_lang"]=="frFR" and ".m3u8" in i["url"]:
                tmp=m3u8.load(i["url"])
                for arg in tmp.playlists:
                    # arg=re.search(tmp.text,re.MULTILINE).groupdict()
                    # print(arg)
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
    raise "Error"


def main(infos,outfile,username=None,password=None):
    print("\033[1m"+"╔"+"═"*40+"╗")
    print("║"+("Resolution: "+str(infos.stream_info.resolution[0])+"x"+str(infos.stream_info.resolution[1])).ljust(40)+"║")
    print("║"+("Framerate:  "+str(infos.stream_info.frame_rate)).ljust(40)+"║")
    print("║"+("Bandwidth:  "+str(infos.stream_info.bandwidth)).ljust(40)+"║")
    print("╚"+"═"*40+"╝"+ "\033[0m")
    r=m3u8.load(infos.uri)
    key=requests.get(r.keys[0].uri).content
    n=1
    with open(outfile,"wb") as output_file:
        for fil in r.segments:
            input_stream=requests.get(fil.uri,stream=True) 
            cipher_encrypt = AES.new(key, AES.MODE_CBC, key)
            for part in input_stream.iter_content(chunk_size=512):
                output_file.write(cipher_encrypt.decrypt(part))
            print(str(n).rjust(3,"_"),end="\r")
            n+=1

parser = argparse.ArgumentParser()
# parser.add_argument("-l", "--link"    , type=str, help="link")
# parser.add_argument("-o", "--out"     ,type=str, help="output file")
parser.add_argument("l", type=str, help="link")
parser.add_argument("o", type=str, help="output file")
parser.add_argument("-u", "--username", type=str, help="username", default=None)#,required=False)
parser.add_argument("-p", "--password", type=str, help="password", default=None)#,required=False)
args = parser.parse_args()
main(getter(args.l),args.o,args.username,args.password)
