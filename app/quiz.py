import wx
from gemini_functions import Gemini
import sys
import time
import json
class RoundedTextCtrl(wx.Panel):
    def __init__(self, parent, on_enter_callback, size=(300, 40)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.on_enter_callback = on_enter_callback
      
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER | wx.BORDER_NONE)
        # Grayish black background for the text control itself
        self.text_ctrl.SetBackgroundColour(wx.Colour(40, 40, 40)) 
        self.text_ctrl.SetForegroundColour(wx.Colour(255, 255, 255)) # White text
        
        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.text_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)
        
        # Layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10) # Padding for "oval" look
        self.SetSizer(self.sizer)

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        
        # Set the background of the panel to match the parent (Black) so corners look transparent
        # We assume the parent has a black background. If not, this might need adjustment.
        dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0)))
        dc.Clear()
        
        # Draw oval/rounded background
        gc = wx.GraphicsContext.Create(dc)
        if gc:
            # Grayish black fill for the oval
            gc.SetBrush(wx.Brush(wx.Colour(40, 40, 40)))
            gc.SetPen(wx.Pen(wx.Colour(60, 60, 60), 1)) # Slightly lighter border
            
            w, h = self.GetSize()
            # Draw a rounded rectangle with high radius to look like an oval/pill
            gc.DrawRoundedRectangle(0, 0, w, h, h/2) 

    def OnSize(self, event):
        self.Layout()
        self.Refresh()

    def OnEnter(self, event):
        text = self.text_ctrl.GetValue()
        if text.strip():
            self.text_ctrl.Clear()
            self.on_enter_callback(text)

class QuizFrame(wx.Frame):
    def __init__(self,res):
        super().__init__(None, title="Quiz", size=(800, 600))
        self.res = res
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(0, 0, 0)) # Dark background
        self.gemini = Gemini()
        self.i = 0
        self.score = 0
        # Main vertical sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Text Display Area
        self.display_area = wx.ScrolledWindow(self.panel, style=wx.VSCROLL)
        self.display_area.SetScrollRate(5, 5)
        self.display_area.SetBackgroundColour(wx.Colour(0, 0, 0))
        
        self.display_sizer = wx.BoxSizer(wx.VERTICAL)
        self.display_area.SetSizer(self.display_sizer)
        
        # Add display area to main sizer (expand to fill available space)
        self.main_sizer.Add(self.display_area, 1, wx.EXPAND | wx.ALL, 20)
        
        # Input Area (Curved Textbox)
        self.input_box = RoundedTextCtrl(self.panel, on_enter_callback=self.on_user_input, size=(400, 50))
        self.main_sizer.Add(self.input_box, 0, wx.CENTER | wx.BOTTOM, 20)
        
        self.panel.SetSizer(self.main_sizer)
        
        # Center the frame on screen
        self.Centre()
        
        # Add some initial text
        self.add_text("Welcome to the Quiz! Answer with the choice of number 1,2,3,4", wx.Colour(255, 255, 255), 18) # Gold color
        self.add_text("Question 1:", wx.Colour(255, 255, 255), 18) 
        self.add_text(self.res[self.i]['question'], wx.Colour(255, 255, 255), 12)
        self.add_text("Options: ", wx.Colour(255, 255, 255), 18) 
        for option in self.res[self.i]['answers']:
            self.add_text(option, wx.Colour(255, 255, 255), 12)
    def add_text(self, text, color=wx.Colour(255, 255, 255), font_size=12):
        st = wx.StaticText(self.display_area, label=text)
        st.SetForegroundColour(color)
        st.Wrap(700) # Wrap text
        
        font = st.GetFont()
        font.SetPointSize(font_size)
        st.SetFont(font)
        
        self.display_sizer.Add(st, 0, wx.BOTTOM | wx.LEFT, 10)
        
        # Refresh layout and scroll to bottom
        self.display_area.Layout()
        self.display_area.FitInside()
        self.display_area.Scroll(-1, self.display_area.GetVirtualSize()[1])
    def extract_option_number(self,inp):
        return self.gemini.extract_option_number(inp,self.res[self.i]['answers'])
    def on_user_input(self, text):
        self.add_text(f"Your Answer: {text}", wx.Colour(144, 238, 144))
        option_number  = self.extract_option_number(text)
        print(option_number)
        if self.res[self.i]['answers'][int(option_number)-1] == self.res[self.i]['correct_answer']:
            self.score += 1
        #self.add_text(f"System: Received '{text}'", wx.Colour(100, 255, 100))
        self.i = self.i+1
        if self.i < len(self.res):
            self.add_text(f"Question {self.i+1}: ", wx.Colour(255, 255, 255), 18) 
            self.add_text(self.res[self.i]['question'], wx.Colour(255, 255, 255), 12)
            self.add_text("Options: ", wx.Colour(255, 255, 255), 18) 
            for option in self.res[self.i]['answers']:
                self.add_text(option, wx.Colour(255, 255, 255), 12)
        else:
            self.add_text("Quiz Over!", wx.Colour(144, 238, 144), 18)
            #self.add_text(f"Your score is {self.score}", wx.Colour(144, 238, 144), 18)
            
            with open('data/score.txt','w') as f:
                f.write(str(self.score) + " " + str(self.score/len(self.res)*100))
            time.sleep(2)
            sys.exit(0)
def open_quiz_window(questions):
    app = wx.App()
    frame = QuizFrame(questions)
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    open_quiz_window(json.load(open('data/questions.json','r')))
