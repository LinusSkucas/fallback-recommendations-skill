from mycroft.skills.core import FallbackSkill
from mycroft.filesystem import FileSystemAccess
from mycroft.util import normalize
import requests

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
        r = requests.get(url, allow_redirects=True)
        self.write_file_bytes("skills_data.json", r.content)
        
        #TODO: Do we really need to write this to a file?
        self.log.info("Loading examples for fallback")
        data = self.read_file("skills_data.json")
        data = json.loads(self.data)
        
        self.examples_list = []
        
        for key, value in self.examples_list.items():
            self.examples_list.append({"skill":key, "examples":value.get("examples")})
    
    def read_file(self, filename):
        fs = FileSystemAccess(str(self.skill_id))
        data_file = fs.open(filename, "r")
        data = data_file.read()
        data_file.close()
        return data

    def write_file_bytes(self, filename, data):
        fs = FileSystemAccess(str(self.skill_id))
        data_file = open(filename, 'wb')
        data_file.write(data)
        data_file.close()
        return True
    
    def skill_search(utter):
        for idx, dic in enumerate(self.examples_list):
            for idx, example in enumerate(dic.get("examples")):
                if example.normalize(remove_articles=True) == utter.normalize(remove_articles=True):
                    return str(dic.get("skill"))
    
    def handle_fallback(self, message):
        """Find the skill and offer to download it"""
        utter = message.data.get("utterance")
        suggested_skill = self.skill_search(utter)
        if suggested_skill == None:
            return False
        else:
            #We can download the skill
            pass
        
        def shutdown(self):
            """Remove skill from list of skills"""
            self.remove_fallback(self.handle_fallback)
            super(SkillRecommendationsFallback, self).shutdown()

def create_skill():
    return SkillRecommendationsFallback()
