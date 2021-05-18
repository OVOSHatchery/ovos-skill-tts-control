# <img src='./icon.png' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/>  TTS control skill

allows to change or retrieve info about Text to Speech by voice

# usage

* "what is the current voice"
* "available voice engines"
* "text to speech demo"
* "change voice to alan pope"
* "change voice to kusal"
* "change voice to google"
* "change voice to alan black"
* "change voice to female"
* "change voice to richard"
* "change voice to amazon"
* "change voice to whisper"

engines confirmed working: espeak, polly, google, mimic, mimic2

# TODO

- gui integration
- "use that voice" follow up intent (voice demo)
- needs better parsing for untested engines (yandex, bing, ibm) 
- PR fix for responsive voice in mycroft-core

# Platform support

- :heavy_check_mark: - tested and confirmed working
- :x: - incompatible/non-functional
- :question: - untested
- :construction: - partial support

|     platform    |   status   |  tag  | version | last tested | 
|:---------------:|:----------:|:-----:|:-------:|:-----------:|
|    [Chatterbox](https://hellochatterbox.com)   | :question: |  dev  |         |    never    | 
|     [HolmesV](https://github.com/HelloChatterbox/HolmesV)     | :question: |  dev  |         |    never    | 
|    [LocalHive](https://github.com/JarbasHiveMind/LocalHive)    | :question: |  dev  |         |    never    |  
|  [Mycroft Mark1](https://github.com/MycroftAI/enclosure-mark1)    | :question: |  dev  |         |    never    | 
|  [Mycroft Mark2](https://github.com/MycroftAI/hardware-mycroft-mark-II)    | :question: |  dev  |         |    never    |  
|    [NeonGecko](https://neon.ai)      | :question: |  dev  |         |    never    |   
|       [OVOS](https://github.com/OpenVoiceOS)        | :question: |  dev  |         |    never    |    
|     [Picroft](https://github.com/MycroftAI/enclosure-picroft)       | :question: |  dev  |         |    never    |  
| [Plasma Bigscreen](https://plasma-bigscreen.org/)  | :question: |  dev  |         |    never    |  

- `tag` - link to github release / branch / commit
- `version` - link to release/commit of platform repo where this was tested

