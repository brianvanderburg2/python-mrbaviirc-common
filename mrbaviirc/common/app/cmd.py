"""
This module provides for a simple command-line application supporting
subcommands.  A class is provided as a base for the application, along
with methdos to register arguments, and a class is provided as the base
for a command to be executed.  Any derived class from the applications
command class will automatically be used as an available command.
"""


class Command(object):
    """ Base class for a command. """

    command_name=None
    """ The name of the command as used on the command line. """

    command_desc=None
    """ The description of the command to be used by the parser. """

    def __init__(self, app):
        """
        Initialize the command. 
        Derived classes should not generally override this.
        """

        self.app = None
        """ Reference to the application instances. """
    
    def add_args(self, parser):
        """ Add arguments to the parser. """
        pass

    def run(self):
        """ Run the command. """

    @staticmethod
    def find_subclasses(cls=None, result=None):
        """
        Find all subclasses of a particular class. 

        Todo:

            This should be a separate utility function.
        """
        
        if cls is None:
            cls = Command

        if result is None:
            result = []

        subclasses = cls.__subclasses__()
        result.extend(subclasses)

        for subclass in subclasses:
            Command.find_subclasses(subclass, result)
        
        return result

    


class App(object):
    """ Represent our application object. """
    app_desc=None
    app_cmd_class=Command

    def __init__(self):
        """
            Basic initialization for the application.
            A derived class should not generally override this.
        """

        self.args = None
        """ A result of the parsed arguments. """

        self.commands = {}
        """ A result of all found commands. """

    def add_args(self, parser):
        """ Allow for adding common args before command args """
        pass

    def init(self):
        """ Perform common initialization before executing command. """
        pass

    def run(self):
        """ execute the command. """
        pass

    def cleanup(self):
        """ Perform cleanup. """
        pass

    def execute(self):
        """ Run the application. """
        import argparse

        # Argument parser
        parser = argparse.ArgumentParser(description=self.app_desc)
        self.add_args(parser)

        # Determine available commands
        cmd_classes = Command.find_subclasses(self.app_cmd_class)
        if cmd_classes:
            subparsers = parser.add_subparsers(dest="command")
            for cmd_class in cmd_classes:
                cmd = cmd_class(self)
                cmd_parser = subparsers.add_parser(cmd.command_name,
                                                   description=cmd.command_desc)
                cmd.add_args(cmd_parser)

                self.commands[cmd.command_name] = cmd

        # Parse the arguments
        self.args = parser.parse_args()

        # Run the application
        self.init()

        if cmd_classes:
            cmd = self.commands[self.args.command]
            cmd.run()
        else:
            self.run()
        self.cleanup()


""" Example usage::
    
    class Speak(Command):
        cmd_name="speak"
        cmd_desc="Say some words."

        def add_args(self, parser):
            parser.add_argument("words")

        def run(self):
            print("Speaking: {0}".format(str(self.app.args.words)))


    class Eat(Command):
        cmd_name="eat"
        cmd_desc="Eat some food."

        def add_args(self, parser):
            parser.add_argument("food")

        def run(self):
            print("Eating: {0}".format(str(self.app.args.food)))

    class MyApp(App):
        pass

    app = MyApp()
    app.execute()


    CLI:

    myapp speak hello
    myapp speak goodbye
    myapp eat steak
    myapp eat salad

"""
