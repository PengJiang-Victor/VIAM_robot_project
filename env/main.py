import asyncio

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.services.vision import VisionClient
from viam.components.camera import Camera
from viam.components.base import Base
from viam.media.utils.pil import pil_to_viam_image, viam_to_pil_image

API_id = 'aea32b7d-9ccf-40ff-ad55-4f0197188740'
API_key = 'm0yj8zxlz1capzwpl3krseb0azozn0y7'
API_addr = 'rover-lalala-main.y3r5oijw6x.viam.cloud' 
g_camera_name = 'cam'
g_my_base = 'viam_base'
g_color_detector = 'vision-1'
 
async def connect():
    opts = RobotClient.Options.with_api_key(
        # Replace "<API-KEY>" (including brackets) with your machine's API key
        api_key=API_key,
        # Replace "<API-KEY-ID>" (including brackets) with your machine's
        # API key ID
        api_key_id=API_id
    )
    return await RobotClient.at_address(API_addr, opts)


# Get largest detection box and see if it's center is in the left, center, or
# right third
def leftOrRight(detections, midpoint):
    largest_area = 0
    largest = {"x_max": 0, "x_min": 0, "y_max": 0, "y_min": 0}
    if not detections:
        print("nothing detected :(")
        return -1
    for d in detections:
        a = (d.x_max - d.x_min) * (d.y_max-d.y_min)
        if a > largest_area:
            a = largest_area
            largest = d
    centerX = largest.x_min + largest.x_max/2
    if centerX < midpoint-midpoint/6:
        return 0  # on the left
    if centerX > midpoint+midpoint/6:
        return 2  # on the right
    else:
        return 1  # basically centered

async def base_search(base, vel, spinNum, my_detector, camera_name):
    for _ in range(6):
        await base.spin(spinNum, vel)
        await asyncio.sleep(1)
        detections = await my_detector.get_detections_from_camera(camera_name)
        if detections:
            return detections
            
    return None

async def main():
    spinNum = 10         # when turning, spin the motor this much
    straightNum = 300    # when going straight, spin motor this much
    numCycles = 200      # run the loop X times
    vel = 500            # go this fast when moving motor

    memory_direction = None
    count = 0

    # Connect to robot client and set up components
    machine = await connect()
    base = Base.from_robot(machine, g_my_base)
    camera_name = g_camera_name
    camera = Camera.from_robot(machine, g_camera_name)
    frame = await camera.get_image(mime_type="image/jpeg")

    # Convert to PIL Image
    pil_frame = viam_to_pil_image(frame)

    # Grab the vision service for the detector
    my_detector = VisionClient.from_robot(machine, g_color_detector)

    # Main loop. Detect the ball, determine if it's on the left or right, and
    # head that way. Repeat this for numCycles
    for i in range(numCycles):
        detections = await my_detector.get_detections_from_camera(camera_name)

        if detections:
            answer = leftOrRight(detections, pil_frame.size[0]/2)
            memory_direction = answer
            count = 0

            if answer == 0:
                print("left")
                await base.spin(spinNum, vel)     # CCW is positive
                await base.move_straight(straightNum, vel)
            if answer == 1:
                print("center")
                await base.move_straight(straightNum, vel)
            if answer == 2:
                print("right")
                await base.spin(-spinNum, vel)
        # If nothing is detected, nothing moves
        else:
            cycles = 3
            if count < cycles and memory_direction is not None:
                if memory_direction == 0:
                    await base.spin(spinNum, vel)
                elif memory_direction == 1:
                    await base.move_straight(straightNum, vel)
                elif memory_direction == 2:
                    await base.spin(-spinNum, vel)
                count += 1
            else:
                detections = await base_search(base, vel, spinNum, my_detector, camera_name)
                if detections:
                    answer = leftOrRight(detections, pil_frame.size[0] / 2)
                    memory_direction = answer

    await machine.close()

if __name__ == "__main__":
    print("Starting up... ")
    asyncio.run(main())
    print("Done.")