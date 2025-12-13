import wx
from agent import call_agent
from langchain_core.messages import HumanMessage, AIMessage
import threading

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

class ChatbotFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Chatbot", size=(800, 600))
        
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        
        self.conversational_history = []
        
        # Main vertical sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Chat Display Area (Scrolled Window)
        self.chat_display = wx.ScrolledWindow(self.panel, style=wx.VSCROLL)
        self.chat_display.SetScrollRate(5, 5)
        self.chat_display.SetBackgroundColour(wx.Colour(0, 0, 0))
        
        self.chat_sizer = wx.BoxSizer(wx.VERTICAL)
        self.chat_display.SetSizer(self.chat_sizer)
        
        # Add chat display to main sizer (expand to fill available space)
        self.main_sizer.Add(self.chat_display, 1, wx.EXPAND | wx.ALL, 10)
        
        # Input Area
        self.input_box = RoundedTextCtrl(self.panel, on_enter_callback=self.on_user_input, size=(400, 50))
        self.main_sizer.Add(self.input_box, 0, wx.CENTER | wx.BOTTOM, 20)

        # Add initial suggestions
        self.add_suggestions()
        
        self.panel.SetSizer(self.main_sizer)
        
        # Center the frame on screen
        self.Centre()

    def add_suggestions(self):
        texts = [
            "Here are some suggestions",
            "Create a to-do list for tommorow",
            "Make a timetable for the week",
            "Create a quiz for me on cricket",
        ]
        
        for text in texts:
            st = wx.StaticText(self.panel, label=text)
            st.SetForegroundColour(wx.Colour(200, 200, 200)) # Light gray text
            font = st.GetFont()
            font.SetPointSize(12)
            st.SetFont(font)
            self.main_sizer.Add(st, 0, wx.CENTER | wx.TOP, 5)
            
        self.panel.Layout()

    def on_user_input(self, text):
        # Display User Message
        self.add_message(f"User: {text}", wx.Colour(255, 255, 255), wx.ALIGN_RIGHT)
        self.conversational_history.append(HumanMessage(content=text))
        
        # Process with Agent (using a separate thread to keep GUI responsive)
        threading.Thread(target=self.process_agent_response, daemon=True).start()

    def process_agent_response(self):
        try:
            # Call the agent
            response = call_agent(self.conversational_history)
            
            # Update GUI on the main thread
            wx.CallAfter(self.display_agent_response, response)
        except Exception as e:
            wx.CallAfter(self.display_agent_response, f"Error: {str(e)}")

    def display_agent_response(self, response):
        self.add_message(f"AI: {response}", wx.Colour(100, 255, 100), wx.ALIGN_LEFT)
        self.conversational_history.append(AIMessage(content=response))

    def add_message(self, text, color, alignment):
        # Create a container for the message to handle alignment
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        st = wx.StaticText(self.chat_display, label=text)
        st.SetForegroundColour(color)
        st.Wrap(600) # Wrap text to fit within the window width roughly
        
        font = st.GetFont()
        font.SetPointSize(12)
        st.SetFont(font)
        
        if alignment == wx.ALIGN_RIGHT:
            h_sizer.AddStretchSpacer()
            h_sizer.Add(st, 0, wx.ALL, 5)
        else:
            h_sizer.Add(st, 0, wx.ALL, 5)
            h_sizer.AddStretchSpacer()
            
        self.chat_sizer.Add(h_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        
        # Refresh layout and scroll to bottom
        self.chat_display.Layout()
        self.chat_display.FitInside()
        self.chat_display.Scroll(-1, self.chat_display.GetVirtualSize()[1])

if __name__ == "__main__":
    app = wx.App()
    frame = ChatbotFrame()
    frame.Show()
    app.MainLoop()
