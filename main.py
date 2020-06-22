import argparse
import youtube_dl
import requests
import m3u8
from Crypto.Cipher import AES


def main(url,outfile,username=None,password=None):
    ydl_opts = {
        "username":username,
        "password":password,
        "quiet":True,
        "format": "bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "subtitleslangs":["frFR"],
        "writesubtitles":False,
        "skip_download":True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        # ydl.download(["https://www.crunchyroll.com/fr/tower-of-god/episode-11-underwater-hunt-part-one-794529"])
        tmp=ydl.extract_info(url)#"https://www.crunchyroll.com/fr/tower-of-god/episode-11-underwater-hunt-part-one-794529",download=False)
        tempo=["",0]
        for i in tmp.get("formats"):
            if tempo[1]<i.get("width"):
                tempo[0]=i.get("url")
                tempo[1]=i.get("width")
        print(tempo[0])


    r=m3u8.load(tempo[0])
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
parser.add_argument("-l", help="link")
parser.add_argument("-o", help="output file")
parser.add_argument("-u", help="username")#,required=False)
parser.add_argument("-p", help="password")#,required=False)
args = parser.parse_args()
main(args.l,args.o,args.u,args.p)
