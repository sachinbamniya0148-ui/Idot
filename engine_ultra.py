#!/usr/bin/env python3
"""
engine_ultra.py v36 — ZipPasswordCrack.in
==========================================
ULTRA SPEED ENGINE — 10k-100k/s ZIP, 500-2k/s PDF
v36 FINAL:
  - BATCH=8000, N_WORKERS=32 → max throughput on Railway
  - EMOJI_PASSWORDS constant — actually used in gen_top_common
  - Bank patterns, Aadhaar patterns, India PIN/vehicle patterns
  - 15 GitHub wordlists streaming (SecLists, RockYou, DarkWeb etc.)
  - Smart personal: name+DOB+mobile+city combos (50M+ variants)
  - Calendar attack: all date formats x prefix x suffix
  - Mobile attack: 18 country generators
  - Brute force: 100T+ combinations
  - Parallel batch ZIP: ThreadPoolExecutor, each worker opens own ZipFile
  - AES-256: single-threaded (PBKDF2 hardware limit — can't parallelize)
  - PDF: pikepdf parallel OR pypdf fallback (pure Python)
"""
import itertools, string, logging, time, zipfile, re, tempfile, shutil
import os, threading, hashlib
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger("engine")

try:
    import pyzipper; HAS_AES = True
except ImportError:
    HAS_AES = False

try:
    import pikepdf; HAS_PIKE = True
except ImportError:
    HAS_PIKE = False

try:
    from pypdf import PdfReader as _PDF; HAS_PDF = True
except ImportError:
    try:
        from PyPDF2 import PdfReader as _PDF; HAS_PDF = True
    except ImportError:
        HAS_PDF = False

# ─── Character Sets ───────────────────────────────────────────────────────────
CS = {
    "lower":     string.ascii_lowercase,
    "upper":     string.ascii_uppercase,
    "digits":    string.digits,
    "alpha":     string.ascii_letters,
    "alnum":     string.ascii_letters + string.digits,
    "sym":       "!@#$%^&*()-_+=[]{}|;:',.<>?/`~\\",
    "sym_india": "!@#$%&*_-.+~",
    "hex":       "0123456789abcdef",
    "full":      string.printable.strip(),
}

# ─── GitHub Wordlists ─────────────────────────────────────────────────────────
GITHUB_LISTS = {
    "top1m":    "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",
    "top100k":  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100000.txt",
    "top10k":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
    "best1050": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/best1050.txt",
    "xato1m":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/xato-net-10-million-passwords-1000000.txt",
    "probable": "https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/Top12Thousand-probable-v2.txt",
    "weakpass": "https://raw.githubusercontent.com/kkrypt0nn/wordlists/main/wordlists/passwords/common_passwords_win.txt",
    "leaked":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/alleged-gmail-passwords.txt",
    "rockyou":  "https://raw.githubusercontent.com/brannondorsey/naive-hashcat/master/rockyou.txt",
    "common_3k":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/common-passwords-win.txt",
    "bt4":      "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/bt4-password.txt",
    "darkweb":  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/darkweb2017-top10000.txt",
    "top500":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/500-worst-passwords.txt",
    "hak5":     "https://raw.githubusercontent.com/nicowillis/passwords/master/common_10000_passwords.txt",
    "kaonashi": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/Ashley-Madison.txt",
}

# ─── Word Banks ───────────────────────────────────────────────────────────────
TOP_COMMON = [
    "123456","password","123456789","12345678","12345","qwerty","abc123","password1",
    "admin","letmein","welcome","monkey","dragon","master","sunshine","princess",
    "iloveyou","111111","000000","password123","admin123","root","toor","pass","test",
    "guest","1234","1234567","1234567890","qwertyuiop","asdfghjkl","qwerty123","1q2w3e4r",
    "zaq1xsw2","p@ssw0rd","P@ssword","pa55word","pa$$word","admin@123","Admin@123",
    "Admin123","user123","test123","demo123","india","bharat","india123","bharat123",
    "india786","bharat786","india2024","786","786786","007","007007","420","420420",
    "108","108108","999","9999","pakistan","pakistan123","lahore","karachi","islamabad",
    "bangladesh","dhaka","pass@123","Pass@123","P@ss123","1qaz2wsx","!QAZ2wsx","zxcvbn",
    "q1w2e3r4","a1s2d3f4","abcd1234","1234abcd","abc@123","ABC123","Abc@123",
    "letmein123","master123","batman","superman","pokemon","samsung","iphone","android",
    "windows","google","facebook","instagram","whatsapp","cricket","dhoni","kohli",
    "sachin","rohit","virat","msdhoni","bollywood","shahrukh","salman","aamir","hrithik",
    "deepika","katrina","rahul","priya","pooja","neha","anjali","sunny","lucky","rocky",
    "sharma","verma","gupta","kumar","singh","patel","mumbai","delhi",
    "maa","baap","papa","bhai","didi","dost","yaar","786@123","@786",
    "qwerty1","password2","123456a","a123456","football","baseball","soccer",
    "love","loveyou","iloveu","hello","hello123","secret","secret1","god","lord",
    "allah786","michael","jessica","daniel","jordan","harley",
    "1234pass","pass1234","mypassword","mypass","changeme","change123",
    "letmein1","welcome1","admin1234","administrator","superuser","superadmin",
    "root123","rootpass","system","system123","default","default123",
    "123","1234","12345","password!","pass123","abc","abcd","1111","2222","3333",
    "4444","5555","6666","7777","8888","9999","0000","11111","22222","33333",
    "12341234","pass@1234","Password@1","Admin@1234","welcome123","Welcome@123",
    "Test@1234","User@1234","login","Login123","login123","qazwsx","edcrfv",
    "tgbyhn","ikmnbv","plmnko","1029384756","2580","258025","147","1478","1470",
    "159","1596","7894","4561","7415","8520","9630","2143","6589","0987654321",
    "bharat2024","india@2024","jai@hind","vandemataram","jai786","786jai","om786",
    "krishna786","ram786","shiv786","ganesh786","allah786","waheguru786",
    "1947india","india1947","bharat1947","swatantrata","independence",
    "abc@1234","Abc1234","abc1234@","@abc1234","1234@abc","Password1!",
    "password@1","pass@word1","india@123","India@123","INDIA123","india2025",
    "786@786","@786786","007@007","password@786","pass@786","admin@786",
    "india@786","bharat@786","2024@786","2025@786","786@2024","786@2025",
    "1234@786","786@1234","pass@007","admin@007","india@007",
    "password2025","admin2025","user2025","test2025","login2025",
    "Pass@2025","Admin@2025","India@2025","User@2025",
    "abcd@786","abc@786","xyz@786","pqr@786",
    "ram@786","shyam@786","mohan@786","sohan@786",
    "786#786","#786786","@786@","786#","#786",
]

YEARS = [str(y) for y in range(1940, 2026)]

SUFS = ["","1","2","3","12","21","123","321","1234","4321","12345","54321","123456","654321",
        "1234567","12345678","123456789","1234567890","@","@1","@12","@123","@1234","@12345",
        "@786","@007","@420","@108","#","#123","!","!123","_","_123","_786","_007","0","00",
        "000","0000","786","786786","007","007007","420","108","999","9999",
        "@2024","@2025","@india","ji","_ji","bhai","india","kumar",
        "2024","2025","2023","2022","@2023","@2022","@2021","@2020",
        "jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec",
        "@jan","@feb","@mar","@apr","@may","@jun","@jul","@aug","@sep","@oct","@nov","@dec",
        "1996","1997","1998","1999","2000","2001","2002","2003","2004","2005",
        "@1996","@1997","@1998","@1999","@2000","@2001","@2002","@2003",
        "@123","@1234","!123","#123","@786","_123","_786","@2024","@2025","@india",
        "!@#","@1","!1","#1","_1","_12","_2024","@786786","#786","@123456","!1234","@12345",
        "@2022","#2024","!2024","_2024","@000","@111","#123456","@2025","!2025","#2025"]

PRES = ["","my","the","new","old","its","real","true","shri","dr","mr","mrs","786","007","@","#","1"]

DATE_FMTS = ["%d%m%Y","%d%m%y","%Y%m%d","%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%m%d%Y",
             "%Y%d%m","%d%m","%m%Y","%Y","%d","%m","%d%b%Y","%b%Y","%B%Y",
             "%Y-%m-%d","%y%m%d","%m/%d/%Y","%d%b%y","%b%d%Y","%d%b","%b%d"]

INDIAN_NAMES = [
    "rahul","amit","sunil","anil","ravi","sanjay","vijay","ajay","raj","ram","krishna",
    "shyam","mohan","rohan","karan","arjun","vikram","suresh","mahesh","ganesh","dinesh","rajesh",
    "mukesh","deepak","pradeep","sandeep","kuldeep","pankaj","vivek","abhishek","manish","ankit",
    "mohit","rohit","sumit","lalit","nikhil","sahil","tushar","gaurav","sourav","anurag","mayank",
    "neeraj","dheeraj","kunal","vishal","vaibhav","saurabh","himanshu","shubham","akash","prakash",
    "aditya","harsh","yash","sunny","lucky","bobby","rocky","pappu","guddu","bunty","bablu","pintu",
    "rinku","raju","raja","sonu","monu","harpreet","gurpreet","manpreet","balwinder","amarjit",
    "gurjit","ranjit","imran","asif","zaid","farhan","ayaan","danish","faizan","rizwan","bilal",
    "usman","hassan","ali","amir","salman","sultan","shahid","khalid","rashid","mohd","mohammed",
    "muhammad","ahmad","ahmed","iqbal","nawaz","asad","babar","murugan","karthik","senthil",
    "anand","prasad","priya","pooja","neha","rita","geeta","sita","meena","seema","reena","sunita",
    "kavita","lalita","rekha","meera","sheela","kamla","vimla","sharmila","shweta","nisha","disha",
    "asha","usha","radha","divya","kavya","riya","tara","anjali","mamta","deepika","shreya",
    "sweety","pinky","simran","ayesha","fatima","zainab","maryam","khadija","zahra","asma",
    "noor","sana","hina","mehak","mehwish","amna","bushra","farida","nasreen","parveen",
    "sachin","virat","dhoni","kohli","tendulkar","rohit","bumrah","jadeja","shami","pandya",
    "harbhajan","yuraj","zaheer","sehwag","gambhir","dravid","laxman","ganguly","kumble",
    "ratan","naresh","sudhir","surendra","mahendra","rajendra","narendra","virendra","devendra",
    "jitendra","yogendra","ravindra","harendra","shailendra",
    "poonam","ritu","preeti","jyoti","manju","geeta","lata","gita","sushma","rama","savita","sudha",
    "varsha","meenu","baby","sweetu","dolly","sukhwinder","lakhwinder","jaswinder",
    "tariq","waseem","nadeem","naseem","saleem","raheem","hakeem","naeem","azeem","kareem",
    "venkat","raman","subramaniam","krishnamurthy","srinivasan","balakrishnan",
    "arumugam","karuppasamy","murugesan","selvam","tamilarasan","velayutham","manikandan",
    "sachinbamniya","bamniya","aryan","aarav","vivan","ishaan","advait","reyansh","ayansh","atharv",
    "ananya","aanya","aadhya","pari","myra","kyra","zara","diya","sia",
    "om","dev","ved","jai","tej","nav","dhruv","kabir","shaan",
]

SURNAMES = [
    "sharma","verma","gupta","kumar","singh","patel","shah","mehta","joshi","tiwari",
    "pandey","mishra","yadav","chauhan","rajput","thakur","rao","reddy","naidu","nair","pillai",
    "iyer","menon","banerjee","chatterjee","mukherjee","ghosh","das","bose","roy","saha","mitra",
    "basu","chowdhury","khan","ansari","qureshi","shaikh","sheikh","siddiqui","malik","mirza",
    "gill","dhillon","sandhu","grewal","sidhu","kang","brar","agarwal","goyal","mittal","goel",
    "jain","kapoor","khanna","chopra","malhotra","arora","kohli","shukla","dubey","tripathi",
    "upadhyay","bamniya","solanki","rawat","bisht","negi","bhandari","rana","maurya","bajpai",
    "srivastava","awasthi","saxena","tyagi","garg","bansal","bhatt","dixit","trivedi",
    "chaudhary","rathore","sisodiya","bundela","chandel","gahlot","sisodia","naruka","gehlot",
    "dalit","meena","gurjar","jat","ahir","lohar","kumhar","nai","kumbhar","goud",
]

CITIES = [
    "mumbai","delhi","bangalore","bengaluru","chennai","kolkata","hyderabad","pune",
    "ahmedabad","jaipur","surat","lucknow","kanpur","nagpur","indore","bhopal","patna","vadodara",
    "agra","nashik","faridabad","meerut","rajkot","amritsar","varanasi","prayagraj","jodhpur",
    "guwahati","kochi","chandigarh","noida","gurgaon","thane","ranchi","lahore","karachi",
    "islamabad","rawalpindi","peshawar","dhaka","chittagong","sylhet","dubai","abudhabi","riyadh",
    "vizag","coimbatore","madurai","bhilai","raipur","gwalior","allahabad","jabalpur","srinagar",
]

HINDI = [
    "pyar","mohabbat","ishq","prem","preet","sneh","mamta","dard","khushi","gham","dukh",
    "sukh","aanand","shanti","umeed","aasha","sapna","khwaab","armaan","dil","zindagi","jeevan",
    "duniya","maa","baap","papa","baba","amma","ammi","abbu","dadi","dada","nani","nana","bhai",
    "bhaiya","didi","behan","beta","beti","baccha","parivaar","ghar","ram","krishna","shiva",
    "ganesh","allah","waheguru","sona","mona","gudiya","munni","rani","raja","dost","yaar",
    "sahab","ji","cricket","dhoni","kohli","sachin","rohit","virat","ipl","t20","bollywood",
    "shahrukh","salman","deepika","katrina","priyanka","anushka","india","bharat","hindustan",
    "786","007","420","108","999","1947","jai","hind","vande","mataram","bhagwan","ishwar",
    "zindabad","aman","chain","barkat","dua","nazar","hifazat","mehnat","kamyabi","khuda",
    "bismillah","mashallah","inshallah","alhamdulillah","subhanallah","jazakallah",
]

MOBILE_CC = {
    "+91":  {"px": ["6","7","8","9","70","71","72","73","74","75","76","77","78","79",
                    "80","81","82","83","84","85","86","87","88","89","90","91","92","93","94","95","96","97","98","99"], "tlen": 10},
    "+92":  {"px": ["30","31","32","33","34","300","301","310","320","321","330","331"], "tlen": 10},
    "+880": {"px": ["13","14","15","16","17","18","19","130","140","150","170","180"], "tlen": 10},
    "+1":   {"px": ["201","202","212","213","310","312","408","415","469","646","702","917"], "tlen": 10},
    "+44":  {"px": ["7400","7500","7600","7700","7800","7900"], "tlen": 10},
    "+86":  {"px": ["130","131","132","135","136","137","138","150","151","158","180","181"], "tlen": 11},
    "+971": {"px": ["50","52","54","55","56","58"], "tlen": 9},
    "+966": {"px": ["50","53","54","55","56","57","58","59"], "tlen": 9},
    "+62":  {"px": ["81","82","83","85","87","89","811","812","821","852"], "tlen": 10},
    "+55":  {"px": ["11","21","31","41","51","61","71","81","91"], "tlen": 11},
    "+7":   {"px": ["900","901","903","905","910","911","912","916","917"], "tlen": 10},
    "+49":  {"px": ["151","152","157","159","160","162","163","170","171","172"], "tlen": 11},
    "+33":  {"px": ["60","61","62","63","64","65","66","67","68","69"], "tlen": 9},
    "+81":  {"px": ["70","80","90"], "tlen": 10},
    "+82":  {"px": ["10","11","16","17","18","19"], "tlen": 10},
    "+234": {"px": ["70","80","81","90","803","806","810","813"], "tlen": 10},
    "+20":  {"px": ["10","11","12","15","19"], "tlen": 10},
    "+27":  {"px": ["60","61","71","72","73","74","76","78","79","81","82","83"], "tlen": 9},
}

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _ok(pw):
    return bool(pw and isinstance(pw, str) and 3 <= len(pw) <= 128)

LEET = [
    {'a':'@','e':'3','i':'1','o':'0','s':'$','t':'7','b':'8','g':'9','l':'1'},
    {'a':'4','e':'3','i':'!','o':'0','s':'5','t':'7','b':'6','g':'9'},
    {'a':'@','e':'€','i':'|','o':'()','s':'$','n':'^','h':'#'},
    {'a':'4','e':'3','i':'|','o':'0','s':'5','g':'6','t':'+'},
]

def leet(w):
    r = set()
    for m in LEET:
        v = w.lower()
        for k, val in m.items():
            v = v.replace(k, val)
        if v != w.lower() and _ok(v):
            r.add(v)
    return list(r)

def rules(word):
    if not word: return []
    w = word.lower(); wc = word.capitalize()
    wu = word.upper(); wr = word[::-1]
    return list(set(r for r in [w, wc, wu, wr, wr.capitalize()] + leet(w) if _ok(r)))

def interleave(word, num):
    results = []
    w = word[:8]; n = str(num)[:8]
    r = "".join(a + b for a, b in zip(w, n.ljust(len(w), '0')))
    if _ok(r): results.append(r)
    for i in range(0, len(w) + 1, 2):
        pw = w[:i] + n + w[i:]
        if _ok(pw): results.append(pw)
    return results

def google_style(words):
    nums = ["786","007","420","108","2024","2025","1947","999","123456","12345","1234","123"]
    for word in words:
        w = word.lower(); wc = word.capitalize(); wu = word.upper()
        for yr in ["2020","2021","2022","2023","2024","2025","2019","2018","2015","2010","2000","1999","1998","1997","1996"]:
            yield w + yr; yield wc + yr; yield wu + yr
            yield w + "@" + yr; yield wc + "@" + yr
        for n in ["1","2","3","12","21","123","321","1234","4321","786","007","420","108","2024","2025","00","01","99"]:
            yield w + n; yield wc + n; yield wu + n; yield n + w; yield n + wc
        for sym in ["@","!","#","_"]:
            for n in ["1","12","123","786","2024","2025","007","420"]:
                yield w + sym + n; yield wc + sym + n
        for n in nums:
            for sep in ["","@","#","_","."]:
                yield w + sep + n; yield wc + sep + n; yield wu + n
        if len(w) <= 6:
            yield w + w; yield wc + w; yield w + wc
        for r in leet(w):
            yield r; yield r.capitalize()

# ─── v32 NEW: Bank Statement Password Patterns ────────────────────────────────
def gen_bank_patterns(user_info=None):
    """
    Bank PDFs typically use: account last 4-6 digits, DOB, mobile,
    DDMMYYYY, account number combinations.
    SBI, HDFC, ICICI, Axis, PNB, BOB, Kotak common patterns.
    """
    ui = user_info or {}
    name   = (ui.get("name")   or "").strip().lower()
    dob    = (ui.get("dob")    or "").strip()
    mobile = (ui.get("mobile") or "").strip()
    seen   = set()

    def _y(pw):
        if _ok(pw) and pw not in seen:
            seen.add(pw); return pw
        return None

    # DOB-based (most common for bank statements)
    dt = None
    if dob:
        for fmt in ("%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%Y-%m-%d","%d%m%Y","%d%m%y","%Y%m%d","%d/%m/%y"):
            try: dt = datetime.strptime(dob.strip(), fmt); break
            except: pass

    if dt:
        d = f"{dt.day:02d}"; m = f"{dt.month:02d}"
        y = str(dt.year); y2 = y[-2:]; y4 = y

        # Most common bank statement passwords
        bank_pats = [
            f"{d}{m}{y4}",         # 25121990
            f"{d}{m}{y2}",         # 251290
            f"{y4}{m}{d}",         # 19901225
            f"{y2}{m}{d}",         # 901225
            f"{d}{m}",             # 2512
            f"{m}{y4}",            # 121990
            f"{d}{m}{y4}@",        # 25121990@
            f"@{d}{m}{y4}",        # @25121990
            f"{d}{m}{y4}#",        # 25121990#
            f"{d}/{m}/{y4}",       # 25/12/1990
            f"{d}-{m}-{y4}",       # 25-12-1990
            f"{d}.{m}.{y4}",       # 25.12.1990
            f"{d}{m}{y4}!",        # 25121990!
            f"{d}{m}{y2}!",        # 251290!
            f"{y4}",               # 1990
            f"{y2}",               # 90
            # SBI, HDFC patterns
            f"SBI{d}{m}{y4}",f"sbi{d}{m}{y4}",
            f"HDFC{d}{m}{y4}",f"hdfc{d}{m}{y4}",
            f"ICICI{d}{m}{y4}",f"icici{d}{m}{y4}",
            f"AXIS{d}{m}{y4}",f"axis{d}{m}{y4}",
            f"PNB{d}{m}{y4}",f"pnb{d}{m}{y4}",
            f"BOI{d}{m}{y4}",f"boi{d}{m}{y4}",
            f"KOTAK{d}{m}{y4}",f"kotak{d}{m}{y4}",
        ]
        if name:
            bank_pats += [
                f"{name}{d}{m}{y4}",f"{name.capitalize()}{d}{m}{y4}",
                f"{name}{y4}",f"{name.capitalize()}{y4}",
                f"{name}{d}{m}{y2}",f"{name.capitalize()}{d}{m}{y2}",
                f"{name}@{d}{m}{y4}",f"{name.capitalize()}@{d}{m}{y4}",
            ]
        if mobile:
            m_clean = re.sub(r'[\s\-\+\(\)]','',mobile)
            last4 = m_clean[-4:] if len(m_clean)>=4 else m_clean
            last6 = m_clean[-6:] if len(m_clean)>=6 else m_clean
            bank_pats += [
                f"{last4}{d}{m}{y4}",f"{d}{m}{y4}{last4}",
                f"{last6}{d}{m}{y2}",f"{d}{m}{y2}{last4}",
            ]
        for p in bank_pats:
            pw = _y(p)
            if pw: yield pw

    # Mobile-based bank passwords
    if mobile:
        m_clean = re.sub(r'[\s\-\+\(\)]','',mobile)
        last4 = m_clean[-4:] if len(m_clean)>=4 else m_clean
        last6 = m_clean[-6:] if len(m_clean)>=6 else m_clean
        last8 = m_clean[-8:] if len(m_clean)>=8 else m_clean
        mob_pats = [
            last4, last6, last8, m_clean[-10:],
            f"{last4}@",f"@{last4}",f"{last6}@",
            f"{last4}786",f"{last4}123",f"786{last4}",
        ]
        if name:
            mob_pats += [f"{name}{last4}",f"{name.capitalize()}{last4}",
                         f"{name}{last6}",f"{last4}{name}"]
        for p in mob_pats:
            pw = _y(p)
            if pw: yield pw

    # Name-based
    if name:
        name_pats = [
            f"{name}123",f"{name.capitalize()}123",f"{name}@123",
            f"{name.capitalize()}@123",f"{name}786",f"{name.capitalize()}786",
            f"{name}@786",f"{name.capitalize()}@786",
            f"{name}1234",f"{name.capitalize()}1234",
            f"{name}12345",f"{name.capitalize()}12345",
            f"{name}2024",f"{name.capitalize()}2024",f"{name}@2024",
            f"{name}2025",f"{name.capitalize()}2025",f"{name}@2025",
            f"{name}!",f"{name.capitalize()}!",
            f"{name}#",f"{name.capitalize()}#",
            f"{name}@",f"{name.capitalize()}@",
            f"@{name}",f"@{name.capitalize()}",
        ]
        for p in name_pats:
            pw = _y(p)
            if pw: yield pw

# ─── v32 NEW: Aadhaar Card Password Patterns ─────────────────────────────────
def gen_aadhaar_patterns(user_info=None):
    """
    Aadhaar PDFs: typically password = DOB (DDMMYYYY), name+DOB,
    last 4 digits of Aadhaar, or PIN code.
    UIDAI common: DDMMYYYY, DDMMYY, name+DOB combos.
    """
    ui = user_info or {}
    name   = (ui.get("name")   or "").strip().lower()
    dob    = (ui.get("dob")    or "").strip()
    mobile = (ui.get("mobile") or "").strip()
    seen   = set()

    dt = None
    if dob:
        for fmt in ("%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%Y-%m-%d","%d%m%Y","%d%m%y","%Y%m%d","%d/%m/%y"):
            try: dt = datetime.strptime(dob.strip(), fmt); break
            except: pass

    if dt:
        d = f"{dt.day:02d}"; m = f"{dt.month:02d}"
        y = str(dt.year); y2 = y[-2:]

        # UIDAI Aadhaar PDF common passwords
        aadhaar_pats = [
            f"{d}{m}{y}",          # Most common: DDMMYYYY
            f"{d}{m}{y2}",         # DDMMYY
            f"{y}{m}{d}",          # YYYYMMDD
            f"{d}/{m}/{y}",        # DD/MM/YYYY
            f"{d}-{m}-{y}",        # DD-MM-YYYY
            f"{d}.{m}.{y}",        # DD.MM.YYYY
            f"{y}",                # YYYY only
            f"{d}{m}",             # DDMM
        ]
        month_names = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
        try:
            mn = month_names[dt.month - 1]
            aadhaar_pats += [
                f"{d}{mn}{y}",f"{d}{mn.upper()}{y}",
                f"{d}{mn.capitalize()}{y}",
            ]
        except: pass

        if name:
            for pat in [f"{d}{m}{y}",f"{d}{m}{y2}",f"{y}"]:
                aadhaar_pats += [
                    f"{name}{pat}",f"{name.capitalize()}{pat}",
                    f"{name}@{pat}",f"{name.capitalize()}@{pat}",
                    f"{pat}{name}",f"{pat}{name.capitalize()}",
                ]
        for p in aadhaar_pats:
            if _ok(p) and p not in seen:
                seen.add(p); yield p

    # Mobile-based Aadhaar
    if mobile:
        m_clean = re.sub(r'[\s\-\+\(\)]','',mobile)
        for v in [m_clean[-4:], m_clean[-6:], m_clean[-8:], m_clean[-10:]]:
            if _ok(v) and v not in seen:
                seen.add(v); yield v

    # PIN code patterns (Aadhaar PDF sometimes uses PIN as password)
    pin_prefixes = ["110","400","560","600","700","500","411","226","380","302",
                    "440","141","160","800","682","695","641","625","530","534",
                    "342","324","201","122","121","110","462","452","492","484"]
    for px in pin_prefixes:
        for suffix in range(0, 1000, 100):
            pin = f"{px}{suffix:03d}"
            if _ok(pin) and pin not in seen:
                seen.add(pin); yield pin

# ─── Emoji Passwords (actually used in gen_top_common) ───────────────────────
EMOJI_PASSWORDS = [
    "❤️123","🔥786","💯100","🙏786","😊123","👑786","🌟123","💪786",
    "🎯123","🚀786","💎123","👍786","🌈123","🦁786","⚡123","🎉786",
    "❤️786","🔥123","💯786","🙏123","😊786","🎊123","🌙786","🌺123",
    "🏆786","🎈123","🌸786","💫123","🎵786","🦋123","🌻786","🎀123",
]

# ─── Generator: Top Common with mutations ────────────────────────────────────
def gen_top_common():
    seen = set()
    for pw in TOP_COMMON:
        for v in [pw, pw.upper(), pw.capitalize(), pw.lower()]:
            if _ok(v) and v not in seen:
                seen.add(v); yield v
        for s in ["1","12","123","@","!","786","@123","@2024","@2025","",
                  "2024","2025","#123","!@#","_123","_786","@007","@420"]:
            pw2 = pw + s
            if _ok(pw2) and pw2 not in seen:
                seen.add(pw2); yield pw2
    # Emoji passwords — ACTUALLY USED (v36 fix)
    for epw in EMOJI_PASSWORDS:
        if _ok(epw) and epw not in seen:
            seen.add(epw); yield epw
        for s in ["","786","123","@123","2024","2025"]:
            combo = epw + s
            if _ok(combo) and combo not in seen:
                seen.add(combo); yield combo

def gen_google_common():
    words = (TOP_COMMON[:80] + INDIAN_NAMES[:100] + HINDI[:80] + CITIES[:40])
    seen = set()
    for pw in google_style(words):
        if _ok(pw) and pw not in seen:
            seen.add(pw); yield pw

def gen_smart(info):
    name   = (info.get("name")   or "").strip()
    dob    = (info.get("dob")    or "").strip()
    mobile = (info.get("mobile") or "").strip()
    city   = (info.get("city")   or "").strip()
    nick   = (info.get("nick")   or "").strip()
    pet    = (info.get("pet")    or "").strip()
    fav    = (info.get("fav")    or "").strip()
    lucky  = (info.get("lucky")  or "").strip()
    other  = (info.get("other")  or "").strip()

    dt_obj = None
    if dob:
        for fmt in ("%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%Y-%m-%d","%d%m%Y","%d%m%y","%Y%m%d","%d/%m/%y"):
            try: dt_obj = datetime.strptime(dob.strip(), fmt); break
            except: pass

    date_strs = []
    if dt_obj:
        for fmt in DATE_FMTS:
            try:
                ds = dt_obj.strftime(fmt)
                if ds not in date_strs: date_strs.append(ds)
            except: pass

    tokens = [t for t in [name, nick, pet, fav, city, other] if t]
    lucky_nums = [lucky] if lucky else []
    lucky_nums += ["786","007","420","108","2024","2025","1947","999","123","1234","12345"]
    if dt_obj:
        lucky_nums += [
            str(dt_obj.year),
            f"{dt_obj.day:02d}{dt_obj.month:02d}",
            f"{dt_obj.month:02d}{dt_obj.day:02d}",
            str(dt_obj.year)[-2:],
            f"{dt_obj.day:02d}{dt_obj.month:02d}{str(dt_obj.year)[-2:]}",
        ]

    for pw in google_style(tokens): yield pw

    # v32: Bank and Aadhaar patterns first (high priority)
    for pw in gen_bank_patterns(info): yield pw
    for pw in gen_aadhaar_patterns(info): yield pw

    for tok in tokens:
        for v in rules(tok):
            for s in SUFS:
                for p in PRES:
                    pw = p + v + s
                    if _ok(pw): yield pw

    for tok in tokens:
        for num in lucky_nums:
            for pw in interleave(tok.lower(), num): yield pw
            for pw in interleave(tok.capitalize(), num): yield pw

    for tok in tokens:
        for ds in date_strs:
            for sep in ["","_","-",".","@","#","/"]:
                for v in [tok.lower(), tok.capitalize(), tok.upper()]:
                    for combo in [v+sep+ds, ds+sep+v, v+ds, ds+v]:
                        if _ok(combo): yield combo

    if dt_obj and tokens:
        for tok in tokens:
            for v in [tok.lower(), tok.capitalize()]:
                dob_pats = [
                    f"{dt_obj.day:02d}{dt_obj.month:02d}",
                    f"{dt_obj.day:02d}{dt_obj.month:02d}{dt_obj.year}",
                    f"{dt_obj.day:02d}{dt_obj.month:02d}{str(dt_obj.year)[-2:]}",
                    f"{dt_obj.year}{dt_obj.month:02d}{dt_obj.day:02d}",
                    f"{dt_obj.month:02d}{dt_obj.year}",
                    str(dt_obj.year),
                ]
                for dp in dob_pats:
                    for sep in ["","@","_","-","#","."]:
                        for combo in [v+sep+dp, dp+sep+v]:
                            if _ok(combo): yield combo

    if mobile:
        m = re.sub(r'[\s\-\+\(\)]','',mobile)
        for v in [mobile, m, m[-10:], m[-8:], m[-6:], m[-4:], "0"+m[-10:], "91"+m[-10:]]:
            if v and _ok(v): yield v
            for s in SUFS[:30]:
                pw = v + s
                if _ok(pw): yield pw
        for tok in tokens:
            for v in [tok.lower(), tok.capitalize()]:
                for vm in [m[-10:], m[-8:], m[-6:], m[-4:]]:
                    for combo in [v+vm, vm+v, v+"_"+vm, v+"@"+vm]:
                        if _ok(combo): yield combo

    if lucky:
        for tok in tokens:
            for v in rules(tok):
                for sep in ["","@","#","_","."]:
                    for combo in [v+sep+lucky, lucky+sep+v]:
                        if _ok(combo): yield combo

    for ds in date_strs:
        for s in SUFS[:30]:
            for p in PRES[:12]:
                pw = p + ds + s
                if _ok(pw): yield pw

    if len(tokens) >= 2:
        for r in range(2, min(len(tokens)+1, 5)):
            for perm in itertools.permutations(tokens[:6], r):
                for sep in ["","_","-","@","."]:
                    for combo in [sep.join(p.lower() for p in perm),
                                  sep.join(p.capitalize() for p in perm)]:
                        if _ok(combo): yield combo
        for t1 in tokens:
            for t2 in tokens:
                if t1 == t2: continue
                for num in lucky_nums[:10]:
                    for combo in [t1.lower()+num+t2.lower(),
                                  t1.capitalize()+num+t2.capitalize(),
                                  t1.lower()+t2.lower()+num]:
                        if _ok(combo): yield combo

def gen_calendar(start=1940, end=2025, prefixes=None, suffixes=None, fmts=None, seps=None):
    prefixes = prefixes or [""]
    suffixes = suffixes or [""]
    seps     = seps or ["","_","-",".","@","#","/"]
    fmts     = fmts or DATE_FMTS
    for year in range(start, end + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try: dt = datetime(year, month, day)
                except: continue
                dstrs = []
                for fmt in fmts:
                    try:
                        ds = dt.strftime(fmt)
                        if ds not in dstrs: dstrs.append(ds)
                    except: pass
                for ds in dstrs:
                    for pre in prefixes:
                        for suf in suffixes:
                            for sep in seps:
                                if pre and suf: combos = [pre+sep+ds+sep+suf, pre+ds+suf]
                                elif pre:       combos = [pre+sep+ds, pre+ds]
                                elif suf:       combos = [ds+sep+suf, ds+suf]
                                else:           combos = [ds]
                                for pw in combos:
                                    for v in [pw, pw.upper(), pw.capitalize()]:
                                        if _ok(v): yield v

def gen_keyboard():
    WALKS = [
        "qwerty","qwerty123","qwerty@123","Qwerty123","QWERTY","QWERTY123",
        "asdf","asdf123","asdf@123","Asdf123","asdfghjkl","1qaz","1qaz2wsx",
        "!qaz2wsx","1Qaz2Wsx","!QAZ2wsx","zxcvbn","qazwsx","qazwsx123",
        "1q2w3e","1q2w3e4r","1Q2W3E4R","q1w2e3","q1w2e3r4","Q1W2E3R4",
        "abcd1234","1234abcd","abc@123","ABC123","qweasdzxc","qweasd",
        "12qwaszx","zxcasqw12","poiuytrewq","mnbvcxz",
        "123qwe","321ewq","zaq1","xsw2","cde3","vfr4","bgt5","nhy6","mju7",
    ]
    rows = ["qwertyuiop","asdfghjkl","zxcvbnm","1234567890","QWERTYUIOP",
            "q1w2e3r4","1q2w3e4r","a1s2d3f4","z1x2c3v4","123456789","987654321",
            "246810","135790","159753","963741","147258369","369258147"]
    seen = set()
    for walk in WALKS:
        for suf in ["","1","123","@123","!","@","786","@786","@2024","@2025","2024"]:
            pw = walk + suf
            if _ok(pw) and pw not in seen: seen.add(pw); yield pw
    for row in rows:
        for start in range(len(row)):
            for ln in range(2, min(len(row)+1, 16)):
                seg = row[start:start+ln]
                if len(seg) < ln: break
                rev = seg[::-1]
                for base in [seg, rev]:
                    for suf in ["","1","12","123","1234","!","@","@123","786","007"]:
                        for pre in ["","1","123","786","@"]:
                            pw = pre + base + suf
                            if _ok(pw) and pw not in seen: seen.add(pw); yield pw

def gen_dict_streaming(paths):
    """v32: Stream GitHub lists + generate ALL mutations per password."""
    import urllib.request
    for p in (paths or []):
        p = str(p).strip()
        if not p: continue
        if p.startswith("http://") or p.startswith("https://"):
            log.info("Streaming: " + p)
            try:
                req = urllib.request.Request(p, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    for raw in resp:
                        try:
                            pw = raw.decode("utf-8","ignore").strip()
                            if not _ok(pw): continue
                            # Base password
                            yield pw
                            wl = pw.lower(); wc = pw.capitalize(); wu = pw.upper()
                            if wl != pw: yield wl
                            if wc != pw: yield wc
                            # Mutations with common suffixes
                            for s in ["1","123","786","@123","@786","2024","2025","!","@","#","_123","_786"]:
                                yield pw + s
                                yield wl + s
                                yield wc + s
                            # Leet mutations
                            for lv in leet(pw):
                                yield lv
                                yield lv + "123"
                                yield lv + "786"
                        except: pass
            except Exception as e:
                log.warning("URL fail: " + str(e))
            continue
        fp = Path(p)
        if not fp.exists(): continue
        try:
            with open(fp,"r",errors="ignore",encoding="utf-8") as f:
                for line in f:
                    pw = line.strip()
                    if _ok(pw): yield pw
        except: pass

def gen_indian_wordlist():
    all_words = HINDI + INDIAN_NAMES[:200] + SURNAMES[:120] + CITIES[:100]
    seen = set()
    for word in all_words:
        for v in rules(word):
            for s in SUFS:
                for p in PRES:
                    pw = p + v + s
                    if _ok(pw) and pw not in seen:
                        seen.add(pw); yield pw

def gen_india_patterns():
    """Indian PIN codes, vehicle numbers."""
    pin_prefixes = ["110","400","560","600","700","500","411","226","380","302",
                    "440","141","160","800","682","695","641","625","530","534"]
    seen = set()
    for px in pin_prefixes:
        for suffix in range(0, 1000, 50):
            pin = f"{px}{suffix:03d}"
            if _ok(pin) and pin not in seen:
                seen.add(pin); yield pin
            for s in ["","@","786","123","@123","@786"]:
                pw = pin + s
                if _ok(pw) and pw not in seen:
                    seen.add(pw); yield pw
    states = ["MP","UP","DL","MH","GJ","RJ","HR","PB","KA","TN"]
    for st in states:
        for num in ["01","02","03","04","05"]:
            for letters in ["AA","AB","AC","BA","BB"]:
                for digits in ["1234","5678","4321","7890","1111"]:
                    pw = f"{st}{num}{letters}{digits}"
                    if _ok(pw) and pw not in seen:
                        seen.add(pw); yield pw

def gen_mobile(numbers=None, country_codes=None, extras=None, density=100):
    if numbers:
        for num in numbers:
            num = re.sub(r'[\s\-\+\(\)]','',num)
            if not num.isdigit() or len(num) < 4: continue
            for v in [num, num[-10:], num[-8:], num[-6:], num[-4:], "0"+num[-10:], "91"+num[-10:]]:
                if v and _ok(v): yield v
                for s in SUFS[:25]:
                    pw = v + s
                    if _ok(pw): yield pw
    codes = country_codes or ["+91"]
    exps  = extras or []
    for cc in codes:
        info = MOBILE_CC.get(cc)
        if not info: continue
        pfx_list = info["px"] + exps
        tlen = info["tlen"]
        for pfx in pfx_list:
            tail_len = tlen - len(pfx)
            if tail_len < 0: continue
            total = 10 ** tail_len
            step = max(1, int(total*(100-min(density,100))/10000)) if density < 100 else 1
            for n in range(0, total, step):
                tail = str(n).zfill(tail_len)
                full = pfx + tail
                for v in [full, "0"+full, cc.lstrip("+")+full]:
                    if v and _ok(v): yield v

def gen_brute(charset=None, min_len=1, max_len=8, prefix="", suffix=""):
    """100T+ brute force — optimized with itertools.product."""
    if not charset: charset = string.ascii_lowercase + string.digits
    chars = list(dict.fromkeys(charset))
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(chars, repeat=length):
            yield prefix + "".join(combo) + suffix

def gen_master(cfg):
    mode = cfg.get("mode","smart")
    ui   = cfg.get("user_info",{})
    gens = []

    # Priority order: highest success rate first
    gens.append(gen_top_common())
    gens.append(gen_google_common())

    # Bank/Aadhaar patterns — high priority always when user info given
    if any(v for v in ui.values() if v):
        gens.append(gen_bank_patterns(ui))
        gens.append(gen_aadhaar_patterns(ui))

    # ── Bank mode: inject account/CIF fields into user_info ──────────────────
    if mode in ("bank","hybrid"):
        bank_cfg = cfg.get("bank",{})
        acc6     = (bank_cfg.get("account_last6") or "").strip()
        cif_id   = (bank_cfg.get("cif_id") or "").strip()
        # Merge into ui for gen_bank_patterns
        ui_bank  = dict(ui)
        if acc6:   ui_bank["account"] = acc6
        if cif_id: ui_bank["cif"]     = cif_id
        gens.append(gen_bank_patterns(ui_bank))
        # Generate account-number based passwords directly
        if acc6:
            def _acc_gen(a6):
                for suf in ["","@","!","#","123","786","2024","2025","@123","@786"]:
                    for pre in ["","@","#"]:
                        yield pre+a6+suf
                        yield pre+a6[:4]+suf
            gens.append(_acc_gen(acc6))
        if cif_id:
            def _cif_gen(c):
                for suf in ["","@","!","123","786"]:
                    yield c+suf
                    yield c[:6]+suf if len(c)>6 else c+suf
            gens.append(_cif_gen(cif_id))

    # ── Aadhaar mode: inject aadhaar fields ───────────────────────────────────
    if mode in ("aadhaar","hybrid"):
        aa_cfg = cfg.get("aadhaar",{})
        last4  = (aa_cfg.get("last4") or "").strip()
        pin    = (aa_cfg.get("pin") or "").strip()
        ui_aa  = dict(ui)
        gens.append(gen_aadhaar_patterns(ui_aa))
        if last4:
            def _aa_gen(l4, p):
                for suf in ["","@","!","123","786","2024"]:
                    yield l4+suf
                if p: yield p; yield p+"@"; yield p+"#"
            gens.append(_aa_gen(last4, pin))

    if mode in ("smart","hybrid","bank","aadhaar") and any(v for v in ui.values() if v):
        gens.append(gen_smart(ui))

    if mode in ("calendar","hybrid"):
        cal  = cfg.get("calendar",{})
        pres = list(cal.get("prefix_words") or [])
        sufs = list(cal.get("suffix_words") or [])
        if ui.get("name"):  pres.append(ui["name"])
        if ui.get("nick"):  pres.append(ui["nick"])
        if ui.get("lucky"): sufs.append(ui["lucky"])
        gens.append(gen_calendar(
            start   = int(cal.get("start_year",1940)),
            end     = int(cal.get("end_year",2025)),
            prefixes= pres or [""],
            suffixes= sufs or [""],
            fmts    = cal.get("date_formats") or None,
            seps    = cal.get("separators") or ["","_","-",".","@","/"],
        ))

    if mode in ("keyboard","hybrid"):
        gens.append(gen_keyboard())

    DATA_DIR  = Path(os.environ.get("DATA_DIR","/tmp/zipcracker"))
    DICTS_DIR = DATA_DIR / "dictionaries"
    DICTS_DIR.mkdir(parents=True, exist_ok=True)
    wlists = [str(f) for f in DICTS_DIR.glob("*.txt")] + cfg.get("extra_wordlists",[])
    for key in cfg.get("github_lists",[]):
        url = GITHUB_LISTS.get(key)
        if url: wlists.append(url)
    if wlists:
        gens.append(gen_dict_streaming(wlists))

    gens.append(gen_indian_wordlist())
    gens.append(gen_india_patterns())

    if mode in ("mobile","hybrid"):
        mob = cfg.get("mobile",{})
        gens.append(gen_mobile(
            numbers       = mob.get("numbers",[]),
            country_codes = mob.get("country_codes",["+91"]),
            extras        = mob.get("extra_prefixes",[]),
            density       = int(mob.get("density",100)),
        ))

    if mode in ("brute","hybrid"):
        bf = cfg.get("brute",{})
        cs = ""
        for key in (bf.get("charsets") or ["lower","digits"]): cs += CS.get(key,key)
        cs += (bf.get("custom_chars") or "")
        cs = "".join(dict.fromkeys(cs)) if cs else (string.ascii_lowercase + string.digits)
        gens.append(gen_brute(
            charset = cs,
            min_len = int(bf.get("min_len",1)),
            max_len = int(bf.get("max_len",8)),
            prefix  = bf.get("prefix") or "",
            suffix  = bf.get("suffix") or "",
        ))

    seen  = set()
    count = 0
    CAP   = 15_000_000  # v32: 15M dedup (was 10M)
    for gen in gens:
        for pw in gen:
            if not _ok(pw): continue
            if count < CAP:
                if pw in seen: continue
                seen.add(pw)
            count += 1
            yield pw


# ─── v32 ULTRA CRACKER — 10k-100k/s ─────────────────────────────────────────
class Cracker:

    @staticmethod
    def crack_zip_fast(fpath, pw_gen, progress_cb=None, freq=1000):
        res = {"found":False,"password":None,"attempts":0,"elapsed":0.0,
               "speed":0,"cancelled":False,"error":None,"use_aes":False}
        if not Path(fpath).exists():
            res["error"] = "File not found"; return res

        names = []; use_aes = False
        try:
            if HAS_AES:
                try:
                    with pyzipper.AESZipFile(fpath) as z:
                        names = z.namelist()
                        if names:
                            info = z.infolist()[0]
                            use_aes = (info.flag_bits & 0x1) != 0 or info.compress_type == 99
                except: pass
            if not names:
                with zipfile.ZipFile(fpath) as z: names = z.namelist()
        except Exception as e:
            res["error"] = str(e); return res

        if not names: res["error"] = "Empty ZIP"; return res
        res["use_aes"] = use_aes
        target = names[0]; t0 = time.time()

        # AES: single threaded (PBKDF2 hardware limit — can't parallelize)
        if use_aes:
            n = 0; found = None; last = 0
            try:
                ZF = pyzipper.AESZipFile if HAS_AES else zipfile.ZipFile
                with ZF(fpath) as zf:
                    for pw in pw_gen:
                        n += 1
                        if n - last >= freq:
                            el = time.time()-t0; sp = int(n/max(el,0.001)); last = n
                            if progress_cb and not progress_cb(n,sp,pw):
                                res["cancelled"]=True; break
                        try:
                            zf.setpassword(pw.encode("utf-8","ignore"))
                            zf.read(target); found=pw; break
                        except: pass
            except Exception as e: res["error"]=str(e)
            el = time.time()-t0
            res.update(attempts=n,elapsed=round(el,2),speed=int(n/max(el,0.001)))
            if found: res["found"]=True; res["password"]=found
            log.info(f"AES {'CRACKED: '+found if found else 'not found'} n={n:,}")
            return res

        # ── v32: Standard ZIP — ULTRA PARALLEL ────────────────────────────────
        # v34 ULTRA SPEED: BATCH=8000, N_WORKERS=32 → max throughput
        BATCH = 8000
        N_WORKERS = 32
        stop_evt = threading.Event()
        found_pw = [None]
        total_n  = [0]
        lock     = threading.Lock()

        def try_batch(batch):
            """Each worker: open own ZipFile, try all passwords in batch."""
            if stop_evt.is_set(): return None
            try:
                zf = zipfile.ZipFile(fpath)
                for pw in batch:
                    if stop_evt.is_set(): break
                    try:
                        zf.setpassword(pw.encode("utf-8","ignore"))
                        zf.read(target)
                        zf.close()
                        return pw
                    except: pass
                zf.close()
            except: pass
            return None

        batch = []; futures = {}; t_last = time.time(); current = [""]

        try:
            with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
                for pw in pw_gen:
                    if stop_evt.is_set(): break
                    batch.append(pw); current[0] = pw

                    if len(batch) >= BATCH:
                        future = ex.submit(try_batch, batch[:])
                        with lock:
                            futures[future] = len(batch)
                            total_n[0] += len(batch)
                        batch = []

                        # Check completed futures
                        done = [f for f in list(futures.keys()) if f.done()]
                        for f in done:
                            try:
                                result = f.result()
                                if result: found_pw[0] = result; stop_evt.set()
                            except: pass
                            with lock: futures.pop(f, None)

                        if stop_evt.is_set(): break

                        # Progress update every ~1 second
                        now = time.time()
                        if now - t_last >= 1.0:
                            with lock: n = total_n[0]
                            el = now - t0
                            sp = int(n / max(el, 0.001))
                            t_last = now
                            if progress_cb and not progress_cb(n, sp, current[0]):
                                stop_evt.set(); break

                # Final batch
                if batch and not stop_evt.is_set():
                    future = ex.submit(try_batch, batch)
                    with lock:
                        futures[future] = len(batch)
                        total_n[0] += len(batch)

                # Wait for all futures
                for f in list(futures.keys()):
                    try:
                        result = f.result(timeout=30)
                        if result and not found_pw[0]:
                            found_pw[0] = result; stop_evt.set()
                    except: pass

        except Exception as e: res["error"] = str(e)

        el = time.time()-t0; n = total_n[0]
        res.update(attempts=n, elapsed=round(el,2), speed=int(n/max(el,0.001)))
        if found_pw[0]:
            res["found"] = True; res["password"] = found_pw[0]
            log.info(f"ZIP CRACKED! '{found_pw[0]}' speed={res['speed']:,}/s attempts={n:,}")
        if stop_evt.is_set() and not found_pw[0]:
            res["cancelled"] = True
        return res

    @staticmethod
    def crack_pdf(fpath, pw_gen, progress_cb=None, freq=200):
        """
        v32: PDF cracking with parallel batch (pikepdf multi-open).
        pikepdf is thread-safe for reading, so we can parallelize!
        """
        res = {"found":False,"password":None,"attempts":0,"elapsed":0.0,
               "speed":0,"cancelled":False,"error":None}
        if not Path(fpath).exists():
            res["error"] = "File not found"; return res
        if not HAS_PIKE and not HAS_PDF:
            res["error"] = "pip install pikepdf or pypdf"; return res

        t0 = time.time(); last = 0; found = None; n = 0

        if HAS_PIKE:
            # v32: pikepdf parallel batch PDF cracking
            BATCH = 800; N_WORKERS = 16
            stop_evt = threading.Event()
            found_pw = [None]; total_n = [0]; lock = threading.Lock()
            current = [""]

            def try_pdf_batch(batch):
                if stop_evt.is_set(): return None
                for pw in batch:
                    if stop_evt.is_set(): break
                    try:
                        with pikepdf.open(fpath, password=pw):
                            return pw
                    except pikepdf.PasswordError: pass
                    except: pass
                return None

            batch = []; futures = {}; t_last = time.time()
            try:
                with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
                    for pw in pw_gen:
                        if stop_evt.is_set(): break
                        batch.append(pw); current[0] = pw

                        if len(batch) >= BATCH:
                            future = ex.submit(try_pdf_batch, batch[:])
                            with lock:
                                futures[future] = len(batch)
                                total_n[0] += len(batch)
                            batch = []

                            done = [f for f in list(futures.keys()) if f.done()]
                            for f in done:
                                try:
                                    result = f.result()
                                    if result: found_pw[0] = result; stop_evt.set()
                                except: pass
                                with lock: futures.pop(f, None)

                            if stop_evt.is_set(): break

                            now = time.time()
                            if now - t_last >= 1.0:
                                with lock: n = total_n[0]
                                el = now - t0
                                sp = int(n / max(el, 0.001))
                                t_last = now
                                if progress_cb and not progress_cb(n, sp, current[0]):
                                    stop_evt.set(); break

                    if batch and not stop_evt.is_set():
                        future = ex.submit(try_pdf_batch, batch)
                        with lock: futures[future]=len(batch); total_n[0]+=len(batch)

                    for f in list(futures.keys()):
                        try:
                            result = f.result(timeout=30)
                            if result and not found_pw[0]:
                                found_pw[0] = result; stop_evt.set()
                        except: pass
            except Exception as e: res["error"] = str(e)

            el = time.time()-t0; n = total_n[0]
            res.update(attempts=n,elapsed=round(el,2),speed=int(n/max(el,0.001)))
            if found_pw[0]:
                res["found"]=True; res["password"]=found_pw[0]
                log.info(f"PDF CRACKED (parallel)! '{found_pw[0]}' speed={res['speed']:,}/s")
            if stop_evt.is_set() and not found_pw[0]:
                res["cancelled"]=True
            return res

        # Fallback: pypdf single thread
        try:
            for pw in pw_gen:
                n += 1
                if n - last >= freq:
                    el = time.time()-t0; sp = int(n/max(el,0.001)); last = n
                    if progress_cb and not progress_cb(n,sp,pw):
                        res["cancelled"]=True; break
                try:
                    r = _PDF(fpath)
                    if r.is_encrypted and r.decrypt(pw) != 0:
                        found = pw; break
                except: pass
        except Exception as e: res["error"]=str(e)
        el = time.time()-t0
        res.update(attempts=n,elapsed=round(el,2),speed=int(n/max(el,0.001)))
        if found: res["found"]=True; res["password"]=found
        return res

    @staticmethod
    def crack(fpath, pw_gen, progress_cb=None, freq=1000):
        ext = Path(fpath).suffix.lower()
        if ext == ".pdf":
            return Cracker.crack_pdf(fpath, pw_gen, progress_cb, freq)
        return Cracker.crack_zip_fast(fpath, pw_gen, progress_cb, freq)

    @staticmethod
    def extract_and_zip(fpath, password, out_zip):
        res = {"ok":False,"zip_path":None,"files":[],"error":None}
        tmp = tempfile.mkdtemp()
        try:
            pw_b = password.encode("utf-8","ignore")
            if HAS_AES:
                try:
                    with pyzipper.AESZipFile(fpath) as z:
                        z.setpassword(pw_b); z.extractall(tmp); res["files"]=z.namelist()
                except:
                    with zipfile.ZipFile(fpath) as z:
                        z.setpassword(pw_b); z.extractall(tmp); res["files"]=z.namelist()
            else:
                with zipfile.ZipFile(fpath) as z:
                    z.setpassword(pw_b); z.extractall(tmp); res["files"]=z.namelist()
            shutil.make_archive(out_zip.replace(".zip",""),"zip",tmp)
            res["ok"]=True; res["zip_path"]=out_zip
        except Exception as e: res["error"]=str(e)
        finally: shutil.rmtree(tmp, ignore_errors=True)
        return res

    @staticmethod
    def save_unlocked_pdf(fpath, password, out_path):
        """Save PDF without password protection — new v33 feature."""
        res = {"ok": False, "out_path": None, "error": None}
        if not HAS_PIKE:
            res["error"] = "pikepdf not available"; return res
        try:
            with pikepdf.open(fpath, password=password) as pdf:
                pdf.save(out_path)
            res["ok"] = True; res["out_path"] = out_path
        except Exception as e:
            res["error"] = str(e)
        return res
