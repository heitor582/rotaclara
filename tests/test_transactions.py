import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rotaclara.database import Database


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Database(Path(self.directory.name) / 'test.db')
        with self.database.transaction(write=True) as connection:
            connection.execute('CREATE TABLE counter (value INTEGER)')
            connection.execute('INSERT INTO counter VALUES (0)')

    def test_failed_operation_rolls_back_and_closes_connection(self):
        with self.assertRaises(ValueError):
            with self.database.transaction(write=True) as connection:
                connection.execute('UPDATE counter SET value=1')
                raise ValueError('Falha na auditoria')
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute('SELECT 1')
        with self.database.transaction() as connection:
            self.assertEqual(connection.execute('SELECT value FROM counter').fetchone()[0], 0)

    def test_success_closes_connection(self):
        with self.database.transaction() as connection:
            connection.execute('SELECT 1')
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute('SELECT 1')

    def test_concurrent_read_modify_write_does_not_lose_updates(self):
        def increment(_):
            with self.database.transaction(write=True) as connection:
                value = connection.execute('SELECT value FROM counter').fetchone()[0]
                connection.execute('UPDATE counter SET value=?', (value + 1,))

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(increment, range(12)))
        with self.database.transaction() as connection:
            self.assertEqual(connection.execute('SELECT value FROM counter').fetchone()[0], 12)
