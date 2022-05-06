import os.path
import socket
import time
import logging
import json

#Log Configuration
logging.basicConfig(filename = "~/.pf400_logs/robot_client_logs.log", level=logging.DEBUG, format = '[%(levelname)s] [%(asctime)s] [%(name)s] %(message)s', datefmt = '%Y-%m-%d %H:%M:%S')

class PF400(object):
    """
    Description: 
                 - Python interface that allows remote commands to be executed using simple string messages over TCP/IP on PF400 cobot. 
                 - Arm_Robot is the main object that will be used for operations such as remote connection as well as sending movement commands.
                 - Programs are sent to the 10x000 port (first robot port: 101000). 
                 - A program sent to robot will be executed immediately unless there is a prior operation running on the robot. 
                 - If a second motion command is sent while the referenced robot is moving, the second command is blocked and will not reply until the first motion is complete.
                 - Blended motion tolerance can be adjusted in the motion profile

    Serial Communication Messages from the Robot:
                 - Responses begin with a "0" if the command was successful, or a negative error code number

    """
    def __init__(self):
        self.logger = logging.getLogger("PF400_Client")
        self.logger.addHandler(logging.StreamHandler())
        
        robot1, motion_profile, locations = self.load_robot_data()
        self.ID = robot1["ID"]
        self.host = robot1["Host"]
        self.port = robot1["Port"]
       
        
        # Default Motion Profile Paramiters. Using two profiles for faster and slower movements
        self.motion_profile = motion_profile
        # TODO: Use second motion prfile for slower movements 

        # Predefined locations for plate transferring oparetions
        self.location_dictionary = locations

        self.logger.info("Robot created. Robot ID: {} ~ Host: {} ~ Port: {}".format(self.ID, self.host, self.port))
    
    def load_robot_data(self):
        # Setting parent file directory 
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.split(current_directory)[0] 
        file_path = os.path.join(parent_directory + '/utils/robot_data.json')

        # load json file
        with open(file_path) as f:
            data = json.load(f)

        f.close()

        return data["Robot_Data"][0], data["Robot_Data"][0]["motion_profile"],data["Robot_Data"][0]["locations"][0]


    #Connect the socket object to the robot
    def connect_robot(self):    
        #create an INET, Streaming socket (IPv4, TCP/IP)
        try:
            PF400 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  

        except socket.error:
            self.logger.error('Failed to create socket')

        else:
            PF400.connect((self.host,self.port))
            # self.logger.info('Socket Created')
            return PF400     

        #self.logger.info('Socket Connected to ' + self.host + " Port:", self.port )
        #TODO:Read the status of the robot 


    def disconnect_robot(self, PF400):
        PF400.close()
        # self.logger.info("TCP/IP client is closed")

    def send_command(self, command_name):

        PF400_sock = self.connect_robot()
        try:
            PF400_sock.send(bytes(command_name.encode('ascii')))
            output_msg = PF400_sock.recv(4096).decode("utf-8")
            
            # TODO: Remove the below info logger once each function has the capability to process the output message
            self.logger.info(output_msg)
            
            self.logger.info("New command sent to the robot {}".format(command_name))

        PF400_sock = self.connect_robot()
        try:
            if log_msg:
                self.logger.info(log_msg)
            PF400_sock.send(bytes(cmd.encode('ascii')))
            robot_state = PF400.recv(4096).decode("utf-8")
            self.logger.info(robot_state)
        except socket.error as err:

            self.logger.error('Failed to send the command [{}]! ERROR: {}'.format(command_name, err))
        else:
            self.disconnect_robot(PF400_sock)
            return output_msg

    def enable_power(self):

        #Send cmd to Activate the robot
        command_name = 'hp 1\n'
        output_msg = self.send_command(command_name)

        if output_msg == "0":
            self.logger.info("Power enabled")
        else:
            self.logger.info("Error occurred while enabling power. Error code: {}".format(output_msg))


       


    def attach_robot(self):

        cmd = 'attach 1\n'
        ini_msg = "Attaching the robot"
        err_msg = 'Failed to attach the robot:'

        self.send_command(cmd, ini_msg, err_msg)

        
    def home_robot(self):

        cmd = 'home\n'
        ini_msg = 'Homing the robot'
        err_msg = 'Failed to home the robot: '

        self.send_command(cmd, ini_msg, err_msg)

    
    def initialize_robot(self):
        
        # Enable power 
        self.enable_power()
        time.sleep(5)
        # Attach robot
        self.attach_robot()
        time.sleep(5)

        # Home robot
        self.home_robot()
        time.sleep(15)

        # Set default motion profile
        self.set_profile()
        time.sleep(5)

        self.check_robot_state()

        self.logger.info("Robot initialization is successfully completed!")

        
    ##create "profile section" apart from the "command section"
    def set_profile(self, profile_dict = {"0":0}):

        if len(profile_dict) == 1:
           
            self.logger.info("Setting defult values to the motion profile 1 and 2")

            PF400 = self.connect_robot()
            command = 'Profile 1'
            for key, value in self.motion_profile[0].items():
                command += ' ' + str(value)
            command += '\n'
            
            try:
                PF400.send(bytes(command.encode('ascii')))
                robot_state = PF400.recv(4096).decode("utf-8")
                self.logger.info(robot_state)

            except socket.error as err:
                self.logger.error('Failed to set motion profile 1: {}'.format(err))

            else:
                self.disconnect_robot(PF400)  

            PF400 = self.connect_robot()
            command = 'Profile 2'
            for key, value in self.motion_profile[1].items():
                command += ' ' + str(value)
            command += '\n'
            
            try:
                PF400.send(bytes(command.encode('ascii')))
                robot_state = PF400.recv(4096).decode("utf-8")
                self.logger.info(robot_state)

            except socket.error as err:
                self.logger.error('Failed to set motion profile 2: {}'.format(err))

            else:
                self.disconnect_robot(PF400)  

        elif len(profile_dict) == 8:

            self.logger.info("Setting new values to the motion profile 1")

            PF400 = self.connect_robot()
            command = 'Profile 3'
            for key, value in profile_dict.items():
                command += ' ' + str(value)
            command += '\n'
            
            try:
                PF400.send(bytes(command.encode('ascii')))
                robot_state = PF400.recv(4096).decode("utf-8")
                self.logger.info(robot_state)

            except socket.error as err:
                self.logger.error('Failed to set motion profile: {}'.format(err))

            else:
                self.disconnect_robot(PF400)  
        
        else:
            raise Exception("Motion profile takes 8 arguments, {} where given".format(len(profile_dict)))


    
    def set_motion_blend_tolerance(self, tolerance: int = 0):
        """
        Description: Gets or sets the InRange property of the selected profile, which is a parameter to set tolorance between blended motions.
        
        Paramiters
                tolerance:  from -1 to 100
                            -1 means do not stop at the end of motion if blending is possible.  
                            0 means always stop but do not check the end point error.  
                            > 0 means wait until close to the end point.  
                            Larger numbers mean less position error is allowed.
        """
        pass

    def check_robot_heartbeat(self):

        PF400 = self.connect_robot()

        command = 'nop\n'
        try:
            PF400.send(bytes(command.encode('ascii')))
            out_msg = PF400.recv(4096).decode("utf-8")
            self.logger.info(out_msg)

            if out_msg != None:
                self.logger.info("Robot is alive")
            else:
                self.logger.warning("Lost robot heartbeat")

        except socket.error as err:
            self.logger.error('Failed to check robot heartbeat: {}'.format(err))
        else:
            self.disconnect_robot(PF400)  

    def stop_robot(self):
        """
        Stops the robot immediately but leaves power on.
        """

        PF400 = self.connect_robot()

        command = 'halt\n'
        try:
            PF400.send(bytes(command.encode('ascii')))
            out = PF400.recv(4096).decode("utf-8")
            self.logger.info(out)

        except socket.error as err:
            self.logger.error('Failed to stop robot : {}'.format(err))

        else:
            self.disconnect_robot(PF400)  

    def wait_before_next_move(self):
        """
        If you want to wait for the robot to stop moving, issue a waitForEom command
        """
        pass

    def clear_programs(self):
        #TODO: CLEAR ROBOT MEMORY BEFORE STARTING A PROGRAM TO MAKE SURE THERE IS NO QUEUED PROGRAMS FROM PREVIOUS EXECUTION
        pass

    def set_move_command(self, robot_location, profile, grab: bool = False, release: bool = False):
        # TODO: FIND THE 5th JOINT VALUE FOR WHEN THE GRABBER IS CLOSE AND OPEN
        if profile == 1:
            robot_command = "MoveJ 1" 

        elif profile == 2:
            robot_command = "MoveJ 2" 

        elif profile == 3:    
            robot_command = "MoveJ 3" 

        else:
            raise Exception("Please enter a valid motion profiile! 1 for slower movement, 2 for faster movement profile, 3 for modified profile")
       
        for count, location in enumerate(self.location_dictionary[robot_location]):
            if grab == True and count == 4:
                robot_command += " " + str(120.0)
            elif release == True and count == 4:
                robot_command += " " + str(127.0)
            else:    
                robot_command += " " + str(location) 
        robot_command += '\n'
        
        return robot_command

    def pick_plate_ot2(self, ot2_ID , profile = 0):
        
        # TODO:ADD Motion profile index
        
        if profile == 3: 
            slow, fast = 3, 3
        else:
            slow, fast = 1, 2
            

        # self.logger.info("Setting defult values to the motion profile")

        # Set movement commands to complete a pick_plate_ot2 operation
        move_front = self.set_move_command("OT2_" + str(ot2_ID) + "_front",fast)
        above_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_above_plate",fast)
        approach_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_pick_plate",fast)
        pick_up_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_pick_plate", slow, True, False)
        above_with_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_above_plate", slow, True, False)
        front_with_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_front", slow, True, False)

        pick_up_commands = [move_front, above_plate] ......
        for count, command in enumerate(pick_up_commands):
            # time.sleep(1)
            PF400 = self.connect_robot()
            try:
                PF400.send(bytes(command.encode('ascii')))
                out_msg = PF400.recv(4096).decode("utf-8")
                self.logger.info(out_msg)

                # TODO: CHECK FOR ERROR RETURN FORM ROBOT FIRST 
                self.logger.info("[pick_plate_ot2 ID:{}] Robot is moved to the {}th location".format(str(ot2_ID), count+1))

            except socket.error as err:
                self.logger.error('Failed move the robot {}'.format(err))
            else:
                self.disconnect_robot(PF400)  


    def drop_plate_ot2(self, ot2_ID, profile = 0):

        # Set movement commands to complete a drop_plate_ot2 operation
        if profile == 3: 
            slow, fast = 3, 3
        else:
            slow, fast = 1, 2
            

        front_with_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_front", slow, True, False)
        above_with_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_above_plate", slow, True, False)
        approach_with_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_pick_plate", slow, True, False)
        drop_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_pick_plate", slow, False, True)
        above_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_above_plate", fast)
        front_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_front", fast)


        drop_commands = [front_with_plate, above_with_plate, approach_with_plate, drop_plate, above_plate, front_plate]

        for count, command in enumerate(drop_commands):
            # time.sleep(1)

            PF400 = self.connect_robot()
            try:
                PF400.send(bytes(command.encode('ascii')))
                out_msg = PF400.recv(4096).decode("utf-8")
                self.logger.info(out_msg)

                # TODO: CHECK FOR ERROR RETURN FORM ROBOT FIRST 
                self.logger.info("[pick_plate_ot2 ID:{}] Robot is moved to the {}th location".format(str(ot2_ID), count+1))

            except socket.error as err:
                self.logger.error('Failed move the robot {}'.format(err))
            else:
                self.disconnect_robot(PF400)  
                
    def pick_plate_from_rack(self, ot2_ID, profile = 0):
        
        if profile == 3: 
            slow, fast = 3, 3
        else:
            slow, fast = 1, 2

        approach_plate_rack = self.set_move_command("OT2_" + str(ot2_ID) + "_approach_plate_rack", fast, False, False)
        front_rack = self.set_move_command("OT2_" + str(ot2_ID) + "_front_plate_rack", slow, False, False)
        plate_rack = self.set_move_command("OT2_" + str(ot2_ID) + "_plate_rack", slow, False, False)
        pick_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_plate_rack", slow, True, False)
        front_with_plate = self.set_move_command("OT2_" + str(ot2_ID) + "_front_plate_rack", slow, True, False)
        approach_rack_back = self.set_move_command("OT2_" + str(ot2_ID) + "_approach_plate_rack", slow, True, False)
       


        drop_commands = [approach_plate_rack, front_rack, plate_rack, pick_plate, front_with_plate, approach_rack_back]

        for count, command in enumerate(drop_commands):
            # time.sleep(1)

            PF400 = self.connect_robot()
            try:
                PF400.send(bytes(command.encode('ascii')))
                out_msg = PF400.recv(4096).decode("utf-8")
                self.logger.info(out_msg)

                # TODO: CHECK FOR ERROR RETURN FORM ROBOT FIRST 
                self.logger.info("[pick_plate_from_rack ID:{}] Robot is moved to the {}th location".format(str(ot2_ID), count+1))

            except socket.error as err:
                self.logger.error('Failed move the robot {}'.format(err))
            else:
                self.disconnect_robot(PF400)  

    def drop_complete_plate(self, profile = 0):
        
        if profile == 3: 
            slow = 3
            fast = 3
        else:
            slow = 1
            fast = 2 

        completed_plate_above = self.set_move_command("Completed_plate_above", slow, True, False)
        drop_with_plate = self.set_move_command("Completed_plate", slow, True, False)
        drop_plate = self.set_move_command("Completed_plate", slow, False, True)
        completed_plate = self.set_move_command("Completed_plate_above", slow, False, False)
       

        drop_commands = [completed_plate_above, drop_with_plate, drop_plate, completed_plate]

        for count, command in enumerate(drop_commands):
            # time.sleep(1)

            PF400 = self.connect_robot()
            try:
                PF400.send(bytes(command.encode('ascii')))
                out_msg = PF400.recv(4096).decode("utf-8")
                self.logger.info(out_msg)

                # TODO: CHECK FOR ERROR RETURN FORM ROBOT FIRST 
                self.logger.info("[drop_complete_plate] Robot is moved to the {}th location".format(count+1))

            except socket.error as err:
                self.logger.error('Failed move the robot {}'.format(err))
            else:
                self.disconnect_robot(PF400)  


    def move_single(self, target_location, profile = 0, grap: bool = False, release: bool = False):

        """
            Executes only one movement to the target location which is from the location dictionary
        """
        PF400 = self.connect_robot()       
        command = self.set_move_command(target_location, profile, grap, release)


        try:
            PF400.send(bytes(command.encode('ascii')))
            out_msg = PF400.recv(4096).decode("utf-8")
            self.logger.info(out_msg)

            # TODO: CHECK FOR ERROR RETURN FORM ROBOT FIRST 
            self.logger.info("Robot is moved to the {} location".format(target_location))

        except socket.error as err:
            self.logger.error('Failed move the robot {}'.format(err))
        else:
            self.disconnect_robot(PF400)  


    def program_robot_target(self, job:str, robot_ID_list: list = [0,0]):
        """
            Programs the robot to execute sequance of movements from its' current location to a given target location
        """
        # TODO: Find current robot pose
        # TODO: Find robot location in the operation environment and plan movements dependiging on the surrounding obstacles
        # TODO: HOME the robot arm before starting a program & Plan different movements dependng of the current grabber state

        if job.upper() == "TRANSFER":

            self.logger.info("Executing plate transfer between OT2 ID: {} and OT2 ID: {}".format(robot_ID_list[0],robot_ID_list[1]))
            self.move_single("HomeALL", 2)
            self.pick_plate_ot2(robot_ID_list[0])
            self.drop_plate_ot2(robot_ID_list[1])
            

        elif job.upper() == "FULL_TRANSFER":

            self.logger.info("Executing full transfer")
            self.move_single("HomeALL", 2)
            self.pick_plate_from_rack(1)
            self.drop_plate_ot2(1)
            time.sleep(50)
            self.pick_plate_ot2(1)
            self.drop_plate_ot2(2)
            time.sleep(50)
            self.pick_plate_ot2(2)
            self.drop_plate_ot2(3)
            time.sleep(50)
            self.pick_plate_ot2(3)
            self.drop_complete_plate()

            

    
    def manualy_move_cartesian(self, target_joint):
        """
        A Cartesian location specifies the coordinates of a position in space using X, Y, and Z coordinates, and an orientation of the robot tool using yaw, pitch, and roll angles.
        Depending on the robot kinematics, there may be more than one set of joint angles that puts the robot's gripper at the same Cartesian location.
        """
        pass

    def manualy_move_joints(self, target_joint_location):
        """
        An angles location is a collection of the joint angles for the robot.  
        Joint angles are in units of degrees for rotary axes and in millimeters for linear axes.  
        By moving all joints to the specified values, the robot moves to an unambiguous position and orientation in space.
        """

        pass

    def set_speed(self, speed):

        PF400 = self.connect_robot()

        command = "mspeed" + str(speed) +"\n"
        try:
            PF400.send(bytes(command.encode('ascii')))
            out_msg = PF400.recv(4096).decode("utf-8")
            self.logger.info(out_msg)
        except socket.error as err:
            self.logger.error('Failed to send data: {}'.format(err))
        else:
            self.disconnect_robot(PF400) 

    def locate_robot(self):
        
        PF400 = self.connect_robot()

        command = 'wherej\n'
        # Add ASCII NULL character at the end of the cmd string
        try:
            PF400.send(bytes(command.encode('ascii')))
            location = PF400.recv(4096).decode("utf-8")
            self.logger.info(location)
            # location = "5 6 7 8 9 10"
            coordinate_list = list(map(int,location.split(" ")))

        except socket.error as err:
            self.logger.error('Failed to find robot location: {}'.format(err))
        else:
            self.disconnect_robot(PF400)  

        return coordinate_list

    def teach_location(self, location: str, robot_id:int = None):

        current_location = self.locate_robot()
        try:
            if robot_id == None and (location.lower == "homeall" or location.lower == "homearm" or location.lower == "mobile_robot" or location.lower == "trash") :
            # TODO: Find a better way for this 
                for count, loc in enumerate(self.location_dictionary[location]):
                    self.location_dictionary[location][count] = current_location[count]

            elif robot_id != None:
                if location.upper() == "FRONT":
                    key_name = "OT2_" + str(robot_id) + "_front"
                elif location.upper() == "ABOVE_PLATE":
                    key_name =  "OT2_" + str(robot_id) + "_above_plate"
                elif location.upper() == "PICK_PLATE":
                    key_name = "OT2_" + str(robot_id) + "_pick_plate"
                elif location.upper() == "PLATE_RACK":
                    key_name = "OT2_" + str(robot_id) + "_plate_rack"
            else:
                raise Exception("Please enter a valid location name!!! Format: location: str, robot_id:int = None ")
            
            for count, loc in enumerate(self.location_dictionary[key_name]):
                self.location_dictionary[key_name][count] = current_location[count]        
           
        
        except Exception as err:
            self.logger.error(err)



if __name__ == "__main__":
    robot = PF400()
    # robot.initialize_robot()
    # robot.pick_plate_ot2(1)
    # robot.load_robot_data()
    robot.enable_power()

    #TODO: Return out msg and error code



    # robot.pick_plate_from_rack(1)
    # robot.program_robot_target("full_transfer")
    # robot.move_single("HomeALL")
    # robot.pick_plate_ot2(1)
    # robot.drop_plate_ot2(2)
    # robot.teach_location("HomeALL")
    # robot.teach_location("above_plate",2)


    # try:
    #     while True:
    #         robot.program_robot_target("Transfer",[1,2])
    #         robot.program_robot_target("Transfer",[2,1])
    # except KeyboardInterrupt as err:
    #     print(err)

