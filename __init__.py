from mycroft.skills.core import FallbackSkill
from mycroft.util import normalize
from mycroft.util.parse import match_one
from mycroft.messagebus.message import Message
import os
import time
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
        
        self.examples_dict = {}
        
        for skill, data in data.items():
            examples = data.get("examples")
            for idx, example in enumerate(examples):
                self.examples_dict[str(self._get_ready(example))] = str(skill)

    def _get_ready(self, utter):
        """Lowercase and normalize any strings get rid of puncuations"""
        return normalize(utter, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation})

    def skill_search(self, utter):
        """Redo with fuzzy mathcing"""
        skill, confidence = match_one(utter, self.examples_dict)
        if confidence >0.5:
            return skill
        else:
            None
    
    def send_ws_utterance(self, utter):
        self.bus.emit(Message("recognizer_utterance", {"utterances": "[{}]".format(utter), "lang":"en-us"})) #TODO: Localize!!
        
    def handle_fallback(self, message):
        """Find the skill and offer to download it"""
        utter = message.data.get("utterance")
        suggested_skill = self.skill_search(self._get_ready(utter))
        self.log.info(str(suggested_skill))
        if suggested_skill == None:
            return False
        else:
            #We can download the skill
            self.speak_dialog("skill.downloading")
            os.system("msm install {}".format(suggested_skill)) #Not sure how this plays with the marketplace thing
            # TODO:  Now have mycroft respond to the utterance
            time.sleep(15) #Wait for the training to be done TODO: THere should be some messagebus thing
            #Downloaded/installed, now replay the utterance NEED To fix!
            #self.send_ws_utterance(utter)

            #In the meantime, just say the user can say that again.
            self.speak_dialog("done.downloading")
            return True
        
        def shutdown(self):
            """Remove skill from list of skills"""
            self.remove_fallback(self.handle_fallback)
            super(SkillRecommendationsFallback, self).shutdown()

def create_skill():
    return SkillRecommendationsFallback()
