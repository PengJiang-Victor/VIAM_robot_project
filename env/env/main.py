# ---------------------------------------------Lib---------------------------------------------
import asyncio, math
from viam.components.base import Base
from viam.robot.client import RobotClient
from viam.services.slam import SLAMClient

# ---------------------------------------------Key---------------------------------------------
API_KEYID = 'aa407263-ffda-44df-a93e-a96d99499d9e'
API_KEY = 'oyz54e8pbdgs2zrwxv01nfoza2mbrutb'
API_ADDR = 'machine-main.y3r5oijw6x.viam.cloud'
SLAM_SERVICE_NAME = 'slam-1'
BASE = 'viam_base'

# ---------------------------------------------Constant---------------------------------------------
SPIN_VELOCITY=50
GO_VELOCITY=50

# ---------------------------------------------Func---------------------------------------------
async def move_to_position(base, slam_service, target_x, target_y, target_theta, velocity=GO_VELOCITY, step_size=150, tolerance=150):
    while True:
        current_position = await slam_service.get_position()
        current_x = current_position.x
        current_y = current_position.y
        current_theta = current_position.theta

        delta_x = abs(target_x - current_x)
        delta_y = abs(target_y - current_y)
        distance_to_target = math.sqrt(delta_x**2 + delta_y**2)

        target_angle = math.degrees(math.atan2(delta_y, delta_x))
        angle_to_rotate = target_angle - current_theta
        angle_to_rotate = (angle_to_rotate + 180) % 360 - 180
        
        if distance_to_target < tolerance:
            break

        try:
            print(f"Spin {angle_to_rotate} degrees")
            await base.spin(velocity=SPIN_VELOCITY, angle=int(angle_to_rotate))
        except Exception as e:
            print(f"Error: {e} -- Continue.")
            continue

        distance_to_move = min(step_size, distance_to_target)
        print(f"Moving {distance_to_move:.2f}mm")
        await base.move_straight(velocity=int(velocity), distance=int(distance_to_move))

    final_adj = target_theta - current_theta
    final_adj = (final_adj + 180) % 360 - 180
    print(f"final orientation by {final_adj:.2f}")
    await base.spin(velocity=SPIN_VELOCITY, angle=int(final_adj))
    print("Finished.")

async def connect():
    opts = RobotClient.Options.with_api_key(api_key=API_KEY, api_key_id=API_KEYID)
    return await RobotClient.at_address(API_ADDR, opts)

async def move_in_square(base):
    for _ in range(4):
        await base.move_straight(velocity=GO_VELOCITY, distance=500)
        await base.spin(velocity=SPIN_VELOCITY, angle=90)

# ---------------------------------------------Main ---------------------------------------------
async def main():
    # init variables.
    robot = await connect()
    base = Base.from_robot(robot, BASE)
    slam_service = SLAMClient.from_robot(robot, SLAM_SERVICE_NAME)

    # retreive the original position 
    src_pos = await slam_service.get_position()
    
    for i in range(4): 
        await move_in_square(base)
        # sleep for a while to manually move robot  
        await asyncio.sleep(5)
        dst_pos = await slam_service.get_position()
        
        
        if (abs(dst_pos.x - src_pos.x) > 300) or (abs(dst_pos.y - src_pos.y) > 300) or (abs(dst_pos.theta - src_pos.theta) > 3):
            await move_to_position(
                base,
                slam_service,
                target_x=src_pos.x,
                target_y=src_pos.y,
                target_theta=src_pos.theta,
            )
            print(f"src_pos: {src_pos}")
            print(f"dst_pos: {dst_pos}")

    await robot.close()
    
    
# ---------------------------------------------Where everything starts...---------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())