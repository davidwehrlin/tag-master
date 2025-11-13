"""
Unit tests for app/utils/pagination.py pagination utilities.

Tests verify:
- Pagination parameter validation (get_pagination_params)
- Metadata model
- Edge cases (page 0, negative size, max size enforcement)

Note: Full integration testing of paginate() function is deferred to
integration tests where real SQLAlchemy queries can be used.
"""

from math import ceil

import pytest

from app.utils.pagination import (
    PaginationMetadata,
    PaginatedResponse,
    get_pagination_params,
)


class TestPaginationMetadata:
    """Test PaginationMetadata model."""

    def test_pagination_metadata_creation(self):
        """Test creating PaginationMetadata."""
        metadata = PaginationMetadata(total=100, page=1, size=20, pages=5)
        
        assert metadata.total == 100
        assert metadata.page == 1
        assert metadata.size == 20
        assert metadata.pages == 5

    def test_pagination_metadata_zero_items(self):
        """Test metadata with zero items."""
        metadata = PaginationMetadata(total=0, page=1, size=20, pages=1)
        
        assert metadata.total == 0
        assert metadata.pages == 1

    def test_pagination_metadata_partial_last_page(self):
        """Test metadata calculation with partial last page."""
        # 45 items / 20 per page = 3 pages (last page has 5 items)
        total = 45
        size = 20
        pages = ceil(total / size)
        
        metadata = PaginationMetadata(total=total, page=1, size=size, pages=pages)
        
        assert metadata.pages == 3
        assert metadata.total == 45


class TestGetPaginationParams:
    """Test pagination parameter validation."""

    def test_get_pagination_params_valid_values(self):
        """Test with valid parameters."""
        page, size = get_pagination_params(page=2, size=10)
        
        assert page == 2
        assert size == 10

    def test_get_pagination_params_negative_page(self):
        """Test that negative page is normalized to 1."""
        page, size = get_pagination_params(page=-5, size=20)
        
        assert page == 1
        assert size == 20

    def test_get_pagination_params_zero_page(self):
        """Test that page 0 is normalized to 1."""
        page, size = get_pagination_params(page=0, size=20)
        
        assert page == 1

    def test_get_pagination_params_negative_size(self):
        """Test that negative size is normalized to 1."""
        page, size = get_pagination_params(page=1, size=-10)
        
        assert page == 1
        assert size == 1

    def test_get_pagination_params_zero_size(self):
        """Test that size 0 is normalized to 1."""
        page, size = get_pagination_params(page=1, size=0)
        
        assert size == 1

    def test_get_pagination_params_exceeds_max_size(self):
        """Test that size > 100 is capped at 100."""
        page, size = get_pagination_params(page=1, size=200)
        
        assert size == 100

    def test_get_pagination_params_defaults(self):
        """Test default parameter values."""
        page, size = get_pagination_params()
        
        assert page == 1
        assert size == 20

    def test_get_pagination_params_exact_max_size(self):
        """Test size exactly at max_size."""
        page, size = get_pagination_params(page=1, size=100)
        
        assert size == 100

    def test_get_pagination_params_just_under_max_size(self):
        """Test size just under max_size."""
        page, size = get_pagination_params(page=1, size=99)
        
        assert size == 99

    def test_get_pagination_params_large_page_number(self):
        """Test with large page number."""
        page, size = get_pagination_params(page=1000, size=20)
        
        assert page == 1000
        assert size == 20


class TestPaginationCalculations:
    """Test pagination calculation logic."""

    def test_offset_calculation_page_1(self):
        """Test offset calculation for page 1."""
        page = 1
        size = 20
        offset = (page - 1) * size
        
        assert offset == 0

    def test_offset_calculation_page_2(self):
        """Test offset calculation for page 2."""
        page = 2
        size = 20
        offset = (page - 1) * size
        
        assert offset == 20

    def test_offset_calculation_page_5(self):
        """Test offset calculation for page 5."""
        page = 5
        size = 25
        offset = (page - 1) * size
        
        assert offset == 100

    def test_pages_calculation_exact_division(self):
        """Test pages calculation when items divide evenly."""
        total = 100
        size = 20
        pages = ceil(total / size) if total > 0 else 1
        
        assert pages == 5

    def test_pages_calculation_with_remainder(self):
        """Test pages calculation with partial last page."""
        total = 45
        size = 20
        pages = ceil(total / size) if total > 0 else 1
        
        assert pages == 3

    def test_pages_calculation_empty_results(self):
        """Test pages calculation with zero items."""
        total = 0
        size = 20
        pages = ceil(total / size) if total > 0 else 1
        
        assert pages == 1

    def test_pages_calculation_one_item(self):
        """Test pages calculation with one item."""
        total = 1
        size = 20
        pages = ceil(total / size) if total > 0 else 1
        
        assert pages == 1

    def test_pages_calculation_size_one(self):
        """Test pages calculation with size 1."""
        total = 50
        size = 1
        pages = ceil(total / size) if total > 0 else 1
        
        assert pages == 50


class TestPaginatedResponse:
    """Test PaginatedResponse wrapper."""

    def test_paginated_response_creation(self):
        """Test creating PaginatedResponse."""
        items = [1, 2, 3, 4, 5]
        metadata = PaginationMetadata(total=100, page=1, size=20, pages=5)
        
        response = PaginatedResponse(items=items, metadata=metadata)
        
        assert response.items == items
        assert response.metadata == metadata

    def test_paginated_response_empty_items(self):
        """Test PaginatedResponse with empty items list."""
        items = []
        metadata = PaginationMetadata(total=0, page=1, size=20, pages=1)
        
        response = PaginatedResponse(items=items, metadata=metadata)
        
        assert response.items == []
        assert response.metadata.total == 0
