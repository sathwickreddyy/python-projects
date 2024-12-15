import time
import socket
import logging

from redis_manager import RedisManager

#Configure logging
# logging.basicConfig(
#     filename="/var/log/leader_election.log",
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s"
# )


class LeaderElection:
    def __init__(self, unique_id, ssm_config_manager=None):
        """
        Leader Election Service 
           
        :param unique_id: Could be the API Call Name or something that can be identified as unique across distributed instances. Note this should not be randomly generated
        :param ssm_config_manager: SSM Config Manager
        """
        # Fetch configurations from SSM Parameter Store
        redis_endpoint = ssm_config_manager.get_parameter("/app/config/redis_endpoint")

        if not redis_endpoint:
            raise Exception("Failed to fetch necessary configuration from SSM.")

        # Initialize managers
        self.instance_id = socket.gethostname()
        self.redis_manager = RedisManager(redis_endpoint)
        self.unique_id = unique_id+"_"+self.instance_id
        self.leader_key = unique_id+"_leader"
        self.heartbeat_key = "heartbeat:"+self.leader_key


    def acquire_leader(self):
        """
        Attempt to become the leader by setting a unique value in Redis.
        """
        return self.redis_manager.acquire_lock(self.leader_key, self.unique_id, 120) # acquire lock for 60 seconds

    def send_heartbeats(self):
        """
        Send periodic heartbeat to indicate this instance is alive. until program executes
        """
        current_leader = self.redis_manager.get_value(self.leader_key)
        while current_leader and current_leader.decode() == self.unique_id:
            logging.info(f"Sending heartbeat for {self.unique_id}")
            print(f"Sending heartbeat for {self.unique_id}")
            self.redis_manager.set_value(self.heartbeat_key, "alive", 5)  # Heartbeat expires in 5 seconds
            time.sleep(3)

    def elect_leader(self):
        """
        Elects the leader if not already elected
        :return: current leader
        """
        current_leader = self.redis_manager.get_value(self.leader_key)
        if current_leader is None:  # No active leader
            self.redis_manager.acquire_lock(self.leader_key, self.unique_id, 10) # Leader expires in 10 seconds : Must be more or else duplicate instances will acquire the lock.
            logging.info(f"{self.unique_id} is elected as the leader!")
            print(f"{self.unique_id} is elected as the leader!")
            return self.leader_key
        return self.redis_manager.get_value(self.leader_key)

    def i_am_leader(self):
        return self.redis_manager.get_value(self.leader_key).decode() == self.unique_id

    def monitor_leader(self):
        """
        Monitor the current leader's heartbeat.
        """
        current_leader = self.redis_manager.get_value(self.leader_key).decode()
        heartbeat = self.redis_manager.get_value(f"heartbeat:{current_leader}")
        while current_leader and heartbeat and self.redis_manager.get_value(f"heartbeat:{current_leader}").decode() != "alive":
            print("Waiting for leader to complete execution... - from follower :" + self.unique_id)
            logging.info(f"{self.unique_id} is a follower waiting for current leader: {current_leader.decode()} to complete execution")
            time.sleep(2)

    def cleanup(self):
        # Release locks, etc.
        logging.info("Cleaning & release locks...")
        print("Cleaning & release locks...")
        # Clean up leadership after execution
        self.redis_manager.release_lock(self.leader_key, self.unique_id)
        # Clean up program lock
        self.redis_manager.release_lock(self.leader_key, self.unique_id)
        # delete heartbeat key
        if self.redis_manager.get_value(self.heartbeat_key):
            self.redis_manager.delete(self.heartbeat_key)
        # delete leader key
        if self.redis_manager.get_value(self.leader_key):
            self.redis_manager.delete(self.leader_key)
