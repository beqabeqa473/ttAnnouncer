import addonHandler
import api
import config
import core
import globalPluginHandler
import globalVars
import gui
from NVDAHelper import localLib, _setDllFuncPointer, WINFUNCTYPE, c_long, c_wchar_p
import queueHandler
import re
import scriptHandler 
import speech
import synthDriverHandler
import ui
from .interface import TTAnnouncerSettingsPanel
addonHandler.initTranslation()

CONF_SPEC = {
    "engine": "string(default='')",
    "enabled": "boolean(default=False)",
    "regexTranslation": "boolean(default=True)"
}

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    addonInstance = addonHandler.getCodeAddon()
    addonName = addonInstance.name
    addonSummary = addonInstance.manifest["summary"]
    scriptCategory = addonSummary

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config.conf.spec[self.addonName] = CONF_SPEC
        self.addonConf = config.conf[self.addonName]
        self.enabled = self.addonConf["enabled"]
        self.suppresable = False
        self.origSpeak = speech.speech.speak
        speech.speech.speak = self.localSpeak
        TTAnnouncerSettingsPanel.addonConf = self.addonConf
        TTAnnouncerSettingsPanel.onSaveCallback = self.reloadSynth
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(TTAnnouncerSettingsPanel)
        self.processText = WINFUNCTYPE(c_long,c_wchar_p)(self.processText)
        _setDllFuncPointer(localLib, "_nvdaController_speakText", self.processText)
        core.postNvdaStartup.register(self.initSynth)
        if hasattr(globalVars, self.addonName):
            self.initSynth()
        globalVars.ttAnnouncer = None

    def localSpeak(self, sequence, *args, **kwargs):
        if self.suppresable:
            self.suppresable = False
            return
        return self.origSpeak(sequence, *args, **kwargs)

    def processText(self, text):
        focus=api.getFocusObject()
        if focus.sleepMode==focus.SLEEP_FULL:
            return -1
        msg = re.match(self.chanMsgRe, text) if self.enabled else None
        if msg is not None:
            self.suppresable = True
            queueHandler.queueFunction(queueHandler.eventQueue, self.synthInstance.speak, f"{msg['userName']} - {msg['text']}")
        queueHandler.queueFunction(queueHandler.eventQueue,speech.speakText,text)
        return 0

    def initSynth(self):
        if not self.enabled:
            return
        chanMsg = _("Channel message from") if self.addonConf["regexTranslation"] else "Channel message from"
        self.chanMsgRe = re.compile(f"^{chanMsg} (?P<userName>.*?)[:.] (?P<text>.*)$", flags=re.DOTALL)
        self.synthInstance = synthDriverHandler._getSynthDriver(self.addonConf["engine"])()
        self.synthInstance.initSettings()

    def reloadSynth(self):
        self.terminateSynth()
        self.initSynth()

    def terminateSynth(self):
        if hasattr(self, "synthInstance"):
            self.synthInstance.terminate()
            self.synthInstance = None
            del self.synthInstance

    def terminate(self):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(TTAnnouncerSettingsPanel)
        self.terminateSynth()
        speech.speak = self.origSpeak
        core.postNvdaStartup.unregister(self.initSynth)

    @scriptHandler.script(
        description=_("Stops speech on first press, on second press - toggles addon"),
        gesture="kb:nvda+shift+pause"
    )
    def script_stopSpeechOrToggle(self, gesture):
        if self.addonConf["engine"] == "":
            ui.message(_("Please select desired tts engine before using this addon"))
            return
        if scriptHandler.getLastScriptRepeatCount() == 0:
            if hasattr(self, "synthInstance"):
                self.synthInstance.cancel()
        else:
            self.enabled = not self.enabled
            self.addonConf["enabled"] = self.enabled
            self.initSynth() if self.enabled else self.terminateSynth()
            ui.message(_("TT channel messages will be announced with selected synthesizer in addon settings") if self.enabled else _("TT channel mesages will be announced with main synthesizer"))