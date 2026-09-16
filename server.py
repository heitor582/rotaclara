"""RotaClara - servidor local, API JSON e SQLite, sem dependências externas."""
import argparse
import csv
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo
from business import numero, horario, calcularTempoParadoPonto, calcularTempoTotalRoteiro, calcularCustoRoteiro

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('ROTACLARA_DB', ROOT / 'data/rotaclara.db'))
TZ = ZoneInfo('America/Sao_Paulo')
LOGIN_ATTEMPTS = {}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript((ROOT / 'schema.sql').read_text())
        db.execute('INSERT OR IGNORE INTO parametro VALUES (1,6.19,10,0.619,8,1,?)', ('saida_menos_chegada',))
        if not db.execute('SELECT id FROM usuario LIMIT 1').fetchone():
            password = os.environ.get('ROTACLARA_ADMIN_PASSWORD') or secrets.token_urlsafe(12)
            db.execute('INSERT INTO usuario(login,senha_hash,perfil) VALUES (?,?,?)', ('admin',password_hash(password),'administrador'))
            print(f'Primeiro acesso: admin / {password}', flush=True)
    os.chmod(DB_PATH, 0o600)


def seed_demo():
    """Carga explícita e idempotente, exclusivamente fictícia."""
    with connect() as db:
        if db.execute('SELECT id FROM motorista LIMIT 1').fetchone():
            return
        db.execute("INSERT INTO gerente VALUES (1,'Marina Demo','31900000000','marina@example.invalid')")
        for mid, name, vehicle in [(1,'Lucas Demo','Van • DEMO-001'),(2,'Ana Demo','Moto • DEMO-002')]:
            db.execute('INSERT INTO motorista VALUES (?,?,?,?,?,?,?)', (mid,1,name,'31900000000',f'DEMO-{mid}',vehicle,10 if mid==1 else 30))
        credentials = []
        for login, role, mid, gid in [('gerente','gerente',None,1),('motorista','motorista',1,None)]:
            pw = secrets.token_urlsafe(10)
            db.execute('INSERT INTO usuario(login,senha_hash,perfil,motorista_id,gerente_id) VALUES (?,?,?,?,?)', (login,password_hash(pw),role,mid,gid))
            credentials.append(f'{login}: {pw}')
        today = datetime.now(TZ).date()
        addresses = ['Base • Seg. Família','Rua Peru, 55','Rua X, 5','Av. João César']
        for days in range(7):
            for mid in [1,2]:
                day = today - timedelta(days=days)
                distance = 42 + days * 3 + mid * 4
                kmpl = 10 if mid==1 else 30
                rid = db.execute('INSERT INTO roteiro(data,motorista_id,distancia_total,valor_combustivel,km_por_litro,custo_por_km,jornada_padrao_horas,status) VALUES (?,?,?,?,?,?,?,?)', (str(day),mid,distance,6.19,kmpl,6.19/kmpl,8,'planejado' if days==0 else 'concluido')).lastrowid
                clock = datetime.combine(day, datetime.min.time(),TZ).replace(hour=8)
                times = [0,15,10,50] if mid==1 else [0,10,5,26]
                for order, (address, mins) in enumerate(zip(addresses,times),1):
                    arrival = clock
                    departure = clock + timedelta(minutes=mins+days)
                    clock = departure + timedelta(minutes=20)
                    db.execute('INSERT INTO ponto(roteiro_id,endereco,latitude,longitude,data_hora_chegada,data_hora_saida,ordem_sequencial) VALUES (?,?,?,?,?,?,?)', (rid,address,-19.93 + order*.005,-44.05 + order*.005,arrival.astimezone(timezone.utc).isoformat() if days else None,departure.astimezone(timezone.utc).isoformat() if days else None,order))
                recalc(db,rid)
        content = 'Dados fictícios. Senhas locais geradas aleatoriamente.\n' + '\n'.join(credentials) + '\n'
        path = ROOT / 'data/credenciais-demo.txt'
        path.write_text(content)
        path.chmod(0o600)
        print(content, flush=True)


def recalc(db, rid):
    points = [dict(p) for p in db.execute('SELECT * FROM ponto WHERE roteiro_id=? ORDER BY ordem_sequencial',(rid,))]
    for p in points:
        db.execute('UPDATE ponto SET tempo_parado_minutos=? WHERE id=?',(calcularTempoParadoPonto(p),p['id']))
    r = db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone()
    db.execute('UPDATE roteiro SET tempo_total_parado=?,custo_estimado=? WHERE id=?',(calcularTempoTotalRoteiro(points),calcularCustoRoteiro(r['distancia_total'],r['valor_combustivel'],r['km_por_litro']),rid))


def scope(user, alias='r'):
    if user['perfil']=='motorista': return f'{alias}.motorista_id=?', [user['motorista_id']]
    if user['perfil']=='gerente': return f'{alias}.motorista_id IN (SELECT id FROM motorista WHERE gerente_id=?)', [user['gerente_id']]
    return '1=1', []


def text_field(data, key, limit=200):
    value = str(data.get(key,'')).strip()
    if not value or len(value)>limit: raise ValueError(f'{key}: preenchimento obrigatório (até {limit} caracteres).')
    return value


def date_field(value):
    try: return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError): raise ValueError('Data inválida.')


def report_data(db,user,query):
    today = datetime.now(TZ).date().isoformat()
    start,end = date_field(query.get('inicio',[today])[0]),date_field(query.get('fim',[today])[0])
    if end < start: raise ValueError('Data final deve ser igual ou posterior à inicial.')
    where,args = scope(user)
    selected = query.get('motorista',[''])[0]
    if selected:
        where += ' AND r.motorista_id=?'; args.append(int(selected))
    routes = [dict(r) for r in db.execute(f'SELECT r.*,m.nome motorista FROM roteiro r JOIN motorista m ON m.id=r.motorista_id WHERE {where} AND r.data BETWEEN ? AND ? ORDER BY r.data,r.id',args+[start,end])]
    points = [dict(p) for p in db.execute(f'SELECT p.*,r.data,m.nome motorista,r.motorista_id FROM ponto p JOIN roteiro r ON r.id=p.roteiro_id JOIN motorista m ON m.id=r.motorista_id WHERE {where} AND r.data BETWEEN ? AND ? ORDER BY r.data,p.roteiro_id,p.ordem_sequencial',args+[start,end])]
    search=query.get('busca',[''])[0].casefold().strip()
    if search:
        points=[p for p in points if search in p['endereco'].casefold() or search in p['motorista'].casefold()]
    days={}
    for r in routes:
        d=days.setdefault(r['data'],{'data':r['data'],'minutos':0,'jornada':0})
        d['minutos']+=r['tempo_total_parado']; d['jornada']+=r['jornada_padrao_horas']*60
    total=sum(r['tempo_total_parado'] for r in routes)
    base=sum(r['jornada_padrao_horas']*60 for r in routes)
    return {'inicio':start,'fim':end,'roteiros':routes,'pontos':points,'dias':list(days.values()),'total_minutos':total,'custo':sum(r['custo_estimado'] for r in routes),'percentual':total/base*100 if base else 0,'base_minutos':base,'distancia':sum(r['distancia_total'] for r in routes)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Não registrar query strings, credenciais ou corpos das requisições.
        pass

    def send(self, data, status=200, kind='application/json; charset=utf-8', headers=None):
        payload = json.dumps(data,ensure_ascii=False).encode() if kind.startswith('application/json') else (data.encode() if isinstance(data,str) else data)
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store' if self.path.startswith('/api/') else 'no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://www.plantuml.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(payload)

    def body(self):
        size=int(self.headers.get('Content-Length','0'))
        if size>200000: raise ValueError('Solicitação muito grande.')
        try:
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError()
            return data
        except (json.JSONDecodeError,ValueError): raise ValueError('JSON inválido.')

    def user(self,db):
        c=cookies.SimpleCookie()
        try: c.load(self.headers.get('Cookie',''))
        except cookies.CookieError: return None
        token=c.get('rotaclara')
        if not token: return None
        hashed=hashlib.sha256(token.value.encode()).hexdigest()
        u=db.execute('SELECT u.* FROM sessao s JOIN usuario u ON u.id=s.usuario_id WHERE s.token_hash=? AND s.expira>?',(hashed,time.time())).fetchone()
        return dict(u) if u else None

    def do_GET(self): self.handle_request('GET')
    def do_POST(self): self.handle_request('POST')
    def do_PUT(self): self.handle_request('PUT')

    def handle_request(self,method):
        parsed=urlparse(self.path); path=parsed.path; query=parse_qs(parsed.query,keep_blank_values=True)
        try:
            if not path.startswith('/api/'):
                if method!='GET': return self.send({'erro':'Método não permitido'},405)
                documents = {f'/documentacao/arquivos/{p.name}': p for p in (ROOT/'docs').glob('*.md')}
                documents.update({f'/documentacao/arquivos/{p.name}': p for p in (ROOT/'docs/diagramas').glob('*.puml')})
                documents['/documentacao/arquivos/schema.sql'] = ROOT/'schema.sql'
                documents['/documentacao/arquivos/README.md'] = ROOT/'README.md'
                if path in documents:
                    document = documents[path]
                    return self.send(document.read_bytes(), kind='text/plain; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{document.name}"'})
                allowed={'/documentacao':'documentacao.html','/documentacao/':'documentacao.html','/docs.css':'docs.css','/docs.js':'docs.js','/':'index.html','/app.js':'app.js','/style.css':'style.css','/campanha':'campanha.html','/manifest.webmanifest':'manifest.webmanifest','/icon.svg':'icon.svg','/sw.js':'sw.js'}
                name=allowed.get(path)
                if not name: return self.send({'erro':'Não encontrado'},404)
                mime={'html':'text/html; charset=utf-8','js':'application/javascript; charset=utf-8','css':'text/css; charset=utf-8','svg':'image/svg+xml','webmanifest':'application/manifest+json'}
                return self.send((ROOT/'static'/name).read_bytes(),kind=mime[name.split('.')[-1]])
            if method!='GET':
                origin=self.headers.get('Origin')
                if origin and origin!=f'http://{self.headers.get("Host")}' and origin!=f'https://{self.headers.get("Host")}':
                    return self.send({'erro':'Origem não autorizada'},403)
                if self.headers.get('X-RotaClara')!='1': return self.send({'erro':'Cabeçalho de proteção ausente'},403)
            with connect() as db:
                if path=='/api/login' and method=='POST':
                    data=self.body(); key=self.client_address[0]
                    attempts=[t for t in LOGIN_ATTEMPTS.get(key,[]) if t>time.time()-300]
                    if len(attempts)>=10: return self.send({'erro':'Muitas tentativas. Aguarde cinco minutos.'},429)
                    u=db.execute('SELECT * FROM usuario WHERE login=?',(data.get('login',''),)).fetchone()
                    valid=u and hmac.compare_digest(u['senha_hash'],password_hash(str(data.get('senha','')),u['senha_hash'].split(':')[0]))
                    if not valid:
                        LOGIN_ATTEMPTS[key]=attempts+[time.time()]
                        return self.send({'erro':'Login ou senha incorretos.'},401)
                    LOGIN_ATTEMPTS.pop(key,None)
                    token=secrets.token_urlsafe(32)
                    db.execute('DELETE FROM sessao WHERE expira<?',(time.time(),))
                    db.execute('INSERT INTO sessao VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),u['id'],time.time()+28800))
                    secure='; Secure' if os.environ.get('ROTACLARA_SECURE_COOKIE')=='1' else ''
                    return self.send({'ok':True},headers={'Set-Cookie':f'rotaclara={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}'})
                user=self.user(db)
                if not user: return self.send({'erro':'Entre para continuar.'},401)
                if path=='/api/me': return self.send({k:user[k] for k in ['id','login','perfil','motorista_id','gerente_id']})
                if path=='/api/logout' and method=='POST':
                    c=cookies.SimpleCookie(self.headers.get('Cookie',''))
                    db.execute('DELETE FROM sessao WHERE token_hash=?',(hashlib.sha256(c['rotaclara'].value.encode()).hexdigest(),))
                    return self.send({'ok':True},headers={'Set-Cookie':'rotaclara=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0'})
                if method=='GET': return self.get_api(db,user,path,query)
                return self.write_api(db,user,path,method,self.body())
        except PermissionError as exc: self.send({'erro':str(exc)},403)
        except (ValueError,KeyError,TypeError) as exc: self.send({'erro':str(exc)},400)
        except sqlite3.IntegrityError: self.send({'erro':'Registro duplicado ou vínculo inválido. Confira os dados; só é permitido um roteiro por motorista e data.'},409)
        except Exception as exc:
            print('Erro interno:',type(exc).__name__,flush=True)
            self.send({'erro':'Não foi possível concluir a operação.'},500)

    def require(self,user,*roles):
        if user['perfil'] not in roles: raise PermissionError('Seu perfil não permite esta ação.')

    def route(self,db,user,rid):
        where,args=scope(user)
        row=db.execute(f'SELECT r.* FROM roteiro r WHERE r.id=? AND {where}',[rid]+args).fetchone()
        if not row: raise PermissionError('Roteiro indisponível para este usuário.')
        return dict(row)

    def get_api(self,db,user,path,q):
        if path=='/api/parametros': return self.send(dict(db.execute('SELECT * FROM parametro WHERE id=1').fetchone()))
        if path=='/api/pessoas':
            if user['perfil']=='administrador':
                drivers=[dict(r) for r in db.execute('SELECT * FROM motorista ORDER BY nome')]
                managers=[dict(r) for r in db.execute('SELECT * FROM gerente ORDER BY nome')]
            elif user['perfil']=='gerente':
                drivers=[dict(r) for r in db.execute('SELECT * FROM motorista WHERE gerente_id=? ORDER BY nome',(user['gerente_id'],))]
                managers=[dict(r) for r in db.execute('SELECT * FROM gerente WHERE id=?',(user['gerente_id'],))]
            else:
                drivers=[dict(r) for r in db.execute('SELECT id,nome,veiculo,km_por_litro FROM motorista WHERE id=?',(user['motorista_id'],))]; managers=[]
            return self.send({'motoristas':drivers,'gerentes':managers})
        if path in ['/api/relatorio','/api/exportar.csv']:
            report=report_data(db,user,q)
            if path.endswith('.csv'):
                output=io.StringIO(); output.write('\ufeff'); writer=csv.writer(output,delimiter=';')
                writer.writerow(['Data','Roteiro','Motorista','Ordem','Endereço','Chegada','Saída','Minutos parados'])
                for p in report['pontos']:
                    def safe(v):
                        v=str(v if v is not None else '')
                        return "'"+v if v.lstrip().startswith(('=','+','-','@','\t','\r')) else v
                    writer.writerow([safe(p[k]) for k in ['data','roteiro_id','motorista','ordem_sequencial','endereco','data_hora_chegada','data_hora_saida','tempo_parado_minutos']])
                return self.send(output.getvalue(),kind='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="rotaclara-relatorio.csv"'})
            return self.send(report)
        if path=='/api/auditoria':
            self.require(user,'administrador','gerente')
            where,args=scope(user)
            rows=db.execute(f'SELECT a.*,u.login FROM auditoria a JOIN usuario u ON u.id=a.usuario_id LEFT JOIN ponto p ON p.id=a.ponto_id LEFT JOIN roteiro r ON r.id=p.roteiro_id WHERE {where} ORDER BY a.id DESC LIMIT 500',args)
            return self.send([dict(r) for r in rows])
        return self.send({'erro':'Não encontrado'},404)

    def audit(self,db,user,pid,action,before,after,reason):
        db.execute('INSERT INTO auditoria(usuario_id,instante,ponto_id,acao,antes,depois,motivo) VALUES (?,?,?,?,?,?,?)',(user['id'],now(),pid,action,json.dumps(before,ensure_ascii=False),json.dumps(after,ensure_ascii=False),reason))

    def write_api(self,db,user,path,method,data):
        if path=='/api/parametros' and method=='PUT':
            self.require(user,'administrador','gerente')
            fuel=numero(data.get('valor_combustivel'),'Combustível'); km=numero(data.get('km_por_litro'),'Rendimento',.01)
            hours=numero(data.get('jornada_padrao_horas'),'Jornada',.01,24)
            before=dict(db.execute('SELECT * FROM parametro WHERE id=1').fetchone())
            db.execute('UPDATE parametro SET valor_combustivel=?,km_por_litro=?,custo_por_km=?,jornada_padrao_horas=? WHERE id=1',(fuel,km,fuel/km,hours))
            self.audit(db,user,None,'parametros',before,{'valor_combustivel':fuel,'km_por_litro':km,'jornada_padrao_horas':hours},'Configuração para novos roteiros')
            return self.send({'ok':True})
        if path in ['/api/motoristas','/api/gerentes'] and method=='POST':
            self.require(user,'administrador','gerente')
            is_driver=path.endswith('motoristas')
            if not is_driver: self.require(user,'administrador')
            name=text_field(data,'nome'); phone=text_field(data,'telefone',30)
            login=text_field(data,'login',80); pw=text_field(data,'senha',200)
            if len(pw)<10: raise ValueError('Use uma senha de pelo menos 10 caracteres.')
            if is_driver:
                gid=user['gerente_id'] if user['perfil']=='gerente' else int(data['gerente_id'])
                person=db.execute('INSERT INTO motorista(gerente_id,nome,telefone,documento,veiculo,km_por_litro) VALUES (?,?,?,?,?,?)',(gid,name,phone,text_field(data,'documento',40),text_field(data,'veiculo',100),numero(data.get('km_por_litro'),'Rendimento',.01))).lastrowid
            else:
                email=text_field(data,'email')
                if '@' not in email: raise ValueError('Informe um e-mail válido.')
                person=db.execute('INSERT INTO gerente(nome,telefone,email) VALUES (?,?,?)',(name,phone,email)).lastrowid
            db.execute('INSERT INTO usuario(login,senha_hash,perfil,motorista_id,gerente_id) VALUES (?,?,?,?,?)',(login,password_hash(pw),'motorista' if is_driver else 'gerente',person if is_driver else None,None if is_driver else person))
            return self.send({'id':person},201)
        if path=='/api/roteiros' and method=='POST':
            mid=user['motorista_id'] if user['perfil']=='motorista' else int(data['motorista_id'])
            driver=db.execute('SELECT * FROM motorista WHERE id=?',(mid,)).fetchone()
            if not driver or (user['perfil']=='gerente' and driver['gerente_id']!=user['gerente_id']): raise PermissionError('Motorista fora da sua equipe.')
            day=date_field(data.get('data')); distance=numero(data.get('distancia_total'),'Distância')
            points=data.get('pontos',[])
            if not isinstance(points,list) or not 2<=len(points)<=100: raise ValueError('O roteiro precisa de 2 a 100 pontos ordenados.')
            p=db.execute('SELECT * FROM parametro WHERE id=1').fetchone(); km=driver['km_por_litro']
            rid=db.execute('INSERT INTO roteiro(data,motorista_id,distancia_total,valor_combustivel,km_por_litro,custo_por_km,jornada_padrao_horas) VALUES (?,?,?,?,?,?,?)',(day,mid,distance,p['valor_combustivel'],km,p['valor_combustivel']/km,p['jornada_padrao_horas'])).lastrowid
            for order,point in enumerate(points,1):
                pid=db.execute('INSERT INTO ponto(roteiro_id,endereco,latitude,longitude,ordem_sequencial) VALUES (?,?,?,?,?)',(rid,text_field(point,'endereco'),numero(point.get('latitude'),'Latitude',-90,90),numero(point.get('longitude'),'Longitude',-180,180),order)).lastrowid
                self.audit(db,user,pid,'criacao',{},point,'Montagem do roteiro')
            recalc(db,rid)
            return self.send({'id':rid},201)
        if path.startswith('/api/roteiros/') and path.endswith('/iniciar') and method=='POST':
            rid=int(path.split('/')[3]); r=self.route(db,user,rid)
            if r['status']!='planejado': raise ValueError('Este roteiro já foi iniciado.')
            if r['data']!=datetime.now(TZ).date().isoformat(): raise ValueError('Inicie o roteiro na data planejada.')
            db.execute("UPDATE roteiro SET status='em_andamento' WHERE id=?",(rid,))
            return self.send({'ok':True})
        if path.startswith('/api/pontos/') and method in ['POST','PUT']:
            pid=int(path.split('/')[3]); row=db.execute('SELECT * FROM ponto WHERE id=?',(pid,)).fetchone()
            if not row: raise ValueError('Ponto não encontrado.')
            before=dict(row); r=self.route(db,user,row['roteiro_id']); after=before.copy()
            if method=='POST':
                if r['status']!='em_andamento': raise ValueError('Inicie o roteiro antes de registrar pontos.')
                action=data.get('acao')
                if action not in ['chegada','saida']: raise ValueError('Ação inválida.')
                field='data_hora_'+action
                if after[field]: raise ValueError('Registro já realizado. Use a correção auditada.')
                previous=db.execute('SELECT id FROM ponto WHERE roteiro_id=? AND ordem_sequencial<? AND data_hora_saida IS NULL',(r['id'],row['ordem_sequencial'])).fetchone()
                if previous: raise ValueError('Conclua o ponto anterior antes de continuar.')
                after[field]=now(); reason='Coleta pelo relógio do servidor'
            else:
                self.require(user,'administrador','gerente'); reason=text_field(data,'motivo',500)
                after['endereco']=text_field(data,'endereco')
                after['latitude']=numero(data.get('latitude'),'Latitude',-90,90)
                after['longitude']=numero(data.get('longitude'),'Longitude',-180,180)
                for f in ['data_hora_chegada','data_hora_saida']:
                    dt=horario(data.get(f)); after[f]=dt.isoformat(timespec='seconds') if dt else None
            after['tempo_parado_minutos']=calcularTempoParadoPonto(after)
            arrival=horario(after['data_hora_chegada']); departure=horario(after['data_hora_saida'])
            if arrival and arrival.astimezone(TZ).date().isoformat()!=r['data']: raise ValueError('A chegada deve estar na data do roteiro.')
            if (arrival and arrival>datetime.now(timezone.utc)) or (departure and departure>datetime.now(timezone.utc)): raise ValueError('Não é permitido registrar horários futuros.')
            prev=db.execute('SELECT * FROM ponto WHERE roteiro_id=? AND ordem_sequencial=?',(r['id'],row['ordem_sequencial']-1)).fetchone()
            nxt=db.execute('SELECT * FROM ponto WHERE roteiro_id=? AND ordem_sequencial=?',(r['id'],row['ordem_sequencial']+1)).fetchone()
            if arrival and prev and (not prev['data_hora_saida'] or arrival<horario(prev['data_hora_saida'])): raise ValueError('A chegada deve ocorrer após a saída do ponto anterior.')
            if nxt and nxt['data_hora_chegada'] and (not departure or departure>horario(nxt['data_hora_chegada'])): raise ValueError('A saída deve ocorrer antes da chegada ao próximo ponto.')
            keys=['endereco','latitude','longitude','data_hora_chegada','data_hora_saida','tempo_parado_minutos']
            db.execute('UPDATE ponto SET '+','.join(k+'=?' for k in keys)+' WHERE id=?',[after[k] for k in keys]+[pid])
            self.audit(db,user,pid,'correcao' if method=='PUT' else data['acao'],before,after,reason)
            recalc(db,r['id'])
            pending=db.execute('SELECT id FROM ponto WHERE roteiro_id=? AND data_hora_saida IS NULL',(r['id'],)).fetchone()
            new_status='concluido' if not pending else ('em_andamento' if r['status']!='planejado' or arrival else 'planejado')
            db.execute('UPDATE roteiro SET status=? WHERE id=?',(new_status,r['id']))
            return self.send({'ok':True})
        return self.send({'erro':'Operação não encontrada'},404)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true',help='Cria dados fictícios de demonstração')
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args(); init_db()
    if args.demo: seed_demo()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'RotaClara: http://127.0.0.1:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()


if __name__=='__main__': main()
