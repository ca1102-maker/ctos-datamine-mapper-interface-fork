import json
import os
from datetime import datetime, date

class DataManager:
    """
    Manages saving and loading of training data to daily JSON files.
    """
    def __init__(self, data_dir="training_data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_filename(self, date_obj=None):
        """Generates the filename for training data based on a specific date."""
        if date_obj is None:
            date_obj = date.today()
        return os.path.join(self.data_dir, f"training_data_{date_obj.strftime('%Y%m%d')}.json")
    
    def save_entry(self, data):
        """Appends a single training data entry to today's file."""
        filename = self.get_filename()
        
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content: # Check if file is not empty
                        existing_data = json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_data = []
        
        existing_data.append(data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, default=str)
    
    def load_data(self, date_obj=None):
        """Loads all training data for a specific date."""
        filename = self.get_filename(date_obj)
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def get_statistics(self):
        """Calculates and returns statistics for today's training data."""
        today_data = self.load_data()
        
        stats = {
            'entries_today': len(today_data),
            'total_queries': len(set(entry.get('query', '') for entry in today_data)),
            'avg_confidence': 0.0,
            'quality_distribution': {}
        }
        
        if today_data:
            # --- MODIFIED: Access nested 'feedback' dictionary for statistics ---
            feedback_list = [entry.get('feedback', {}) for entry in today_data]
            
            # Calculate average user confidence
            confidence_map = {'Very Confident': 4, 'Confident': 3, 'Somewhat Confident': 2, 'Not Confident': 1}
            confidences = [
                confidence_map.get(fb.get('confidence', 'Not Confident'), 1)
                for fb in feedback_list
            ]
            if confidences:
                stats['avg_confidence'] = round(sum(confidences) / len(confidences), 2)
            
            # Calculate distribution of overall quality ratings
            qualities = [fb.get('overall_quality', 'Unknown') for fb in feedback_list]
            stats['quality_distribution'] = {q: qualities.count(q) for q in set(qualities)}
        
        return stats

# Convenience function to be called from other modules
def save_training_data(data):
    """Saves a single training data entry using the DataManager."""
    manager = DataManager()
    manager.save_entry(data)