import random
import string
import requests
import json
import os
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)#to keep console clean

CHARACTERS = string.ascii_letters + string.digits #characters to generate invite code from
TIMEOUT = 3  # web request timeout
MAX_CONSECUTIVE_ERRORS = 10
STATS_INTERVAL = 5  # How often to print stats
PROXY_RECOVERY_TIME = 40  # Time in seconds before retrying a not working proxy
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://discord.com/",
    "Origin": "https://discord.com",
    "X-Discord-Locale": "en-US",
}#to make requests look like a real requests from humans
running = True
proxy_lock = threading.Lock()
file_lock = threading.Lock()
class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.total_requests = 0
        self.successful_checks = 0
        self.valid_servers = 0
        self.rate_limits = 0
        self.connection_errors = 0
        self.active_proxies = 0
        self.cooling_proxies = 0
        self.recovered_proxies = 0
        self.start_time = time.time()# stats are cool :3

    def increment(self, field):
        with self.lock:
            setattr(self, field, getattr(self, field) + 1)
    
    def decrement(self, field):
        with self.lock:
            setattr(self, field, getattr(self, field) - 1)
    
    def print_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            requests_per_second = self.total_requests / elapsed if elapsed > 0 else 0
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            print("\n" + "~" * 60)
            print(f"[⏲]  Runtime: {minutes}m {seconds}s")
            print(f"[⧻] Total requests made: {self.total_requests} ({requests_per_second:.2f} req/s)")
            print(f"[✔] Successful checks: {self.successful_checks}")
            print(f"[🗹] Valid servers found: {self.valid_servers}")
            print(f"[✌] Active proxies: {self.active_proxies + self.recovered_proxies},[⛑] Cooling: {self.cooling_proxies}")
            print(f"[˟] Rate limits: {self.rate_limits}, [╳] Errors: {self.connection_errors}")
            print("~" * 60 + "\n")

stats = Stats()
cooling_proxies = []
available_proxies = []
def init_results_file():
    with file_lock:
        if not os.path.exists("valid_servers.json"):
            with open("valid_servers.json", "w") as f:
                f.write("[\n")
        elif os.path.getsize("valid_servers.json") == 0:
            with open("valid_servers.json", "w") as f:
                f.write("[\n")
def save_valid_server(invite_code, guild_name, guild_id):
    with file_lock:
        with open("valid_servers.json", "a") as f:
            json.dump({
                "invite": invite_code,
                "name": guild_name,
                "id": guild_id
            }, f)
            f.write(",\n")
def proxy_worker(proxy_info):
    global running, cooling_proxies
    
    proxy_url = proxy_info["url"]
    proxy = {
        "http": proxy_url,
        "https": proxy_url
    }
    consecutive_errors = 0
    stats.increment("active_proxies")
    try:
        while running:
            invite_code = ''.join(random.choices(CHARACTERS, k=10))
            url = f"https://discord.com/api/v9/invites/{invite_code}"
            
            try:
                stats.increment("total_requests")
                response = requests.get(
                    url, 
                    headers=HEADERS, 
                    proxies=proxy, 
                    verify=False, 
                    timeout=TIMEOUT
                )
                if consecutive_errors > 0:
                    consecutive_errors = 0
                
                if response.status_code == 200:
                    stats.increment("successful_checks")
                    
                    try:
                        if response.text.strip() == "":
                            continue
                        
                        data = response.json()
                        if "guild" in data and isinstance(data["guild"], dict) and "name" in data["guild"]:
                            guild_name = data["guild"]["name"]
                            guild_id = data["guild"]["id"]
                            stats.increment("valid_servers")
                            print(f"Valid Server found: https://discord.gg/{invite_code} | {guild_name}")
                            save_valid_server(invite_code, guild_name, guild_id)
                    except json.JSONDecodeError:
                        pass
                if response.status_code == 429:
                    stats.increment("rate_limits")
                    
                    try:
                        retry_after = response.json().get("retry_after", 5)
                        retry_after = min(retry_after, 15)
                    except (json.JSONDecodeError, KeyError):
                        retry_after = 5
                    time.sleep(retry_after)
                else:
                    stats.increment("successful_checks")
            except requests.exceptions.RequestException:
                consecutive_errors += 1
                stats.increment("connection_errors")
                
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    stats.decrement("active_proxies")
                    stats.increment("cooling_proxies")
                    with proxy_lock:
                        cooling_proxies.append({
                            "proxy": proxy_info,
                            "recover_at": time.time() + PROXY_RECOVERY_TIME
                        })
                    return
                        
    except Exception as e:
        if running:
            stats.increment("connection_errors")
            stats.decrement("active_proxies")

# stats printeeeeeeer
def stats_printer():
    global running
    while running:
        time.sleep(STATS_INTERVAL)
        stats.print_stats()
        check_recovered_proxies()

def check_recovered_proxies():
    global cooling_proxies, available_proxies
    recovered = []
    
    with proxy_lock:
        current_time = time.time()
        
        for cooling_proxy in cooling_proxies:
            if current_time >= cooling_proxy["recover_at"]:
                recovered.append(cooling_proxy["proxy"])
                stats.decrement("cooling_proxies")
                stats.increment("recovered_proxies")
        cooling_proxies = [p for p in cooling_proxies if time.time() < p["recover_at"]]
        available_proxies.extend(recovered)

def start_available_proxies(executor):
    global available_proxies
    
    with proxy_lock:
        proxies_to_start = available_proxies.copy()
        available_proxies = []
    
    for proxy in proxies_to_start:
        if running:
            executor.submit(proxy_worker, proxy)

def proxy_manager(executor):
    global running
    while running:
        start_available_proxies(executor)
        time.sleep(3)

def main():
    global running, available_proxies
    
    init_results_file()
    with open('proxies.json', 'r') as file:
        all_proxies = json.load(file)
    
    max_proxies = len(all_proxies)
    print(f"Loaded {max_proxies} proxies")
    try:
        num_proxies = int(input(f"How many proxies to use (max {max_proxies})(leave blank for max)? "))
        num_proxies = min(num_proxies, max_proxies)
    except ValueError:
        num_proxies = min(max_proxies, max_proxies)
    
    print(f"Starting with {num_proxies} proxies")
    print(f"Proxies will cool off for {PROXY_RECOVERY_TIME} seconds after {MAX_CONSECUTIVE_ERRORS} consecutive errors")
    available_proxies = all_proxies[:num_proxies]
    
    try:
        max_workers = num_proxies + 3  # +3 for stats, proxy manager, and some buffer        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.submit(stats_printer)
            executor.submit(proxy_manager, executor)
            for proxy in available_proxies:
                executor.submit(proxy_worker, proxy)
            available_proxies = []
            while True:
                time.sleep(10) #keep the main thread running
    
    except KeyboardInterrupt:
        print("\nUser stoped the program")
        running = False
        with file_lock:
            with open("valid_servers.json", "a") as f:
                f.write("\n]")
        print("Results saved to valid_servers.json")

if __name__ == "__main__":
    main()