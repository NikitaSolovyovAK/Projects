import json
import os


class Leaderboard:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.records = []
        self.load()

    def load(self):
        if not os.path.exists(self.file_path):
            self.records = []
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                self.records = data
            else:
                self.records = []

        except (json.JSONDecodeError, OSError):
            self.records = []

        self.sort_records()

    def save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(self.records, file, ensure_ascii=False, indent=4)

    def sort_records(self):
        self.records.sort(
            key=lambda record: record.get("score", 0),
            reverse=True,
        )

    def add_record(self, name: str, score: int):
        self.records.append({
            "name": name,
            "score": score,
        })
        self.sort_records()
        self.records = self.records[:10]
        self.save()

    def get_best_score(self):
        if not self.records:
            return 0
        return self.records[0].get("score", 0)