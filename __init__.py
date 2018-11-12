from mycroft.skills.core import FallbackSkill
from mycroft.util import normalize
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
        
        self.examples_list = []
        
        for key, value in data.items():
            self.examples_list.append({"skill":key, "examples":value.get("examples")})
    
    def skill_search(self, utter):
        for idx, dic in enumerate(self.examples_list):
            for idx, example in enumerate(dic.get("examples")):
                if normalize(example, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation}) == normalize(utter, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation}):
                    return str(dic.get("skill"))
    
    def send_ws_utterance(self, utter):
        self.bus.emit(Message("recognizer_utterance", {"utterances": "[{}]".format(utter), "lang":"en-us"})) #TODO: Localize!!
        

    def handle_fallback(self, message):
        """Find the skill and offer to download it"""
        utter = message.data.get("utterance")
        suggested_skill = self.skill_search(utter)
        self.log.info(str(suggested_skill))
        if suggested_skill == None:
            return False
        else:
            #We can download the skill
            self.speak_dialog("skill.downloading")
            os.system("msm install {}".format(suggested_skill)) #Not sure how this plays with the marketplace thing
            # TODO:  Now have mycroft respond to the utterance
            time.sleep(15) #Wait for the training to be done TODO: THere should be some messagebus thing
            #Downloaded/installed, now replay the utterance
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
