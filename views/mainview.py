""" Main view for paired comparison tool. """

###########
# Imports #
###########
# Import GUI packages
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


#########
# BEGIN #
#########
class MainFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Initialize varibales
        self.chkbtn_toggle = False

        # Populate frame with widgets
        self.draw_widgets()


    def draw_widgets(self):
        """ Populate the main view with all widgets
        """
        ##########
        # Styles #
        ##########
        style = ttk.Style()
        style.configure('B.TLabel', font=("", 20))
        style.configure('trial.TLabel', font=("", 20))
        style.configure('start.TButton', font=("", 20), foreground='green')
        style.configure('B.TButton', font=("", 20))
        style.configure('B.TLabelframe.Label', font=("", 20), foreground='blue')
        style.configure('B.TLabelframe', font=("", 20), foreground='blue')
        style.configure('B.TCheckbutton', font=("", 20))


        #################
        # Create frames #
        #################
        options = {'padx':10, 'pady':10}

        # Main container
        frm_main = ttk.Frame(self)
        frm_main.grid(column=5, row=5, **options)

        # Instructions frame
        lfrm_instruct = ttk.LabelFrame(frm_main, text="Instructions",
            style='B.TLabelframe', width=500, height=150)
        lfrm_instruct.grid(row=5, column=5)
        lfrm_instruct.grid_propagate(0)

        # Selection button frame
        self.frm_select_btn = ttk.Frame(frm_main)
        self.frm_select_btn.grid(row=10, column=5)

        # Next button frame
        frm_next_btn = ttk.Frame(frm_main)
        frm_next_btn.grid(row=15, column=5)


        ##################
        # Create Widgets #
        ##################
        # Instructions label
        msg = "Welcome! Please wait for the investigator to start the task."
        self.text_var = tk.StringVar(value=msg)
        lbl_display = ttk.Label(lfrm_instruct, textvariable=self.text_var,
            style='B.TLabel', wraplength=470, justify='left')
        lbl_display.grid(row=5, column=5, pady=10, padx=10)

        # Canvas
        # self.canvas = tk.Canvas(lfrm_instruct) #276 width=490, height=225
        # self.canvas.grid(row=10, column=5, sticky='we')
        #
        # self.canvas = tk.Canvas(lfrm_instruct, width=259, height=192, bg='blue')
        #self.canvas = tk.Canvas(lfrm_instruct, width=490, height=215)
        #self.canvas.grid(row=10, column=5)

        # Snapshot tk buttons
        self.btn_A = tk.Button(self.frm_select_btn, text="A",
            command=lambda: self.on_A(), state='disabled',
            width=2, font=('TkDefaultFont', 30), bg='grey73',
            activebackground='green3')
        self.btn_A.grid(row=10, column=5, padx=40, pady=20)

        self.btn_B = tk.Button(self.frm_select_btn, text="B",
            command=lambda: self.on_B(), state='disabled',
            width=2, font=('TkDefaultFont', 30), bg='grey73',
            activebackground='green3')
        self.btn_B.grid(row=10, column=10, padx=40, pady=20)


        # Uncomment the Checkbutton to offer a "No Difference"
        # option. The logic is already in place. Snapshot is 
        # returned as "same". 
        self.chkbtn_state = tk.IntVar(value=0)
        self.chkbtn_no_diff = ttk.Checkbutton(
            self.frm_select_btn, text="No Difference", onvalue=1, offvalue=0,
            variable=self.chkbtn_state, takefocus=0, state='disabled',
            command=self.no_difference, style='B.TCheckbutton')
        self.chkbtn_no_diff.grid(row=15, column=5, columnspan=20)

        # Separator
        sep = ttk.Separator(frm_main, orient='horizontal')
        sep.grid(row=12, column=0, columnspan=40, pady=(20,10), sticky='ew')

        # Submit button
        self.btn_submit = ttk.Button(frm_next_btn, text="Submit", 
            command=self._on_submit, takefocus=0, style='B.TButton',
            state='disabled')
        self.btn_submit.grid(row=5, column=5)


    #############
    # Functions #
    #############
    def on_A(self):
        # Update buttons for visual feedback
        self._select_btn('A')
        self._unselect_btn('B')
        self.chkbtn_state.set(0)
        self.update_idletasks()

        # Send call to update snapshot
        self.event_generate('<<MainViewA>>')


    def on_B(self):
        # Update buttons for visual feedback
        self._select_btn('B')
        self._unselect_btn('A')
        self.chkbtn_state.set(0)
        self.update_idletasks()

        # Send call to update snapshot
        self.event_generate('<<MainViewB>>')


    def _select_btn(self, btn):
        """ Update button appearance to indicate selection
        """
        if btn == 'A':
            self.btn_A.config(relief='sunken')
            self.btn_A.config(bg='green3')
            self._unselect_btn('B')
        elif btn == 'B':
            self.btn_B.config(relief='sunken')
            self.btn_B.config(bg='green3')
            self._unselect_btn('A')

        # Reset "no difference" checkbutton
        self.chkbtn_state.set(0)

        self.update_idletasks()


    def _unselect_btn(self, btn):
        """ Update button appearance to normal system state
        """
        if btn == 'A':
            self.btn_A.config(relief='raised')
            self.btn_A.config(bg='grey73')
        elif btn == 'B':
            self.btn_B.config(relief='raised')
            self.btn_B.config(bg='grey73')


    def no_difference(self):
        """ Unselect both A/B buttons when checkbutton 
            is selected. Send event to controller.
        """
        if self.chkbtn_state.get() == 1:
            self._unselect_btn('A')
            self._unselect_btn('B')
            self.update_idletasks()

            # Send event to controller
            self.event_generate('<<MainViewNoDiff>>')
        elif self.chkbtn_state.get() == 0:
            pass


    def toggle_nodiff_chkbtn(self):
        if not self.chkbtn_toggle:
            self.chkbtn_state.set(1)
            self.no_difference()
            self.chkbtn_toggle = True
        elif self.chkbtn_toggle:
            self.chkbtn_state.set(0)
            self.chkbtn_toggle = False


    def enable_widgets(self):
        self.btn_submit.config(state='enabled')
        self.btn_A.config(state='normal')
        self.btn_B.config(state='normal')
        self.chkbtn_no_diff.config(state='enabled')
        self.update_idletasks()


    def _on_submit(self):
        """ Reset buttons and start next trial.
        """
        # Check for no answer
        self.update_idletasks() # Get all button states
        if (str(self.btn_A['relief'])=='raised') and \
            (str(self.btn_B['relief'])=='raised') and \
            (self.chkbtn_state.get()==0):
            print("\nmainview: Please select a response first!")
            messagebox.showerror(title="Missing Response",
                message="No response provided!",
                detail="Please provide a response before continuing. "
            )
            return

        # Reset button appearance
        self._unselect_btn('A')
        self._unselect_btn('B')
        self.chkbtn_state.set(0)
        self.update_idletasks()

        # Disable NEXT button
        #self.btn_submit.config(state='disabled')

        # Send event to controller
        self.event_generate('<<MainViewNext>>')
