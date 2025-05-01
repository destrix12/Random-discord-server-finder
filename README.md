# Random discord server finder
 Script I made to search for random discord servers (I know its in python and im not proud of it)
 
 **Warning**
 Before you decide to run it I must warn you that this is agains discord rules (this oroject is for educational purposes only)

You will need proxies for this script, if you dont have any working you can get some from my [proxy fetcher](https://github.com/destrix12/Proxy-fetcher) (its why I made it at first point xd)

# Math
I've done some math to check how efective this script is:
You have 62^10 = 839,299,365,868,340,224 possible combinations of the invite code you can get.
There is no official information how many servers are there on discord but we can take a guess. Since there were around 800,000,000 registered accounts lets take like one server for each account (idk like I have like 10 servers where im alone or just with like 3 another people) so that's 800,000,000 servers
So that is 839,299,365,868,340,224 divided by 800,000,000 --> thats around 1,049,124,207 --> you have around 0.0000001 chance to find a server :c. I know that's horrible that's where proxies come in use.

# Proxies
This script uses proxies from json file in same folder named **proxies.json** and in this format:
```
[
    {
        "ip": "proxy ip",
        "port": "proxy port",
        "type": "proxy type (http, socks4, etc.)",
        "url": "proxy url"
    },
    {
        "ip": "", "port": "", "type": "", "url": ""
    }
]    
```    
You get around 10,000,000 tries per day so you will get around 1 server per 10 days with 600 working proxies :c.
However there are many servises that give you free trial with free proxies and if you combine them with free proxies from my proxy fetcher you can get around 6000 proxies and that is one server per 1 day.

If you get any idea how to make this script more effective please let me know!
