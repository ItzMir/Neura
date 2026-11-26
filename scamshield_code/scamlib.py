"""ScamShield BD - normalizer, synthetic data generator, corruptions.
All synthetic data is written by us (templates), no test text used.  Seeds are explicit."""
import random, re, unicodedata
import numpy as np

# ----------------------------------------------------------------- normalizer
_ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad\u200e\u200f"), None)
_LOOK = {  # Cyrillic / Greek lookalikes -> Latin
 'а':'a','е':'e','о':'o','р':'p','с':'c','у':'y','х':'x','і':'i','ј':'j','ѕ':'s','ԁ':'d','һ':'h','ո':'n','ɡ':'g',
 'А':'A','В':'B','Е':'E','К':'K','М':'M','Н':'H','О':'O','Р':'P','С':'C','Т':'T','Х':'X','І':'I',
 'ο':'o','ν':'v','α':'a','ρ':'p','τ':'t','ι':'i','κ':'k'}
_BN_DIG = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_LEET = str.maketrans({'0':'o','1':'i','3':'e','4':'a','5':'s','@':'a','$':'s'})
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")
def normalize(t, leet=False):
    t = unicodedata.normalize('NFKC', str(t)).translate(_ZW)
    t = ''.join(_LOOK.get(c, c) for c in t)
    t = _EMOJI.sub(' ', t).translate(_BN_DIG)
    t = re.sub(r'\[\.\]', '.', t).replace('hxxp', 'http')
    t = re.sub(r'(.)\1{2,}', r'\1\1', t)           # cap repeats
    t = t.lower()
    t = re.sub(r'\|\|\|', ' ||| ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def squash(t):  # space-free view (defeats irregular spacing)
    return re.sub(r'[\s\W_]+', '', t, flags=re.U)

# ----------------------------------------------------------------- corruption
_INV = {v: k for k, v in _LOOK.items() if v.islower()}
def corrupt(t, rnd, strength=None):
    s = strength if strength is not None else rnd.choice([0.03, 0.06, 0.1, 0.16])
    out = []
    for ch in t:
        r = rnd.random()
        if ch.isalpha() and r < s * 0.5 and ch.lower() in _INV: out.append(_INV[ch.lower()])
        elif r < s * 0.6: out.append(ch); out.append(ch)               # repeat
        elif r < s * 0.7 and ch.isalpha(): continue                    # delete
        elif r < s * 0.8: out.append(ch + '\u200b')                    # zero width
        elif r < s * 0.9 and ch == ' ': continue                       # drop space
        elif r < s and ch.isalpha(): out.append(ch.upper() if ch.islower() else ch.lower())
        else: out.append(ch)
    t = ''.join(out)
    if rnd.random() < 0.3:
        w = t.split(' '); i = rnd.randrange(len(w))
        w.insert(i, ''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rnd.randint(5, 10))))
        t = ' '.join(w)
    if rnd.random() < 0.25: t = t.translate(str.maketrans({'a': '@', 'o': '0', 'i': '1', 'e': '3'})) if rnd.random() < .3 else t
    if rnd.random() < 0.25: t = rnd.choice(['📲 ', '🎁 ', '🔥 ', '⚠️ ', '💰 ', '']) + t + rnd.choice(['', ' 🔥', ' ✅', ' 🙏'])
    if rnd.random() < 0.15:  # irregular spacing
        t = re.sub(r'(?<=\w)(?=\w)', lambda m: ' ' if rnd.random() < 0.04 else '', t)
    return t

def noise_record(rnd):
    parts = []
    for _ in range(rnd.randint(1, 5)):
        k = rnd.random()
        if k < .6: parts.append(''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rnd.randint(4, 14))))
        elif k < .8: parts.append(''.join(rnd.choice('!@#$%^&*()_+=~?') for _ in range(rnd.randint(2, 8))))
        else: parts.append(''.join(rnd.choice('😀🔥🎁💰📲✅') for _ in range(rnd.randint(1, 4))))
    return ' '.join(parts)

# ----------------------------------------------------------------- pools
MFS = ['bKash', 'Nagad', 'Rocket', 'Upay', 'bKash Helpline', 'Nagad Support', 'mCash', 'Tap']
BANK = ['DBBL', 'City Bank', 'BRAC Bank', 'Islami Bank', 'EBL', 'Sonali Bank', 'Prime Bank', 'UCB']
TEL = ['Grameenphone', 'GP', 'Robi', 'Banglalink', 'Airtel', 'Teletalk', 'Skitto']
COUR = ['Pathao Courier', 'Steadfast', 'RedX', 'Sundarban Courier', 'SA Paribahan', 'Paperfly', 'eCourier', 'DHL', 'Bangladesh Post', 'Customs']
SHOP = ['Daraz', 'Foodpanda', 'Pathao', 'Chaldal', 'Evaly', 'Rokomari', 'Shajgoj', 'Startech', 'Ajkerdeal', 'Pickaboo']
GOV = ['BTRC', 'NBR', 'BRTA', 'Election Commission', 'Bangladesh Bank', 'DESCO', 'Titas Gas', 'WASA']
ALLORG = MFS + BANK + TEL + COUR + SHOP + GOV
TLD = ['top', 'xyz', 'click', 'online', 'site', 'icu', 'live', 'cc', 'info', 'vip']
def link(rnd, org=None):
    w = (org or rnd.choice(['bd', 'claim', 'win', 'secure', 'bonus', 'pay'])).lower().replace(' ', '')
    return f"hxxps://{w}-{rnd.choice(['fee','confirm','gift','verify','update','spin','login','track'])}[.]{rnd.choice(TLD)}" \
           f"{rnd.choice(['', '/a', '/claim', '/x1', '/app.apk'])}"
def amt(rnd, lo=50, hi=50000):
    v = rnd.choice([rnd.randint(min(lo, 900), 1000) // 10 * 10, rnd.randint(1, 50) * 1000, rnd.randint(1, 9) * 100, rnd.randint(1, 5) * 100000])
    return v
def money(rnd, v, lang):
    s = f"{v:,}"
    if lang == 'bn': return s.translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")) + rnd.choice([" টাকা", "৳"])
    return rnd.choice([f"Tk {s}", f"{s} taka", f"BDT {s}", f"Tk{s}", f"{s} tk"]) if lang == 'bl' else rnd.choice([f"Tk {s}", f"BDT {s}", f"{s} taka"])
def code(rnd, n=6): return ''.join(rnd.choice('0123456789') for _ in range(n))
def pick(rnd, d, lang): return rnd.choice(d[lang])

# ----------------------------------------------------------------- building blocks (en / bl=Banglish / bn=Bangla)
URG = {
 'en': ['Act within 1 hour.', 'Offer expires today!', 'Your account will be blocked in 24 hours.', 'Do it now or lose access.', 'Last chance!', 'Urgent!', 'Otherwise your SIM will be deactivated.'],
 'bl': ['1 ghontar moddhe korun.', 'Offer ajkei shesh!', 'Na korle 24 ghontar moddhe account band hobe.', 'Ekhoni korun na hole SIM off hoye jabe.', 'Jaldi korun!', 'Joruri!'],
 'bn': ['১ ঘণ্টার মধ্যে করুন।', 'অফার আজই শেষ!', 'না করলে ২৪ ঘণ্টার মধ্যে অ্যাকাউন্ট বন্ধ হয়ে যাবে।', 'এখনই করুন, নইলে সিম বন্ধ হয়ে যাবে।', 'জরুরি!']}
CRED_HOOK = {
 'en': ['Unusual login detected on your account.', 'KYC update is required.', 'Your account has been restricted.', 'Verification pending for your wallet.', 'Security alert on your account.', 'Your refund is on hold.', 'Support ticket #{n} needs confirmation.', 'Your SIM registration is incomplete.'],
 'bl': ['Apnar account e unusual login detect hoyeche.', 'KYC update korte hobe.', 'Apnar account restrict kora hoyeche.', 'Wallet verification baki ase.', 'Security alert: apnar account risk e ase.', 'Apnar refund atke ase.', 'SIM registration complete hoy nai.'],
 'bn': ['আপনার অ্যাকাউন্টে অস্বাভাবিক লগইন শনাক্ত হয়েছে।', 'কেওয়াইসি আপডেট করতে হবে।', 'আপনার অ্যাকাউন্ট সীমাবদ্ধ করা হয়েছে।', 'আপনার ওয়ালেট ভেরিফিকেশন বাকি আছে।', 'সিম রেজিস্ট্রেশন অসম্পূর্ণ।']}
CRED_ASK = {  # (text, tech add, action)
 'en': ['Send the 6 digit code you received.', 'Reply with your PIN to verify.', 'Share your OTP to continue.', 'Send NID front and back photo.', 'Send card number, expiry and CVV.', 'Dial *167# and enter your PIN.', 'Tell me the code we just sent.', 'Provide your password and OTP.'],
 'bl': ['Apnar phone e ashа 6 digit code ta pathan.', 'Verify korte apnar PIN ta bolen.', 'Chalu rakhte OTP ta share korun.', 'NID er front back photo pathan.', 'Card number, expiry ar CVV pathan.', '*167# dial kore PIN din.', 'Ei matro pathano code ta bolen.', 'Password ar OTP dien.'],
 'bn': ['আপনার ফোনে আসা ৬ ডিজিটের কোডটি পাঠান।', 'ভেরিফাই করতে আপনার পিন বলুন।', 'চালিয়ে যেতে ওটিপি শেয়ার করুন।', 'এনআইডির ছবি পাঠান।', 'কার্ড নম্বর ও সিভিভি পাঠান।']}
MISTAKE = {
 'en': ['Hello, I am a {o} agent. I sent {a} to your number by mistake. Please return it.', 'Sorry brother, wrong transfer of {a} to your number. Send it back to {p}.', 'I accidentally sent you {a}. Kindly refund to {p}, I will lose my job.'],
 'bl': ['Ami {o} agent. Vul e apnar number e {a} chole gese. Ferot din.', 'Bhai ekta bhul hoye geche, {a} vul number e pathaisi. Please {p} number e ferot den.', 'Vul kore {a} apnake pathiye felechi, ferot na dile amar chakri jabe.'],
 'bn': ['আমি {o} এজেন্ট। ভুল করে আপনার নম্বরে {a} চলে গেছে। ফেরত দিন।', 'ভাই একটা ভুল হয়ে গেছে, {a} আপনার নাম্বারে চলে গেছে। {p} নম্বরে ফেরত দিন।']}
PRIZE_HOOK = {
 'en': ['You won {a} cashback in our lucky draw!', 'Congratulations! You have won a free {d}.', 'You are selected for a {d} gift from {o}!', 'Your number won {a} in the Eid mega draw.', 'Free {g}GB data gift for you from {o}!', 'Claim your loyalty reward of {a} today.'],
 'bl': ['Apni lucky draw te {a} cashback jitechen!', 'Congratulations! Apni free {d} jitechen.', '{o} theke apnake {d} gift deya hocche!', 'Apnar number Eid mega draw te {a} jitese.', '{o} theke apnake {g}GB data gift!', 'Apnar {a} loyalty reward claim korun.'],
 'bn': ['অভিনন্দন! আপনি লাকি ড্রতে {a} ক্যাশব্যাক জিতেছেন।', 'আপনি একটি ফ্রি {d} জিতেছেন!', '{o} থেকে আপনার জন্য {g}GB ডাটা গিফট!', 'ঈদ মেগা ড্রতে আপনার নম্বর {a} জিতেছে।']}
PRIZE_ITEM = ['iPhone 15', 'smartphone', 'motorbike', 'laptop', 'gold coin', 'TV', 'Samsung phone']
PRIZE_CLAIM = {  # (text, tech, action)
 'link': {'en': ['Click to claim: {l}', 'Tap {l} now to claim.', 'Visit {l} to receive your prize.'], 'bl': ['Claim korte click korun: {l}', '{l} e giye prize nin.', 'Link e click korun {l}'], 'bn': ['পেতে লিংকে ক্লিক করুন {l}', 'প্রাইজ নিতে {l} এ যান।']},
 'fee': {'en': ['Pay {f} processing fee to claim.', 'Just pay {f} delivery charge to get it.', 'Send {f} via bKash 01XXXXXXXXX to release the prize.'], 'bl': ['Claim korte {f} processing fee din.', 'Matro {f} delivery charge dilei pabena.', '{f} bKash 01XXXXXXXXX e pathan, prize release hobe.'], 'bn': ['পেতে {f} প্রসেসিং ফি দিন।', 'শুধু {f} ডেলিভারি চার্জ দিন।']},
 'app': {'en': ['Download the spin app: {l}', 'Install our reward app {l} to claim.'], 'bl': ['Spin app download korun: {l}', 'Reward app install korun {l}'], 'bn': ['অ্যাপ ডাউনলোড করুন {l}']},
 'otp': {'en': ['Share your OTP to claim.', 'Send your PIN to confirm the prize.'], 'bl': ['Claim korte apnar OTP ta share korun.', 'Prize confirm korte PIN din.'], 'bn': ['পেতে আপনার ওটিপি শেয়ার করুন।']}}
PARCEL_HOOK = {
 'en': ['Your parcel {t} is held at the hub.', 'Parcel {t} could not be delivered.', 'Package {t} from China is held at customs.', 'You have an unclaimed parcel {t}.', 'Delivery attempt failed for {t}.'],
 'bl': ['Apnar parcel {t} hub e atke ase.', 'Parcel {t} deliver kora jayni.', 'China theke asha package {t} customs e atkano.', 'Apnar ekta parcel {t} unclaimed ase.', 'Delivery failed hoyeche {t}.'],
 'bn': ['আপনার পার্সেল {t} হাবে আটকে আছে।', 'পার্সেল {t} ডেলিভারি করা যায়নি।', 'চীন থেকে আসা প্যাকেজ {t} কাস্টমসে আটকে আছে।']}
PARCEL_ASK = {
 'fee': {'en': ['Pay {f} fee to release: {l}', 'Pay {f} customs duty via bKash to release it.', 'Pay {f} redelivery charge.'], 'bl': ['Delivery fee {f} dite link e jan: {l}', '{f} duty bKash e din, release hobe.', '{f} redelivery charge din.'], 'bn': ['ডেলিভারি চার্জ {f} পরিশোধ করতে লিংকে ক্লিক করুন {l}', '{f} শুল্ক বিকাশে দিন।']},
 'link': {'en': ['Confirm your address: {l}', 'Update address within 24h {l}', 'Track here: {l}'], 'bl': ['Address confirm korun: {l}', '{l} e address update korun.', 'Tracking link: {l}'], 'bn': ['ঠিকানা নিশ্চিত করুন {l}', 'ট্র্যাক করুন {l}']}}
JOB_HOOK = {
 'en': ['Work from home and earn {a} daily.', 'Part-time job: like videos, earn {a} per task.', 'Double your money in 7 days. Invest {a}, get {b}.', 'Crypto trading signals: guaranteed 30% weekly profit.', 'Hiring! Data entry, salary {a} per month, no experience needed.', 'Complete 5 simple tasks and earn {a}.', 'Join our forex investment plan, daily profit guaranteed.'],
 'bl': ['Ghor bose din e {a} income korun.', 'Part-time job: video like kore task e {a} income.', '7 din e taka double. {a} invest korun, {b} nin.', 'Crypto trading e guaranteed weekly 30% profit.', 'Lok nibo! Data entry, mashe {a} salary, experience lagbe na.', '5 ta simple task kore {a} income korun.', 'Forex investment plan e join korun, protidin profit guaranteed.'],
 'bn': ['ঘরে বসে প্রতিদিন {a} আয় করুন।', 'পার্ট-টাইম জব: ভিডিও লাইক দিয়ে প্রতি টাস্কে {a} আয়।', '৭ দিনে টাকা ডাবল। {a} বিনিয়োগ করুন, {b} নিন।', 'ক্রিপ্টো ট্রেডিংয়ে সাপ্তাহিক ৩০% লাভ নিশ্চিত।']}
JOB_ASK = {  # kind: (tech, action)
 'join': {'en': ['Join WhatsApp group now: {l}', 'Join our Telegram channel: {l}'], 'bl': ['WhatsApp e join korun {l}', 'Telegram channel e join korun: {l}'], 'bn': ['আজই হোয়াটসঅ্যাপে যোগ দিন।', 'টেলিগ্রামে জয়েন করুন {l}']},
 'fee': {'en': ['Deposit {f} as security first.', 'Pay {f} registration fee to start.', 'Send {f} via bKash 01XXXXXXXXX to activate.'], 'bl': ['Aage {f} security deposit dite hobe.', 'Shuru korte {f} registration fee din.', '{f} bKash 01XXXXXXXXX e pathan.'], 'bn': ['আগে {f} নিরাপত্তা জমা দিন।', 'শুরু করতে {f} রেজিস্ট্রেশন ফি দিন।']},
 'app': {'en': ['Install our task app: {l}'], 'bl': ['Task app install korun {l}'], 'bn': ['টাস্ক অ্যাপ ইনস্টল করুন {l}']},
 'contact': {'en': ['Message us on WhatsApp 01XXXXXXXXX.', 'Reply YES to start.'], 'bl': ['WhatsApp e message din 01XXXXXXXXX.', 'Shuru korte YES reply korun.'], 'bn': ['হোয়াটসঅ্যাপে মেসেজ দিন 01XXXXXXXXX']}}
PROMO = {
 'en': ['{o}: Eid offer! Flat 30% discount on all items.', 'Get 10% cashback on your next top-up with code EID10.', '{o} 11.11 sale starts tonight 12 AM. Vouchers up to {a}.', 'Install our app and get {a} off your first order. Code: WELCOME50', 'Learn English in 30 days! Admission going on. Call now.', '{o}: Special offer! 10GB for {a}, 7 days. Dial *123*199#', 'New collection arrived! Buy 1 get 1 free this weekend.', 'Hair fall problem? Our herbal oil is very popular. 40% discount today only.', 'Open a savings account at {o} and get a free gift.', 'Mega sale at {o}! Up to 50% off. Visit our store.'],
 'bl': ['{o}: Eid offer! Sob item e 30% discount.', 'Prothom top-up e 10% cashback, code EID10.', '{o} 11.11 sale ajk raat 12 tay. {a} porjonto voucher.', 'App install korun, prothom order e {a} off. Code: WELCOME50', 'Matro 30 dine English shikhun! Admission cholche. Ekhoni call korun.', '{o}: Special offer! 7 din e 10GB {a}. Dial *123*199#', 'Notun collection eshese! Weekend e 1 kinle 1 free.', 'Chul poRa? Amader herbal oil khub popular. Ajkei 40% discount.', '{o} showroom e giye 50% porjonto discount nin.'],
 'bn': ['ঈদ অফার! সব আইটেমে ৩০% ছাড়।', '{o}: বিশেষ অফার! ৭ দিনের জন্য ১০ জিবি {a}। ডায়াল *১২৩*১৯৯#', 'নতুন কালেকশন এসেছে! এই সপ্তাহে ১টি কিনলে ১টি ফ্রি।', '৩০ দিনে ইংরেজি শিখুন! ভর্তি চলছে। এখনই কল করুন।']}
# --- legitimate
def legit_single(rnd, lang):
    o = rnd.choice(MFS + BANK + TEL + SHOP); v = amt(rnd); m = money(rnd, v, lang); c = code(rnd)
    en = ['{o} OTP: {c}. Do not share it with anyone. Valid for 3 minutes.', 'Your OTP is {c} for Tk {v} payment to {s}. Never share this OTP with anyone.', 'Your {o} cash-out of {m} is successful. Balance {m2}. TrxID {t}.', 'Your {s} order #{n} is out for delivery today.', 'Reminder: Your {o} bill of {m} is due on {d} Dec. Pay via the {o} app.', '{o}: BDT {v} debited from A/C XXXX{n4} at {s}. Avl bal BDT {v2}.', 'Your {s} refund of {m} has been credited to your {o} account.', 'Your parcel {t} arrived at the {s} hub. Collect it from the branch with this SMS and your ID.', 'Thank you for your recharge of {m}. Balance {m2}.', 'Payment of {m} was successful. Receipt no. {t}.', 'Your appointment is confirmed for {d} Dec at 10 AM. Reply STOP to unsubscribe.', 'Dear customer, {o} will never ask for your PIN or OTP. Stay safe.', 'Your {s} order #{n} has been shipped and will arrive by {d} Dec. Track in the app.', 'Interview scheduled for {d} Dec 11 AM at our Gulshan office. No fee is required. - HR, {s}']
    bl = ['{o} OTP: {c}. Eta kauke bolben na. Meyad 3 minute.', 'Apnar {o} cash-out {m} successful. Balance {m2}. TrxID {t}.', 'Apnar {s} order #{n} ajk deliver hobe.', 'Dhonyobad! Apnar {m} recharge successful. Balance {m2}.', 'Reminder: {o} bill {m}, {d} Dec er moddhe pay korun {o} app e.', '{o}: Apnar {s} refund {m} account e jomा hoyeche.', 'Apnar payment {m} successful. Receipt {t}.', '{o} kokhono apnar PIN ba OTP chaibe na. Sotorko thakun.']
    bn = ['আপনার ৫০০ টাকা ক্যাশ আউট সফল হয়েছে। বর্তমান ব্যালেন্স {m2}।', 'আপনার {s} অর্ডার আজ ডেলিভারি হবে।', '{o} ওটিপি: {c}। কাউকে বলবেন না। মেয়াদ ৩ মিনিট।', 'আপনার বিল {m} পরিশোধের শেষ তারিখ {d} ডিসেম্বর।', 'আপনার রিচার্জ {m} সফল হয়েছে।']
    t = rnd.choice({'en': en, 'bl': bl + en[:3], 'bn': bn}[lang])
    return t.format(o=o, s=rnd.choice(SHOP + COUR), v=f"{v:,}", v2=f"{amt(rnd):,}", m=m, m2=money(rnd, amt(rnd), lang), c=c, t=rnd.choice(['9K4L2M1X', 'TG55120', 'SC77124', 'DZ88123']) + code(rnd, 2), n=code(rnd, 4), n4=code(rnd, 4), d=rnd.randint(1, 30))

LEGIT_CONV = [
 ['A: bhai, {a} taka ferot dibi kobe?', 'B: sunday dibo, bkash e pathaya dibo', 'A: ok thik ase'],
 ['R: I forgot my bKash PIN. How can I reset it?', 'S: Dial *247# and choose Reset PIN. Never share your PIN with anyone, including our staff.', 'R: Thank you'],
 ['R: Is my order here?', 'S: Rider called, will deliver at 5', "R: ok I'll pay cash on delivery"],
 ['A: eta dekh, ekta scam msg ashche: "apnar PIN din na hole account band". ', 'B: eta scam, kauke PIN dis na', 'A: ha ami ignore korsi'],
 ['[You] Mom, got a message saying I won a prize and must click a link', '[Sender] Dont click it beta, it is a scam. Delete it.', '[You] ok deleting'],
 ['A: ajke meeting kokhon?', 'B: 4 tay, office e', 'A: thik ache dekha hobe'],
 ['S: Your {s} order #{n} is delayed by a day, sorry.', 'R: ok no problem', 'S: Thank you for your patience.'],
 ['R: Apnader support number ta ki?', 'S: Amader helpline 16247, shokal 9 ta theke raat 9 ta.', 'R: dhonyobad'],
 ['A: bkash e {a} pathalam, paisos?', 'B: ha paisi, thanks bhai', 'A: welcome'],
 ['A: Did you get the OTP from the bank for the exam fee?', 'B: yes it came, I entered it myself on the official site', 'A: good'],
]
CHATTER = {'en': ['Hi', 'Hello, how are you?', 'Assalamu alaikum', 'Hi, I got your number from a friend', 'Sorry to disturb you'], 'bl': ['Assalamu alaikum', 'Bhai ekta help lagbe', 'Apu, ekta kotha chilo', 'Hi, kemon achen?', 'Ke bolchen?'], 'bn': ['আসসালামু আলাইকুম', 'ভাই একটা সাহায্য লাগবে', 'কেমন আছেন?']}
VIC = {'en': ['what is this?', 'ok', 'who are you?', 'how much?', 'really?', 'I am busy now', 'send details'], 'bl': ['ki?', 'ok', 'ke apni?', 'koto taka?', 'sotti?', 'ami ekhon busy', 'details den'], 'bn': ['কি?', 'ঠিক আছে', 'আপনি কে?', 'কত টাকা?', 'ব্যস্ত আছি']}
STYLES = [('S: ', 'R: '), ('A: ', 'B: '), ('[Sender] ', '[You] '), ('Caller: ', 'You: '), ('', ''), ('[Group] Rahim: ', '[Group] Karim: ')]

# ----------------------------------------------------------------- scam message composer
def f(t, rnd, lang, **kw):
    d = dict(a=money(rnd, amt(rnd, 500), lang), b=money(rnd, amt(rnd, 2000), lang), f=money(rnd, rnd.choice([45, 50, 100, 300, 500, 1850, 2000]), lang),
             l=link(rnd), o=rnd.choice(MFS + TEL), t=rnd.choice(['SP2271', 'CN8821', 'SC77124', 'DZ12']) + code(rnd, 2), n=code(rnd, 4), p='01XXXXXXXXX',
             d=rnd.choice(PRIZE_ITEM), g=rnd.choice([5, 10, 20]))
    d.update(kw); return t.format(**d)

def scam_msg(rnd, cls, lang):
    """returns (msg_text, techniques set, action). cls in 1..4"""
    org = rnd.random() < .8; urg = rnd.random() < .45; T = set(); A = None
    def prefix(orgs):
        if not org: return '', None
        o = rnd.choice(orgs); T.add('T1')
        return rnd.choice([f'{o}: ', f'{o} Helpline: ', f'Dear {o} user, ', f'[{o}] ']), o
    parts = []
    if cls == 1:
        if rnd.random() < .3:  # mistaken transfer
            o = rnd.choice(MFS); parts.append(f(pick(rnd, MISTAKE, lang), rnd, lang, o=o))
            if rnd.random() < .5: T.add('T1')
            T |= {'T3', 'T5'}; A = 2
            if rnd.random() < .35: parts.append(rnd.choice({'en': ['Also tell your PIN to verify.'], 'bl': ['Verify korte PIN ta bolen.'], 'bn': ['ভেরিফাই করতে পিন বলুন।']}[lang])); T.add('T2'); A = 1
        else:
            p, o = prefix(MFS + BANK + TEL + GOV); parts.append(p + f(pick(rnd, CRED_HOOK, lang), rnd, lang))
            parts.append(f(pick(rnd, CRED_ASK, lang), rnd, lang)); T.add('T2'); A = 1
            if urg or rnd.random() < .3: parts.append(pick(rnd, URG, lang)); T.add('T5')
    elif cls == 2:
        p, o = prefix(MFS + TEL + SHOP + BANK)
        kind = rnd.choices(['link', 'fee', 'app', 'otp'], [.4, .3, .15, .15])[0]
        parts.append(p + f(pick(rnd, PRIZE_HOOK, lang), rnd, lang, o=o or rnd.choice(MFS + TEL))); T.add('T4')
        parts.append(f(pick(rnd, PRIZE_CLAIM[kind], lang), rnd, lang))
        A = {'link': 3, 'fee': 2, 'app': 4, 'otp': 1}[kind]
        if kind == 'fee': T.add('T3')
        if kind == 'otp': T.add('T2')
        if urg: parts.append(pick(rnd, URG, lang)); T.add('T5')
        if kind == 'otp': pass
    elif cls == 4:
        p, o = prefix(COUR); T.add('T1'); p = p or f'{rnd.choice(COUR)}: '
        kind = rnd.choices(['fee', 'link'], [.5, .5])[0]
        parts.append(p + f(pick(rnd, PARCEL_HOOK, lang), rnd, lang)); parts.append(f(pick(rnd, PARCEL_ASK[kind], lang), rnd, lang))
        A = 2 if kind == 'fee' else 3
        if kind == 'fee': T.add('T3')
        if urg: parts.append(pick(rnd, URG, lang)); T.add('T5')
    else:
        p, o = prefix(['Bdjobs', 'HR Dept', 'Daraz', 'Binance Agent', 'Amazon HR', 'Robi Jobs']); parts.append(p + f(pick(rnd, JOB_HOOK, lang), rnd, lang)); T.add('T6')
        kind = rnd.choices(['join', 'fee', 'app', 'contact'], [.4, .3, .15, .15])[0]
        parts.append(f(pick(rnd, JOB_ASK[kind], lang), rnd, lang))
        A = {'join': 4, 'fee': 2, 'app': 4, 'contact': 5}[kind]
        if kind == 'fee': T.add('T3')
        if urg: parts.append(pick(rnd, URG, lang)); T.add('T5')
    return ' '.join(x for x in parts if x), T, A

def tech_str(T): return '|'.join(sorted(T)) if T else 'NONE'

# ----------------------------------------------------------------- one record
def make_record(rnd, cls=None, lang=None, corrupt_p=0.35, conv_p=0.4):
    cls = rnd.choices(range(7), [26, 14, 11, 13, 12, 13, 2])[0] if cls is None else cls   # 6 = noise only
    lang = lang or rnd.choices(['en', 'bl', 'bn'], [.35, .45, .2])[0]
    if cls == 6:
        return noise_record(rnd), 0, 'NONE', 0
    hybrid = rnd.random() < .06 and cls in (1, 2, 3)   # priority hybrids -> class 1
    if cls == 0:
        if rnd.random() < conv_p * 0.7:
            c = rnd.choice(LEGIT_CONV); st = rnd.choice(STYLES)
            msgs = [x.format(a=money(rnd, amt(rnd), 'bl'), s=rnd.choice(SHOP), n=code(rnd, 4)) for x in c]
            text = ' ||| '.join(msgs)
        else:
            text = legit_single(rnd, lang)
            if rnd.random() < .12: text = ' ||| '.join([rnd.choice(['S: ', '']) + text, 'R: ' + pick(rnd, VIC, lang)])
        lab, T, A = 0, set(), 0
    elif cls == 5:
        text = f(pick(rnd, PROMO, lang), rnd, lang); lab, T, A = 5, set(), 0
        if rnd.random() < .3: text += ' ' + rnd.choice([link(rnd).replace('hxxps', 'https').replace('[.]', '.'), 'Call 16xxx', 'Visit www.shop.com.bd'])
    else:
        lab = cls
        if hybrid:
            text, T, A = scam_msg(rnd, 2 if cls != 3 else 3, lang); text += ' ' + f(pick(rnd, PRIZE_CLAIM['otp'], lang), rnd, lang); T |= {'T2'}; lab = 1; A = 1
        else:
            text, T, A = scam_msg(rnd, cls, lang)
        if rnd.random() < conv_p:  # conversation: chatter -> scam -> victim
            st = rnd.choice(STYLES); S, R = st
            msgs = [S + pick(rnd, CHATTER, lang)]
            for _ in range(rnd.choice([0, 1, 2])): msgs += [R + pick(rnd, VIC, lang), S + pick(rnd, CHATTER, lang)]
            sent = re.split(r'(?<=[.!?])\s+', text)
            if len(sent) > 1 and rnd.random() < .6:  # split pitch across turns
                k = rnd.randint(1, len(sent) - 1); msgs += [S + ' '.join(sent[:k]), R + pick(rnd, VIC, lang), S + ' '.join(sent[k:])]
            else: msgs += [S + text]
            if rnd.random() < .5: msgs += [R + pick(rnd, VIC, lang)]
            text = ' ||| '.join(msgs); T.add('T5') if rnd.random() < .5 and lab != 0 else None
    if rnd.random() < corrupt_p: text = corrupt(text, rnd)
    return text, lab, tech_str(T), A

def make_dataset(n, seed):
    rnd = random.Random(seed); rows = [make_record(rnd) for _ in range(n)]
    import pandas as pd
    return pd.DataFrame(rows, columns=['text', 'label', 'techniques', 'action'])
