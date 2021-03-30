import requests
import sys
from time import sleep
URL = sys.argv[1]
TOTAL_COUNT = int(sys.argv[2])
AVG_TIME = 0

for i in range(int(TOTAL_COUNT)):
    resp = requests.get(URL)
    AVG_TIME += resp.elapsed.total_seconds()
    print(f"[{i+1}]:  {round(resp.elapsed.total_seconds(), 4)}")
    sleep(1)

AVG_TIME /= TOTAL_COUNT
print("-" * 13)
print("Average time: " , round(AVG_TIME, 5))