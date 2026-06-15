import pytest
from src.core.ecs.entity import Entity
from src.utils.spatial_hash import SpatialHashGrid


@pytest.fixture
def grid():
    """Create a spatial hash grid with cell_size=64."""
    return SpatialHashGrid(cell_size=64.0)


@pytest.fixture
def entities():
    """Create test entities."""
    return [
        Entity(id=1, generation=0),
        Entity(id=2, generation=0),
        Entity(id=3, generation=0),
    ]


# --- __init__ tests ---

def test_init_creates_empty_grid():
    """Test that __init__ creates an empty grid."""
    grid = SpatialHashGrid(cell_size=32.0)
    assert grid._cell_size == 32.0
    assert len(grid._cells) == 0
    assert len(grid._entity_cells) == 0


def test_init_different_cell_sizes():
    """Test initialization with different cell sizes."""
    grid_small = SpatialHashGrid(cell_size=16.0)
    grid_large = SpatialHashGrid(cell_size=128.0)
    assert grid_small._cell_size == 16.0
    assert grid_large._cell_size == 128.0


# --- insert tests ---

def test_insert_single_entity(grid, entities):
    """Test inserting a single entity."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=200.0)
    
    assert entity in grid._entity_cells
    assert len(grid._cells) == 1
    assert len(grid._entity_cells) == 1


def test_insert_multiple_entities_same_cell(grid, entities):
    """Test inserting multiple entities into the same cell."""
    e1, e2 = entities[0], entities[1]
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=120.0, y=120.0)
    
    assert e1 in grid._entity_cells
    assert e2 in grid._entity_cells
    assert len(grid._cells) == 1
    assert len(grid._entity_cells) == 2


def test_insert_multiple_entities_different_cells(grid, entities):
    """Test inserting entities into different cells."""
    e1, e2, e3 = entities
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=500.0, y=500.0)
    grid.insert(e3, x=1000.0, y=1000.0)
    
    assert len(grid._cells) == 3
    assert len(grid._entity_cells) == 3


def test_insert_entity_reinsert_moves_to_new_cell(grid, entities):
    """Test that reinserting an entity moves it to a new cell."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    old_cell = grid._entity_cells[entity]
    
    grid.insert(entity, x=500.0, y=500.0)
    new_cell = grid._entity_cells[entity]
    
    assert old_cell != new_cell
    assert len(grid._cells) == 1


# --- remove tests ---

def test_remove_existing_entity(grid, entities):
    """Test removing an existing entity."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    
    result = grid.remove(entity)
    
    assert result is True
    assert entity not in grid._entity_cells
    assert len(grid._cells) == 0


def test_remove_nonexistent_entity(grid, entities):
    """Test removing an entity that doesn't exist."""
    entity = entities[0]
    
    result = grid.remove(entity)
    
    assert result is False
    assert len(grid._cells) == 0
    assert len(grid._entity_cells) == 0


def test_remove_cleans_empty_cells(grid, entities):
    """Test that removing the last entity from a cell deletes the cell."""
    e1, e2 = entities[0], entities[1]
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=500.0, y=500.0)
    assert len(grid._cells) == 2
    
    grid.remove(e1)
    
    assert len(grid._cells) == 1
    assert len(grid._entity_cells) == 1


def test_remove_keeps_cell_with_other_entities(grid, entities):
    """Test that removing an entity doesn't delete cell if other entities remain."""
    e1, e2 = entities[0], entities[1]
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=120.0, y=120.0)
    
    grid.remove(e1)
    
    assert len(grid._cells) == 1
    assert len(grid._entity_cells) == 1
    assert e2 in grid._entity_cells


# --- update tests ---

def test_update_moves_entity(grid, entities):
    """Test updating an entity's position."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    old_cell = grid._entity_cells[entity]
    
    grid.update(entity, x=500.0, y=500.0)
    new_cell = grid._entity_cells[entity]
    
    assert old_cell != new_cell
    assert len(grid._cells) == 1


def test_update_nonexistent_entity_inserts_it(grid, entities):
    """Test that updating a nonexistent entity inserts it."""
    entity = entities[0]
    
    grid.update(entity, x=100.0, y=100.0)
    
    assert entity in grid._entity_cells
    assert len(grid._cells) == 1
    assert len(grid._entity_cells) == 1


def test_update_same_cell(grid, entities):
    """Test updating an entity within the same cell."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    old_cell = grid._entity_cells[entity]
    
    grid.update(entity, x=120.0, y=120.0)
    new_cell = grid._entity_cells[entity]
    
    assert old_cell == new_cell
    assert len(grid._cells) == 1


# --- query_circle tests ---

def test_query_circle_empty_grid(grid):
    """Test querying an empty grid returns empty set."""
    result = grid.query_circle(x=100.0, y=100.0, radius=50.0)
    assert result == set()


def test_query_circle_finds_entity_in_range(grid, entities):
    """Test that query_circle finds entities in range."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    
    result = grid.query_circle(x=100.0, y=100.0, radius=50.0)
    
    assert entity in result


def test_query_circle_finds_entity_nearby(grid, entities):
    """Test that query_circle finds entities in nearby cells."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    
    result = grid.query_circle(x=150.0, y=150.0, radius=100.0)
    
    assert entity in result


def test_query_circle_excludes_entity(grid, entities):
    """Test that exclude parameter removes entity from results."""
    e1, e2 = entities[0], entities[1]
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=120.0, y=120.0)
    
    result = grid.query_circle(x=100.0, y=100.0, radius=50.0, exclude=e1)
    
    assert e1 not in result
    assert e2 in result


def test_query_circle_large_radius(grid, entities):
    """Test query_circle with large radius covers multiple cells."""
    e1, e2, e3 = entities
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=300.0, y=300.0)
    grid.insert(e3, x=500.0, y=500.0)
    
    result = grid.query_circle(x=300.0, y=300.0, radius=300.0)
    
    assert e1 in result
    assert e2 in result
    assert e3 in result


# --- query_rect tests ---

def test_query_rect_empty_grid(grid):
    """Test querying an empty grid returns empty set."""
    result = grid.query_rect(x=100.0, y=100.0, half_width=50.0, half_height=50.0)
    assert result == set()


def test_query_rect_finds_entity_in_range(grid, entities):
    """Test that query_rect finds entities in range."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    
    result = grid.query_rect(x=100.0, y=100.0, half_width=50.0, half_height=50.0)
    
    assert entity in result


def test_query_rect_finds_entity_nearby(grid, entities):
    """Test that query_rect finds entities in nearby cells."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    
    result = grid.query_rect(x=150.0, y=150.0, half_width=100.0, half_height=100.0)
    
    assert entity in result


def test_query_rect_excludes_entity(grid, entities):
    """Test that exclude parameter removes entity from results."""
    e1, e2 = entities[0], entities[1]
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=120.0, y=120.0)
    
    result = grid.query_rect(x=100.0, y=100.0, half_width=50.0, half_height=50.0, exclude=e1)
    
    assert e1 not in result
    assert e2 in result


def test_query_rect_large_area(grid, entities):
    """Test query_rect with large area covers multiple cells."""
    e1, e2, e3 = entities
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=300.0, y=300.0)
    grid.insert(e3, x=500.0, y=500.0)
    
    result = grid.query_rect(x=300.0, y=300.0, half_width=300.0, half_height=300.0)
    
    assert e1 in result
    assert e2 in result
    assert e3 in result


# --- clear tests ---

def test_clear_empty_grid(grid):
    """Test clearing an already empty grid."""
    grid.clear()
    
    assert len(grid._cells) == 0
    assert len(grid._entity_cells) == 0


def test_clear_populated_grid(grid, entities):
    """Test clearing a grid with entities."""
    e1, e2, e3 = entities
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=500.0, y=500.0)
    grid.insert(e3, x=1000.0, y=1000.0)
    
    grid.clear()
    
    assert len(grid._cells) == 0
    assert len(grid._entity_cells) == 0


def test_clear_allows_reuse(grid, entities):
    """Test that grid can be reused after clear."""
    entity = entities[0]
    grid.insert(entity, x=100.0, y=100.0)
    grid.clear()
    
    grid.insert(entity, x=200.0, y=200.0)
    
    assert entity in grid._entity_cells
    assert len(grid._cells) == 1


# --- __repr__ tests ---

def test_repr_empty_grid():
    """Test string representation of empty grid."""
    grid = SpatialHashGrid(cell_size=64.0)
    result = repr(grid)
    
    assert "SpatialHashGrid" in result
    assert "cell_size=64.0" in result
    assert "cells=0" in result
    assert "entities=0" in result


def test_repr_populated_grid(grid, entities):
    """Test string representation of populated grid."""
    e1, e2 = entities[0], entities[1]
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=500.0, y=500.0)
    
    result = repr(grid)
    
    assert "cell_size=64.0" in result
    assert "cells=2" in result
    assert "entities=2" in result


# --- Integration test ---

def test_full_workflow(grid, entities):
    """Test complete workflow: insert, query, update, remove, clear."""
    e1, e2, e3 = entities
    
    # Insert entities
    grid.insert(e1, x=100.0, y=100.0)
    grid.insert(e2, x=200.0, y=200.0)
    grid.insert(e3, x=500.0, y=500.0)
    assert len(grid._cells) == 3
    assert len(grid._entity_cells) == 3
    
    # Query circle
    circle_results = grid.query_circle(x=150.0, y=150.0, radius=100.0)
    assert e1 in circle_results
    assert e2 in circle_results
    
    # Query rect
    rect_results = grid.query_rect(x=300.0, y=300.0, half_width=200.0, half_height=200.0)
    assert e1 in rect_results
    assert e2 in rect_results
    assert e3 in rect_results
    
    # Query with exclude
    excluded_results = grid.query_circle(x=150.0, y=150.0, radius=100.0, exclude=e1)
    assert e1 not in excluded_results
    assert e2 in excluded_results
    
    # Update entity position
    grid.update(e1, x=600.0, y=600.0)
    assert len(grid._cells) == 3
    
    # Remove entity
    removed = grid.remove(e2)
    assert removed is True
    assert e2 not in grid._entity_cells
    assert len(grid._entity_cells) == 2
    
    # Remove nonexistent entity
    removed = grid.remove(e2)
    assert removed is False
    
    # Clear grid
    grid.clear()
    assert len(grid._cells) == 0
    assert len(grid._entity_cells) == 0
    
    # Reuse after clear
    grid.insert(e1, x=100.0, y=100.0)
    assert len(grid._cells) == 1
    assert len(grid._entity_cells) == 1
