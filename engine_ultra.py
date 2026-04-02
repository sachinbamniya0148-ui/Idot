#!/usr/bin/env python3
"""engine_ultra.py v46 ULTRA — ZipPasswordCrack.in — 1M+/sec C engine"""
import itertools,string,logging,time,zipfile,re,tempfile,shutil
import os,threading,io,struct,ctypes,subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

log=logging.getLogger("engine")
try: import pyzipper;HAS_AES=True
except: HAS_AES=False
try: import pikepdf;HAS_PIKE=True
except: HAS_PIKE=False
try: from pypdf import PdfReader as _PDFR;HAS_PDF=True
except:
    try: from PyPDF2 import PdfReader as _PDFR;HAS_PDF=True
    except: HAS_PDF=False

CS={"lower":string.ascii_lowercase,"upper":string.ascii_uppercase,"digits":string.digits,
    "alpha":string.ascii_letters,"alnum":string.ascii_letters+string.digits,
    "sym":"!@#$%^&*()-_+=[]{}|;:',.<>?/`~\\","sym_india":"!@#$%&*_-.+~@786",
    "hex":"0123456789abcdef","full":string.printable.strip()}

TOP_PASSWORDS=["123456","password","123456789","12345678","12345","qwerty","abc123","111111",
"iloveyou","admin","letmein","monkey","dragon","master","sunshine","princess","welcome",
"shadow","password1","password123","admin123","root","toor","pass","test","guest","000000",
"qwerty123","1q2w3e4r","1234","1234567","1234567890","p@ssw0rd","P@ssword","pa55word",
"admin@123","Admin@123","Admin123","user123","demo123","india","bharat","india123",
"786","786786","007","420","108","999","786@123","pass@123","Pass@123","abc@123",
"ABC123","qwerty@123","1qaz2wsx","zxcvbn","qazwsx","1q2w3e","abcd1234","1234abcd",
"changeme","batman","superman","cricket","dhoni","kohli","sachin","rohit","virat",
"india2024","india2025","india786","bharat786","bharat2024","ram786","krishna786",
"allah786","waheguru","bismillah","inshallah","123","1111","2222","3333","4444",
"5555","6666","7777","8888","9999","0000","11111","12341234","pass@1234",
"Password@1","Admin@1234","welcome123","Test@1234","login123","1029384756",
"a1b2c3d4","p@ss123","P@ss1234","India@123","India@2024","Bharat@786","maa786",
"papa786","bhai786","dil786","zindagi786","jaan786","sona786","lucky786","love786",
"shahrukh","salman","deepika","katrina","priyanka","bollywood","iphone","samsung",
"google","facebook","instagram","whatsapp","youtube","twitter","netflix","amazon"]

YEARS=[str(y) for y in range(1930,2026)]
NUMS=["1","2","3","4","5","6","7","8","9","0","12","21","23","11","22","33",
"123","321","456","789","100","786","007","420","108","999","2024","2025",
"1234","4321","12345","54321","123456","1947","2000","2001","1999","1990",
"00","01","02","03","11","22","33","44","55","66","77","88","99","786786","007007"]

SYM_SUFFS=["@123","@1234","@786","@007","@420","@108","!123","#123","_123","_786",
"@2024","@2025","@india","!@#","_1","_12","@1","#1","!1","@12345","@2023","@2022",
"#786","!786","_007","@000","#2024","!2024","@786786",".123",".786","#123456",
"@123456","!@#$",".2024","_2024","@9999","123!","786!","@007786","786@123","123@786"]

SUFFS=["","1","2","3","12","21","123","321","1234","4321","12345","54321","123456",
"1234567","12345678","123456789","1234567890","@","@1","@12","@123","@1234","@12345",
"@786","@007","@420","@108","#","#123","!","!123","_","_123","_786","_007","0","00",
"000","0000","786","007","420","108","999","9999","1947","@2024","@2025","@india",
"ji","_ji","bhai","india","kumar","2024","2025","2023","2022","@2023","@2022"]+SYM_SUFFS

PRES=["","my","the","new","old","its","real","true","shri","dr","mr","mrs","786","007",
"@","#","1","i","we","our","jai","sri","raj","dev","hari","om","bhai","ji","master"]

DATE_FMTS=["%d%m%Y","%d%m%y","%Y%m%d","%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%m%d%Y",
"%Y%d%m","%d%m","%m%Y","%Y","%d","%m","%d%b%Y","%b%Y","%B%Y","%Y-%m-%d","%y%m%d",
"%m/%d/%Y","%d%b%y","%b%d%Y","%d%b","%b%d","%d%b%y","%y%d%m"]

INDIAN_MALE=["rahul","amit","sunil","anil","ravi","sanjay","vijay","ajay","raj","ram",
"krishna","shyam","mohan","rohan","karan","arjun","vikram","suresh","mahesh","ganesh",
"dinesh","rajesh","mukesh","deepak","pradeep","sandeep","kuldeep","pankaj","vivek",
"abhishek","manish","ankit","mohit","rohit","sumit","lalit","nikhil","sahil","tushar",
"gaurav","sourav","anurag","mayank","neeraj","dheeraj","kunal","vishal","vaibhav",
"saurabh","himanshu","shubham","akash","prakash","aditya","harsh","yash","sunny","lucky",
"bobby","rocky","pappu","guddu","bunty","bablu","pintu","rinku","raju","raja","sonu",
"monu","harpreet","gurpreet","manpreet","balwinder","imran","asif","zaid","farhan",
"ayaan","danish","faizan","rizwan","bilal","usman","hassan","ali","amir","sultan",
"shahid","khalid","rashid","mohd","mohammed","muhammad","ahmad","ahmed","iqbal","nawaz",
"asad","babar","murugan","karthik","senthil","anand","prasad","venkat","raman",
"naveen","pawan","ratan","naresh","sudhir","surendra","mahendra","rajendra","narendra",
"pravin","sachin","virat","kohli","tendulkar","bumrah","jadeja","hardik","pandya",
"shahrukh","salman","aamir","hrithik","ranbir","ranveer","akshay","ajay","sonu","manu",
"chotu","lal","jagdish","sitaram","omprakash","mahavir","brijmohan","prashant","jayant"]

INDIAN_FEMALE=["priya","pooja","neha","rita","geeta","sita","meena","seema","reena",
"sunita","kavita","lalita","rekha","meera","sheela","kamla","vimla","sharmila","shweta",
"nisha","disha","asha","usha","radha","divya","kavya","riya","tara","anjali","mamta",
"deepika","shreya","sweety","pinky","simran","ayesha","fatima","zainab","maryam",
"khadija","zahra","asma","noor","sana","hina","mehak","mehwish","amna","bushra",
"farida","nasreen","parveen","rubina","shabana","mumtaz","salma","reshma","radhika",
"madhuri","juhi","kajol","aishwarya","priyanka","katrina","kareena","sonam","shraddha",
"sara","janhvi","anushka","rani","vidya","kangana","preity","bipasha","poonam","ritu",
"preeti","jyoti","manju","baby","sweetu","dolly","bittu","guddu","bubbly","payel",
"debjani","tanushree","swapna","mousumi","champa","durga","savitri","kaushalya","yashoda"]

SURNAMES=["sharma","verma","gupta","kumar","singh","patel","shah","mehta","joshi",
"tiwari","pandey","mishra","yadav","chauhan","rajput","thakur","rao","reddy","naidu",
"nair","pillai","iyer","menon","banerjee","chatterjee","mukherjee","ghosh","das","bose",
"roy","saha","mitra","basu","chowdhury","khan","ansari","qureshi","shaikh","sheikh",
"siddiqui","malik","mirza","gill","dhillon","sandhu","grewal","sidhu","kang","brar",
"agarwal","goyal","mittal","goel","jain","kapoor","khanna","chopra","malhotra","arora",
"kohli","shukla","dubey","tripathi","upadhyay","solanki","rawat","bisht","negi",
"bhandari","rana","maurya","bajpai","srivastava","awasthi","saxena","tyagi","garg",
"bansal","bhatt","dixit","trivedi","chaudhary","rathore","sisodiya","meena","gurjar",
"jat","goud","saini","kashyap","yadava","gautam","bharti","bharadwaj","khatri","soni",
"desai","dalal","modi","ambani","tata","birla","bajaj","bamniya","hooda","phogat","malik"]

CITIES=["mumbai","delhi","bangalore","bengaluru","chennai","kolkata","hyderabad","pune",
"ahmedabad","jaipur","surat","lucknow","kanpur","nagpur","indore","bhopal","patna",
"vadodara","agra","nashik","faridabad","meerut","rajkot","amritsar","varanasi",
"prayagraj","jodhpur","guwahati","kochi","chandigarh","noida","gurgaon","gurugram",
"thane","ranchi","lahore","karachi","islamabad","rawalpindi","peshawar","dhaka",
"chittagong","sylhet","dubai","abudhabi","sharjah","riyadh","jeddah","doha","muscat",
"london","birmingham","toronto","brampton","newyork","chicago","sydney","melbourne",
"singapore","vizag","coimbatore","madurai","gwalior","allahabad","jabalpur","srinagar",
"aurangabad","solapur","bareilly","moradabad","ghaziabad","rohtak","panipat","mathura",
"gorakhpur","shimla","dehradun","haridwar","rishikesh","nainital","manali","ludhiana"]

HINDI=["pyar","mohabbat","ishq","prem","preet","sneh","mamta","dard","khushi","gham",
"dukh","sukh","aanand","shanti","umeed","aasha","sapna","khwaab","armaan","dil",
"zindagi","jeevan","duniya","maa","baap","papa","baba","amma","ammi","abbu","dadi",
"dada","nani","nana","bhai","bhaiya","didi","behan","beta","beti","baccha","parivaar",
"ghar","ram","krishna","shiva","ganesh","allah","waheguru","sona","mona","gudiya",
"munni","rani","raja","dost","yaar","sahab","cricket","bollywood","786","007","420",
"108","999","1947","jai","hind","vande","mataram","bhagwan","ishwar","zindabad",
"bismillah","mashallah","inshallah","alhamdulillah","subhanallah","allahu","akbar",
"khiladi","fighter","dhamaka","dhamal","baap","baazigar","devdas","gabbar","sholay",
"dilwale","janeman","jaanam","jaanu","baby","honey","darling","love","pyaara","pyaari",
"hero","star","superstar","bhai","bhaijaan","dada","chacha","chachi","mama","mami",
"saali","devar","devrani","jethani","nanad","sasur","saas","paajii","veerji","bhabhi"]

WORLD_NAMES=["john","james","robert","michael","william","david","joseph","thomas",
"charles","christopher","daniel","matthew","anthony","mark","donald","paul","steven",
"george","kenneth","andrew","mary","patricia","linda","barbara","elizabeth","jennifer",
"maria","susan","margaret","dorothy","jessica","sarah","emily","karen","donna","carol",
"emma","olivia","sophia","isabella","mia","charlotte","amelia","evelyn","abigail",
"omar","hassan","hussain","ibrahim","ismail","yusuf","mustafa","mahmoud","tariq",
"waseem","nadeem","saleem","raheem","kareem","nabil","walid","waqas","zubair","faisal",
"nadir","adnan","hamza","hasan","mehmet","ahmet","ayse","fatma","zeynep","merve","elif",
"shahbaz","nawaz","bilawal","maryam","hina","fawad","murad","sohel","kamal","jamal",
"tamim","mashrafe","shakib","mushfiqur","alex","max","leo","luca","noah","ethan","liam",
"mason","lucas","oliver","elijah","aiden","jacob","jackson","mateo","jayden","sofia",
"luna","isla","aria","zoe","lily","ella","chloe","aurora","layla","victoria","natalie",
"grace","zoey","addison","riley","nora","scarlett","rajinikanth","vijay","ajith","suriya"]

ALL_WORDS=list(dict.fromkeys(
    INDIAN_MALE+INDIAN_FEMALE+SURNAMES+CITIES+HINDI+WORLD_NAMES+
    [w.lower() for w in TOP_PASSWORDS if w.isalpha()]))

MOBILE_CC={
    "+91":{"px":["6","7","8","9","70","71","72","73","74","75","76","77","78","79",
                 "80","81","82","83","84","85","86","87","88","89","90","91","92",
                 "93","94","95","96","97","98","99"],"tlen":10},
    "+92":{"px":["30","31","32","33","34","300","310","320","321"],"tlen":10},
    "+880":{"px":["13","14","15","16","17","18","19"],"tlen":10},
    "+1":{"px":["201","212","310","312","415","646","917"],"tlen":10},
    "+44":{"px":["7400","7500","7700","7800","7900"],"tlen":10},
    "+971":{"px":["50","52","55","56","58"],"tlen":9},
    "+966":{"px":["50","53","55","56","57","58"],"tlen":9},
    "+86":{"px":["130","135","138","150","180","181"],"tlen":11},
}

GITHUB_LISTS={
    "top1m":  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",
    "top100k":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100000.txt",
    "top10k": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
    "rockyou":"https://raw.githubusercontent.com/brannondorsey/naive-hashcat/master/rockyou.txt",
    "darkweb":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/darkweb2017-top10000.txt",
    "xato1m": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/xato-net-10-million-passwords-1000000.txt",
    "best1050":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/best1050.txt",
    "probable":"https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/Top12Thousand-probable-v2.txt",
    "weakpass":"https://raw.githubusercontent.com/kkrypt0nn/wordlists/main/wordlists/passwords/common_passwords_win.txt",
    "leaked": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/alleged-gmail-passwords.txt",
    "common3k":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/common-passwords-win.txt",
    "bt4":    "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/bt4-password.txt",
    "top500": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/500-worst-passwords.txt",
    "hak5":   "https://raw.githubusercontent.com/nicowillis/passwords/master/common_10000_passwords.txt",
    "kaonashi":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/Ashley-Madison.txt",
}

def _ok(pw): return bool(pw and isinstance(pw,str) and 3<=len(pw)<=128)
LEET_MAP=[{'a':'@','e':'3','i':'1','o':'0','s':'$','t':'7','b':'8','g':'9','l':'1'},
          {'a':'4','e':'3','i':'!','o':'0','s':'5','t':'7','b':'6'}]
def leet(w):
    r=set()
    for m in LEET_MAP:
        v=w.lower()
        for k,val in m.items(): v=v.replace(k,val)
        if v!=w.lower() and _ok(v): r.add(v)
    return list(r)
def rules(word):
    if not word: return []
    w=word.lower();wc=word.capitalize();wu=word.upper();wr=word[::-1]
    return list(set(r for r in [w,wc,wu,wr,wr.capitalize()]+leet(w) if _ok(r)))
def interleave(word,num):
    results=[];w=word[:8];n=str(num)[:8]
    r="".join(a+b for a,b in zip(w,n.ljust(len(w),'0')))
    if _ok(r): results.append(r)
    for i in range(0,len(w)+1,2):
        pw=w[:i]+n+w[i:]
        if _ok(pw): results.append(pw)
    return results
def google_style(words):
    for word in words:
        w=word.lower();wc=word.capitalize();wu=word.upper()
        for yr in YEARS: yield w+yr;yield wc+yr
        for n in NUMS: yield w+n;yield wc+n;yield n+w;yield n+wc
        for sym in ["@","!","#","_"]:
            for n in ["1","12","123","786","2024","2025","007","420"]:
                yield w+sym+n;yield wc+sym+n
        for n in ["786","007","420","108","2024","2025","1947","999","123456"]:
            for sep in ["","@","#","_","."]:
                yield w+sep+n;yield wc+sep+n
        if len(w)<=6: yield w+w;yield wc+w
        for r in leet(w): yield r;yield r.capitalize()

def gen_top_common():
    seen=set()
    for pw in TOP_PASSWORDS:
        for v in [pw,pw.upper(),pw.capitalize(),pw.lower()]:
            if _ok(v) and v not in seen: seen.add(v);yield v
        for s in ["1","12","123","@","!","786","@123","@2024","@2025","",
                  "2024","2025","#123","_123","_786","@007","@420","@786786"]:
            pw2=pw+s
            if _ok(pw2) and pw2 not in seen: seen.add(pw2);yield pw2

def gen_google_common():
    seen=set()
    words=TOP_PASSWORDS[:60]+INDIAN_MALE[:60]+INDIAN_FEMALE[:40]+HINDI[:60]+CITIES[:40]+WORLD_NAMES[:40]
    for pw in google_style(words):
        if _ok(pw) and pw not in seen: seen.add(pw);yield pw

def gen_smart(info):
    name=(info.get("name") or "").strip()
    dob=(info.get("dob") or "").strip()
    mobile=(info.get("mobile") or "").strip()
    city=(info.get("city") or "").strip()
    nick=(info.get("nick") or "").strip()
    pet=(info.get("pet") or "").strip()
    fav=(info.get("fav") or "").strip()
    lucky=(info.get("lucky") or "").strip()
    other=(info.get("other") or "").strip()
    dt_obj=None
    if dob:
        for fmt in ("%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%Y-%m-%d","%d%m%Y","%d%m%y","%Y%m%d"):
            try: dt_obj=datetime.strptime(dob.strip(),fmt);break
            except: pass
    date_strs=[]
    if dt_obj:
        for fmt in DATE_FMTS:
            try:
                ds=dt_obj.strftime(fmt)
                if ds not in date_strs: date_strs.append(ds)
            except: pass
    tokens=[t for t in [name,nick,pet,fav,city,other] if t]
    lucky_nums=[lucky] if lucky else []
    lucky_nums+=["786","007","420","108","999","123","1234","2024","2025","1947"]
    if dt_obj:
        lucky_nums+=[str(dt_obj.year),f"{dt_obj.day:02d}{dt_obj.month:02d}",
                     f"{dt_obj.month:02d}{dt_obj.day:02d}",str(dt_obj.year)[-2:],
                     f"{dt_obj.day:02d}{dt_obj.month:02d}{str(dt_obj.year)[-2:]}"]
    for pw in google_style(tokens): yield pw
    for tok in tokens:
        for v in rules(tok):
            for s in SUFFS:
                for p in PRES:
                    pw=p+v+s
                    if _ok(pw): yield pw
    for tok in tokens:
        for num in lucky_nums:
            for pw in interleave(tok.lower(),num): yield pw
            for pw in interleave(tok.capitalize(),num): yield pw
    for tok in tokens:
        for ds in date_strs:
            for sep in ["","_","-",".","@","#","/"]:
                for v in [tok.lower(),tok.capitalize(),tok.upper()]:
                    for combo in [v+sep+ds,ds+sep+v,v+ds,ds+v]:
                        if _ok(combo): yield combo
    if dt_obj and tokens:
        for tok in tokens:
            for v in [tok.lower(),tok.capitalize()]:
                for dp in [f"{dt_obj.day:02d}{dt_obj.month:02d}",
                           f"{dt_obj.day:02d}{dt_obj.month:02d}{dt_obj.year}",
                           f"{dt_obj.day:02d}{dt_obj.month:02d}{str(dt_obj.year)[-2:]}",
                           f"{dt_obj.year}{dt_obj.month:02d}{dt_obj.day:02d}",
                           str(dt_obj.year)]:
                    for sep in ["","@","_","-","#","."]:
                        for combo in [v+sep+dp,dp+sep+v]:
                            if _ok(combo): yield combo
    if mobile:
        m=re.sub(r'[\s\-\+\(\)]','',mobile)
        for v in [mobile,m,m[-10:],m[-8:],m[-6:],m[-4:],"0"+m[-10:],"91"+m[-10:]]:
            if v and _ok(v): yield v
            for s in SUFFS[:25]:
                pw=v+s
                if _ok(pw): yield pw
        for tok in tokens:
            for v in [tok.lower(),tok.capitalize()]:
                for vm in [m[-10:],m[-8:],m[-6:],m[-4:]]:
                    for combo in [v+vm,vm+v,v+"_"+vm,v+"@"+vm]:
                        if _ok(combo): yield combo
    if lucky:
        for tok in tokens:
            for v in rules(tok):
                for sep in ["","@","#","_","."]:
                    for combo in [v+sep+lucky,lucky+sep+v]:
                        if _ok(combo): yield combo
    for ds in date_strs:
        for s in SUFFS[:30]:
            for p in PRES[:12]:
                pw=p+ds+s
                if _ok(pw): yield pw
    if len(tokens)>=2:
        for r in range(2,min(len(tokens)+1,5)):
            for perm in itertools.permutations(tokens[:6],r):
                for sep in ["","_","-","@","."]:
                    pw=sep.join(p.lower() for p in perm)
                    if _ok(pw): yield pw
                    pw=sep.join(p.capitalize() for p in perm)
                    if _ok(pw): yield pw
    if len(tokens)>=2:
        for t1 in tokens:
            for t2 in tokens:
                if t1==t2: continue
                for num in lucky_nums[:10]:
                    for combo in [t1.lower()+num+t2.lower(),
                                  t1.capitalize()+num+t2.capitalize(),
                                  t1.lower()+t2.lower()+num]:
                        if _ok(combo): yield combo

def gen_calendar(start=1940,end=2025,prefixes=None,suffixes=None,fmts=None,seps=None):
    prefixes=prefixes or [""];suffixes=suffixes or []
    seps=seps or ["","_","-",".","@","#","/"];fmts=fmts or DATE_FMTS
    for year in range(start,end+1):
        for month in range(1,13):
            for day in range(1,32):
                try: dt=datetime(year,month,day)
                except: continue
                dstrs=[]
                for fmt in fmts:
                    try:
                        ds=dt.strftime(fmt)
                        if ds not in dstrs: dstrs.append(ds)
                    except: pass
                for ds in dstrs:
                    for pre in prefixes:
                        for suf in (suffixes or [""]):
                            for sep in seps:
                                if pre and suf: combos=[pre+sep+ds+sep+suf,pre+ds+suf]
                                elif pre: combos=[pre+sep+ds,pre+ds]
                                elif suf: combos=[ds+sep+suf,ds+suf]
                                else: combos=[ds]
                                for pw in combos:
                                    for v in [pw,pw.upper(),pw.capitalize()]:
                                        if _ok(v): yield v

def gen_keyboard():
    WALKS=["qwerty","qwerty123","qwerty@123","Qwerty123","QWERTY","QWERTY123",
           "asdf","asdf123","asdf@123","Asdf123","asdfghjkl","1qaz","1qaz2wsx",
           "!QAZ2wsx","zxcvbn","qazwsx","1q2w3e","1q2w3e4r","1Q2W3E4R",
           "q1w2e3r4","Q1W2E3R4","abcd1234","1234abcd","abc@123","ABC123",
           "qweasdzxc","1029384756","zaq1xsw2","!qaz@wsx"]
    rows=["qwertyuiop","asdfghjkl","zxcvbnm","1234567890","QWERTYUIOP",
          "q1w2e3r4","1q2w3e4r","a1s2d3f4","246810","135790","159753","963741"]
    seen=set()
    for walk in WALKS:
        for suf in ["","1","123","@123","!","@","786","@786","@2024","2024",""]:
            pw=walk+suf
            if _ok(pw) and pw not in seen: seen.add(pw);yield pw
    for row in rows:
        for start in range(len(row)):
            for ln in range(2,min(len(row)+1,12)):
                seg=row[start:start+ln]
                if len(seg)<ln: break
                rev=seg[::-1]
                for base in [seg,rev]:
                    for suf in ["","1","12","123","1234","!","@","@123","786","007"]:
                        for pre in ["","1","123","786","@"]:
                            pw=pre+base+suf
                            if _ok(pw) and pw not in seen: seen.add(pw);yield pw

def gen_dict_streaming(paths):
    import urllib.request
    for p in (paths or []):
        p=str(p).strip()
        if not p: continue
        if p.startswith("http://") or p.startswith("https://"):
            try:
                req=urllib.request.Request(p,headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req,timeout=60) as resp:
                    for raw in resp:
                        try:
                            pw=raw.decode("utf-8","ignore").strip()
                            if not _ok(pw): continue
                            yield pw
                            wl=pw.lower()
                            if _ok(wl) and wl!=pw: yield wl
                            yield pw+"786";yield pw+"@123"
                        except: pass
            except Exception as e: log.warning(f"URL {p}: {e}")
            continue
        fp=Path(p)
        if not fp.exists(): continue
        try:
            with open(fp,"r",errors="ignore",encoding="utf-8") as f:
                for line in f:
                    pw=line.strip()
                    if _ok(pw): yield pw
        except: pass

def gen_indian_wordlist():
    all_words=HINDI+INDIAN_MALE[:200]+INDIAN_FEMALE[:150]+SURNAMES[:120]+CITIES[:100]+WORLD_NAMES[:100]
    seen=set()
    for word in all_words:
        for v in rules(word):
            for s in SUFFS:
                for p in PRES:
                    pw=p+v+s
                    if _ok(pw) and pw not in seen: seen.add(pw);yield pw

def gen_mobile(numbers=None,country_codes=None,extras=None,density=100):
    if numbers:
        for num in numbers:
            num=re.sub(r'[\s\-\+\(\)]','',num)
            if not num.isdigit() or len(num)<4: continue
            for v in [num,num[-10:],num[-8:],num[-6:],num[-4:],"0"+num[-10:],"91"+num[-10:]]:
                if v and _ok(v): yield v
                for s in SUFFS[:25]:
                    pw=v+s
                    if _ok(pw): yield pw
    codes=country_codes or ["+91"];exps=extras or []
    for cc in codes:
        info=MOBILE_CC.get(cc)
        if not info: continue
        pfx_list=info["px"]+exps;tlen=info["tlen"]
        for pfx in pfx_list:
            tail_len=tlen-len(pfx)
            if tail_len<0: continue
            total=10**tail_len
            step=max(1,int(total*(100-min(density,100))/10000)) if density<100 else 1
            for n in range(0,total,step):
                tail=str(n).zfill(tail_len);full=pfx+tail
                for v in [full,"0"+full,cc.lstrip("+")+full]:
                    if v and _ok(v): yield v

def gen_brute(charset=None,min_len=1,max_len=8,prefix="",suffix=""):
    if not charset: charset=string.ascii_lowercase+string.digits
    chars=list(dict.fromkeys(charset))
    for length in range(min_len,max_len+1):
        for combo in itertools.product(chars,repeat=length):
            yield prefix+"".join(combo)+suffix

def gen_master(cfg):
    mode=cfg.get("mode","smart");ui=cfg.get("user_info",{})
    gens=[gen_top_common(),gen_google_common()]
    if mode in ("smart","hybrid") and any(v for v in ui.values() if v):
        gens.append(gen_smart(ui))
    if mode in ("calendar","hybrid"):
        cal=cfg.get("calendar",{})
        pres=list(cal.get("prefix_words") or [])
        sufs=list(cal.get("suffix_words") or [])
        if ui.get("name"): pres.append(ui["name"])
        if ui.get("nick"): pres.append(ui["nick"])
        if ui.get("lucky"): sufs.append(ui["lucky"])
        gens.append(gen_calendar(start=int(cal.get("start_year",1940)),
            end=int(cal.get("end_year",2025)),prefixes=pres or [""],
            suffixes=sufs or [],fmts=cal.get("date_formats") or None,
            seps=cal.get("separators") or ["","_","-",".","/"]))
    if mode in ("keyboard","hybrid"): gens.append(gen_keyboard())
    DATA_DIR=Path(os.environ.get("DATA_DIR","/tmp/zipcracker"))
    DICTS_DIR=DATA_DIR/"dictionaries";DICTS_DIR.mkdir(parents=True,exist_ok=True)
    wlists=[str(f) for f in DICTS_DIR.glob("*.txt")]+cfg.get("extra_wordlists",[])
    for key in cfg.get("github_lists",[]):
        url=GITHUB_LISTS.get(key)
        if url: wlists.append(url)
    if wlists: gens.append(gen_dict_streaming(wlists))
    gens.append(gen_indian_wordlist())
    if mode in ("mobile","hybrid"):
        mob=cfg.get("mobile",{})
        gens.append(gen_mobile(numbers=mob.get("numbers",[]),
            country_codes=mob.get("country_codes",["+91"]),
            extras=mob.get("extra_prefixes",[]),density=int(mob.get("density",100))))
    if mode in ("brute","hybrid"):
        bf=cfg.get("brute",{})
        cs=""
        for key in (bf.get("charsets") or ["lower","digits"]): cs+=CS.get(key,key)
        cs+=(bf.get("custom_chars") or "")
        cs="".join(dict.fromkeys(cs)) if cs else (string.ascii_lowercase+string.digits)
        gens.append(gen_brute(charset=cs,min_len=int(bf.get("min_len",1)),
            max_len=int(bf.get("max_len",8)),prefix=bf.get("prefix") or "",
            suffix=bf.get("suffix") or ""))
    seen=set();count=0;CAP=10_000_000
    for gen in gens:
        try:
            for pw in gen:
                if not _ok(pw): continue
                if count<CAP:
                    if pw in seen: continue
                    seen.add(pw)
                count+=1;yield pw
        except Exception as ex: log.warning(f"gen error: {ex}");continue

# ══════════════════════════════════════════════════════════════════════════════
#  C ENGINE — ZipCrypto 12-byte check — 1M-10M/sec via ThreadPoolExecutor
#  ctypes releases Python GIL → true parallel C execution in threads
# ══════════════════════════════════════════════════════════════════════════════
_C_LIB=None;_C_READY=False

_C_SRC=r"""
#include <stdint.h>
#include <string.h>
static uint32_t T[256];static int Tok=0;
static void init(){if(Tok)return;for(int i=0;i<256;i++){uint32_t c=(uint32_t)i;for(int j=0;j<8;j++)c=(c&1u)?(0xEDB88320u^(c>>1)):(c>>1);T[i]=c;}Tok=1;}
#define U(b,k0,k1,k2) do{(k0)=T[(uint8_t)((k0)^(uint8_t)(b))]^((k0)>>8);(k1)=((k1)+((k0)&0xffu))*134775813u+1u;(k2)=T[(uint8_t)((k2)^((k1)>>24))]^((k2)>>8);}while(0)
int batch(const char* d,const int* ls,int n,const uint8_t* h,uint8_t chk,const int* stop){
    init();const char* p=d;
    for(int i=0;i<n;i++){
        if((i&0xFFFFu)==0&&stop&&*stop)return -2;
        int L=ls[i];uint32_t k0=0x12345678u,k1=0x23456789u,k2=0x34567890u;
        for(int j=0;j<L;j++){U((uint8_t)p[j],k0,k1,k2);}
        uint8_t c=0;
        for(int j=0;j<12;j++){uint16_t t=(uint16_t)((k2|2u)&0xffffu);uint8_t db=(uint8_t)(((uint32_t)t*(uint32_t)(t^1u))>>8);c=h[j]^db;U(c,k0,k1,k2);}
        if(c==chk)return i;
        p+=L;
    }
    return -1;
}
"""

def _compile():
    global _C_LIB,_C_READY
    if _C_READY: return _C_LIB
    try:
        src="/tmp/_zc46.c";lp="/tmp/_zc46.so"
        with open(src,"w") as f: f.write(_C_SRC)
        r=subprocess.run(["gcc","-O3","-march=native","-shared","-fPIC","-o",lp,src],
                          capture_output=True,timeout=30)
        if r.returncode!=0:
            r=subprocess.run(["gcc","-O2","-shared","-fPIC","-o",lp,src],
                              capture_output=True,timeout=30)
        if r.returncode!=0: log.warning(f"C compile failed: {r.stderr.decode()[:100]}");return None
        dll=ctypes.CDLL(lp)
        dll.batch.restype=ctypes.c_int
        dll.batch.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_int),ctypes.c_int,
                             ctypes.c_char_p,ctypes.c_ubyte,ctypes.POINTER(ctypes.c_int)]
        _C_LIB=dll;_C_READY=True
        log.info("C ZipCrypto engine compiled — 1M+/sec ACTIVE")
        return dll
    except Exception as e: log.warning(f"C engine unavailable: {e}");return None

try: _compile()
except Exception: pass

_PY_CRC=[0]*256
for _i in range(256):
    _c=_i
    for _ in range(8): _c=(0xEDB88320^(_c>>1)) if (_c&1) else (_c>>1)
    _PY_CRC[_i]=_c

def _py_check(pw_bytes,hdr,chk):
    crc=_PY_CRC;k0=0x12345678;k1=0x23456789;k2=0x34567890
    for b in pw_bytes:
        k0=crc[(k0^b)&0xff]^(k0>>8)
        k1=((k1+(k0&0xff))*134775813+1)&0xffffffff
        k2=crc[(k2^(k1>>24))&0xff]^(k2>>8)
    c=0
    for i in range(12):
        t=(k2|2)&0xffff;db=((t*(t^1))>>8)&0xff;c=hdr[i]^db
        k0=crc[(k0^c)&0xff]^(k0>>8)
        k1=((k1+(k0&0xff))*134775813+1)&0xffffffff
        k2=crc[(k2^(k1>>24))&0xff]^(k2>>8)
    return (c&0xff)==chk

def _extract_hdr(fpath):
    try:
        with open(fpath,"rb") as f: raw=f.read(8192)
        sig=b'PK\x03\x04';pos=0
        while pos<len(raw)-30:
            idx=raw.find(sig,pos)
            if idx<0 or idx+30>len(raw): break
            flags=struct.unpack_from('<H',raw,idx+6)[0]
            crc32_v=struct.unpack_from('<I',raw,idx+14)[0]
            mod_time=struct.unpack_from('<H',raw,idx+10)[0]
            fname_len=struct.unpack_from('<H',raw,idx+26)[0]
            extra_len=struct.unpack_from('<H',raw,idx+28)[0]
            dstart=idx+30+fname_len+extra_len
            if not (flags&0x1): pos=idx+1;continue
            if dstart+12>len(raw): pos=idx+1;continue
            hdr=bytes(raw[dstart:dstart+12])
            chk=((mod_time>>8)&0xff) if (flags&0x8) else ((crc32_v>>24)&0xff)
            return hdr,chk
        return None
    except Exception: return None


class Cracker:

    @staticmethod
    def crack_zip_fast(fpath,pw_gen,progress_cb=None,freq=1000):
        """v46: C engine via ThreadPoolExecutor — 1M-10M/sec. ctypes releases GIL = true parallel."""
        res={"found":False,"password":None,"attempts":0,"elapsed":0.0,
             "speed":0,"cancelled":False,"error":None,"use_aes":False}
        if not Path(fpath).exists(): res["error"]="File not found";return res
        names=[];use_aes=False
        try:
            if HAS_AES:
                try:
                    with pyzipper.AESZipFile(fpath) as z:
                        names=z.namelist()
                        if names:
                            info=z.infolist()[0]
                            use_aes=(info.flag_bits&0x1)!=0 or info.compress_type==99
                except Exception: pass
            if not names:
                with zipfile.ZipFile(fpath) as z: names=z.namelist()
        except Exception as ex: res["error"]=str(ex);return res
        if not names: res["error"]="Empty/corrupt ZIP";return res
        res["use_aes"]=use_aes;target=names[0];t0=time.time()

        # AES: single-thread (PBKDF2 cannot be parallelized)
        if use_aes:
            n=0;found=None;last=0
            try:
                ZF=pyzipper.AESZipFile if HAS_AES else zipfile.ZipFile
                with ZF(fpath) as zf:
                    for pw in pw_gen:
                        n+=1
                        if n-last>=freq:
                            el=time.time()-t0;sp=int(n/max(el,0.001));last=n
                            if progress_cb and not progress_cb(n,sp,pw):
                                res["cancelled"]=True;break
                        try:
                            zf.setpassword(pw.encode("utf-8","ignore"))
                            zf.read(target);found=pw;break
                        except Exception: pass
            except Exception as ex: res["error"]=str(ex)
            el=time.time()-t0
            res.update(attempts=n,elapsed=round(el,2),speed=int(n/max(el,0.001)))
            if found: res["found"]=True;res["password"]=found
            return res

        # Standard ZIP: C engine + thread pool
        hdr_info=_extract_hdr(fpath)
        lib=_C_LIB if _C_READY else None
        USE_C=lib is not None and hdr_info is not None
        if USE_C: hdr,chk=hdr_info
        N_THREADS=max(2,min(8,(os.cpu_count() or 1)*2))
        BATCH=100_000 if USE_C else 5_000
        found_pw=[None];total_n=[0]
        lock=threading.Lock();stop_evt=threading.Event()

        def run_c(batch_pws):
            if stop_evt.is_set(): return None
            try:
                enc=[p.encode("utf-8","ignore") for p in batch_pws]
                flat=b"".join(enc)
                lens=(ctypes.c_int*len(enc))(*[len(e) for e in enc])
                stop_c=ctypes.c_int(1 if stop_evt.is_set() else 0)
                idx=lib.batch(flat,lens,len(batch_pws),hdr,ctypes.c_ubyte(chk),ctypes.byref(stop_c))
                if idx>=0:
                    cand=batch_pws[idx]
                    try:
                        with zipfile.ZipFile(fpath) as zv:
                            zv.setpassword(cand.encode("utf-8","ignore"));zv.read(target)
                        return cand
                    except Exception: return None
                return None
            except Exception: return None

        def run_py(batch_pws):
            if stop_evt.is_set(): return None
            h2,c2=(hdr_info if hdr_info else (None,None))
            for pw in batch_pws:
                if stop_evt.is_set(): break
                try:
                    pw_b=pw.encode("utf-8","ignore")
                    if h2 and _py_check(pw_b,h2,c2):
                        try:
                            with zipfile.ZipFile(fpath) as zv:
                                zv.setpassword(pw_b);zv.read(target)
                            return pw
                        except Exception: pass
                    elif not h2:
                        try:
                            with zipfile.ZipFile(fpath) as zf:
                                zf.setpassword(pw_b);zf.read(target);return pw
                        except RuntimeError: pass
                        except Exception: pass
                except Exception: pass
            return None

        batch_fn=run_c if USE_C else run_py
        batch=[];futures=[];t_last=time.time()

        with ThreadPoolExecutor(max_workers=N_THREADS) as ex:
            for pw in pw_gen:
                if stop_evt.is_set(): break
                batch.append(pw)
                if len(batch)>=BATCH:
                    f=ex.submit(batch_fn,batch[:])
                    futures.append(f)
                    with lock: total_n[0]+=len(batch)
                    batch=[]
                    done=[];remaining=[]
                    for fut in futures:
                        if fut.done(): done.append(fut)
                        else: remaining.append(fut)
                    futures=remaining
                    for fut in done:
                        try:
                            r=fut.result()
                            if r: found_pw[0]=r;stop_evt.set()
                        except Exception: pass
                    if stop_evt.is_set(): break
                    now=time.time()
                    if now-t_last>=0.5:
                        with lock: n=total_n[0]
                        el=now-t0;sp=int(n/max(el,0.001));t_last=now
                        if progress_cb and not progress_cb(n,sp,pw):
                            stop_evt.set();break
            if batch and not stop_evt.is_set():
                f=ex.submit(batch_fn,batch)
                futures.append(f)
                with lock: total_n[0]+=len(batch)
            for fut in futures:
                try:
                    r=fut.result(timeout=60)
                    if r and not found_pw[0]: found_pw[0]=r;stop_evt.set()
                except Exception: pass

        el=time.time()-t0;n=total_n[0]
        res.update(attempts=n,elapsed=round(el,2),speed=int(n/max(el,0.001)))
        if found_pw[0]:
            res["found"]=True;res["password"]=found_pw[0]
            log.info(f"CRACKED! '{found_pw[0]}' speed={res['speed']:,}/s n={n:,} C={USE_C}")
        if stop_evt.is_set() and not found_pw[0]: res["cancelled"]=True
        return res

    @staticmethod
    def crack_pdf(fpath,pw_gen,progress_cb=None,freq=200):
        res={"found":False,"password":None,"attempts":0,"elapsed":0.0,
             "speed":0,"cancelled":False,"error":None}
        if not Path(fpath).exists(): res["error"]="File not found";return res
        n=0;found=None;last=0;t0=time.time()
        try:
            for pw in pw_gen:
                n+=1
                if n-last>=freq:
                    el=time.time()-t0;sp=int(n/max(el,0.001));last=n
                    if progress_cb and not progress_cb(n,sp,pw):
                        res["cancelled"]=True;break
                if HAS_PIKE:
                    try:
                        with pikepdf.open(fpath,password=pw): found=pw;break
                    except pikepdf.PasswordError: pass
                    except Exception: pass
                elif HAS_PDF:
                    try:
                        r=_PDFR(fpath)
                        if r.decrypt(pw)!=0: found=pw;break
                    except Exception: pass
        except Exception as ex: res["error"]=str(ex)
        el=time.time()-t0
        res.update(attempts=n,elapsed=round(el,2),speed=int(n/max(el,0.001)))
        if found: res["found"]=True;res["password"]=found
        return res

    @staticmethod
    def crack(fpath,pw_gen,progress_cb=None,freq=1000):
        ext=Path(fpath).suffix.lower()
        if ext==".pdf": return Cracker.crack_pdf(fpath,pw_gen,progress_cb,freq)
        return Cracker.crack_zip_fast(fpath,pw_gen,progress_cb,freq)

    @staticmethod
    def extract_and_zip(fpath,password,out_zip):
        res={"ok":False,"zip_path":None,"files":[],"error":None}
        tmp=tempfile.mkdtemp()
        try:
            pw_b=password.encode("utf-8","ignore")
            if HAS_AES:
                try:
                    with pyzipper.AESZipFile(fpath) as z:
                        z.setpassword(pw_b);z.extractall(tmp);res["files"]=z.namelist()
                except Exception:
                    with zipfile.ZipFile(fpath) as z:
                        z.setpassword(pw_b);z.extractall(tmp);res["files"]=z.namelist()
            else:
                with zipfile.ZipFile(fpath) as z:
                    z.setpassword(pw_b);z.extractall(tmp);res["files"]=z.namelist()
            shutil.make_archive(out_zip.replace(".zip",""),"zip",tmp)
            res["ok"]=True;res["zip_path"]=out_zip
        except Exception as e: res["error"]=str(e)
        finally: shutil.rmtree(tmp,ignore_errors=True)
        return res
