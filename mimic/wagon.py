import json
import os
import datetime

class Wagon:
    def __init__(self, run_id):
        self.run_id = run_id
        self.log = []
        self.wagon_dir = "wagon_logs"
        self.sensory = {}
        self.working = {}
        self.longterm = {}

    def sense(self, raw_input):
        self.sensory = {
            "raw": raw_input,
            "timestamp": datetime.datetime.now().isoformat(),
            "processed": False
        }
        self.log.append({"layer": "sensory", "entry": self.sensory})

    def remember(self, key, value):
        self.working[key] = {
            "value": value,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.log.append({"layer": "working", "entry": {key: self.working[key]}})

    def consolidate(self):
        for key, value in self.working.items():
            self.longterm[key] = value
        self.log.append({
            "layer": "consolidation",
            "entry": "working memory consolidated to longterm",
            "timestamp": datetime.datetime.now().isoformat()
        })
        self.working = {}

    def save(self):
        if not os.path.exists(self.wagon_dir):
            os.makedirs(self.wagon_dir)
        filename = f"{self.wagon_dir}/run_{self.run_id}.json"
        data = {
            "run_id": self.run_id,
            "sensory": self.sensory,
            "working": self.working,
            "longterm": self.longterm,
            "log": self.log
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        return filename