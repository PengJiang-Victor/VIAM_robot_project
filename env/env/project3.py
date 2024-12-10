# ---------------------------------------------Lib---------------------------------------------
import asyncio
import math
from viam.components.base import Base
from viam.robot.client import RobotClient
from viam.services.slam import SLAMClient
from viam.app.data_client import DataClient
from viam.rpc.dial import Credentials, DialOptions
from viam.services.vision import VisionClient
from viam.components.camera import Camera
from viam.components.base import Base
from viam.media.utils.pil import pil_to_viam_image, viam_to_pil_image

# ---------------------------------------------Key---------------------------------------------
API_KEYID = 'aa407263-ffda-44df-a93e-a96d99499d9e'
API_KEY = 'oyz54e8pbdgs2zrwxv01nfoza2mbrutb'
API_ADDR = 'machine-main.y3r5oijw6x.viam.cloud'

# ---------------------------------------------Service---------------------------------------------
SLAM_SERVICE_NAME = 'slam-1'
BASE = 'viam_base'
camera_name = 'cam'

async def connect():
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY, api_key_id=API_KEYID)
    return await RobotClient.at_address(API_ADDR, opts)

def detect_direction_and_size(detections, midpoint):
    largest_area = 0
    largest = None
    for d in detections:
        area = (d.x_max - d.x_min) * (d.y_max - d.y_min)
        if area > largest_area:
            largest_area = area
            largest = d
    if largest is None:
        return -1, 0
    centerX = (largest.x_min + largest.x_max) / 2
    direction = (
        0 if centerX < midpoint - midpoint / 3 else
        2 if centerX > midpoint + midpoint / 3 else
        1
    )
    return direction, largest_area


async def avoid_obstacle(base, obstacle_direction, spinNum, straightNum, vel):
    print(f"Avoiding obstacle on the {'left' if obstacle_direction == 0 else 'right' if obstacle_direction == 2 else 'center'}...")
    # left -> go right
    if obstacle_direction == 0:  
        await base.spin(-spinNum, vel)
        await base.move_straight(straightNum, vel)
        # realign 
        await base.spin(spinNum, vel)
    # right -> go left
    elif obstacle_direction == 2:
        await base.spin(spinNum, vel)
        await base.move_straight(straightNum, vel)
        await base.spin(-spinNum, vel)
    else:  # center
        await base.spin(spinNum, vel)
        await base.move_straight(straightNum, vel)
        await base.spin(-spinNum, vel)

# ---------------------------------------------main---------------------------------------------
async def main():
    robot = await connect()
    base = Base.from_robot(robot, BASE)
    camera = Camera.from_robot(robot, camera_name)
    frame = await camera.get_image(mime_type="image/jpeg")

    detectors = [
        VisionClient.from_robot(robot, "red"),
        VisionClient.from_robot(robot, "blue"),
        VisionClient.from_robot(robot, "violet"),
        VisionClient.from_robot(robot, "yellow"),
        VisionClient.from_robot(robot, "green"),
    ]
    COLOR_OPTIONS = ['red', 'blue', 'violet', 'yellow', 'green']

    # parse 
    print(f"Available colors: {', '.join(COLOR_OPTIONS)}")
    target_colors = input("Enter three target colors (comma-separated): ").strip().split(',')
    obstacle_colors = input("Enter two obstacle colors (comma-separated): ").strip().split(',')

    if len(target_colors) != 3 or len(obstacle_colors) != 2:
        print("Error: Please enter exactly three target colors and two obstacle colors.")
        return
    if not all(color in COLOR_OPTIONS for color in target_colors + obstacle_colors):
        print("Error: Invalid color(s) provided. Please use the available colors.")
        return

    # fine tune val
    TARGET_SIZE_THRESHOLD = 0.5
    spinNum = 8
    spinNum_find = 20
    spinNum_bizhang = 45
    straightNum = 100
    straightNum_bizhang = 300
    vel = 70

    # Map colors to their detectors
    detector_map = {color: detector for color, detector in zip(COLOR_OPTIONS, detectors)}

    for target_color in target_colors:
        print(f"Tracking {target_color}...")
        reached_target = False
        while not reached_target:
            frame = await camera.get_image(mime_type="image/jpeg")
            pil_frame = viam_to_pil_image(frame)
            target_detector = detector_map[target_color]
            target_detections = await target_detector.get_detections_from_camera(camera_name)

            obstacle_detections = []
            obstacle_color_detected = []
            
            for obstacle_color in obstacle_colors:
                obstacle_color_detected = []
                obstacle_detector = detector_map[obstacle_color]
                obstacle_detections += await obstacle_detector.get_detections_from_camera(camera_name)

            if obstacle_detections:
                for color in obstacle_color_detected: 
                    print('color: ' + color + "\n")
                obstacle_direction, _ = detect_direction_and_size(obstacle_detections, pil_frame.size[0] / 2)
                await avoid_obstacle(base, obstacle_direction, spinNum_bizhang, straightNum_bizhang, vel)
                continue

            direction, size = detect_direction_and_size(target_detections, pil_frame.size[0] / 2)
            if direction == -1:
                print("Target not detected, searching...")
                await base.spin(spinNum_find, vel)
            elif size / (pil_frame.size[0] * pil_frame.size[1]) >= TARGET_SIZE_THRESHOLD:
                print(f"Reached {target_color}!")
                reached_target = True
            else:
                if direction == 0:
                    print("Moving left...")
                    await base.spin(spinNum, vel)
                elif direction == 1:
                    print("Moving forward...")
                    await base.move_straight(straightNum, vel)
                elif direction == 2:
                    print("Moving right...")
                    await base.spin(-spinNum, vel)

    print("Completed all targets!")
    await robot.close()

if __name__ == "__main__":
    asyncio.run(main())