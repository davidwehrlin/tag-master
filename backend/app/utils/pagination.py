"""
Pagination utilities for list endpoints.

Provides functions to paginate SQLAlchemy queries with metadata.
"""
from typing import Any, Dict, List, TypeVar
from math import ceil

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    """Metadata about paginated results."""
    
    total: int  # Total number of items
    page: int  # Current page number (1-indexed)
    size: int  # Items per page
    pages: int  # Total number of pages


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    
    items: List[Any]
    metadata: PaginationMetadata


async def paginate(
    query,
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query and return results with metadata.
    
    Args:
        query: SQLAlchemy select statement
        db: Database session
        page: Page number (1-indexed)
        size: Items per page
        max_size: Maximum allowed page size
        
    Returns:
        Dictionary with 'items' and 'metadata' keys
        
    Example:
        query = select(Player).where(Player.deleted_at.is_(None))
        result = await paginate(query, db, page=1, size=20)
        # result = {
        #     "items": [<Player>, <Player>, ...],
        #     "metadata": {"total": 45, "page": 1, "size": 20, "pages": 3}
        # }
    """
    # Validate and normalize parameters
    page = max(1, page)
    size = min(max(1, size), max_size)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Calculate pagination
    pages = ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size
    
    # Execute paginated query
    paginated_query = query.limit(size).offset(offset)
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "metadata": PaginationMetadata(
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    }


def get_pagination_params(page: int = 1, size: int = 20) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        size: Items per page
        
    Returns:
        Tuple of (page, size) with validated values
        
    Example:
        page, size = get_pagination_params(page=-1, size=1000)
        # Returns: (1, 100) - normalized to valid range
    """
    page = max(1, page)
    size = min(max(1, size), 100)
    return page, size
