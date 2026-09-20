import unittest
from datetime import datetime, timezone
from rotaclara.domain import calculate_stop_minutes, calculate_route_minutes, calculate_fuel_cost, calculate_journey_percentage, parse_timestamp


def point(order, minutes):
    start=datetime(2026,9,1,10,tzinfo=timezone.utc)
    from datetime import timedelta
    return {'ordem_sequencial':order,'data_hora_chegada':start.isoformat(),'data_hora_saida':(start+timedelta(minutes=minutes)).isoformat()}


class BusinessTests(unittest.TestCase):
    def test_partida(self): self.assertEqual(calculate_stop_minutes(point(1,90)),0)
    def test_examples(self):
        for times,expected in [([15,10,50],75),([10,5,26],41),([5,10,30],45)]:
            self.assertEqual(calculate_route_minutes([point(1,120)]+[point(i+2,t) for i,t in enumerate(times)]),expected)
    def test_cost(self): self.assertEqual(calculate_fuel_cost(100,6,10),60)
    def test_percentage(self): self.assertAlmostEqual(calculate_journey_percentage(75,8),15.625)
    def test_partial_minute(self): self.assertEqual(calculate_stop_minutes(point(2,.5)),.5)
    def test_missing_departure(self):
        p=point(2,10);p['data_hora_saida']=None;self.assertEqual(calculate_stop_minutes(p),0)
    def test_missing_arrival(self):
        p=point(2,10);p['data_hora_chegada']=None
        with self.assertRaises(ValueError): calculate_stop_minutes(p)
    def test_reverse_even_at_origin(self):
        for order in [1,2]:
            with self.assertRaises(ValueError): calculate_stop_minutes(point(order,-1))
    def test_invalid_numbers(self):
        for n in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError): calculate_fuel_cost(1,6,n)
    def test_timezone_and_midnight(self):
        self.assertEqual(calculate_stop_minutes({'ordem_sequencial':2,'data_hora_chegada':'2026-09-01T23:50:00-03:00','data_hora_saida':'2026-09-02T03:10:00Z'}),20)
    def test_naive_datetime(self):
        with self.assertRaises(ValueError): parse_timestamp('2026-09-01T12:00:00')
    def test_more_than_journey(self): self.assertEqual(calculate_journey_percentage(960),200)

if __name__=='__main__': unittest.main()
