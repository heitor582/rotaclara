"""Testes do handler real sem abrir sockets; cada caso usa SQLite temporário."""
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime,timedelta,timezone
import server


class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.original=server.DB_PATH
        server.DB_PATH=Path(cls.tmp.name)/'test.db'
        with patch.dict(os.environ,{'ROTACLARA_ADMIN_PASSWORD':'test-admin-password'}): server.init_db()
        cls.admin=cls.request('POST','/api/login',{'login':'admin','senha':'test-admin-password'})[2]['Set-Cookie'].split(';')[0]
        cls.request('POST','/api/gerentes',{'nome':'Gestor Um','telefone':'1','email':'g1@example.invalid','login':'g1','senha':'password-g1'},cls.admin)
        cls.request('POST','/api/gerentes',{'nome':'Gestor Dois','telefone':'2','email':'g2@example.invalid','login':'g2','senha':'password-g2'},cls.admin)
        for i in [1,2]:
            cls.request('POST','/api/motoristas',{'nome':f'Motorista {i}','telefone':'0','documento':f'TEST-{i}','veiculo':'Teste','km_por_litro':10,'gerente_id':i,'login':f'm{i}','senha':'password-motorista'},cls.admin)
        cls.driver=cls.request('POST','/api/login',{'login':'m1','senha':'password-motorista'})[2]['Set-Cookie'].split(';')[0]
        cls.manager=cls.request('POST','/api/login',{'login':'g1','senha':'password-g1'})[2]['Set-Cookie'].split(';')[0]

    @classmethod
    def tearDownClass(cls): server.DB_PATH=cls.original;cls.tmp.cleanup()

    @staticmethod
    def request(method,path,data=None,cookie='',headers=None):
        h=object.__new__(server.Handler);h.path=path;h.client_address=('test-client',1)
        body=json.dumps(data or {}).encode();h.rfile=io.BytesIO(body)
        h.headers={'Content-Length':str(len(body)),'X-RotaClara':'1','Host':'localhost','Cookie':cookie,**(headers or {})}
        result={}
        def send(data,status=200,kind='application/json; charset=utf-8',headers=None): result.update(data=data,status=status,headers=headers or {})
        h.send=send;h.handle_request(method)
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
        day=datetime.now(server.TZ).date().isoformat();rid=self.make_route(day)
        with server.connect() as db: ids=[p['id'] for p in db.execute('SELECT id FROM ponto WHERE roteiro_id=? ORDER BY ordem_sequencial',(rid,))]
        self.assertEqual(self.request('POST',f'/api/pontos/{ids[0]}',{'acao':'chegada'},self.driver)[0],400)
        self.assertEqual(self.request('POST',f'/api/roteiros/{rid}/iniciar',{},self.driver)[0],200)
        self.assertEqual(self.request('POST',f'/api/pontos/{ids[1]}',{'acao':'chegada'},self.driver)[0],400)
        self.assertEqual(self.request('POST',f'/api/pontos/{ids[0]}',{'acao':'saida'},self.driver)[0],400)
        for pid in ids:
            for action in ['chegada','saida']:
                code,result,_=self.request('POST',f'/api/pontos/{pid}',{'acao':action},self.driver);self.assertEqual(code,200,result)
        with server.connect() as db:
            r=dict(db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone())
            self.assertEqual(r['status'],'concluido');self.assertEqual(db.execute('SELECT tempo_parado_minutos FROM ponto WHERE id=?',(ids[0],)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM auditoria WHERE ponto_id IN (?,?)',ids).fetchone()[0],6)
            before=dict(db.execute('SELECT * FROM ponto WHERE id=?',(ids[1],)).fetchone())
        code,result,_=self.request('PUT',f'/api/pontos/{ids[1]}',{**before,'endereco':'=SUM(1,2)','motivo':'Correção de teste'},self.manager)
        self.assertEqual(code,200,result)
        csv=self.request('GET',f'/api/exportar.csv?inicio={day}&fim={day}&busca=SUM',cookie=self.manager)[1]
        self.assertIn("'=SUM",csv);self.assertNotIn(';Base;',csv)
        with server.connect() as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute('DELETE FROM auditoria')

    def test_parameter_snapshot(self):
        rid=self.make_route('2026-02-02')
        with server.connect() as db: old=dict(db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone())
        code,result,_=self.request('PUT','/api/parametros',{'valor_combustivel':9,'km_por_litro':12,'jornada_padrao_horas':6},self.admin);self.assertEqual(code,200,result)
        with server.connect() as db: new=dict(db.execute('SELECT * FROM roteiro WHERE id=?',(rid,)).fetchone())
        self.assertEqual(old,new)

    def test_duplicate_and_transaction(self):
        self.make_route('2026-03-03')
        code,_,_=self.request('POST','/api/roteiros',{'motorista_id':1,'data':'2026-03-03','distancia_total':1,'pontos':[{'endereco':'A','latitude':0,'longitude':0}]*2},self.admin)
        self.assertEqual(code,409)
        code,_,_=self.request('POST','/api/roteiros',{'motorista_id':1,'data':'2026-03-04','distancia_total':1,'pontos':[{'endereco':'A','latitude':0,'longitude':0},{'endereco':'B','latitude':100,'longitude':0}]},self.admin)
        self.assertEqual(code,400)
        with server.connect() as db: self.assertEqual(db.execute("SELECT count(*) FROM roteiro WHERE data='2026-03-04'").fetchone()[0],0)

    def test_invalid_interval(self):
        self.assertEqual(self.request('GET','/api/relatorio?inicio=2026-04-02&fim=2026-04-01',cookie=self.admin)[0],400)

    def test_persistence_and_weighted_base(self):
        self.make_route('2026-05-05',1);self.make_route('2026-05-05',2)
        with server.connect() as db: db.execute("UPDATE roteiro SET jornada_padrao_horas=8,tempo_total_parado=75 WHERE data='2026-05-05'")
        r=self.request('GET','/api/relatorio?inicio=2026-05-05&fim=2026-05-05',cookie=self.admin)[1]
        self.assertEqual(r['base_minutos'],960);self.assertEqual(r['percentual'],15.625)

if __name__=='__main__': unittest.main()
