# Elias Posen
# Behaviour based AI system to control a Scribbler
#   robot (interfaced through the Myro library)

from Myro import *
from random import random
from math import *

class Controller(object):

    def __init__(self, configure=False):
        '''Create controller for object-finding robot.'''
        if configure:
            setIRPower(150)
            configureBlob(0, 200, 0, 140, 160, 254)
        else:
            pass
        #Initialize Behaviours
        self.goalStateBehavior = GoalStateReached()
        self.pushBehavior = PylonPush()
        self.avoidBehavior = Avoid()
        self.trackPylonBehavior = TrackPylon()
        self.wanderBehavior = Wander()
        
        # Order implements priority arbitration.
        self.behaviors = [self.goalStateBehavior, self.pushBehavior, self.avoidBehavior, self.trackPylonBehavior,  self.wanderBehavior]

    def arbitrate(self):
        '''Decide which behavior, in order of priority
        has a recommendation for the robot'''
        for behavior in self.behaviors:
            wantToRun = behavior.check()
            if wantToRun:
                behavior.run()
                return # No other behavior runs

    def run(self):
        setForwardness('fluke-forward')
        # This is the simplest loop.  You may like to stop the bot in other ways.
        for seconds in timer(180): # Run for 3 min
            self.arbitrate()
        stop()
        print('LOOP TERMINATED')

####################################################################################################

class Behavior(object):
    '''High level class for all behaviors.  Any behavior is a
    subclass of Behavior.'''
    NO_ACTION = 0
    def __init__(self):
        # Current state of the behavior. Governs how it will respond to percepts.
        self.state = None
    def check(self):
        '''Return True if this behavior wants to execute
        Return False if it does not.'''
        return False
    def run(self):
        '''Execute whatever this behavior does.'''
        return

####################################################################################################

class GoalStateReached(Behavior):
    '''Has the goal state been reached?'''
    #States
    GOAL = 1
    #Important Values
    BLOB_THRESH = 5000 #blob takes up most of the camera's view

    def __init__(self):
        '''Initializer for the Goal State behavior'''
        self.state = GoalStateReached.NO_ACTION

    def check(self):
        '''Checks if the cone is right in front of the robot and if the robot is stalling'''
        num, x, y = getBlob()
        if num > GoalStateReached.BLOB_THRESH and getStall()==1:
           self.state = GoalStateReached.GOAL
           return True
        else:
            self.state = GoalStateReached.NO_ACTION
            return False

    def run(self):
        '''If goal state has been reached, stop pushing and start dancing'''
        print ('goal reached')
        if self.state == GoalStateReached.NO_ACTION:
            motors(1,-1)
            speak("Goal Reached")
            wait(4)
            stop()
        
####################################################################################################

class PylonPush(Behavior):
    '''If the pylon is directly in front of our robot, push it forward, higher priority than avoid'''
    #States
    PUSH_LEFT = 1
    PUSH_RIGHT = 2
    PUSH_STRAIGHT = 3
    #Important values
    BLOB_THRESH = 5000 #Blob takes up most of the camera's view
    IMAGE_WIDTH = 427
    PUSH_SPEED = 0.5
    TSPEED = 0.1
    
    def __init__(self):
        '''Initializer for the Pylon push behavior'''
        self.state = PylonPush.NO_ACTION
        self.lspeed = PylonPush.PUSH_SPEED
        self.rspeed = PylonPush.PUSH_SPEED
    
    def check(self):
        '''Check if pylon is directly in front of robot, and to which side it needs to drive'''
        num, x, y = getBlob()
        if num >= PylonPush.BLOB_THRESH:
            blobLocation = x/PylonPush.IMAGE_WIDTH # Normalizes center of blob in relation to image width
            if blobLocation < 0.35: #Center of blob is on the left side of image
                self.state = PylonPush.PUSH_LEFT
            elif blobLocation > 0.65:#Center of blob is on the right side of image
                self.state = PylonPush.PUSH_RIGHT
            else: #Center of blob is in center of image
                self.state = PylonPush.PUSH_STRAIGHT
            return True
        else:
            self.state = PylonPush.NO_ACTION
            return False

    def run(self):
        '''Push the pylon towards the wall'''
        print ('pushing pylon')
        if self.state == PylonPush.PUSH_LEFT: #Rotate left to get center of blob to be in center of image
            self.rspeed = PylonPush.TSPEED
            self.lspeed = -PylonPush.TSPEED
            print('left')
        elif self.state == PylonPush.PUSH_RIGHT: #Rotate right to get center of blob to be in center of image
            self.rspeed = -PylonPush.TSPEED
            self.lspeed = PylonPush.TSPEED
            print('right')
        elif self.state == PylonPush.PUSH_STRAIGHT: #Push the pylon
            self.rspeed = PylonPush.PUSH_SPEED
            self.lspeed = PylonPush.PUSH_SPEED
            print('straight')
        motors(self.lspeed, self.rspeed)

####################################################################################################

class Avoid(Behavior):
    '''Behavior to avoid obstacles.  Simply turns away.'''
    #States
    TURN_LEFT = 1
    TURN_RIGHT = 2
    #Important values
    BACKUP_SPEED = 0.5
    BACKUP_DUR = 0.4
    OBSTACLE_THRESH = 2000

    def __init__(self):
        '''Initializer for the Avoid behavior'''
        self.state = Avoid.NO_ACTION
        self.turnspeed = 0.5
        self.turndur = 0.9

    def check(self):
        '''See if there are any obstacles'''
        L, C, R = getObstacle()
        #Avoids if robot is stalling or if getObstacle senses an objet
        if ((C+L+R)/3) > Avoid.OBSTACLE_THRESH or getStall() == 1: 
            self.state = Avoid.TURN_LEFT
            return True
        else:
            self.state = Avoid.NO_ACTION
        return False


    def run(self):
        '''See if there are any obstacles.  If so always back up and turn left'''
        print ('Avoid')
        backward(self.BACKUP_SPEED, self.BACKUP_DUR)
        if self.state == Avoid.TURN_LEFT:
            print('turning left')
            turnLeft(self.turnspeed, self.turndur)

####################################################################################################
class TrackPylon(Behavior):
    '''If we have found the pylon in our view, move towards it'''
    #States
    ATTACK_LEFT = 1
    ATTACK_RIGHT = 2
    ATTACK_STRAIGHT = 3
    #Important values
    IMAGE_WIDTH = 427
    BLOB_THRESH = 2000 #Approximately the size of blob from opposite end of arena
    ATTACK_SPEED = 0.5
    TSPEED = 0.1

    def __init__(self):
        '''Initializer for the tracking pylon behavior'''
        self.state = TrackPylon.NO_ACTION
        self.lspeed = TrackPylon.ATTACK_SPEED
        self.rspeed = TrackPylon.ATTACK_SPEED

    def check(self):
        
        '''Check if pylon in robot's view, and if the robot needs to rotate to have it at the center of view'''
        num, x, y = getBlob()
        if num >= TrackPylon.BLOB_THRESH:
            blobLocation = x/TrackPylon.IMAGE_WIDTH #Normalizes center of blob in relation to image width
            if blobLocation < 0.35: #Center of blob in left portion of image
                self.state = TrackPylon.ATTACK_LEFT
            elif blobLocation > 0.65: #Center of blob in right portion of image
                self.state = TrackPylon.ATTACK_RIGHT
            else: #Center of blob in center of image
                self.state = TrackPylon.ATTACK_STRAIGHT
            return True
        else:
            self.state = TrackPylon.NO_ACTION
            return False
    
    def run(self):
        '''If pylon is in view, drive towards it while adjusting for where the blob is on screen'''
        print ('track pylon')
        if self.state == TrackPylon.ATTACK_LEFT: #Rotate left to get center of blob to be in center of image
            print("left")
            self.lspeed = -TrackPylon.TSPEED
            self.rspeed = TrackPylon.TSPEED
        elif self.state == TrackPylon.ATTACK_RIGHT:#Rotate right to get center of blob to be in center of image
            print("right")
            self.lspeed = TrackPylon.TSPEED
            self.rspeed = -TrackPylon.TSPEED
        elif self.state == TrackPylon.ATTACK_STRAIGHT:#Track toward pylon
            print("straight")
            self.lspeed = TrackPylon.ATTACK_SPEED
            self.rspeed = TrackPylon.ATTACK_SPEED
        motors(self.lspeed, self.rspeed)

####################################################################################################
class Wander(Behavior):
    '''Behavior to wander forward. Heads in direction that varies a bit each time it executes.'''
    #States
    WANDER = 1
    #Important values
    OBSTACLE_THRESH = 200
    MAX_SPEED = 1.0
    MIN_SPEED = 0.1
    DSPEED_MAX = 0.1 # most speed can change on one call

    def __init__(self):
        '''Initializer for the Wander behavior'''
        self.state = Wander.NO_ACTION
        self.lspeed = Wander.MAX_SPEED # speed of left motor
        self.rspeed = Wander.MAX_SPEED # speed of right motor

    def check(self):
        '''see if there are any possible obstacles.  If not, then wander.'''
        # XX might want to behave differently if we previously have detected the pylon.
        L, C, R = getObstacle()
        if (L+C+R)/3.0 < Wander.OBSTACLE_THRESH:
            self.state = Wander.WANDER
            return True
        else:
            self.state = Wander.NO_ACTION
            return False

    def run(self):
        '''Modify current motor commands by a value in range [-0.25,0.25].'''
        print ('Wander')
        dl = (2 * random() - 1) * Wander.DSPEED_MAX
        dr = (2 * random() - 1) * Wander.DSPEED_MAX
        self.lspeed = max(Wander.MIN_SPEED,min(Wander.MAX_SPEED,self.lspeed+dl))
        self.rspeed = max(Wander.MIN_SPEED,min(Wander.MAX_SPEED,self.rspeed+dr))
        motors(self.lspeed,self.rspeed)

####################################################################################################

if __name__ == "__main__":
    ctl = Controller(True) #Always configure blob and IR sensors in case a different robot is used
    ctl.run()
