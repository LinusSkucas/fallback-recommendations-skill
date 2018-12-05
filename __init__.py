# Copyright 2018 Linus S
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from mycroft.skills.core import FallbackSkill
from mycroft.util import normalize
from mycroft.util.parse import match_one
from mycroft.messagebus.message import Message
from mycroft.skills.skill_manager import SkillManager
import datetime
import time
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
        self.msm = SkillManager.create_msm()
        
    def initialize(self):
        """Register and download the file"""
        self.register_fallback(self.handle_fallback, 17) # Q:why 17? A:Why not?
        ## Setup a event scheduler for auto update
        # Delete any other schedulers that this skill has set up
        try:
            self.cancel_scheduled_event("SkillRecommendationsFallback.auto_refresh.lists")
        except:
            #No event exists: OKAY!
            pass
        # Now create a repeating event, starting now so that it updates now. Updates every 4 hours(14400 seconds=4 hours)
        self.schedule_repeating_event(handler=self._update_lists, when=datetime.datetime.now(), frequency=14400, data=None, name="SkillRecommendationsFallback.auto_refresh.lists")

    def _get_ready(self, utter):
        """Lowercase and normalize any strings get rid of puncuations :)"""
        return normalize(utter, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation})

    def _update_lists(self):
        """Update the example lists"""
        self.log.info("Updating example lists")
        #Download
        data = requests.get(url, allow_redirects=True).json()
        #format
        self.examples_dict = {}
        
        for skill, data in data.items():
            examples = data.get("examples")
            for idx, example in enumerate(examples):
                self.examples_dict[str(self._get_ready(example))] = str(skill)
        self.log.info("Done updating example lists")

    def skill_search(self, utter):
        """Redo with fuzzy mathcing"""
        skill, confidence = match_one(utter, self.examples_dict)
        if confidence >0.5:
            return skill
        else:
            None
    
    def send_ws_utterance(self, utter):
        self.bus.emit(Message("recognizer_utterance", {"utterances": "[{}]".format(utter), "lang":"en-us"})) #TODO: Localize!!

    def install_skill(self, skill):
            skills_data = SkillManager.load_skills_data()
            skill_data = skills_data.setdefault(skill.name, {})
            skill.install()

            #Marketplace Junk - just to update it
            skill_data['beta'] = False
            skill_data['name'] = skill.name
            skill_data['origin'] = 'voice'
            skill_data['installation'] = 'installed'
            skill_data['installed'] = time.time()
            skill_data['failure-message'] = ''
            SkillManager.write_skills_data(skills_data)
        
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
            #install the skill
            skill = self.msm.find_skill(suggested_skill, False)
            self.install_skill(skill)
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
