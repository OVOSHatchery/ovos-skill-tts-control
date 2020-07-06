# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

import tempfile
from itertools import chain
from os.path import join, exists
import random
from adapt.intent import Intent, IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler, \
    intent_file_handler
from mycroft.messagebus import Message
from mycroft.skills.skill_data import read_vocab_file
from mycroft.configuration import LocalConf, USER_CONFIG
from mycroft.tts import TTSFactory
from mycroft.tts.mimic_tts import BIN as MIMIC_BIN
from mycroft.util import resolve_resource_file
from mycroft.util.audio_utils import play_audio_file
from mycroft.util.parse import match_one
from text2speech import TTSFactory as _TTS


class TTSSkill(MycroftSkill):

    def __init__(self):
        super(TTSSkill, self).__init__("TTSControl")
        self.voices = {}
        self.voice_configs = {}
        self.voice_demo = {}
        self._in_use = False
        self.default_male = ("mimic", "ap")
        self.default_female = ("mimic", "slt")
        self.selected_voice = (None, None)

    def initialize(self):
        self.validate_voices()
        self.selected_voice = (self.current_engine, self.current_voice)

    # internal helpers
    def validate_voices(self):
        for clazz in TTSFactory.CLASSES:
            if clazz in self.voices:
                continue
            try:
                mycroft_config = self.config_core["tts"].get(clazz, {})
                mycroft_config["lang"] = self.lang
                config = {"module": clazz,
                          "lang": self.lang,
                          clazz: mycroft_config}

                # TODO maybe extract describe_voices from chatterbox package
                #  to avoid requirement, ideally changes from text2speech
                #  package should be ported to mycroft-core
                tts = _TTS.create(config)
                voice_data = tts.describe_voices()
                #self.log.debug("VOICES - " + clazz + " : " + str(voice_data))
                names = voice_data.get(self.lang) or \
                        voice_data.get(self.lang.split("-")[0])

                for voice in names:
                    config[clazz]["voice"] = voice
                    if clazz == "mimic":
                        config["bin"] = MIMIC_BIN
                    try:
                        tts = TTSFactory.CLASSES.get(clazz)(self.lang,
                                                            config[clazz])
                        path = join(tempfile.gettempdir(),
                                    clazz + "." + voice + ".voice_demo." + tts.audio_ext)
                        text = self.dialog_renderer.render("voice",
                                                           {"clazz": clazz,
                                                            "voice": voice})
                        if not exists(path):
                            tts.get_tts(text.format(name=voice, clazz=clazz),
                                        path)
                        if clazz not in self.voices:
                            self.voices[clazz] = []
                        self.voices[clazz] += [voice]
                        self.voice_configs[clazz + "." + voice] = config
                        self.voice_demo[clazz + "." + voice] = path
                    except Exception as e:
                        continue
            except Exception as e:
                self.log.info("TTS " + clazz + " does not seem to be "
                                                "available or is incorrectly configured")
        self.log.info("VOICES - " + str(self.voices))

    def get_voc(self, voc_filename):
        # Check for both skill resources and mycroft-core resources
        voc = self.find_resource(voc_filename + '.voc', 'vocab')
        if not voc:  # Check for vocab in mycroft core resources
            voc = resolve_resource_file(join('text', self.lang,
                                             voc_filename + '.voc'))

        if not voc or not exists(voc):
            raise FileNotFoundError(
                'Could not find {}.voc file'.format(voc_filename))
        # load vocab and flatten into a simple list
        vocab = read_vocab_file(voc)
        return list(chain(*vocab))

    @property
    def current_engine(self):
        return self.config_core["tts"]["module"]

    @property
    def current_voice(self):
        tts = self.config_core["tts"][self.current_engine]
        return tts.get("voice") or tts.get("lang") or self.lang

    @property
    def available_engines(self):
        return list(self.voices)

    @property
    def available_voices(self):
        voices = []
        for k in self.voices:
            voices += self.voices[k]
        return [v.lower().strip() for v in voices]

    def _message_to_engine(self, message):
        module = None
        voice = None
        # fuzzy match for first pass
        if not voice or not engine:
            words = message.data["utterance"].split(" ")
            for w in words:
                _voice, vscore = match_one(w, self.available_voices)
                if vscore >= 0.8:
                    voice = _voice
                _engine, escore = match_one(w, self.available_engines)
                if escore >= 0.8:
                    module = _engine

        # match .voc files for module name aliases
        if message.data.get("espeak") or message.data.get("espeakVoices") or \
                message.data.get("whisper") or message.data.get("croak"):
            module = "espeak"
            if message.data.get("espeakVoices"):
                voice = message.data["espeakVoices"].replace(" ", "") \
                    .replace("female", "f").replace("male", "m")
            elif message.data.get("croak"):
                voice = "croak"
            elif message.data.get("whisper"):
                voice = "whisper"
            elif message.data.get("female"):
                voice = "f1"
            elif message.data.get("male"):
                voice = "m1"
        elif message.data.get("google"):
            module = "google"
        elif message.data.get("mimic") or message.data.get("ap") or \
                message.data.get("kal") or message.data.get("rms") or \
                message.data.get("awb") or message.data.get("mimicVoicesMale") \
                or message.data.get("mimicVoicesFemale"):
            module = "mimic"
            voice = "ap"
            if message.data.get("ap"):
                voice = "ap"
            elif message.data.get("kal"):
                voice = "kal"
            elif message.data.get("awb"):
                voice = "awb"
            elif message.data.get("rms"):
                voice = "rms"
            elif message.data.get("mimicVoicesMale"):
                voice = message.data.get("mimicVoicesMale")
            elif message.data.get("mimicVoicesFemale"):
                voice = message.data.get("mimicVoicesFemale")
            elif message.data.get("female"):
                voices = self.get_voc("mimicVoicesFemale")
                voice = random.choice(voices)
            elif message.data.get("male"):
                voices = self.get_voc("mimicVoicesMale")
                voice = random.choice(voices)
        elif message.data.get("mimic2") or \
                message.data.get("mimic2VoicesMale"):
            module = "mimic2"
            # TODO mimic2VoicesFemale once a new voice is released
            # TODO handle self hosted mimic instances with custom voices
            if message.data.get("mimic2VoicesMale"):
                voices = self.get_voc("mimic2VoicesMale")
                voice = random.choice(voices)
        elif message.data.get("ibm"):
            module = "ibm"
            # TODO dont have key to test and finish implementing
            # module will match but voice will not until .voc is added
        elif message.data.get("polly") or \
                message.data.get("pollyVoicesFemale") or \
                message.data.get("pollyVoicesMale"):
            module = "polly"
            if message.data.get("pollyVoicesFemale"):
                voice = message.data.get("pollyVoicesFemale")
            elif message.data.get("pollyVoicesMale"):
                voice = message.data.get("pollyVoicesMale")
            elif message.data.get("female"):
                voices = self.get_voc("pollyVoicesFemale")
                voice = random.choice(voices)
            elif message.data.get("male"):
                voices = self.get_voc("pollyVoicesMale")
                voice = random.choice(voices)
        elif message.data.get("bing"):
            module = "bing"
            # TODO dont have key to test and finish implementing
            # module will match but voice will not until .voc is added
        elif message.data.get("yandex"):
            module = "yandex"
            # TODO dont have key to test and finish implementing
            # module will match but voice will not until .voc is added
        elif message.data.get("mary"):
            module = "mary"
            # TODO dont have key to test and finish implementing
            # module will match but voice will not until .voc is added
        elif message.data.get("responsivevoice"):
            # TODO PR for mycroft-core, responsivevoice is borked
            # it is fixed in text2speech from hellochatterbox
            module = "responsivevoice"
            if message.data.get("female"):
                voice = "female"
            if message.data.get("male"):
                voice = "male"

        if module is None and message.data.get("female"):
            module, voice = self.default_female
        elif module is None and message.data.get("male"):
            module, voice = self.default_male
        return module, voice

    # intents
    @intent_handler(IntentBuilder("VoiceDemo")
                    .require("DemoKeyword")
                    .one_of("TTSKeyword", "VoiceKeyword")
                    .optionally("engine"))
    def handle_demo_tts_intent(self, message):
        self._in_use = True
        self.validate_voices()
        for engine in self.voices:
            self.set_context("TTSModule", engine)
            for voice in self.voices[engine]:
                # pre generated on load
                self.set_context("TTSVoice", voice)
                path = self.voice_demo[engine + "." + voice]
                self.selected_voice = (engine, voice)
                play_audio_file(path).wait()
                if not self._in_use:
                    self.speak_dialog("demo.cancel")
                    return  # abort demo, signaled by stop
        self._in_use = False
        self.selected_voice = (self.current_engine, self.current_voice)
        # TODO use context to allow "use that voice"

    @intent_handler(IntentBuilder("CurrentTTS")
                    .require("CurrentKeyword")
                    .one_of("TTSKeyword", "VoiceKeyword")
                    .optionally("engine"))
    def handle_current_module_intent(self, message):
        self.speak_dialog("engine.current", {"engine": self.current_engine})
        self.speak_dialog("voice.current", {"voice": self.current_voice})

    @intent_handler(IntentBuilder("AvailableTTS").require("AvailableKeyword")
                    .one_of("TTSKeyword", "VoiceKeyword")
                    .optionally("engine"))
    def handle_available_modules_intent(self, message):
        self._in_use = True
        self.validate_voices()
        self.speak_dialog("engine.available")
        for module in self.available_engines:
            self.speak(module, wait=True)
            if not self._in_use:
                return  # abort speech, signaled by stop
        self._in_use = False


    @intent_handler(IntentBuilder("ChangeTTS")
                    .require("ChangeKeyword")
                    .one_of("TTSKeyword", "VoiceKeyword")
                    # engine requested
                    .optionally("engine").optionally("google")
                    .optionally("mimic").optionally("mimic2")
                    .optionally("mary").optionally("polly").optionally("ibm")
                    .optionally("yandex").optionally("responsivevoice")
                    .optionally("espeak")
                    # voice requested
                    .optionally("ap").optionally("kal")
                    .optionally("rms").optionally("awb")
                    .optionally("mimicVoicesMale")
                    .optionally("mimicVoicesFemale")
                    .optionally("pollyVoicesMale")
                    .optionally("pollyVoicesFemale")
                    .optionally("mimic2VoicesMale")
                    .optionally("espeakVoices").optionally("croak")
                    .optionally("whisper").optionally("female")
                    .optionally("male"))
    def handle_change_module_intent(self, message):
        self.validate_voices()
        module, voice = self._message_to_engine(message)
        # ask user if engine not explicit
        if not module:
            self.speak_dialog("engine.select", wait=True)
            module = self.ask_selection(self.available_engines)

            # fuzzy match transcription in case STT wasnt perfect
            if module is not None and module not in self.available_engines:
                words = message.data["utterance"].split(" ")
                for w in words:
                    _voice, vscore = match_one(w, self.available_voices)
                    if vscore >= 0.8:
                        voice = _voice
                    _engine, escore = match_one(w, self.available_engines)
                    if escore >= 0.8:
                        module = _engine

        # pick default voice if None selected
        if module is not None and voice is None and module in self.voices:
            self.log.debug("Default voice for engine " + module)
            voice = self.voices[module][0]

        # check if abort is needed
        if module is not None and module not in self.available_engines:
            self.speak_dialog("engine.invalid", {"engine": module})
            self.speak_dialog("check.config")
            return
        if module is None:
            self.speak_dialog("noengine")
            return
        self.log.info("Selected TTS engine: " + str(module))
        self.log.info("Selected TTS voice: " + str(voice))
        self.change_voice(module, voice)

    def change_voice(self, engine, voice):
        self.selected_voice = (engine, voice)
        if engine == "polly":
            voice = voice.capitalize()
        tts_config = self.config_core.get("tts", {})
        tts_config["module"] = engine
        if engine not in tts_config:
            tts_config[engine] = {}
        tts_config[engine]["voice"] = voice
        tts_config[engine]["lang"] = self.lang

        config = LocalConf(USER_CONFIG)
        config["tts"] = tts_config
        config.store()
        self.bus.emit(Message("configuration.updated"))
        self.speak_dialog("engine.changed",
                          {"engine": engine, "voice":voice})


    def stop(self):
        if self._in_use:
            self._in_use = False
            return True
        return False

def create_skill():
    return TTSSkill()
