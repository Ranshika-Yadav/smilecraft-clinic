import os,json,sqlite3,secrets,re,threading,time,csv,io
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse
from datetime import date,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DB=Path(os.getenv('DB_PATH',str(ROOT/'appointments.db')))
ADMIN=os.getenv('ADMIN_TOKEN','')
PORT=int(os.getenv('PORT','8000'))
lock=threading.Lock(); attempts={}
SERVICES={'General Dentistry','Cosmetic Dentistry','Dental Implants','Orthodontics','Root Canal Care',"Children's Dentistry"}
def conn():
 c=sqlite3.connect(DB,timeout=15);c.row_factory=sqlite3.Row;return c
with conn() as c:
 c.execute('CREATE TABLE IF NOT EXISTS appointments (id TEXT PRIMARY KEY,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT NOT NULL,service TEXT NOT NULL,date TEXT NOT NULL,time TEXT NOT NULL,message TEXT,status TEXT NOT NULL DEFAULT "pending",created_at TEXT NOT NULL)')
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'public'),**kwargs)
 def send_json(self,status,data):
  b=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def authorized(self):return bool(ADMIN) and secrets.compare_digest(self.headers.get('Authorization',''), 'Bearer '+ADMIN)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/health':return self.send_json(200,{'ok':True})
  if path=='/api/appointments':
   if not self.authorized():return self.send_json(401,{'error':'Unauthorized'})
   with conn() as c: rows=[dict(x) for x in c.execute('SELECT * FROM appointments ORDER BY created_at DESC LIMIT 1000')]
   return self.send_json(200,{'appointments':rows})
  if path=='/admin':self.path='/admin.html'
  if path.startswith('/api/') or path.endswith('.db'):return self.send_json(404,{'error':'Not found'})
  return super().do_GET()
 def read_json(self):
  length=int(self.headers.get('Content-Length','0'))
  if length<1 or length>10000:raise ValueError('Invalid request size')
  return json.loads(self.rfile.read(length))
 def do_POST(self):
  if urlparse(self.path).path!='/api/appointments':return self.send_json(404,{'error':'Not found'})
  ip=self.client_address[0];now=time.time()
  with lock:
   attempts[ip]=[x for x in attempts.get(ip,[]) if now-x<3600]
   if len(attempts[ip])>=15:return self.send_json(429,{'error':'Too many requests. Try again later.'})
   attempts[ip].append(now)
  try:
   data=self.read_json()
   if not isinstance(data,dict):raise ValueError('Invalid data')
   name=str(data.get('name','')).strip();phone=str(data.get('phone','')).strip();email=str(data.get('email','')).strip().lower();service=str(data.get('service','')).strip();day=str(data.get('date',''));slot=str(data.get('time',''));message=str(data.get('message','')).strip()
   if not (2<=len(name)<=100) or not re.fullmatch(r'[\w .\-\']+',name,re.UNICODE):raise ValueError('Enter a valid name')
   if not re.fullmatch(r'\+?[0-9 ()-]{7,20}',phone):raise ValueError('Enter a valid phone number')
   if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise ValueError('Enter a valid email')
   if service not in SERVICES:raise ValueError('Select a valid service')
   d=date.fromisoformat(day)
   if not date.today()<=d<=date.today().replace(year=date.today().year+1):raise ValueError('Choose a date within the next year')
   if slot not in {'Morning','Afternoon','Evening'}:raise ValueError('Choose a preferred time')
   if len(message)>1000:raise ValueError('Message is too long')
   rid=secrets.token_hex(8)
   with conn() as c:c.execute('INSERT INTO appointments VALUES (?,?,?,?,?,?,?,?,?,?)',(rid,name,phone,email,service,day,slot,message,'pending',datetime.now().astimezone().isoformat()))
   return self.send_json(201,{'success':True,'reference':rid,'message':'Appointment request received. The clinic must confirm availability.'})
  except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:return self.send_json(400,{'error':str(e)})
 def do_PATCH(self):
  if not self.authorized():return self.send_json(401,{'error':'Unauthorized'})
  m=re.fullmatch(r'/api/appointments/([a-f0-9]{16})',urlparse(self.path).path)
  if not m:return self.send_json(404,{'error':'Not found'})
  try:
   d=self.read_json();status=d.get('status')
   if status not in {'pending','confirmed','completed','cancelled'}:raise ValueError('Invalid status')
   with conn() as c:cur=c.execute('UPDATE appointments SET status=? WHERE id=?',(status,m.group(1)))
   return self.send_json(200,{'success':True}) if cur.rowcount else self.send_json(404,{'error':'Not found'})
  except (ValueError,TypeError,AttributeError,json.JSONDecodeError) as e:return self.send_json(400,{'error':str(e)})
if __name__=='__main__':
 print(f'SmileCraft running at http://localhost:{PORT} (admin: /admin)')
 if not ADMIN:print('WARNING: ADMIN_TOKEN is not set; admin API is disabled.')
 ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
