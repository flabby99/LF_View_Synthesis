"""Take in input, perform CNN on it, and return an output"""
import argparse
import configparser
import os
import time
import pathlib

import torch
import h5py
import numpy as np
from PIL import Image

import cnn_utils
import conversions
import helpers
import data_transform
import image_warping

def get_sub_dir_for_saving(base_dir):
    """
    Returns the number of sub directories of base_dir, n, in format
    base_dir + path_separator + n
    Where n is padded on the left by zeroes to be of length four

    Example: base_dir is /home/sean/test with two sub directories
    Output: /home/sean/test/0002
    """
    num_sub_dirs = sum(os.path.isdir(os.path.join(base_dir, el))
                   for el in os.listdir(base_dir))

    sub_dir_to_save_to_name = str(num_sub_dirs)
    sub_dir_to_save_to_name = sub_dir_to_save_to_name.zfill(4)

    sub_dir_to_save_to = os.path.join(base_dir, sub_dir_to_save_to_name)
    os.mkdir(sub_dir_to_save_to)

    return sub_dir_to_save_to

def main(args, config):
    cuda = cnn_utils.check_cuda(config)

    model = cnn_utils.load_model_and_weights(args, config)
    if cuda:
        model = model.cuda()

    model.eval()
    
    # Create output directory
    base_dir = os.path.join(config['PATH']['output_dir'], 'warped')
    if not os.path.isdir(base_dir):
        pathlib.Path(base_dir).mkdir(parents=True, exist_ok=True)
    save_dir = get_sub_dir_for_saving(base_dir)

    # TODO if GT is available, can get diff images
    start_time = time.time()
    if not args.no_hdf5:
        file_path = os.path.join(config['PATH']['hdf5_dir'],
                                  config['PATH']['hdf5_name'])
        with h5py.File(file_path, mode='r', libver='latest') as hdf5_file:
            depth_grp = hdf5_file['val']['disparity']
            SNUM = 3
            depth_images = depth_grp['images'][SNUM, ...]

            colour_grp = hdf5_file['val']['colour']
            colour_images = colour_grp['images'][SNUM, ...]

            warped = data_transform.disparity_based_rendering(
                depth_images,
                colour_images,
                depth_images.shape[0])
            im_input = torch.from_numpy(warped).float().unsqueeze_(0)

            if cuda:
                im_input = im_input.cuda()

            output = model(im_input)
            output += im_input

    else:
        #Expect folder to have format, depth0.png, colour0.png ...
        INPUT_IMAGES = 1
        for i in range(INPUT_IMAGES):
            end_str = str(i) + '.png'
            depth_loc = os.path.join(
                config['PATH']['image_dir'],
                'depth' + end_str
            )
            colour_loc = os.path.join(
                config['PATH']['image_dir'],
                'colour' + end_str
            )
            depth = Image.open(depth_loc)
            depth.load()
            #Convert to disparity - needs metadata
            #warp it as in hdf5
            #combine with other warped
            #do model

    time_taken = time.time() - start_time
    print("Time taken was {:.0f}s".format(time_taken))
    grid_size = 64
    cpu_output = denormalise_lf(output).cpu().detach().numpy().astype(np.uint8)
    for i in range(grid_size):
        file_name = 'Colour{}.png'.format(i)
        save_location = os.path.join(save_dir, file_name)
        if i == 0:
            print("Saving images of size ", cpu_output[0, i, ...].shape)
        image_warping.save_array_as_image(
            cpu_output[0, i, ...], save_location)

def denormalise_lf(lf):
    """Coverts an lf in the range 0 to maximum into -1 1"""
    maximum = 255.0
    lf.add_(1.0).div_(2.0).mul_(maximum)
    return lf

if __name__ == '__main__':
    MODEL_HELP_STR = ' '.join((
        'Model name to load from config model dir',
        'Default value is best_model.pth'))
    HDF_HELP_STR = ' '.join((
        'Should a hdf5 file be used for input?',
        'If yes, config specified hdf5 file is used',
        'Otherwise image_dir is used'))
    PARSER = argparse.ArgumentParser(
        description='Process modifiable parameters from command line')
    PARSER.add_argument('--pretrained', default="best_model.pth", type=str,
                        help=MODEL_HELP_STR)
    PARSER.add_argument('--no_hdf5', action='store_true',
                        help=HDF_HELP_STR)
    #Any unknown argument will go to unparsed
    ARGS, UNPARSED = PARSER.parse_known_args()

    if len(UNPARSED) is not 0:
        print("Unrecognised command line argument passed")
        print(UNPARSED)
        exit(-1)

    #Config file modifiable parameters
    CONFIG = configparser.ConfigParser()
    CONFIG.read(os.path.join('config', 'main.ini'))

    print('Program started with the following options')
    helpers.print_config(CONFIG)
    print('Command Line arguments')
    print(ARGS)
    print()
    main(ARGS, CONFIG)
