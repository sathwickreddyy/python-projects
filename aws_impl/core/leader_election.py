import time
import socket
import logging

from config import ConfigManager
from redis_manager import RedisManager
from sns_manager import SNSManager

# Configure logging
logging.basicConfig(
    filename="/var/log/leader_election.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class LeaderElection:
    def __init__(self):
        # Fetch configurations from SSM Parameter Store
        config_manager = ConfigManager()

        redis_endpoint = config_manager.get_parameter("/app/config/redis_endpoint")
        sns_topic_arn = config_manager.get_parameter("/app/config/sns_topic_arn")

        if not redis_endpoint or not sns_topic_arn:
            raise Exception("Failed to fetch necessary configuration from SSM.")

        # Initialize managers
        self.instance_id = socket.gethostname()
        self.redis_manager = RedisManager(redis_endpoint)
        self.sns_manager = SNSManager(sns_topic_arn)

    def acquire_leader(self):
        """
        Attempt to become the leader by setting a unique value in Redis.
        """
        return self.redis_manager.acquire_lock("leader", self.instance_id, 10)  # Leader expires in 10 seconds

    def send_heartbeat(self):
        """
        Send periodic heartbeat to indicate this instance is alive.
        """
        self.redis_manager.set_value(f"heartbeat:{self.instance_id}", "alive", 5)  # Heartbeat expires in 5 seconds

    def monitor_leader(self):
        """
        Monitor the current leader's heartbeat. If it fails, attempt to become the new leader.
        """
        while True:
            current_leader = self.redis_manager.get_value("leader")
            if current_leader is None:  # No active leader
                if self.acquire_leader():
                    logging.info(f"{self.instance_id} is elected as the leader!")
                    self.sns_manager.send_message(
                        "Leader Election Notification",
                        f"{self.instance_id} is elected as the leader and will execute critical sections."
                    )
                    self.execute_program()  # Execute polling and code execution as leader
                    return
            elif current_leader.decode() == self.instance_id:
                self.send_heartbeat()  # Maintain leadership by sending heartbeat
            else:
                logging.info(f"{self.instance_id} is a follower. Current leader: {current_leader.decode()}")
                self.sns_manager.send_message(
                    "Follower Notification",
                    f"{self.instance_id} is a follower and did not execute critical sections."
                )
            time.sleep(2)

    def execute_program(self):
        """
        Execute polling and code logic as the leader.
        """
        if self.redis_manager.acquire_lock("program_lock", self.instance_id, 30):  # Lock expires in 30 seconds
            try:
                logging.info(f"{self.instance_id} acquired program lock. Executing critical sections...")
                # Simulate polling and execution logic here (CS1 → CS4)
                time.sleep(10)  # Simulate work for CS1 → CS4
                logging.info(f"{self.instance_id} completed execution.")
                self.sns_manager.send_message(
                    "Execution Success",
                    f"{self.instance_id} successfully completed execution of critical sections."
                )
            except Exception as e:
                logging.error(f"Error during execution: {e}")
                self.sns_manager.send_message(
                    "Execution Error",
                    f"{self.instance_id} encountered an error during execution: {e}"
                )
            finally:
                self.redis_manager.release_lock("program_lock", self.instance_id)
                logging.info(f"{self.instance_id} released program lock.")
                # Clean up leadership after execution
                self.redis_manager.release_lock("leader", self.instance_id)
                logging.info(f"{self.instance_id} relinquished leadership.")
                self.sns_manager.send_message(
                    "Leadership Relinquished",
                    f"{self.instance_id} relinquished leadership after completing execution."
                )
