import asyncio, math
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.camera import Camera
from viam.components.board import Board
from viam.components.motor import Motor
from viam.components.base import Base
from viam.components.encoder import Encoder
from viam.components.movement_sensor import MovementSensor
from viam.services.slam import SLAMClient

API_KEYID = 'aa407263-ffda-44df-a93e-a96d99499d9e'
API_KEY = 'oyz54e8pbdgs2zrwxv01nfoza2mbrutb'
API_ADDR = 'machine-main.y3r5oijw6x.viam.cloud'
SLAM_SERVICE_NAME = 'slam-1'
BASE = 'viam_base'
g_camera_name = 'cam'

async def connect():
    opts = RobotClient.Options.with_api_key( 
        api_key=API_KEY,
        api_key_id=API_KEYID
    )
    return await RobotClient.at_address(API_ADDR, opts)

async def gotoPosition(base, slam_service, target_x, target_y):
    # Get current position
    current_pose = await slam_service.get_position()
    dx = target_x - current_pose.x
    dy = target_y - current_pose.y
    distance = math.sqrt(dx**2 + dy**2)

    target_angle = math.degrees(math.atan2(dy, dx))
    current_angle = math.degrees(math.atan2(current_pose.o_y, current_pose.o_x))

    # Calculate rotation needed
    angle_to_rotate = target_angle - current_angle
    angle_to_rotate = (angle_to_rotate + 180) % 360 - 180  # Normalize angle

    await base.spin(angle=int(angle_to_rotate), velocity=30)  # Rotate to the target angle
    await base.move_straight(distance=int(distance), velocity=100)  # Move to the target position
    print(f"Moved to target position: ({target_x}, {target_y})")

async def main():
    robot = await connect()
    slam = SLAMClient.from_robot(robot, SLAM_SERVICE_NAME)
    base = Base.from_robot(robot, BASE)

    current_pose = await slam.get_position()
    print(current_pose.x,current_pose.y)
    await base.move_straight(100,100)
    ps = await slam.get_position()
    print (ps.x,ps.y)
    # Define four corners of a square in millimeters
    current_pose = await slam.get_position()
    initial_x=current_pose.x
    initial_y = current_pose.y
    square_corners = [
        (initial_x, initial_y),       # Origin
        (initial_x+500, initial_y),    # 1 meter to the right
        (initial_x+500, initial_y+500), # 1 meter up
        (initial_x, initial_y+500)     # Back to line with origin
    ]

    for x, y in square_corners:
        await gotoPosition(base, slam, x, y)  # Move to each corner
        await asyncio.sleep(1)  # Wait for a bit at each corner

    await robot.close()

if __name__ == '__main__':
    asyncio.run(main())