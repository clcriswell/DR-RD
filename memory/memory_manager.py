import json
import os
from difflib import SequenceMatcher

class MemoryManager:
    def __init__(self, file_path="memory/project_memory.json"):
        self.file_path = file_path
        # Ensure the memory directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        # Load existing memory data if file exists, otherwise initialize empty list
        try:
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = []
        except json.JSONDecodeError:
            self.data = []
        if not isinstance(self.data, list):
            self.data = []

    def store_project(self, idea, plan, outputs, proposal):
        """Save a completed project (idea, plan, outputs, proposal) to memory."""
        entry = {
            "idea": idea,
            "plan": plan,
            "outputs": outputs,
            "proposal": proposal
        }
        self.data.append(entry)
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def find_similar_ideas(self, idea, top_n=3):
        """Return a list of past project idea strings similar to the given idea."""
        idea_lower = idea.lower()
        similarities = []
        for entry in self.data:
            past_idea = entry.get("idea", "")
            if not past_idea:
                continue
            ratio = SequenceMatcher(None, idea_lower, past_idea.lower()).ratio()
            if ratio > 0.3:
                similarities.append((ratio, past_idea))
        # Sort by similarity score descending and return top N idea strings
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [idea for _, idea in similarities[:top_n]]

    def get_project_summaries(self, similar_ideas_list):
        """Return a combined summary text for a list of idea strings from memory."""
        summaries = []
        for idea_text in similar_ideas_list:
            for entry in self.data:
                if entry.get("idea") == idea_text:
                    proposal = entry.get("proposal", "")
                    summary_text = ""
                    if proposal:
                        text_lower = proposal.lower()
                        idx = text_lower.find("summary")
                        if idx != -1:
                            # Find end of summary section (next heading or about 200 chars)
                            next_heading_idx = text_lower.find("##", idx + 1)
                            if next_heading_idx != -1:
                                summary_text = proposal[idx:next_heading_idx].strip()
                            else:
                                summary_text = proposal[idx: idx + 200].strip()
                        else:
                            summary_text = proposal[:200].strip()
                        if len(proposal) > 200:
                            summary_text += "..."
                    else:
                        summary_text = "(No proposal available)"
                    summaries.append(f"**Idea:** {idea_text}\n**Summary:** {summary_text}")
                    break
        # Join summaries with a blank line between each
        return "\n\n".join(summaries)
