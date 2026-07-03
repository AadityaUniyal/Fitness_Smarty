from locust import HttpUser, task, between

class SmartyFitnessLoadTester(HttpUser):
    """
    Locust load testing script to test backend API throughput limits.
    Run command: locust -f locustfile.py
    """
    wait_time = between(1, 2.5)

    @task(3)
    def view_dashboard(self):
        """Simulate loading the main Mission Control dashboard view."""
        self.client.get("/api/users/user-1/recommendations")

    @task(2)
    def view_exercise_library(self):
        """Simulate browser searching through exercises library."""
        self.client.get("/api/exercises")

    @task(1)
    def query_cycle_insights(self):
        """Simulate loading FemmeCare cycle insights panels."""
        self.client.get("/api/female/cycle-phase/1")

    @task(1)
    def check_telemetry_metrics(self):
        """Simulate Prometheus scraping metrics details."""
        self.client.get("/api/extensions/metrics")
