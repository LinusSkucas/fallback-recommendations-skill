from mycroft import MycroftSkill, intent_file_handler


class FallbackRecommendations(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('recommendations.fallback.intent')
    def handle_recommendations_fallback(self, message):
        self.speak_dialog('recommendations.fallback')


def create_skill():
    return FallbackRecommendations()

