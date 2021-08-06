#!/usr/bin/env python
from __future__ import print_function

from FPS import *
from ImageConverter import *
from ExtraFunctions import *

import os
# 0 for GPU, -1 for CPU
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import sys
import rospy
import cv2

from mask_rcnn_ros.msg import Bbox_values

from Mask_RCNN.scripts.visualize_cv2 import model, display_instances, class_names
from tensorflow.python.client import device_lib
import numpy as np

import threading

def main(args):
  
  print(device_lib.list_local_devices())
  rospy.init_node('drone_detector')
  ic = ImageConverter()
  fps = FPS()
  fps1 = FPS()
  fps2 = FPS()
  fps3 = FPS()
  fps4 = FPS()
  # extra = ExtraFunctions(cropped_path = "/home/dylan/Videos/image_train/")
  
  while not rospy.is_shutdown():

    rospy.loginfo("\n\nMain Thread ID %s\n", threading.current_thread())

    if ic.cv_img is not None:

      fps.start()
      results = model.detect([ic.cv_img], verbose=1)
      fps.stop()
      print(f"Time taken to detect: {fps.elapsed()} ms")

      fps1.start()
      # Visualize results
      r = results[0]
      masked_image = display_instances(ic.cv_img, r['rois'], r['masks'], r['class_ids'], class_names, r['scores'])
      cv2.putText(masked_image, f"FPS: {fps.getFPS():.2f}", (7,40), cv2.FONT_HERSHEY_COMPLEX, 1.4, (100, 255, 0), 3, cv2.LINE_AA)
      fps1.stop()
      print(f"Time taken to display instances: {fps1.elapsed()} ms")

      # publish bbox values when they are available
      # bbox values are in y1,x1,y2,x2
      # have to reformat to x,y,w,h
      fps2.start()
      if len(r['rois']):
        # To publish to rostopic
        bbox_str = np.array_str(r['rois'][0])
        bbox_ls = bbox_str[1:-1].strip().replace("   ", " ").replace("  ", " ").split(" ")
        bbox = Bbox_values()
        bbox.x = int(bbox_ls[1])
        bbox.y = int(bbox_ls[0])
        bbox.w = int(bbox_ls[3]) - int(bbox_ls[1])
        bbox.h = int(bbox_ls[2]) - int(bbox_ls[0])
        ic.image_pub.publish(bbox)
        
        # # For saving cropped images
        # extra.update()
        # extra.crop_objects(ic.cv_img, r['rois'])
      fps2.stop()
      print(f"Time taken to publish on ROS: {fps2.elapsed()} ms")

      fps3.start()
      cv2.imshow("Masked Image", masked_image)
      fps3.stop()
      print(f"Time taken for imshow: {fps3.elapsed()} ms")

    fps4.start()
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
    fps4.stop()
    print(f"Time taken for waitKey: {fps4.elapsed()} ms")

  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)