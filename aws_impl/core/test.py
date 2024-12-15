import threading
from application import ApplicationLogic
from leader_election import LeaderElection
import logging

if __name__ == '__main__':
    leader_election = LeaderElection("some_api_call")
    application_logic = ApplicationLogic()
    leader_election.elect_leader()
    response = ""
    if leader_election.i_am_leader():
        try:
            # create a thread which sends heartbeat every five seconds
            threading.Thread(target=leader_election.send_heartbeats, daemon=True).start()
            application_logic.execute()
        except Exception as e:
            logging.error(f"Leader encountered an error during execution: {e}")
        finally:
            leader_election.cleanup()
    else:
        # followers must wait for leader to complete execution
        leader_election.monitor_leader()