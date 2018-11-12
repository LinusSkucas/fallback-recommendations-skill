from mycroft.skills.core import FallbackSkill
from mycroft.util import normalize
from msm import 
import string
import requests
import json

#The url to get the data
url = "https://raw.githubusercontent.com/MycroftAI/mycroft-skills-data/18.08/skill-metadata.json"

class SkillRecommendationsFallback(FallbackSkill):
    """A fallback skill to search the mycroft data repo
    if a skill is found, it will be prompted to install it."""

    def __init__(self):
        super(SkillRecommendationsFallback, self).__init__(name='Skill Recommendations Fallback')
        
    def initialize(self):
        """Register and download the file"""
        self.register_fallback(self.handle_fallback, 17) # Q:why 17? A:Why not?
        #Download
        data = requests.get(url, allow_redirects=True).json()
        
        self.examples_list = []
        
        for key, value in data.items():
            self.examples_list.append({"skill":key, "examples":value.get("examples")})
    
    def skill_search(self, utter):
        for idx, dic in enumerate(self.examples_list):
            for idx, example in enumerate(dic.get("examples")):
                if normalize(example, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation}) == normalize(utter, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation}):
                    return str(dic.get("skill"))
    
    def handle_fallback(self, message):
        """Find the skill and offer to download it"""
        utter = message.data.get("utterance")
        suggested_skill = self.skill_search(utter)
        self.log.error(str(suggested_skill))
        if suggested_skill == None:
            return False
        else:
            #We can download the skill

            return True
        
        def shutdown(self):
            """Remove skill from list of skills"""
            self.remove_fallback(self.handle_fallback)
            super(SkillRecommendationsFallback, self).shutdown()

def create_skill():
    return SkillRecommendationsFallback()
