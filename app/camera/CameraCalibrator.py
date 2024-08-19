import numpy as np
import cv2
import glob
from pymavlink import mavutil
import pickle
import time

class CameraCalibrator:
    def __init__(self, chessboard_size = (7, 7), base_dir = 'calibration_imgs', path = '*.jpg', path_test = '2024-06-08_10-50-07.jpg') -> None:
        self.chessboard_size = chessboard_size

        self.objpoints = []  # 3D points in real world space
        self.imgpoints = []  # 2D points in image plane

        self.base_dir = base_dir
        self.images_path = base_dir + '/' + path
        self.path_test =   base_dir + '/' + path_test


    def calibrate(self):
        # Prepare object points (0,0,0), (1,0,0), (2,0,0), ..., (7,5,0)
        objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)

        # List of calibration images
        images = glob.glob(self.images_path)

        # Iterate through the list and search for chessboard corners
        for fname in images:
            self.find_chessboard_intersections(fname, objp)
    

        # Load a test image
        img = cv2.imread(self.path_test)
        img_size = (img.shape[1], img.shape[0])

        # Camera calibration
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(self.objpoints, self.imgpoints, img_size, None, None)

        # Undistort a test image and save the result
        dst = cv2.undistort(img, mtx, dist, None, mtx)
        cv2.imwrite(f"{self.base_dir}/test_undist.jpg", dst)

        # Save calibration results for future use
        dist_pickle = {"mtx": mtx, "dist": dist}
        with open(f"{self.base_dir}/wide_dist_pickle.p", "wb") as f:
            pickle.dump(dist_pickle, f)

        # Step 2: ArUco Detection and Precision Landing

        # Load calibration results
        with open(f"{self.base_dir}/wide_dist_pickle.p", "rb") as f:
            calib_data = pickle.load(f)

        camera_matrix = calib_data["mtx"]
        dist_coeffs = calib_data["dist"]

        return camera_matrix, dist_coeffs

    def find_chessboard_intersections(self, fname: str, objp, show = False):
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        # If found, add object points and image points
        if ret:
            self.objpoints.append(objp)
            self.imgpoints.append(corners)
            print('Calibrando imagem...')

            if show:
                cv2.drawChessboardCorners(img, self.chessboard_size, corners, ret)
                cv2.imshow('img', img)
                cv2.waitKey(500)

        if show:
            cv2.destroyAllWindows()


