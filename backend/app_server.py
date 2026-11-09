"""Optional local development server. Set GOOGLE_CLIENT_ID to enable Google sign-in.
For public deployment use HTTPS, persistent secret and reverse proxy.
"""
import base64, hashlib, hmac, json, os, secrets, sqlite3, time, urllib.parse, urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from http.cookies import SimpleCookie

ROOT=Path(__file__).resolve().parent.parent
DB=Path(os.getenv('RISHU_DB',str(Path(__file__).resolve().parent/'users.sqlite3')))
CLIENT_ID=os.getenv('GOOGLE_CLIENT_ID','')
KEYS=('history','rishuDisplayName','rishuAvatarData','rishuTimetableV3','lecturePlanPeriodsV2','qualificationPlansV2','lectureCandidates','licensePlans','licenseCompleted')

def connect():
 db=sqlite3.connect(DB,timeout=15)
 db.execute('PRAGMA journal_mode=WAL')
 db.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY,email TEXT UNIQUE,passhash TEXT,google_sub TEXT UNIQUE,created INTEGER)')
 db.execute('CREATE TABLE IF NOT EXISTS sessions (tokenhash TEXT PRIMARY KEY,user_id TEXT,expires INTEGER)')
 db.execute('CREATE TABLE IF NOT EXISTS state (user_id TEXT PRIMARY KEY,payload TEXT,updated INTEGER)')
 db.commit();return db

def hashpw(password,salt=None):
 salt=salt or secrets.token_bytes(16)
 return base64.b64encode(salt).decode()+':'+base64.b64encode(hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260000)).decode()

def verify(password,stored):
 try:
  salt,digest=stored.split(':');return hmac.compare_digest(hashpw(password,base64.b64decode(salt)),stored)
 except (ValueError,TypeError):return False

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def send_json(self,status,obj,cookie=None):
  body=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(body)
 def payload(self):
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size<1 or size>3_000_000:raise ValueError()
   data=json.loads(self.rfile.read(size));assert isinstance(data,dict);return data
  except (ValueError,AssertionError,TypeError):return None
 def token(self):
  c=SimpleCookie()
  try:c.load(self.headers.get('Cookie',''))
  except Exception:return None
  return c['rishu_session'].value if 'rishu_session' in c else None
 def current(self,db):
  token=self.token()
  if not token:return None
  row=db.execute('SELECT user_id FROM sessions WHERE tokenhash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
  return row[0] if row else None
 def login(self,db,uid):
  token=secrets.token_urlsafe(40);db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),uid,int(time.time())+30*86400));db.commit()
  self.send_json(200,{'ok':True},'rishu_session='+token+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=2592000'+('; Secure' if self.headers.get('X-Forwarded-Proto')=='https' else ''))
 def do_GET(self):
  if self.path.startswith('/api/'):
   with connect() as db:
    uid=self.current(db)
    if self.path=='/api/config':return self.send_json(200,{'googleClientId':CLIENT_ID})
    if self.path=='/api/me':return self.send_json(200,{'authenticated':bool(uid)})
    if self.path=='/api/state':
     if not uid:return self.send_json(401,{'error':'ログインしてください'})
     row=db.execute('SELECT payload FROM state WHERE user_id=?',(uid,)).fetchone();return self.send_json(200,{'state':json.loads(row[0]) if row else {}})
   return self.send_json(404,{'error':'not found'})
  return super().do_GET()
 def do_POST(self):
  if not self.path.startswith('/api/'):return self.send_json(404,{'error':'not found'})
  data=self.payload()
  if data is None:return self.send_json(400,{'error':'不正なデータです'})
  with connect() as db:
   uid=self.current(db)
   if self.path=='/api/register':
    email=str(data.get('email','')).strip().lower();password=str(data.get('password',''))
    if '@' not in email or len(email)>254 or len(password)<10 or len(password)>200:return self.send_json(400,{'error':'メール形式と10文字以上のパスワードを確認してください'})
    try:
     uid=secrets.token_hex(16);db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,email,hashpw(password),None,int(time.time())));db.commit()
    except sqlite3.IntegrityError:return self.send_json(409,{'error':'登録済みのメールアドレスです'})
    return self.login(db,uid)
   if self.path=='/api/login':
    row=db.execute('SELECT id,passhash FROM users WHERE email=?',(str(data.get('email','')).strip().lower(),)).fetchone()
    if not row or not row[1] or not verify(str(data.get('password','')),row[1]):return self.send_json(401,{'error':'メールアドレスまたはパスワードが違います'})
    return self.login(db,row[0])
   if self.path=='/api/google':
    if not CLIENT_ID:return self.send_json(503,{'error':'Google認証の設定が必要です'})
    token=str(data.get('credential',''))
    if not token or len(token)>10000:return self.send_json(400,{'error':'credential required'})
    try:
     url='https://oauth2.googleapis.com/tokeninfo?'+urllib.parse.urlencode({'id_token':token})
     with urllib.request.urlopen(url,timeout=8) as response:claims=json.load(response)
     if claims.get('aud')!=CLIENT_ID or claims.get('iss') not in ('accounts.google.com','https://accounts.google.com') or int(claims.get('exp',0))<=time.time() or claims.get('email_verified') not in ('true',True):raise ValueError()
     sub=claims['sub'];email=claims.get('email','').lower()
    except Exception:return self.send_json(401,{'error':'Google認証を検証できませんでした'})
    row=db.execute('SELECT id FROM users WHERE google_sub=?',(sub,)).fetchone()
    if row:uid=row[0]
    else:
     # Never silently merge an email account with a Google identity.
     if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():return self.send_json(409,{'error':'同じメールアドレスのアカウントがあります。メールでログインして連携してください'})
     uid=secrets.token_hex(16);db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,email,None,sub,int(time.time())));db.commit()
    return self.login(db,uid)
   if self.path=='/api/link-google':
    if not uid:return self.send_json(401,{'error':'ログインしてください'})
    if not CLIENT_ID:return self.send_json(503,{'error':'Google認証の設定が必要です'})
    try:
     url='https://oauth2.googleapis.com/tokeninfo?'+urllib.parse.urlencode({'id_token':str(data.get('credential',''))})
     with urllib.request.urlopen(url,timeout=8) as response:claims=json.load(response)
     if claims.get('aud')!=CLIENT_ID or claims.get('iss') not in ('accounts.google.com','https://accounts.google.com') or int(claims.get('exp',0))<=time.time():raise ValueError()
     db.execute('UPDATE users SET google_sub=? WHERE id=?',(claims['sub'],uid));db.commit()
    except (Exception,sqlite3.IntegrityError):return self.send_json(400,{'error':'連携できませんでした'})
    return self.send_json(200,{'ok':True})
   if self.path=='/api/logout':
    token=self.token()
    if token:db.execute('DELETE FROM sessions WHERE tokenhash=?',(hashlib.sha256(token.encode()).hexdigest(),));db.commit()
    return self.send_json(200,{'ok':True},'rishu_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
   if self.path=='/api/state':
    if not uid:return self.send_json(401,{'error':'ログインしてください'})
    state=data.get('state')
    if not isinstance(state,dict) or any(k not in KEYS for k in state):return self.send_json(400,{'error':'invalid state'})
    db.execute('INSERT INTO state VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated',(uid,json.dumps(state,ensure_ascii=False),int(time.time())));db.commit();return self.send_json(200,{'ok':True})
  return self.send_json(404,{'error':'not found'})

if __name__=='__main__':
 connect().close();port=int(os.getenv('PORT','8000'));print(f'http://127.0.0.1:{port}/index.html');ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
