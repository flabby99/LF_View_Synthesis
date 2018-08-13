"""Contains data transforms which can be passed to the data loader"""
import math
import random

import numpy as np
import torch

import image_warping

def disparity_based_rendering(disparities, views, grid_size):
    """Returns a list of warped images using the input views and disparites"""
     # Alternatively, grid_one_way - 1 can be used below
    shape = (grid_size,) + views.shape[-3:]
    grid_one_way = int(math.sqrt(grid_size))
    sample_index = grid_size // 2 + (grid_one_way // 2)
    return image_warping.depth_rendering(
        ref_view=views[sample_index],
        disparity_map=disparities[sample_index],
        lf_size=shape)

def transform_to_warped(sample):
    """
    Input a dictionary of depth images and reference views,
    Output a dictionary of inputs -warped and targets - reference
    """
    normalise_sample(sample)
    disparity = sample['depth']
    targets = sample['colour']
    grid_size = sample['grid_size']
    warped_images = disparity_based_rendering(
        disparity.numpy(), targets.numpy(), grid_size)

    return {'inputs': warped_images, 'targets': targets}

def normalise_sample(sample):
    """Coverts an lf in the range 0 to maximum into 0 1"""
    maximum = 255.0
    lf = sample['colour']
    lf.div_(maximum)
    return sample

def upper_left_patch(sample):
    width = sample['colour'].shape[2]
    sample['colour'] = sample['colour'][:, 0:width//2, 0:width//2]
    sample['depth'] = sample['depth'][:, 0:width//2, 0:width//2]
    return sample

def get_random_crop(sample, patch_size):
    pixel_end = sample['colour'].shape[1]
    high = pixel_end - 1 - patch_size
    start_h = random.randint(0, high)
    start_v = random.randint(0, high)
    end_h = start_h + patch_size
    end_v = start_v + patch_size
    sample['depth'] = sample['depth'][:, start_h:end_h, start_v:end_v]
    sample['colour'] = sample['colour'][:, start_h:end_h, start_v:end_v]
    return sample

def random_gamma(sample):
    maximum = 255
    gamma = random.uniform(0.4, 1.0)
    sample['colour'] = torch.pow(
        sample['colour'].div_(maximum), gamma).mul_(maximum)
    return sample

def denormalise_lf(lf):
    """Coverts an lf in the range 0 1 to 0 to maximum"""
    maximum = 255.0
    lf.mul_(maximum)
    return lf