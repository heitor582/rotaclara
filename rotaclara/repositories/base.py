class Repository:
    def __init__(self, connection):
        self.connection = connection

    def one(self, sql, parameters=()):
        row = self.connection.execute(sql, parameters).fetchone()
        return dict(row) if row else None

    def all(self, sql, parameters=()):
        return [dict(row) for row in self.connection.execute(sql, parameters)]
