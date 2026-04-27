# -*- coding: utf-8 -*-
"""Tests for filtering system."""
import pytest
from datetime import datetime
from ticketCrawler.filters.factory import FilterFactory
from ticketCrawler.filters.filter_types.price_filter import PriceFilter
from ticketCrawler.filters.filter_types.seat_filter import SeatTypeFilter
from ticketCrawler.filters.filter_types.date_filter import DateFilter
from ticketCrawler.filters.filter_types.quantity_filter import QuantityFilter
from ticketCrawler.filters.combined_filter import CombinedFilter


class TestPriceFilter:
    """Test price filtering."""
    
    def test_price_filter_min(self):
        """Test minimum price filtering."""
        pf = PriceFilter(min_price=10)
        
        assert pf.matches({'price': 15})
        assert pf.matches({'price': 10})
        assert not pf.matches({'price': 5})
    
    def test_price_filter_max(self):
        """Test maximum price filtering."""
        pf = PriceFilter(max_price=100)
        
        assert pf.matches({'price': 50})
        assert pf.matches({'price': 100})
        assert not pf.matches({'price': 150})
    
    def test_price_filter_range(self):
        """Test price range filtering."""
        pf = PriceFilter(min_price=10, max_price=100)
        
        assert pf.matches({'price': 50})
        assert pf.matches({'price': 10})
        assert pf.matches({'price': 100})
        assert not pf.matches({'price': 5})
        assert not pf.matches({'price': 150})
    
    def test_price_filter_no_data(self):
        """Test filter with missing price."""
        pf = PriceFilter(min_price=10)
        assert pf.matches({})  # Should not filter out


class TestSeatTypeFilter:
    """Test seat type filtering."""
    
    def test_seat_type_filter_include(self):
        """Test including specific seat types."""
        stf = SeatTypeFilter(seat_types=['floor', 'vip'])
        
        assert stf.matches({'seat_type': 'floor'})
        assert stf.matches({'seat_type': 'vip'})
        assert not stf.matches({'seat_type': 'balcony'})
    
    def test_seat_type_filter_exclude(self):
        """Test excluding seat types."""
        stf = SeatTypeFilter(exclude_seat_types=['balcony'])
        
        assert stf.matches({'seat_type': 'floor'})
        assert stf.matches({'seat_type': 'vip'})
        assert not stf.matches({'seat_type': 'balcony'})


class TestDateFilter:
    """Test date filtering."""
    
    def test_date_filter_range(self):
        """Test date range filtering."""
        df = DateFilter(start_date='2026-01-01', end_date='2026-12-31')
        
        assert df.matches({'date': '2026-06-15'})
        assert df.matches({'date': '2026-01-01'})
        assert df.matches({'date': '2026-12-31'})
        assert not df.matches({'date': '2025-12-31'})
        assert not df.matches({'date': '2027-01-01'})


class TestQuantityFilter:
    """Test quantity filtering."""
    
    def test_quantity_filter_min(self):
        """Test minimum quantity filtering."""
        qf = QuantityFilter(min_quantity=2)
        
        assert qf.matches({'quantity': 3})
        assert qf.matches({'quantity': 2})
        assert not qf.matches({'quantity': 1})
    
    def test_quantity_filter_max(self):
        """Test maximum quantity filtering."""
        qf = QuantityFilter(max_quantity=10)
        
        assert qf.matches({'quantity': 5})
        assert qf.matches({'quantity': 10})
        assert not qf.matches({'quantity': 15})


class TestCombinedFilter:
    """Test combined filtering with multiple filters."""
    
    def test_combined_filter_all_required(self):
        """Test combined filter with ALL logic."""
        cf = CombinedFilter(require_all=True)
        cf.add_filter(PriceFilter(min_price=10, max_price=100))
        cf.add_filter(SeatTypeFilter(seat_types=['floor', 'vip']))
        
        # Should pass all filters
        assert cf.matches({'price': 50, 'seat_type': 'floor'})
        
        # Should fail price filter
        assert not cf.matches({'price': 150, 'seat_type': 'floor'})
        
        # Should fail seat filter
        assert not cf.matches({'price': 50, 'seat_type': 'balcony'})
    
    def test_combined_filter_any_required(self):
        """Test combined filter with ANY logic."""
        cf = CombinedFilter(require_all=False)
        cf.add_filter(PriceFilter(max_price=50))
        cf.add_filter(SeatTypeFilter(seat_types=['vip']))
        
        # Pass price only
        assert cf.matches({'price': 30, 'seat_type': 'balcony'})
        
        # Pass seat only
        assert cf.matches({'price': 100, 'seat_type': 'vip'})
        
        # Pass both
        assert cf.matches({'price': 30, 'seat_type': 'vip'})
        
        # Pass neither
        assert not cf.matches({'price': 100, 'seat_type': 'balcony'})
    
    def test_combined_filter_list(self):
        """Test filtering a list of tickets."""
        cf = CombinedFilter(require_all=True)
        cf.add_filter(PriceFilter(min_price=10, max_price=100))
        cf.add_filter(SeatTypeFilter(seat_types=['floor', 'vip']))
        
        tickets = [
            {'price': 25, 'seat_type': 'floor', 'date': '2026-06-15'},
            {'price': 150, 'seat_type': 'vip', 'date': '2026-06-15'},
            {'price': 50, 'seat_type': 'balcony', 'date': '2026-06-15'},
            {'price': 75, 'seat_type': 'vip', 'date': '2026-06-15'},
        ]
        
        filtered = cf.filter_tickets(tickets)
        assert len(filtered) == 2
        assert filtered[0]['price'] == 25
        assert filtered[1]['price'] == 75


class TestFilterFactory:
    """Test filter factory."""
    
    def test_create_price_filter(self):
        """Test creating price filter via factory."""
        f = FilterFactory.create_filter('price', min_price=10, max_price=100)
        assert isinstance(f, PriceFilter)
    
    def test_create_combined_filter(self):
        """Test creating combined filter via factory."""
        config = [
            {'type': 'price', 'min_price': 10, 'max_price': 100},
            {'type': 'seat_type', 'seat_types': ['floor']}
        ]
        cf = FilterFactory.create_combined_filter(config)
        assert isinstance(cf, CombinedFilter)
        assert len(cf.filters) == 2
    
    def test_list_available_filters(self):
        """Test listing available filters."""
        filters = FilterFactory.list_filters()
        assert 'price' in filters
        assert 'seat_type' in filters
        assert 'date' in filters
        assert 'quantity' in filters


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
