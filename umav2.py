# %%
from mss import mss
import time
import requests
import pandas as pd
import os
from openocr import OpenOCR
import json
import numpy as np
import time
import pyautogui
import threading
from PIL import Image
import cc3d
from scipy.ndimage import binary_dilation
from google.oauth2 import service_account
from googleapiclient.discovery import build
from manga_ocr import MangaOcr
import regex as re
from dotenv import load_dotenv

load_dotenv()
webhook = os.getenv('WEBHOOK')
servAccJson = os.getenv('GCPJSON')
spreadsheetId = os.getenv('SPREADSHEETID')
sheetname = os.getenv('SHEETNAME')

# %%
engine = OpenOCR(mode='server',drop_score=.01)
mocr = MangaOcr()

# %%
if servAccJson and spreadsheetId:
    creds = service_account.Credentials.from_service_account_file(
    servAccJson,
    scopes=['https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive']
    )
    sheetsService = build('sheets', 'v4', credentials=creds)
    driveService = build('drive', 'v3', credentials=creds)


japanesePattern = re.compile(r'[\p{IsHan}\p{IsHira}\p{IsKatakana}]', re.UNICODE)

def containsJapanese(text):
    return bool(japanesePattern.search(text))

def bbox_2d(arr):
    x,y = np.where(arr)
    return min(x),max(x),min(y),max(y)

# %%
sct = mss()
cvt = lambda im: im[:,:,[2,1,0]]
sct.shot(output='temp.png')
prelim = engine('temp.png')
assert 'Club Info' in [val['transcription'] for val in json.loads(prelim[0][0].split('\t')[-1])], "Looks like you're not on the club info page"
arr = np.array(Image.open('temp.png').convert('RGB'))
os.remove('temp.png')
bounds = (arr[:,:,0] == 242)&(arr[:,:,1] == 243) & (arr[:,:,2] == 242)
bounds = cc3d.largest_k(bounds, k=1)
xmin,xmax,ymin,ymax = bbox_2d(bounds)
height = xmax-xmin
height = .75 * height
width = ymax-ymin
width = .75 * width

monitor = {'top': xmin.item(),'left':ymin.item(),'width':int(width),'height':int(height)}

# %%
def cap(monitor):
    im = np.array(sct.grab(monitor))
    return cvt(im) 


# %%
doneScrolling = threading.Event()

def scrollClub(iters=9, doneEvent=None,monitor = None):
    top,left,width,height = monitor
    y = top + height//2
    x = left +width *1.2
    pyautogui.moveTo(x, y)
    pyautogui.click()
    pyautogui.click()
    for i in range(iters):
        # print(f"[scrollClub] Iteration {i+1}/{iters}")
        pyautogui.dragRel(yOffset=-height*1.5, duration=0.25)
        pyautogui.moveTo(x, y)
    if doneEvent:
        doneEvent.set()


def run_capture_loop(monitor,fps=5):
    capturedFrames = []
    interval = 1 / fps
    while not doneScrolling.is_set():
        start = time.time()
        capturedFrames.append(cap(monitor))
        # print(f"[cap] Captured frame {len(capturedFrames)}")
        elapsed = time.time() - start
        time.sleep(max(0, interval - elapsed))
    return capturedFrames

def scrollCap(fps,monitor):
    # Start scrolling in a background thread
    scrollThread = threading.Thread(target=scrollClub, kwargs={'iters': 9, 'doneEvent': doneScrolling, 'monitor':tuple(monitor.values())})
    scrollThread.start()

    # Run capture loop in foreground so you can interrupt with the notebook
    capturedFrames = run_capture_loop(monitor,fps)
    return capturedFrames
frames = scrollCap(30,monitor)




# %%
height,width,_ = frames[0].shape
working = np.zeros((height*15,*frames[0].shape[1:]),dtype=np.uint8)
currentIdx = 0
working[currentIdx:height+currentIdx] = frames[0]
searchSpace = range(250)
js = []
tol = 15
errs = []
for i in range(1,len(frames)):
    prev = frames[i-1]
    curr = frames[i]
    for j in js:
        
        error = np.sum(((curr[:-j if j else height]-prev[j:])**2))
        # error = mse(curr[:-j if j else height,:300],prev[j:,:300])
        if error < (tol * (height-j) * width*3):
            working[currentIdx+j:currentIdx+j+height] = curr 
            currentIdx += j
            errs.append(error)
            break
    else:
        for j in searchSpace:
            
            error = np.sum(((curr[:-j if j else height]-prev[j:])**2))
            # error = mse(curr[:-j if j else height,:300],prev[j:,:300])
            if error < (tol * (height-j) * width*3):
                # print(error,error2)
                js.append(j)
                working[currentIdx+j:currentIdx+j+height] = curr 
                currentIdx += j
                errs.append(error)
                break
        else:
            print('broke at',i)
            break
final = working[:currentIdx+height]




# %%
borders = (final[:,:,0] == 228) & (final[:,:,1] == 221) & (final[:,:,2] == 210)
idxs = np.where(np.gradient(borders[:,300].astype(int)) > 0)[0][::2]
height = int((idxs[1] - idxs[0] ) * .9)

finalResults = {}
for idx in idxs:
    try:
        sub = final[idx:idx+height]
        y = (sub == [228,221,210]).all(axis=-1)
        y = np.where(y)[1][0]
        x = np.where(sub[:,-2,:] == [228,221,210])[0][-1]
        name = sub[:x,y:]
        circ = np.all(name == 255,axis=-1)
        circ = cc3d.largest_k(circ,k=1)
        cut = min(np.where(circ)[1]) -4
        nameImg = name[:,:cut]
        # plt.imshow(name)
        # plt.show()
        res = engine.text_recognizer(img_numpy=nameImg)
        name = res[0]['text'].strip()
        
        if len(name) == 0 or containsJapanese(name):
            img = Image.fromarray(nameImg)
            name = mocr(img)
        
        _,_,_,ymax = bbox_2d((sub == [236, 231, 228]).all(axis=-1))
        fans = sub[x:,ymax:]
        fanArea = np.mean(fans,axis=-1) < 125
        fanArea = binary_dilation(fanArea,iterations=5)
        fanArea = cc3d.largest_k(fanArea,k=1)
        xmin,xmax,ymin,ymax = bbox_2d(fanArea)
        fanArea = fans[xmin:xmax,ymin:ymax]
        res = engine.text_recognizer(img_numpy = fanArea)
        fans = int(res[0]['text'].replace(',','').replace('.',''))
        finalResults[name] = fans
        # print(name,fans)
    except Exception as e:
        print(e)
        break

print(finalResults)

# %%
# Load historical data
if os.path.exists("uma.csv"):
    dfOld = pd.read_csv("uma.csv", parse_dates=["time"])
else:
    dfOld = pd.DataFrame(columns=["username", "fans", "time"])

# Build new DataFrame and update log
now = pd.Timestamp.now()
dfNew = pd.DataFrame({
    "username": list(finalResults.keys()),
    "fans":     list(finalResults.values()),
    "time":     [now] * len(finalResults)
})
dfAll = pd.concat([dfNew, dfOld], ignore_index=True)
if 'Unnamed: 0' in dfAll.columns:
    dfAll = dfAll.drop(columns=['Unnamed: 0'])
dfAll.to_csv("uma.csv", index=False)


# Prepare and send webhook payload
payloadLines = []
for user, curFans in reversed(sorted(finalResults.items(),key=lambda val: val[1])):
    recentMask = (dfOld["username"] == user) & (now - dfOld["time"] <= pd.Timedelta(hours=8))
    if recentMask.any():
        continue

    # 1-day delta, scaled to exactly 1 day
    dayMask = (dfOld["username"] == user) & (dfOld["time"] <= now - pd.Timedelta(days=1))
    if dayMask.any():
        oldRecord = dfOld.loc[dayMask].iloc[0]
        timeDiff = now - oldRecord["time"]
        # (curFans - oldFans) is total change over timeDiff;
        # dividing by (timeDiff / 1 day) scales it to a 1-day window
        deltaDay = (curFans - oldRecord["fans"]) / (timeDiff / pd.Timedelta(days=1))
    else:
        deltaDay = None

    # 1-week delta, scaled to exactly 1 week
    weekMask = (dfOld["username"] == user) & (dfOld["time"] <= now - pd.Timedelta(days=7))
    if weekMask.any():
        oldRecord = dfOld.loc[weekMask].iloc[0]
        timeDiff = now - oldRecord["time"]
        # dividing by (timeDiff / 7 days) scales change to a 1-week window
        deltaWeek = (curFans - oldRecord["fans"]) / (timeDiff / pd.Timedelta(days=7))
    else:
        deltaWeek = None


    line = f"{user} – {curFans} fans"
    if deltaDay is not None:
        line += f"  ({(deltaDay/1e6):.2f}M fans / 1 d) {'ALERT' if int(deltaDay) < 900000 else ''}" 
    if deltaWeek is not None:
        line += f"  ({(deltaWeek/1e6):.2f}M fans / 7 d) {'ALERT' if int(deltaWeek) < 6000000 else ''}"
    payloadLines.append(line)

if webhook and payloadLines:
    requests.post(
        webhook,
        data=json.dumps({"content": "\n".join(payloadLines), "username": "fan monitor"}),
        headers={"Content-type": "application/json"}
    )
    # print(payloadLines)
dfAll['time'] = dfAll['time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
if sheetsService:
    sheetsService.spreadsheets().values().update(
        spreadsheetId=spreadsheetId,
        range=f'{sheetname}!A1',
        valueInputOption='USER_ENTERED',
        body={'values': dfAll.values.tolist()}
    ).execute()


