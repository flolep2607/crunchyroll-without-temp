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
    wb_page=scraper.get(url)
    if wb_page.ok:
        infos=wb_page.text.split("vilos.config.media = ")[1].split(";")[0]
        infos=json.loads(infos)["streams"]
        best={}
        regex = re.compile(r"#EXT-X-STREAM-INF:PROGRAM-ID=[0-9],BANDWIDTH=(?P<bandwidth>[0-9]+),RESOLUTION=(?P<resolution>[0-9x]+),FRAME-RATE=(?P<frames>[0-9\.]+),CODECS=\"avc[a-zA-Z0-9\.]+,mp4[a-zA-Z0-9\.]+\"\n(?P<url>.+)$",re.MULTILINE)
        for i in infos:
            if i["hardsub_lang"]=="frFR" and ".m3u8" in i["url"]:
                tmp=requests.get(i["url"])
                if tmp.ok:
                    try:
                        tempo=[m.groupdict() for m in regex.finditer(tmp.text)]
                        for arg in tempo:
                            # arg=re.search(tmp.text,re.MULTILINE).groupdict()
                            # print(arg)
                            arg["resolution"]=[int(r) for r in arg["resolution"].split("x")]
                            if not best or best["resolution"][0]<arg["resolution"][0]:
                                best=arg
                            elif best["resolution"][0]==arg["resolution"][0]:
                                if best["resolution"][1]<arg["resolution"][1]:
                                    best=arg
                                elif best["resolution"][1]==arg["resolution"][1]:
                                    if float(best["frames"])<float(arg["frames"]):
                                        best=arg
                                    elif float(best["frames"])==float(arg["frames"]):
                                        if  int(best["bandwidth"])<int(arg["bandwidth"]):
                                            best=arg
                    except:
                        pass
        return best
    raise "Error on requests"

def main(infos,outfile,username=None,password=None):
    print("\033[1m"+"╔"+"═"*40+"╗")
    print("║"+("Resolution: "+str(infos["resolution"][0])+"x"+str(infos["resolution"][1])).ljust(40)+"║")
    print("║"+("Framerate:  "+str(infos["frames"])).ljust(40)+"║")
    print("║"+("Bandwidth:  "+str(infos["bandwidth"])).ljust(40)+"║")
    print("╚"+"═"*40+"╝"+ "\033[0m")
    r=m3u8.load(infos["url"])
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
parser.add_argument("l", type=str, help="link")
parser.add_argument("o", type=str, help="output file")
parser.add_argument("-u", "--username", type=str, help="username", default=None)#,required=False)
parser.add_argument("-p", "--password", type=str, help="password", default=None)#,required=False)
args = parser.parse_args()
main(getter(args.l),args.o,args.username,args.password)
