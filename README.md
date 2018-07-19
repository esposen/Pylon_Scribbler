# Behaviour Based Scribbler AI Project

### Goal
- Wander around the "Play Space" looking for orange pylon.
- Once robot locates pylon, push it against a wall.
- Indicate when robot thinks task goal has been obtained.

### Implementation
- The AI control scheme used in this project was a behaviour based model with priority arbitration.
- The [Sribbler2][1] was the robot used in this project. [Calico][2] was the IDE used (built to facilitate easy interaction with the Sribbler) and the robot was communicated with through the [Myro][3] library.
- **Behaviours:**
    -Each behaviour has a ```check()``` and a ```run()```. In each loop of the controller's ```arbitrate()``` function, the list of behaviours is checked and---according the return of ```check()```---a certain behaviour takes control of the robot.
-List of behaviours (highest to lowest priority):
    - Goal State Reached
    - Push Pylon
    - Avoid Obsatcle
    - Track Toward Pylon
    - Wander

## Evaluation
**Ability:**
This implementation was very sucessful. Prior to each test configurations had to be made concerning the thresholds for the pylon's orange colour according to the amount of light in the room. The scribbler was able to find the pylon and push it against a wall in each test. In addition, the AI was also able to identify when the task was done and completed a vicotry dance.
Sucess decreased when other robots with the same goal entered the playspace. Issues included:
- Difficulty in avoiding moving objects.
- Identifying the pylon amoungst the red robots.
- Loosing track of the pylon and starting to randomly search (wander) in the wrong direction.

**Improvements:**
The controller can be improved in a number of ways. The issue of crashing into other robots could be tackled by slowing down the robot's movement, however, this would also slow the progression of the robot to the goal state and may allow other robots to beat it. Having a smaller threshold for the color "orange" would fix the issue of identifying the pylon amoungst other robots, however this may cause the robot to not recognize the pylon at all. Running the tests in a room with more flat light, or spray painting the robots another color would perhaps be more effective. Finally, implementing *memory* into the control scheme where the robot could remember if it saw the pylon recently and thus initiate a specialized wander behaviour focused on searching the immediate area. 


[1]: https://www.parallax.com/product/28136
[2]: https://www.hummingbirdkit.com/learning/software/calico
[3]: http://wiki.roboteducation.org/Calico_Myro