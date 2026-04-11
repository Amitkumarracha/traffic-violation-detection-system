"""
CycleGAN-style Data Augmentation Module

Provides offline dataset augmentation for training data expansion.
NOT used in live inference.
"""

from .generate import DataAugmentationGAN

__all__ = [
    'DataAugmentationGAN',
]

__version__ = '1.0.0'
