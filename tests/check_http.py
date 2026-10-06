"""针对正在运行的本机服务进行真实 HTTP 冒烟测试。"""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    args = parser.parse_args()
    base = f'http://127.0.0.1:{args.port}'
    records = []
    cases = [('GET','/',None,200,{}),('GET','/app.js',None,200,{}),
             ('GET','/style.css',None,200,{}),('GET','/sdes/core.py',None,404,{}),
             ('POST','/api',{'action':'encrypt','block':'10010111','key':'1010000010'},200,{}),
             ('POST','/api',{'action':'decrypt','block':'00111000','key':'1010000010'},200,{}),
             ('POST','/api',{'action':'encode','text':'Hello, S-DES!','key':'1010000010'},200,{}),
             ('POST','/api',{'action':'decode','text':'C4F80D0D2F99624F365F504F29','key':'1010000010'},200,{}),
             ('POST','/api',{'action':'encrypt','block':'010','key':'1010000010'},400,{}),
             ('POST','/api',{'action':'crack','pairs':''},400,{}),
             ('POST','/api',{'action':'encode','text':'中文','key':'1010000010'},400,{}),
             ('POST','/api',{'action':'collisions','block':'00000000'},200,{}),
             ('POST','/api',{'action':'encrypt','block':'10010111','key':'1010000010'},403,{'Origin':'http://example.invalid'})]
    for method,path,payload,expected,headers in cases:
        raw = json.dumps(payload).encode() if payload is not None else None
        request = Request(base+path,data=raw,method=method,headers={'Content-Type':'application/json',**headers})
        try:
            response = urlopen(request,timeout=5)
        except HTTPError as error:
            response = error
        with response:
            status, body = response.status, response.read()
        assert status == expected, (path,status,expected,body)
        if status == 200 and path == '/api':
            result = json.loads(body)
            if payload['action'] == 'encrypt': assert result['output'] == '00111000'
            if payload['action'] == 'decrypt': assert result['output'] == '10010111'
            if payload['action'] == 'encode': assert result['hex'] == 'C4F80D0D2F99624F365F504F29'
            if payload['action'] == 'decode': assert result['text'] == 'Hello, S-DES!'
            if payload['action'] == 'collisions': assert result['collision_buckets'] == 224
        records.append({'method':method,'path':path,'action':payload.get('action') if payload else None,'expected':expected,'actual':status,'passed':True})
    destination = Path(__file__).resolve().parent.parent/'results/http_tests.json'
    destination.write_text(json.dumps({'cases':records,'passed':len(records),'base_url':base},indent=2),encoding='utf-8')
    print(f'HTTP tests passed: {len(records)}/{len(records)}')


if __name__ == '__main__':
    main()
