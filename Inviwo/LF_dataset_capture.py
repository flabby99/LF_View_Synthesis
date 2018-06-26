from random import seed, random
import os
from time import sleep, time
import pathlib
import math

import inviwopy
import ivw.utils as inviwo_utils
from inviwopy.glm import vec3, normalize

def cross_product(vec_1, vec_2):
    result =  vec3(
        (vec_1.y * vec_2.z) - (vec_1.z * vec_2.y),
        (vec_1.z * vec_2.x) - (vec_1.x * vec_2.z),
        (vec_1.x * vec_2.y) - (vec_1.y * vec_2.x))
    return result

class LightFieldCamera:
    def __init__(self, look_from, look_to, look_up = vec3(0, 1, 0),
                 interspatial_distance = 1.0,
                 spatial_rows = 8, spatial_cols = 8):
        """Create a light field camera array.

        Keyword arguments:
        look_from, look_to, look_up -- vectors for top left cam (default up y)
        interspatial_distance -- distance between cameras in array (default 1.0)
        spatial_rows, spatial_cols -- camera array dimensions (default 8 x 8)
        """
        self.set_look(look_from, look_to, look_up)
        self.spatial_rows = spatial_rows
        self.spatial_cols = spatial_cols
        self.interspatial_distance = interspatial_distance

    def set_look(self, look_from, look_to, look_up):
        """Set the top left camera to look_from, look_to and look_up"""
        self.look_from = look_from
        self.look_to = look_to
        self.look_up = look_up

    def get_row_col_number(self, index):
        row_num = index // self.spatial_cols
        col_num = index % self.spatial_cols
        return row_num, col_num

    def print_look(self):
        print("Look from: {} , Look to: {}, Look up: {}"
                .format(self.look_from, self.look_to, self.look_up))

    def view_array(self, cam, save = False, save_dir = os.path.expanduser('~')):
        """Move the inviwo camera through the array for the current workspace.

        Keyword arguments:
        cam -- the camera to move through the light field array
        save -- save the images to png files (default False)
        save_dir -- the main directory to save the png images to (default home)
        """
        if not os.path.isdir(save_dir):
            raise ValueError("save_dir is not a valid directory.")

        print("Viewing array for lf camera with:")
        self.print_look()
        # Save the current camera position
        prev_cam_look_from = cam.lookFrom
        prev_cam_look_to = cam.lookTo

        for idx, val in enumerate(self.calculate_camera_array()):
            (look_from, look_to) = val
            cam.lookFrom = look_from
            cam.lookTo = look_to
            inviwo_utils.update()
            row_num, col_num = self.get_row_col_number(idx)

            if save:
                #Loop over canvases in the workspace
                canvases = inviwopy.app.network.canvases
                same_names = any(
                    [(canvases[i].displayName == canvases[i + 1].displayName)
                    for i in range(len(canvases) - 1)]
                )
                for canvas_idx, canvas in enumerate(canvases):
                    if same_names:
                        file_name = ('Canvas_'
                                  + str(canvas_idx)
                                  + '_'
                                  + str(row_num)
                                  + str(col_num)
                                  + '.png')
                    else:
                        file_name = (canvas.displayName
                                  + str(row_num)
                                  + str(col_num)
                                  + '.png')
                    full_save_dir = os.path.abspath(save_dir)
                    file_path = os.path.join(full_save_dir, file_name)
                    print('Saving to: ' + file_path)
                    canvas.snapshot(file_path)
            else:
                print("Viewing position ({}, {})".format(row_num, col_num))
                sleep(0.1)

        # Reset the camera to original position
        cam.lookFrom = prev_cam_look_from
        cam.lookTo = prev_cam_look_to

    def get_look_right(self):
        """Get the right look vector for the top left camera"""
        view_direction = self.look_to - self.look_from
        right_vec = normalize(cross_product(view_direction, self.look_up))
        return right_vec

    def calculate_camera_array(self):
        """Returns list of (look_from, look_to) tuples for the camera array"""
        look_list = []

        row_step_vec = normalize(self.look_up) * self.interspatial_distance
        col_step_vec = self.get_look_right() * self.interspatial_distance

        #Start at the top left camera position
        for i in range(self.spatial_rows):
            row_movement = row_step_vec * (-i)
            row_look_from = self.look_from + row_movement
            row_look_to = self.look_to + row_movement

            for j in range(self.spatial_cols):
                col_movement = col_step_vec * j
                cam_look_from = row_look_from + col_movement
                cam_look_to = row_look_to + col_movement

                look_list.append((cam_look_from, cam_look_to))

        return look_list

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

def random_float():
    """returns a random float between -1 and 1"""
    return (random() - 0.5) * 2

def create_random_lf_cameras(num_to_create, max_distance_from_origin,
                             interspatial_distance = 1.0,
                             spatial_rows = 8, spatial_cols = 8):
    """Create a list of randomnly positioned lf cameras

    Keyword arguments:
    num_to_create -- the number of lf cameras to create
    max_distance_from_origin -- the furthest from the origin the cameras sit
    interspatial_distance -- distance between cameras in array (default 1.0)
    spatial_rows, spatial_cols -- dimensions of camera array (default 8 x 8)
    """
    lf_cameras = []
    d = max_distance_from_origin
    look_up = vec3(0, 1, 0)
    for i in range(num_to_create):
        look_from = vec3(random_float(), random_float(), random_float()) * d
        look_to = vec3(random_float(), random_float(), random_float()) * d
        lf_cam = LightFieldCamera(look_from, look_to, look_up,
                                  interspatial_distance,
                                  spatial_rows, spatial_cols)
        lf_cameras.append(lf_cam)
    return lf_cameras

def main(save_main_dir):
    #Setup
    app = inviwopy.app
    network = app.network
    cam = network.EntryExitPoints.camera
    cam.lookTo = vec3(0, 0, 0)
    cam.lookUp = vec3(0, 1, 0)

    if not os.path.isdir(save_main_dir):
        pathlib.Path(save_main_dir).mkdir(parents=True, exist_ok=True)

    #Create a light field camera at the current camera position
    lf_camera_here = LightFieldCamera(cam.lookFrom, cam.lookTo,
                                      interspatial_distance = 0.5)

    #Preview the lf camera array
    random_lfs = create_random_lf_cameras(4, 8)
    for lf in random_lfs:
        lf.view_array(cam)

    #lf_camera_here.view_array(cam)
    """
    #Save the images from the light field camera array
    sub_dir_to_save_to = get_sub_dir_for_saving(save_main_dir)
    try:
        lf_camera_here.view_array(cam, save = True,
                                  save_dir = sub_dir_to_save_to)
    except ValueError as e:
        print(e)
        os.rmdir(sub_dir_to_save_to)
    """

if __name__ == '__main__':
    home = os.path.expanduser('~')
    save_main_dir = os.path.join(home, 'lf_volume_sets','test')
    seed(time())
    main(save_main_dir)