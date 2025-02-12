# NVDA Addon: My Calculator 
# Released under the GNU General Public License v2 
# Copyright (C) 2024 - 2025 Andhi Mardianto

import globalPluginHandler
import ui
import re
import api
import tones
import addonHandler
import wx
import gui
from .help import show_calculator_help
from keyboardHandler import KeyboardInputGesture
from scriptHandler import script
addonHandler.initTranslation()

# Variabel global untuk menyimpan referensi dialog
showDialog = None

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super().__init__()

    @script(
        description=_("Open My Calculator dialog"),
        category=_("MyCalculator"),
        gesture="kb:nvda+shift+m"
    )
    def script_start(self, gesture):
        self.run(None)

    def run(self, event):
        global showDialog
        if not showDialog:
            showDialog = MainDialog(gui.mainFrame)
            showDialog.CenterOnScreen()
            showDialog.Raise()
        else:
            showDialog.Raise()

class MainDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="My Calculator", size=(800, 400))

        # Variabel untuk menyimpan riwayat
        self.history = []
        self.calculationMode = "standard"  # Default mode

        # Panel utama untuk elemen dialog
        panel = wx.Panel(self)

        # Layout komponen di dalam dialog
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Panel kiri untuk input dan hasil
        leftSizer = wx.BoxSizer(wx.VERTICAL)

        # Label dan input untuk operasi aritmatika
        leftSizer.Add(wx.StaticText(panel, label=_("Calculation Input")), 0, wx.ALL, 5)
        self.number1 = wx.TextCtrl(panel, size=(350, 25))
        self.number1.SetBackgroundColour("#f0f8ff")
        self.number1.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.number1.Bind(wx.EVT_CHAR_HOOK, self.onKeyPressed)
        self.number1.Bind(wx.EVT_TEXT, self.onTextChanged)
        leftSizer.Add(self.number1, 0, wx.EXPAND | wx.ALL, 5)

        # Label dan input untuk menampilkan hasil
        leftSizer.Add(wx.StaticText(panel, label=_("Result")), 0, wx.ALL, 5)
        self.re = wx.TextCtrl(panel, size=(350, 100), style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY)
        self.re.SetBackgroundColour("#e6ffe6")
        self.re.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        leftSizer.Add(self.re, 1, wx.EXPAND | wx.ALL, 5)

        # Tombol Copy
        copy_button = wx.Button(panel, label=_("Copy"))
        copy_button.Bind(wx.EVT_BUTTON, self.periksa)
        leftSizer.Add(copy_button, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Tombol Standar
        standard_button = wx.Button(panel, label=_("Standar"))
        standard_button.Bind(wx.EVT_BUTTON, self.set_standard_mode)
        leftSizer.Add(standard_button, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Tombol Left to Right
        ltr_button = wx.Button(panel, label=_("Left to Right"))
        ltr_button.Bind(wx.EVT_BUTTON, self.set_left_to_right_mode)
        leftSizer.Add(ltr_button, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Tombol Help
        help_button = wx.Button(panel, label=_("Help"))
        help_button.Bind(wx.EVT_BUTTON, self.show_help)
        leftSizer.Add(help_button, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Panel kanan untuk riwayat
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(wx.StaticText(panel, label=_("History")), 0, wx.ALL, 5)
        self.historyBox = wx.TextCtrl(
            panel, size=(350, 300), style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY
        )
        self.historyBox.SetBackgroundColour("#f7f7f7")
        self.historyBox.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        rightSizer.Add(self.historyBox, 1, wx.EXPAND | wx.ALL, 5)

        # Gabungkan panel kiri dan kanan
        mainSizer.Add(leftSizer, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(rightSizer, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(mainSizer)

        # Bind event untuk Escape
        self.Bind(wx.EVT_CHAR_HOOK, self.close)

        # Fokus ke input saat dialog muncul
        self.Bind(wx.EVT_SHOW, self.tampilkan)

        self.Show()

    def onTextChanged(self, event):
        """Menangani perubahan teks di kotak input."""
        expression = self.number1.GetValue().strip()
        if not expression:
            self.re.SetValue("")  # Kosongkan kotak hasil jika input kosong
        else:
            tones.beep(750, 50)  # Memutar nada beep saat ada input

            # Validasi input untuk hanya mengizinkan angka dan simbol matematika
            if not all(char.isdigit() or char in "+-*/().xX: " for char in expression):
                ui.message(_("Invalid input, only numbers and arithmetic symbols allowed"))
                tones.beep(440, 100)
                self.number1.SetValue(expression[:-1])  # Hapus karakter tidak valid terakhir
                self.number1.SetInsertionPointEnd()  # Set cursor ke akhir teks
        event.Skip()


    def tampilkan(self, event):
        self.number1.SetFocus()

    def close(self, event):
        k = event.GetKeyCode()
        if k == wx.WXK_ESCAPE:
            self.Destroy()
        else:
            event.Skip()

    def onKeyPressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_TAB or keycode == wx.WXK_NUMPAD_ENTER:
            self.hitung()
            self.re.SetFocus()
        elif not event.ShiftDown() and keycode == 61:  # KeyCode 61 adalah '='
            self.hitung()
            self.re.SetFocus()
        else:
            event.Skip()

    def set_standard_mode(self, event):
        """Mengatur mode perhitungan ke Standar Internasional."""
        self.calculationMode = "standard"
        ui.message(_("Calculation mode set to Standard International"))

    def set_left_to_right_mode(self, event):
        """Mengatur mode perhitungan ke Left to Right."""
        self.calculationMode = "left_to_right"
        ui.message(_("Calculation mode set to Left to Right"))

    def show_help(self, event):
        """Menampilkan pesan bantuan."""
        help.show_calculator_help()
        
    def periksa(self, event):
        """Fungsi untuk menyalin hasil ke clipboard."""
        if self.re.GetValue():
            # Salin hasil ke clipboard
            clipboard = wx.Clipboard.Get()
            if clipboard.Open():
                clipboard.SetData(wx.TextDataObject(self.re.GetValue()))
                clipboard.Close()
                ui.message(_("Result copied to clipboard"))
            else:
                ui.message(_("Failed to access clipboard"))
        else:
            ui.message(_("No result to copy"))


    def hitung(self):
        """Logika utama untuk perhitungan berdasarkan mode yang dipilih."""
        expression = self.number1.Value.strip()

        # Jika input kosong, hentikan eksekusi
        if not expression:
            return

        self.re.Value = ""
        expression = re.sub(r"[xX]", "*", expression).replace(":", "/")

        if not all(char.isdigit() or char in "+-*/().= " for char in expression):
            ui.message(_("Invalid input, only numbers and arithmetic symbols allowed"))
            tones.beep(440, 100)
            expression = expression[:-1]
            self.number1.Value = expression
            self.number1.SetInsertionPoint(len(expression))
            return

        try:
            expression = expression.rstrip('=')  # Hapus simbol = dari akhir ekspresi jika ada

            if self.calculationMode == "standard":
                result = eval(expression)
            elif self.calculationMode == "left_to_right":
                result = self.calculate_left_to_right(expression)
            else:
                ui.message(_("Invalid calculation mode"))
                return

            # Jika hasilnya merupakan bilangan bulat (tanpa desimal), tampilkan sebagai bilangan bulat
            result = int(result) if isinstance(result, float) and result.is_integer() else result
            self.re.Value = str(result)

            # Tambahkan input dan hasil akhir ke riwayat
            self.history.insert(0, f"{expression} = {result}")  # Menambahkan perhitungan dan hasil ke riwayat
            self.updateHistoryBox()

            tones.beep(750, 50)
        except:
            self.re.Value = _("Error! Check Input")
            tones.beep(440, 300)

    def calculate_left_to_right(self, expression):
        """Menghitung ekspresi dari kiri ke kanan."""
        tokens = re.split(r'([+\-*/])', expression.replace(' ', ''))
        result = float(tokens[0])

        i = 1
        while i < len(tokens):
            operator = tokens[i]
            next_number = float(tokens[i + 1])

            if operator == '+':
                result += next_number
            elif operator == '-':
                result -= next_number
            elif operator == '*':
                result *= next_number
            elif operator == '/':
                result /= next_number

            i += 2

        return result

    def updateHistoryBox(self):
        """Perbarui tampilan riwayat di kotak riwayat."""
        self.historyBox.Value = "\n".join(self.history)  # Tampilkan seluruh riwayat




