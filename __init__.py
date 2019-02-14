# Copyright 2019 Linus S (LinusS1)
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

# The url to get the data
url = "https://raw.githubusercontent.com/MycroftAI/mycroft-skills-data/18.08/skill-metadata.json"


class SkillRecommendationsFallback(FallbackSkill):
    """A fallback skill to search the mycroft data repo
    if a skill is found, it will be prompted to install it."""

    def __init__(self):
        super(SkillRecommendationsFallback, self).__init__(name='Skill Recommendations Fallback')
        self.msm = SkillManager.create_msm()

    def initialize(self):
        """Register and download the file"""
        self.register_fallback(self.handle_fallback, 17)  # Q:why 17? A:Why not?
        # Add installation event
        self.add_event('mycroft.skills.loaded', self.handle_skill_loaded)
        ## Setup a event scheduler for auto update
        # Delete any other schedulers that this skill has set up
        try:
            self.cancel_scheduled_event("SkillRecommendationsFallback.auto_refresh.lists")
        except:
            # No event exists: OKAY!
            pass
        # Now create a repeating event, starting now so that it updates now. Updates every 4 hours(14400 seconds=4 hours
        self.schedule_repeating_event(handler=self.update_lists, when=datetime.datetime.now(), frequency=14400,
                                      data=None, name="SkillRecommendationsFallback.auto_refresh.lists")

    def _get_ready(self, utter):
        """Lowercase and normalize any strings get rid of puncuations :)"""
        return normalize(utter, remove_articles=True).lower().translate({ord(c): None for c in string.punctuation})

    def handle_skill_loaded(self, message):
        skill_id = message.data.get("id")
        skill_id = skill_id[0:skill_id.find(".")]
        if skill_id == str(self.settings.get("install_skill")):  # TODO: strip off the endings
            time.sleep(5)
            # notify installation is done!
            self.settings["install_skill"] == ""
            self.send_utterance(str(self.settings.get("utter")))
            self.settings["utter"] == ""

    def update_lists(self):
        """Update the example lists"""
        self.log.info("Updating example lists")
        # Download
        data = requests.get(url, allow_redirects=True).json()
        # format
        self.examples_dict = {}

        for skill, data in data.items():
            examples = data.get("examples")
            for idx, example in enumerate(examples):
                self.examples_dict[str(self._get_ready(example))] = (str(skill), str(data.get("title")))
        self.log.info("Done updating example lists")

    def skill_search(self, utter):
        """Redo with fuzzy mathcing"""
        skill, confidence = match_one(utter, self.examples_dict)
        if confidence > 0.5:
            return skill
        else:
            return None

    def send_utterance(self, utter):
        self.bus.emit(Message("recognizer_loop:utterance",
                              {'utterances': ["{}".format(utter)], 'lang': 'en-us'}))  # TODO: localize

    def install_skill(self, skill):
        skills_data = SkillManager.load_skills_data()
        skill_data = skills_data.setdefault(skill.name, {})
        skill.install()

        # Marketplace Junk - just to update it
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
        search = self.skill_search(self._get_ready(utter))
        suggested_skill = search[0]
        skill_title = search[1].lower().replace("skill", "")
        # Get rid of any "Skill" in the title
        self.log.info(str(suggested_skill))
        if suggested_skill is None:
            return False
        else:
            # We can download the skill

            self.settings["install_skill"] = suggested_skill
            self.settings["utter"] = utter
            self.settings.store()
            # install the skill
            skill = self.msm.find_skill(suggested_skill, False)
            # if it is already installed, return false: we can't help
            if skill.is_local:
                return False
            # Confirmation
            confirmation = self.ask_yesno("skill.download.confirmation", data={"skill_name": skill_title})
            if confirmation != "yes":
                self.speak_dialog("skill.download.refused")  # TODO: Should the skill say anything else? or:
                return False  # TODO: Should this be True to keep it from going through all the other skills?

            self.speak_dialog("skill.downloading", data={"skill_name": skill_title})
            self.install_skill(skill)
            return True

    def shutdown(self):
        """Remove skill from list of skills"""
        self.remove_fallback(self.handle_fallback)
        super(SkillRecommendationsFallback, self).shutdown()


def create_skill():
    return SkillRecommendationsFallback()
