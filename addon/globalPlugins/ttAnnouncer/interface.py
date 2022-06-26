import wx

import addonHandler
import gui
import synthDriverHandler
addonHandler.initTranslation()

class TTAnnouncerSettingsPanel(gui.SettingsPanel):
    title = _("tt-announcer")

    def makeSettings(self, settingsSizer):
        sizer = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        synthEngine = _('&Synthesizer engine to use:')
        drivers = synthDriverHandler.getSynthList()
        self.synthNames = [synth[0] for synth in drivers if synth[0] != synthDriverHandler.getSynth().name]
        options = [synth[1] for synth in drivers if synth[0] != synthDriverHandler.getSynth().name]
        self.synthEngineCB = sizer.addLabeledControl(synthEngine, wx.Choice, choices=options)
        try:
            self.synthEngineCB.SetSelection(self.synthNames.index(self.addonConf["engine"]))
        except ValueError:
            self.synthEngineCB.SetSelection(0)
        self.regexTranslationCHK = sizer.addItem(wx.CheckBox(self, label=_("Consider  NVDA locale for regular expressions")))
        self.regexTranslationCHK.SetValue(self.addonConf['regexTranslation'])

    def postInit(self):
        self.synthEngineCB.SetFocus()

    def onSave(self):
        self.addonConf["engine"] = self.synthNames[self.synthEngineCB.GetSelection()]
        self.addonConf["regexTranslation"] = self.regexTranslationCHK.GetValue()
        self.onSaveCallback()
