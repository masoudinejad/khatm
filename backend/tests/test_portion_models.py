"""Tests for portion models"""

import pytest
from pydantic import ValidationError

from src.models.portion import PortionAssign, PortionProgress


def test_portion_assign_valid():
    """Test valid portion assignment"""
    assign = PortionAssign(portion_number=5)
    assert assign.portion_number == 5


def test_portion_assign_missing_fields():
    """Test portion assignment with missing fields"""
    with pytest.raises(ValidationError):
        PortionAssign()
        # Missing portion_number


def test_portion_assign_invalid_type():
    """Test portion assignment with invalid type"""
    with pytest.raises(ValidationError):
        PortionAssign(portion_number="invalid")


def test_portion_assign_negative_number():
    """Test portion assignment with negative number"""
    # Pydantic allows negative numbers by default unless you add validators
    assign = PortionAssign(portion_number=-1)
    assert assign.portion_number == -1


def test_portion_progress_valid():
    """Test valid portion progress"""
    progress = PortionProgress(progress_percentage=75)
    assert progress.progress_percentage == 75
    assert progress.notes is None


def test_portion_progress_with_notes():
    """Test portion progress with notes"""
    progress = PortionProgress(progress_percentage=50, notes="Making good progress")
    assert progress.progress_percentage == 50
    assert progress.notes == "Making good progress"


def test_portion_progress_zero_percent():
    """Test portion progress at 0%"""
    progress = PortionProgress(progress_percentage=0)
    assert progress.progress_percentage == 0


def test_portion_progress_complete():
    """Test portion progress at 100%"""
    progress = PortionProgress(progress_percentage=100)
    assert progress.progress_percentage == 100


def test_portion_progress_missing_fields():
    """Test portion progress with missing required fields"""
    with pytest.raises(ValidationError):
        PortionProgress(notes="Some notes")
        # Missing progress_percentage


def test_portion_progress_invalid_type():
    """Test portion progress with invalid type"""
    with pytest.raises(ValidationError):
        PortionProgress(progress_percentage="invalid")
