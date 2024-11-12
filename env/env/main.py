import asyncio, math
from viam.components.base import Base
from viam.robot.client import RobotClient
from viam.services.slam import SLAMClient

API_KEYID = 'aa407263-ffda-44df-a93e-a96d99499d9e'
API_KEY = 'oyz54e8pbdgs2zrwxv01nfoza2mbrutb'
API_ADDR = 'machine-main.y3r5oijw6x.viam.cloud'
SLAM_SERVICE_NAME = 'slam-1'
BASE = 'viam_base'

async def move_to_position(base, slam_service, target_x, target_y, target_theta, velocity=500):
    # Get the current position
    current_position = await slam_service.get_position()
    current_x = current_position.x
    current_y = current_position.y
    current_theta = current_position.theta

    # Calculate the distance and angle to the target position
    delta_x = target_x - current_x
    delta_y = target_y - current_y

    # Distance to the target
    distance = math.sqrt(delta_x**2 + delta_y**2)

    # Angle to the target relative to the current orientation
    target_angle = math.degrees(math.atan2(delta_y, delta_x))  # Angle to target in degrees
    angle_to_rotate = target_angle - current_theta

    # Normalize the angle to [-180, 180]
    angle_to_rotate = (angle_to_rotate + 180) % 360 - 180

    # Step 1: Rotate to face the target
    print(f"Rotating by {angle_to_rotate:.2f} degrees to face the target...")
    await base.spin(velocity=100, angle=int(-angle_to_rotate))  # Ensure angle is an integer

    # Step 2: Move straight to the target position
    print(f"Moving straight for {distance:.2f}mm to the target...")
    await base.move_straight(velocity=int(velocity), distance=int(distance))  # Convert both to integers

    # Step 3: Adjust orientation to match the target theta
    final_yaw_adjustment = target_theta - (current_theta + angle_to_rotate)
    final_yaw_adjustment = (final_yaw_adjustment + 180) % 360 - 180
    print(f"Adjusting final orientation by {final_yaw_adjustment:.2f} degrees...")
    await base.spin(velocity=100, angle=int(final_yaw_adjustment))  # Ensure angle is an integer

    print("Reached the target position.")

async def connect():
    opts = RobotClient.Options.with_api_key(api_key=API_KEY, api_key_id=API_KEYID)
    return await RobotClient.at_address(API_ADDR, opts)

async def move_in_square(base):
    for _ in range(4):
        await base.move_straight(velocity=500, distance=500)
        await base.spin(velocity=500, angle=90)


async def main():
    robot = await connect()
    base = Base.from_robot(robot, BASE)
    slam_service = SLAMClient.from_robot(robot, SLAM_SERVICE_NAME)
    
    #get the initial angle
    current_position = await slam_service.get_position()
    current_theta = current_position.theta
    print(current_theta)

    # Record the original position
    original_position = await slam_service.get_position()

    # Move in a square
    print("Moving in a square...")
    while True: 
        await move_in_square(base)

    # Simulate manual movement or delay
    print("Pausing for manual movement...")
    await asyncio.sleep(5)

    # Return to the original position
    print("Returning to the original position...")
    await move_to_position(
        base,
        slam_service,
        target_x=original_position.x,
        target_y=original_position.y,
        target_theta=original_position.theta,
    )

    # Resume moving in a square
    print("Resuming square movement...")

    # Close the robot connection
    await robot.close()
if __name__ == "__main__":
    asyncio.run(main())
