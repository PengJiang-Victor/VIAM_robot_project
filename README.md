# viam-robot logs

## Proj1
*Does not take much time...*

## Proj2 

### target
1. Generate a map, so Lidar know the direction and position clearly 
2. Choose shape like sqaure, circle 
3. come out with a turn around and move function (input: theta? s_x, s_y, d_x, d_y) 
4. Go back to the original position and 

### Step1: map creation 

Some things to remember: 
1. remember to install fuse2 / restart the viam-agent very often before you draw the map
2. turn on cloudpoint mapping and check other config as well. 
3. you can briefly check if the mapping is correct in slam algorithm component that you created.

### easy access to the timestamp
2024/11/12 13:14:30:AM
-
2024/11/12 13:18:30:AM


### Step2: run algorithm 
We design an algorithm that take steps to move a little angle and direction towards the position returned back by get_position, until we reach a limit theta. 

It will reach back its original position and start a new route. 

## Proj3: Given a simple maze, find a way out 

### Target 
* generate a map. Get position of the end point