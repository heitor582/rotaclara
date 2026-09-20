"""Testes do handler real sem abrir sockets; cada caso usa SQLite temporário."""
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from datetime import datetime
from rotaclara.application import Application
from rotaclara.bootstrap import PROJECT_ROOT, initialize_database
from rotaclara.database import Database
from rotaclara.domain import LOCAL_TIMEZONE
from rotaclara.http import create_handler


class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.database=Database(Path(cls.tmp.name)/'test.db')
        initialize_database(cls.database, 'test-admin-password')
        cls.application=Application(cls.database)
        cls.handler_class=create_handler(cls.application, PROJECT_ROOT)
        cls.admin=cls.request('POST','/api/login',{'login':'admin','senha':'test-admin-password'})[2]['Set-Cookie'].split(';')[0]
        cls.request('POST','/api/gerentes',{'nome':'Gestor Um','telefone':'1','email':'g1@example.invalid','login':'g1','senha':'password-g1'},cls.admin)
        cls.request('POST','/api/gerentes',{'nome':'Gestor Dois','telefone':'2','email':'g2@example.invalid','login':'g2','senha':'password-g2'},cls.admin)
        for i in [1,2]:
            cls.request('POST','/api/motoristas',{'nome':f'Motorista {i}','telefone':'0','documento':f'TEST-{i}','veiculo':'Teste','km_por_litro':10,'gerente_id':i,'login':f'm{i}','senha':'password-motorista'},cls.admin)
        cls.driver=cls.request('POST','/api/login',{'login':'m1','senha':'password-motorista'})[2]['Set-Cookie'].split(';')[0]
        cls.manager=cls.request('POST','/api/login',{'login':'g1','senha':'password-g1'})[2]['Set-Cookie'].split(';')[0]

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    @classmethod
    def request(cls,method,path,data=None,cookie='',headers=None):
        h=object.__new__(cls.handler_class);h.path=path;h.client_address=('test-client',1)
        body=json.dumps(data or {}).encode();h.rfile=io.BytesIO(body)
        h.headers={'Content-Length':str(len(body)),'X-RotaClara':'1','Host':'localhost','Cookie':cookie,**(headers or {})}
        result={}
        def send(response): result.update(data=response.data,status=response.status,headers=response.headers)
        h.send_response_data=send;h.handle_request(method)
        return result['status'],result['data'],result['headers']

    def make_route(self,day,mid=1):
        data={'motorista_id':mid,'data':day,'distancia_total':100,'pontos':[{'endereco':a,'latitude':-19,'longitude':-44} for a in ['Base','Rua Teste']]}
        code,result,_=self.request('POST','/api/roteiros',data,self.admin);self.assertEqual(code,201,result);return result['id']

    def test_auth_and_csrf(self):
        self.assertEqual(self.request('GET','/api/relatorio')[0],401)
        self.assertEqual(self.request('POST','/api/logout',{},self.admin,{'Origin':'https://evil.invalid'})[0],403)
        self.assertEqual(self.request('POST','/api/login',{'login':'admin','senha':'wrong'})[0],401)

    def test_driver_denied_settings(self):
        self.assertEqual(self.request('PUT','/api/parametros',{},self.driver)[0],403)
        self.assertEqual(self.request('GET','/api/auditoria',cookie=self.driver)[0],403)

    def test_route_and_scope(self):
        rid=self.make_route('2026-01-01',2)
        for c in [self.driver,self.manager]:
            code,r,_=self.request('GET','/api/relatorio?inicio=2026-01-01&fim=2026-01-01',cookie=c)
            self.assertEqual(code,200);self.assertEqual(r['roteiros'],[])
            self.assertEqual(self.request('POST',f'/api/roteiros/{rid}/iniciar',{},c)[0],403)

    def test_collection_and_audit(self):
        day=datetime.now(LOCAL_TIMEZONE).date().isoformat();rid=self.make_route(day)
        with self.database.transaction(write=True) as db: ids=[p['id'] for p in db.execute('SELECT id FROM ponto WHERE roteiro_id=? ORDER BY ordem_sequencial',(rid,))]
        self.assertEqual(self.request('POST',f'/api/pontos/{ids[0]}',{'acao':'chegada'},self.driver)[0],400)
        self.assertEqual(self.request('POST',f'/api/roteiros/{rid}/iniciar',{},self.driver)[0],200)
        self.assertEqual(self.request('POST',f'/api/pontos/{ids[1]}',{'acao':'chegada'},self.driver)[0],400)
        self.assertEqual(self.request('POST',f'/api/pontos/{ids[0]}',{'acao':'saida'},self.driver)[0],400)
        for pid in ids:
            for action in ['chegada','saida']:
                code,result,_=self.request('POST',f'/api/pontos/{pid}',{'acao':action},self.driver);self.assertEqual(code,200,result)
        with self.database.transaction(write=True) as db:
            r=dict(db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone())
            self.assertEqual(r['status'],'concluido');self.assertEqual(db.execute('SELECT tempo_parado_minutos FROM ponto WHERE id=?',(ids[0],)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM auditoria WHERE ponto_id IN (?,?)',ids).fetchone()[0],6)
            before=dict(db.execute('SELECT * FROM ponto WHERE id=?',(ids[1],)).fetchone())
        code,result,_=self.request('PUT',f'/api/pontos/{ids[1]}',{**before,'endereco':'=SUM(1,2)','motivo':'Correção de teste'},self.manager)
        self.assertEqual(code,200,result)
        csv=self.request('GET',f'/api/exportar.csv?inicio={day}&fim={day}&busca=SUM',cookie=self.manager)[1]
        self.assertIn("'=SUM",csv);self.assertNotIn(';Base;',csv)
        with self.database.transaction(write=True) as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute('DELETE FROM auditoria')

    def test_parameter_snapshot(self):
        rid=self.make_route('2026-02-02')
        with self.database.transaction(write=True) as db: old=dict(db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone())
        code,result,_=self.request('PUT','/api/parametros',{'valor_combustivel':9,'km_por_litro':12,'jornada_padrao_horas':6},self.admin);self.assertEqual(code,200,result)
        with self.database.transaction(write=True) as db: new=dict(db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone())
        self.assertEqual(old,new)

    def test_duplicate_and_transaction(self):
        self.make_route('2026-03-03')
        code,_,_=self.request('POST','/api/roteiros',{'motorista_id':1,'data':'2026-03-03','distancia_total':1,'pontos':[{'endereco':'A','latitude':0,'longitude':0}]*2},self.admin)
        self.assertEqual(code,409)
        code,_,_=self.request('POST','/api/roteiros',{'motorista_id':1,'data':'2026-03-04','distancia_total':1,'pontos':[{'endereco':'A','latitude':0,'longitude':0},{'endereco':'B','latitude':100,'longitude':0}]},self.admin)
        self.assertEqual(code,400)
        with self.database.transaction(write=True) as db: self.assertEqual(db.execute("SELECT count(*) FROM roteiro WHERE data='2026-03-04'").fetchone()[0],0)

    def test_invalid_interval(self):
        self.assertEqual(self.request('GET','/api/relatorio?inicio=2026-04-02&fim=2026-04-01',cookie=self.admin)[0],400)

    def test_exact_resource_path(self):
        self.assertEqual(self.request('POST', '/api/pontos/1/extra', {'acao': 'chegada'}, self.admin)[0], 404)

    def test_csv_path_does_not_accept_wildcards(self):
        self.assertEqual(self.request('GET', '/api/exportarXcsv', cookie=self.admin)[0], 404)

    def test_only_login_post_is_public(self):
        for method, path in [('GET', '/api/login'), ('GET', '/api/pessoas'), ('GET', '/api/unknown')]:
            self.assertEqual(self.request(method, path)[0], 401)
        self.assertEqual(self.request('GET', '/api/login', cookie=self.admin)[0], 404)

    def test_current_user_does_not_expose_password_hash(self):
        status, user, _ = self.request('GET', '/api/me', cookie=self.admin)
        self.assertEqual(status, 200)
        self.assertEqual(set(user), {'id', 'login', 'perfil', 'motorista_id', 'gerente_id'})

    def test_logout_revokes_session(self):
        cookie = self.request('POST', '/api/login', {'login': 'g2', 'senha': 'password-g2'})[2]['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('POST', '/api/logout', {}, cookie)[0], 200)
        self.assertEqual(self.request('GET', '/api/me', cookie=cookie)[0], 401)

    def test_invalid_body_size(self):
        for size in ['-1', '200001', 'invalid']:
            self.assertEqual(self.request('POST', '/api/logout', {}, self.admin, {'Content-Length': size})[0], 400)

    def test_invalid_point_shape(self):
        data = {'motorista_id': 1, 'data': '2026-06-06', 'distancia_total': 10, 'pontos': [None, {}]}
        self.assertEqual(self.request('POST', '/api/roteiros', data, self.admin)[0], 400)

    def test_pending_filter_and_invalid_status(self):
        route_id = self.make_route('2026-07-07')
        query = '/api/relatorio?inicio=2026-07-07&fim=2026-07-07&status='
        report = self.request('GET', query + 'pendencias', cookie=self.admin)[1]
        self.assertEqual([route['id'] for route in report['roteiros']], [route_id])
        self.assertEqual(self.request('GET', query + 'concluido', cookie=self.admin)[1]['roteiros'], [])
        self.assertEqual(self.request('GET', query + 'unknown', cookie=self.admin)[0], 400)

    def test_frontend_modules_are_served(self):
        for filename in ['api.js', 'views.js', 'charts.js', 'formatters.js', 'reporting.js']:
            self.assertEqual(self.request('GET', '/' + filename)[0], 200)

    def test_password_whitespace_is_preserved(self):
        data = {'nome': 'Gestor Espaço', 'telefone': '1', 'email': 'g3@example.invalid',
                'login': 'g3', 'senha': ' password-g3 '}
        self.assertEqual(self.request('POST', '/api/gerentes', data, self.admin)[0], 201)
        self.assertEqual(self.request('POST', '/api/login', {'login': 'g3', 'senha': 'password-g3'})[0], 401)
        self.assertEqual(self.request('POST', '/api/login', {'login': 'g3', 'senha': data['senha']})[0], 200)

    def test_persistence_and_weighted_base(self):
        self.make_route('2026-05-05',1);self.make_route('2026-05-05',2)
        with self.database.transaction(write=True) as db: db.execute("UPDATE roteiro SET jornada_padrao_horas=8,tempo_total_parado=75 WHERE data='2026-05-05'")
        r=self.request('GET','/api/relatorio?inicio=2026-05-05&fim=2026-05-05',cookie=self.admin)[1]
        self.assertEqual(r['base_minutos'],960);self.assertEqual(r['percentual'],15.625)

if __name__=='__main__': unittest.main()
