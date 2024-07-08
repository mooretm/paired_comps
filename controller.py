""" Paired Comparison Tool.

    Tool for collecting paired comparison data over headphones. 
    Recordings must be in WAV format, and specified in the 
    matrix file.

    Written by: Travis M. Moore
    Created: February 02, 2024
"""

###########
# Imports #
###########
# Import GUI packages
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

# Import system packages
from pathlib import Path
import os

# Import misc packages
import webbrowser
import markdown

# Import custom modules
# Menu imports
from menus import mainmenu
# Exception imports
from exceptions import audio_exceptions
# Model imports
from models import sessionmodel
from models import versionmodel
from models import audiomodel
from models import calmodel
from models import csvmodel
from models import stimulusmodel
# View imports
from views import mainview
from views import sessionview
from views import audioview
from views import calibrationview
# Image imports
from app_assets import images
# Help imports
from app_assets import README


#########
# BEGIN #
#########
class Application(tk.Tk):
    """ Application root window
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #############
        # Constants #
        #############
        self.NAME = 'Paired Comparison Tool'
        self.VERSION = '0.1.2'
        self.EDITED = 'February 08, 2024'

        # Create menu settings dictionary
        self._app_info = {
            'name': self.NAME,
            'version': self.VERSION,
            'last_edited': self.EDITED
        }


        ######################################
        # Initialize Models, Menus and Views #
        ######################################
        # Setup main window
        self.withdraw() # Hide window during setup
        self.resizable(False, False)
        self.title(self.NAME)
        self.taskbar_icon = tk.PhotoImage(
            file=images.LOGO_FULL_PNG
            )
        self.iconphoto(True, self.taskbar_icon)

        # Assign special quit function on window close
        # Used to close Vulcan session cleanly even if 
        # user closes window via "X"
        self.protocol('WM_DELETE_WINDOW', self._quit)

        # Start with an invalid response
        self.response = 999

        # Load current session parameters from file
        # or load defaults if file does not exist yet
        # Check for version updates and destroy if mandatory
        self.sessionpars_model = sessionmodel.SessionParsModel(self._app_info)
        self._load_sessionpars()

        # Load CSV writer model
        self.csvmodel = csvmodel.CSVModel(self.sessionpars)

        # Load calibration model
        self.calmodel = calmodel.CalModel(self.sessionpars)

        # Load main view
        self.main_frame = mainview.MainFrame(self)
        self.main_frame.grid(row=5, column=5)

        # Trial counter label
        self.trial_var = tk.StringVar(value="Trial:")
        ttk.Label(self, textvariable=self.trial_var, 
            style='B.TLabel').grid(row=10, column=5, sticky='w', 
            padx=20, pady=(0,10))

        # Load menus
        self.menu = mainmenu.MainMenu(self, self._app_info)
        self.config(menu=self.menu)

        # Create callback dictionary
        event_callbacks = {
            # File menu
            '<<FileSession>>': lambda _: self._show_session_dialog(),
            '<<FileStart>>': lambda _: self.start_task(),
            '<<FileQuit>>': lambda _: self._quit(),

            # Tools menu
            '<<ToolsAudioSettings>>': lambda _: self._show_audio_dialog(),
            '<<ToolsCalibration>>': lambda _: self._show_calibration_dialog(),

            # Help menu
            '<<HelpREADME>>': lambda _: self._show_help(),
            '<<HelpChangelog>>': lambda _: self._show_changelog(),

            # Session dialog commands
            '<<SessionSubmit>>': lambda _: self._save_sessionpars(),

            # Calibration dialog commands
            '<<CalPlay>>': lambda _: self.play_calibration_file(),
            '<<CalStop>>': lambda _: self.stop_audio(),
            '<<CalibrationSubmit>>': lambda _: self._calc_offset(),

            # Audio dialog commands
            '<<AudioDialogSubmit>>': lambda _: self._save_sessionpars(),

            # Main View commands
            '<<MainViewA>>': lambda _: self._on_A(),
            '<<MainViewB>>': lambda _: self._on_B(),
            '<<MainViewNext>>': lambda _: self._on_submit(),
            '<<MainViewNoDiff>>': lambda _: self._on_no_diff(),
        }

        # Bind callbacks to sequences
        for sequence, callback in event_callbacks.items():
            self.bind(sequence, callback)

        """ Temporarily disable help menu until ready. """
        self.menu.help_menu.entryconfig('README...', state='disabled')
        #self.menu.help_menu.entryconfig('Change Log...', state='disabled')


        # Center main window
        self.center_window()

        # Check for updates
        if (self.sessionpars['check_for_updates'].get() == 'yes') and \
        (self.sessionpars['config_file_status'].get() == 1):
            _filepath = self.sessionpars['version_lib_path'].get()
            u = versionmodel.VersionChecker(_filepath, self.NAME, self.VERSION)
            if u.status == 'mandatory':
                messagebox.showerror(
                    title="New Version Available",
                    message="A mandatory update is available. Please install " +
                        f"version {u.new_version} to continue.",
                    detail=f"You are using version {u.app_version}, but " +
                        f"version {u.new_version} is available."
                )
                self.destroy()
            elif u.status == 'optional':
                messagebox.showwarning(
                    title="New Version Available",
                    message="An update is available.",
                    detail=f"You are using version {u.app_version}, but " +
                        f"version {u.new_version} is available."
                )
            elif u.status == 'current':
                pass
            elif u.status == 'app_not_found':
                messagebox.showerror(
                    title="Update Check Failed",
                    message="Cannot retrieve version number!",
                    detail=f"'{self.NAME}' does not exist in the version library."
                 )
            elif u.status == 'library_inaccessible':
                messagebox.showerror(
                    title="Update Check Failed",
                    message="The version library is unreachable!",
                    detail="Please check that you have access to Starfile."
                )


    #####################
    # General Functions #
    #####################
    def center_window(self):
        """ Center the root window 
        """
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = screen_width/2 - size[0]/2
        y = screen_height/2 - size[1]/2
        self.geometry("+%d+%d" % (x, y))
        self.deiconify()


    def _update_trial_label(self):
        """ Update the trial count label.
        """
        self.trial_var.set(f"Trial {self.trial_counter+1} of " + 
            f"{self.matrix.shape[0]}")
        self.update_idletasks()


    def _quit(self):
        """ Exit the application.
        """
        self.destroy()


    ###################
    # File Menu Funcs #
    ###################
    def start_task(self):
        """ Create trial counter.
            Disable "Start Task" from file menu.
            Bind keys to response functions.
            Create stimulus model.
            Present first trial.
        """
        # Create trial counter
        self.trial_counter = 0

        # Disable "Start Task" from File menu
        self.menu.file_menu.entryconfig('Start Task', state='disabled')

        # Bind keys to main_frame response functions
        self.bind('1', lambda event: self.main_frame.on_A())
        self.bind('2', lambda event: self.main_frame.on_B())
        self.bind('7', lambda event: self.main_frame.toggle_nodiff_chkbtn())
        self.bind('<Return>', lambda event: self.main_frame._on_submit())

        # Create stimulus model
        try:
            self.stimmodel = stimulusmodel.StimulusModel(self.sessionpars)
        except FileNotFoundError:
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find matrix file!",
                detail="Go to File>Session to specify a valid matrix file path."
            )
            return

        # Get matrix of trials
        self.matrix = self.stimmodel.matrix
        print('\n', self.matrix)

        # Update trial label
        self._update_trial_label()

        # Update instructions label
        self._set_instructions()

        # Update canvas image
        #self._set_image()

        # Enable NEXT button on mainview
        #self.main_frame.btn_next.config(state='enabled')
        self.main_frame.enable_widgets()

        # Start with "A"
        self.main_frame._select_btn('A')
        self._on_A()


    ########################
    # Main View Functions #
    ########################
    def _on_A(self):
        """ Set response value to 'A'.
        """
        self.response = "A"
        print(f"\ncontroller: Button A was selected")
        
        # Present trial        
        # Convert db level to scaling factor
        # Updates sessionpars
        self._calc_level(self.matrix.iloc[self.trial_counter, 2])

        print(f"controller: A: playing {os.path.basename(self.matrix.iloc[self.trial_counter, 0])}")
        self.present_audio(
            audio=Path(self.matrix.iloc[self.trial_counter, 0]),
            pres_level=self.sessionpars['adjusted_level_dB'].get()
        )


    def _on_B(self):
        """ Set response value to 'B'.
        """
        self.response = "B"
        print(f"\ncontroller: Button B was selected")
        
        # Present trial        
        # Convert db level to scaling factor
        # Updates sessionpars
        self._calc_level(self.matrix.iloc[self.trial_counter, 2])

        print(f"controller: B: playing {os.path.basename(self.matrix.iloc[self.trial_counter, 1])}")
        self.present_audio(
            audio=Path(self.matrix.iloc[self.trial_counter, 1]),
            pres_level=self.sessionpars['adjusted_level_dB'].get()
        )


    def _on_no_diff(self):
        self.response = "no_diff"
        print(f"\ncontroller: No difference was selected")
        

    def _set_instructions(self):
        """ Get the next set of instructions from the master 
            stimulus list.
        """
        # Get instructions
        instructions = self.matrix.iloc[self.trial_counter, 3]
        self.main_frame.text_var.set("")
        self.main_frame.text_var.set(instructions)


    def _set_image(self):
        """ Get the next image file from the master stimulus list.
        """
        img_path = Path(self.matrix.iloc[self.trial_counter, 4])
                        
        img = Image.open(img_path)
        #img = img.resize((259, 192))
        img = img.resize((500, 215))
        self.img = ImageTk.PhotoImage(img)

        # Display image
        #self.main_frame.canvas.create_image(0, 0, anchor='nw', image=self.img)
        self.main_frame.canvas.delete("all")
        self.main_frame.canvas.create_image(490/2, 215/2, anchor='center', image=self.img)
        self.update_idletasks()      


    def _on_submit(self):
        """ Increase trial counter.
            Assign response value and save to file.
            Present next trial.
        """
        # Save the trial data
        self._save_trial_data()
        
        # Increase trial counter
        self.trial_counter += 1

        # Present trial
        if self.trial_counter < self.matrix.shape[0]:
            # Update trial label
            self._update_trial_label()

            # Update instructions label
            self._set_instructions()

            # Update canvas image
            #self._set_image()

            # Start next trial
            # Or they can just click a button to start...
            # Start with "A"
            self.main_frame._select_btn('A')
            self._on_A()
        else:
            print("\ncontroller: Task complete! Goodbye!")
            messagebox.showinfo(
                title="Task Complete",
                message="Please let the investigator know you have " +
                    "finished the task!"
            )
            self.destroy()
            return


    def _save_trial_data(self):
        """ Select data to save and send to csv model.
        """
        # Get tk variable values
        converted = dict()
        for key in self.sessionpars:
            converted[key] = self.sessionpars[key].get()

        converted['trial'] = self.trial_counter + 1
        converted['category'] = self.matrix.iloc[self.trial_counter, 5]
        converted['audio_A'] = os.path.basename(self.matrix.iloc[self.trial_counter, 0])
        converted['audio_B'] = os.path.basename(self.matrix.iloc[self.trial_counter, 1])
        
        if self.response == 'A':
            converted['selected'] = converted['audio_A']
        elif self.response == 'B':
            converted['selected'] = converted['audio_B']
        elif self.response == 'no_diff':
            converted['selected'] = self.response

        # Define selected items for writing to file
        save_list = ['trial', 'subject', 'condition', 'audio_A', 'audio_B',
            'selected', 'category', 'slm_reading', 'cal_level_dB', 
            'slm_offset', 'adjusted_level_dB', 'desired_level_dB',
            'randomize', 'repetitions']

        # Create new dict with desired items
        try:
            data = dict((k, converted[k]) for k in save_list)
        except KeyError as e:
            print('\ncontroller: Unexpected variable when attempting ' +
                  f'to save: {e}')
            messagebox.showerror(
                title="Undefined Variable",
                message="Data not saved!",
                detail=f'{e} is undefined.'
            )
            self.destroy()
            return

        # Write data to file
        print('controller: Calling save record function...')
        try:
            self.csvmodel.save_record(data)
        except PermissionError as e:
            print(e)
            messagebox.showerror(
                title="Access Denied",
                message="Data not saved! Cannot write to file!",
                detail=e
            )
            #self.destroy()
            return
        except OSError as e:
            print(e)
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find file or directory!",
                detail=e
            )
            return


    ############################
    # Session Dialog Functions #
    ############################
    def _show_session_dialog(self):
        """ Show session parameter dialog
        """
        print("\ncontroller: Calling session dialog...")
        sessionview.SessionDialog(self, self.sessionpars)


    def _load_sessionpars(self):
        """ Load parameters into self.sessionpars dict 
        """
        vartypes = {
        'bool': tk.BooleanVar,
        'str': tk.StringVar,
        'int': tk.IntVar,
        'float': tk.DoubleVar
        }

        # Create runtime dict from session model fields
        self.sessionpars = dict()
        for key, data in self.sessionpars_model.fields.items():
            vartype = vartypes.get(data['type'], tk.StringVar)
            self.sessionpars[key] = vartype(value=data['value'])
        print("\ncontroller: Loaded sessionpars model fields into " +
            "running sessionpars dict")


    def _save_sessionpars(self, *_):
        """ Save current runtime parameters to file 
        """
        print("\ncontroller: Calling sessionpars model set and save funcs")
        for key, variable in self.sessionpars.items():
            self.sessionpars_model.set(key, variable.get())
            self.sessionpars_model.save()


    ########################
    # Tools Menu Functions #
    ########################
    def _show_audio_dialog(self):
        """ Show audio settings dialog
        """
        print("\ncontroller: Calling audio dialog...")
        audioview.AudioDialog(self, self.sessionpars)

    def _show_calibration_dialog(self):
        """ Display the calibration dialog window
        """
        print("\ncontroller: Calling calibration dialog...")
        calibrationview.CalibrationDialog(self, self.sessionpars)


    ################################
    # Calibration Dialog Functions #
    ################################
    def play_calibration_file(self):
        """ Load calibration file and present
        """
        # Get calibration file
        try:
            self.calmodel.get_cal_file()
        except AttributeError:
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find internal calibration file!",
                detail="Please use a custom calibration file."
            )
        # Present calibration signal
        self.present_audio(
            audio=Path(self.calmodel.cal_file), 
            pres_level=self.sessionpars['cal_level_dB'].get()
        )


    def _calc_offset(self):
        """ Calculate offset based on SLM reading.
        """
        # Calculate new presentation level
        self.calmodel.calc_offset()
        # Save level - this must be called here!
        self._save_sessionpars()


    def _calc_level(self, desired_spl):
        """ Calculate new dB FS level using slm_offset.
        """
        # Calculate new presentation level
        self.calmodel.calc_level(desired_spl)
        # Save level - this must be called here!
        self._save_sessionpars()


    #######################
    # Help Menu Functions #
    #######################
    def _show_help(self):
        """ Create html help file and display in default browser
        """
        print(f"\ncontroller: Calling README file (will open in browser)")
        # Read markdown file and convert to html
        with open(README.README_MD, 'r') as f:
            text = f.read()
            html = markdown.markdown(text)

        # Create html file for display
        with open(README.README_HTML, 'w') as f:
            f.write(html)

        # Open README in default web browser
        webbrowser.open(README.README_HTML)


    def _show_changelog(self):
        """ Create html help file and display in default browser
        """
        print(f"\ncontroller: Calling CHANGELOG file (will open in browser)")
        # Read markdown file and convert to html
        with open(README.CHANGELOG_MD, 'r') as f:
            text = f.read()
            html = markdown.markdown(text)

        # Create html file for display
        with open(README.CHANGELOG_HTML, 'w') as f:
            f.write(html)

        # Open README in default web browser
        webbrowser.open(README.CHANGELOG_HTML)

    ###################
    # Audio Functions #
    ###################
    def present_audio(self, audio, pres_level, **kwargs):
        # Load audio
        try:
            self._create_audio_object(audio, **kwargs)
        except audio_exceptions.InvalidAudioType as e:
            messagebox.showerror(
                title="Invalid Audio Type",
                message="The audio type is invalid!",
                detail=f"{e} Please provide a Path or ndarray object."
            )
            return
        except audio_exceptions.MissingSamplingRate as e:
            messagebox.showerror(
                title="Missing Sampling Rate",
                message="No sampling rate was provided!",
                detail=f"{e} Please provide a Path or ndarray object."
            )
            return

        # Play audio
        self._play(pres_level)


    def _create_audio_object(self, audio, **kwargs):
        # Create audio object
        try:
            self.a = audiomodel.Audio(
                audio=audio,
                **kwargs
            )
        except FileNotFoundError:
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find the audio file!",
                detail="Go to File>Session to specify a valid audio path."
            )
            self._show_session_dialog()
            return
        except audio_exceptions.InvalidAudioType:
            raise
        except audio_exceptions.MissingSamplingRate:
            raise


    def _play(self, pres_level):
        """ Format channel routing, present audio and catch 
            exceptions.
        """
        # Attempt to present audio
        try:
            self.a.play(
                level=pres_level,
                device_id=self.sessionpars['audio_device'].get(),
                routing=self._format_routing(
                    self.sessionpars['channel_routing'].get())
            )
        except audio_exceptions.InvalidAudioDevice as e:
            print(e)
            messagebox.showerror(
                title="Invalid Device",
                message="Invalid audio device! Go to Tools>Audio Settings " +
                    "to select a valid audio device.",
                detail = e
            )
            # Open Audio Settings window
            self._show_audio_dialog()
        except audio_exceptions.InvalidRouting as e:
            print(e)
            messagebox.showerror(
                title="Invalid Routing",
                message="Speaker routing must correspond with the " +
                    "number of channels in the audio file! Go to " +
                    "Tools>Audio Settings to update the routing.",
                detail=e
            )
            # Open Audio Settings window
            self._show_audio_dialog()
        except audio_exceptions.Clipping:
            print("controller: Clipping has occurred! Aborting!")
            messagebox.showerror(
                title="Clipping",
                message="The level is too high and caused clipping.",
                detail="The waveform will be plotted when this message is " +
                    "closed for visual inspection."
            )
            self.a.plot_waveform("Clipped Waveform")


    def stop_audio(self):
        try:
            self.a.stop()
        except AttributeError:
            print("\ncontroller: Stop called, but there is no audio object!")


    def _format_routing(self, routing):
        """ Convert space-separated string to list of ints
            for speaker routing.
        """
        routing = routing.split()
        routing = [int(x) for x in routing]

        return routing


if __name__ == "__main__":
    app = Application()
    app.mainloop()
